CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS agent_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_code TEXT NOT NULL UNIQUE,
  agent_name TEXT NOT NULL,
  language_code TEXT NOT NULL DEFAULT 'ru',
  system_prompt TEXT NOT NULL,
  guardrails JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'draft')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_sources (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL CHECK (source_type IN ('txt', 'pdf', 'xlsx', 'manual', 'web')),
  title TEXT NOT NULL,
  source_path TEXT,
  raw_text TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id UUID NOT NULL REFERENCES knowledge_sources(id) ON DELETE CASCADE,
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  chunk_order INTEGER NOT NULL DEFAULT 0,
  chunk_text TEXT NOT NULL,
  tokens_est INTEGER,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  search_tsv tsvector GENERATED ALWAYS AS (to_tsvector('russian', coalesce(chunk_text, ''))) STORED,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (source_id, chunk_order)
);

CREATE TABLE IF NOT EXISTS script_templates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  script_code TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  objective TEXT NOT NULL,
  opening_text TEXT,
  closing_text TEXT,
  cta_text TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'draft')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (agent_id, script_code, version)
);

CREATE TABLE IF NOT EXISTS script_steps (
  id BIGSERIAL PRIMARY KEY,
  template_id UUID NOT NULL REFERENCES script_templates(id) ON DELETE CASCADE,
  step_order INTEGER NOT NULL,
  step_name TEXT NOT NULL,
  step_goal TEXT NOT NULL,
  example_phrase TEXT,
  required BOOLEAN NOT NULL DEFAULT TRUE,
  exit_condition TEXT,
  next_step_hint TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (template_id, step_order)
);

CREATE TABLE IF NOT EXISTS objection_playbook (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  objection_key TEXT NOT NULL,
  trigger_patterns TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  response_strategy TEXT NOT NULL,
  example_response TEXT NOT NULL,
  do_not_say TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (agent_id, objection_key)
);

CREATE TABLE IF NOT EXISTS compliance_rules (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  rule_code TEXT NOT NULL,
  rule_type TEXT NOT NULL CHECK (rule_type IN ('deny_phrase', 'mandatory_phrase', 'checklist')),
  rule_text TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'high' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (agent_id, rule_code)
);

-- Non-PII client reference card.
CREATE TABLE IF NOT EXISTS client_memory_refs (
  client_ref TEXT PRIMARY KEY,
  primary_source_system TEXT NOT NULL CHECK (primary_source_system IN ('google_drive', 'google_sheets', 'crm', 'manual', 'api')),
  primary_locator TEXT NOT NULL,
  tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'archived')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Link to external data source row/file. PII stays outside Postgres.
CREATE TABLE IF NOT EXISTS client_source_links (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_ref TEXT NOT NULL REFERENCES client_memory_refs(client_ref) ON DELETE CASCADE,
  external_system TEXT NOT NULL CHECK (external_system IN ('google_drive', 'google_sheets', 'crm', 'manual', 'api')),
  external_locator TEXT NOT NULL,
  record_key TEXT NOT NULL,
  source_status TEXT NOT NULL DEFAULT 'active' CHECK (source_status IN ('active', 'archived', 'error')),
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (external_system, external_locator, record_key)
);

CREATE TABLE IF NOT EXISTS call_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  client_ref TEXT REFERENCES client_memory_refs(client_ref) ON DELETE SET NULL,
  task_id BIGINT,
  provider_call_id TEXT,
  channel TEXT NOT NULL DEFAULT 'phone' CHECK (channel IN ('phone', 'telegram', 'whatsapp', 'webchat')),
  direction TEXT NOT NULL DEFAULT 'outbound' CHECK (direction IN ('inbound', 'outbound')),
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  ended_at TIMESTAMPTZ,
  outcome TEXT,
  outcome_reason TEXT,
  summary_redacted TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Save only redacted text to keep DB non-PII.
CREATE TABLE IF NOT EXISTS call_turns (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES call_sessions(id) ON DELETE CASCADE,
  turn_index INTEGER NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool', 'reviewer')),
  utterance_redacted TEXT NOT NULL,
  intent TEXT,
  sentiment TEXT,
  pii_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
  latency_ms INTEGER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, turn_index)
);

-- Full audit log of assistant actions.
CREATE TABLE IF NOT EXISTS assistant_action_log (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID REFERENCES call_sessions(id) ON DELETE CASCADE,
  agent_id UUID REFERENCES agent_profiles(id) ON DELETE SET NULL,
  action_type TEXT NOT NULL CHECK (
    action_type IN (
      'load_instructions',
      'fetch_client_context',
      'save_client_update_request',
      'llm_request',
      'llm_response',
      'tool_call',
      'policy_check',
      'handoff',
      'error'
    )
  ),
  action_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  status TEXT NOT NULL DEFAULT 'ok' CHECK (status IN ('ok', 'warning', 'error')),
  error_text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Structured durable memory for non-PII facts learned from calls.
CREATE TABLE IF NOT EXISTS memory_facts (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  client_ref TEXT REFERENCES client_memory_refs(client_ref) ON DELETE SET NULL,
  session_id UUID REFERENCES call_sessions(id) ON DELETE SET NULL,
  fact_key TEXT NOT NULL,
  fact_value TEXT NOT NULL,
  confidence NUMERIC(5,2) NOT NULL DEFAULT 0.50 CHECK (confidence >= 0 AND confidence <= 1),
  source_type TEXT NOT NULL DEFAULT 'call' CHECK (source_type IN ('call', 'manual', 'sync')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS call_quality_reviews (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID NOT NULL UNIQUE REFERENCES call_sessions(id) ON DELETE CASCADE,
  reviewer TEXT NOT NULL,
  score_total NUMERIC(5,2) NOT NULL CHECK (score_total >= 0 AND score_total <= 100),
  score_opening NUMERIC(5,2),
  score_qualification NUMERIC(5,2),
  score_product_pitch NUMERIC(5,2),
  score_objection_handling NUMERIC(5,2),
  score_compliance NUMERIC(5,2),
  score_next_step NUMERIC(5,2),
  strengths TEXT,
  weaknesses TEXT,
  recommendations TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS training_samples (
  id BIGSERIAL PRIMARY KEY,
  agent_id UUID NOT NULL REFERENCES agent_profiles(id) ON DELETE CASCADE,
  session_id UUID REFERENCES call_sessions(id) ON DELETE SET NULL,
  sample_type TEXT NOT NULL CHECK (sample_type IN ('good_reply', 'bad_reply', 'rewrite', 'policy')),
  input_text TEXT NOT NULL,
  expected_output TEXT NOT NULL,
  policy_tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  approved BOOLEAN NOT NULL DEFAULT FALSE,
  approved_by TEXT,
  approved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_sources_agent ON knowledge_sources(agent_id, is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_agent ON knowledge_chunks(agent_id, is_active);
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_tsv ON knowledge_chunks USING GIN (search_tsv);
CREATE INDEX IF NOT EXISTS idx_script_templates_agent ON script_templates(agent_id, status);
CREATE INDEX IF NOT EXISTS idx_objection_playbook_agent ON objection_playbook(agent_id);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_agent ON compliance_rules(agent_id, severity);
CREATE INDEX IF NOT EXISTS idx_client_source_links_ref ON client_source_links(client_ref, source_status);
CREATE INDEX IF NOT EXISTS idx_call_sessions_agent_started ON call_sessions(agent_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_call_turns_session_turn ON call_turns(session_id, turn_index);
CREATE INDEX IF NOT EXISTS idx_action_log_session_time ON assistant_action_log(session_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_memory_facts_agent_ref ON memory_facts(agent_id, client_ref, is_active);
CREATE INDEX IF NOT EXISTS idx_training_samples_agent_approved ON training_samples(agent_id, approved);

CREATE OR REPLACE FUNCTION set_generic_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_agent_profiles_updated_at ON agent_profiles;
CREATE TRIGGER trg_agent_profiles_updated_at
BEFORE UPDATE ON agent_profiles
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_knowledge_sources_updated_at ON knowledge_sources;
CREATE TRIGGER trg_knowledge_sources_updated_at
BEFORE UPDATE ON knowledge_sources
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_knowledge_chunks_updated_at ON knowledge_chunks;
CREATE TRIGGER trg_knowledge_chunks_updated_at
BEFORE UPDATE ON knowledge_chunks
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_script_templates_updated_at ON script_templates;
CREATE TRIGGER trg_script_templates_updated_at
BEFORE UPDATE ON script_templates
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_script_steps_updated_at ON script_steps;
CREATE TRIGGER trg_script_steps_updated_at
BEFORE UPDATE ON script_steps
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_objection_playbook_updated_at ON objection_playbook;
CREATE TRIGGER trg_objection_playbook_updated_at
BEFORE UPDATE ON objection_playbook
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_compliance_rules_updated_at ON compliance_rules;
CREATE TRIGGER trg_compliance_rules_updated_at
BEFORE UPDATE ON compliance_rules
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_client_memory_refs_updated_at ON client_memory_refs;
CREATE TRIGGER trg_client_memory_refs_updated_at
BEFORE UPDATE ON client_memory_refs
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_client_source_links_updated_at ON client_source_links;
CREATE TRIGGER trg_client_source_links_updated_at
BEFORE UPDATE ON client_source_links
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_call_sessions_updated_at ON call_sessions;
CREATE TRIGGER trg_call_sessions_updated_at
BEFORE UPDATE ON call_sessions
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_memory_facts_updated_at ON memory_facts;
CREATE TRIGGER trg_memory_facts_updated_at
BEFORE UPDATE ON memory_facts
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_call_quality_reviews_updated_at ON call_quality_reviews;
CREATE TRIGGER trg_call_quality_reviews_updated_at
BEFORE UPDATE ON call_quality_reviews
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();

DROP TRIGGER IF EXISTS trg_training_samples_updated_at ON training_samples;
CREATE TRIGGER trg_training_samples_updated_at
BEFORE UPDATE ON training_samples
FOR EACH ROW
EXECUTE FUNCTION set_generic_updated_at();
