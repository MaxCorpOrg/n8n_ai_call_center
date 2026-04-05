CREATE TABLE IF NOT EXISTS autodial_campaigns (
  campaign_key TEXT PRIMARY KEY,
  spreadsheet_id TEXT NOT NULL,
  sheet_name TEXT NOT NULL DEFAULT 'Лиды_обзвон',
  sheet_url TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'exhausted')),
  current_day DATE NOT NULL DEFAULT CURRENT_DATE,
  daily_success_count INTEGER NOT NULL DEFAULT 0,
  daily_success_limit INTEGER NOT NULL DEFAULT 15,
  max_attempts_per_lead INTEGER NOT NULL DEFAULT 3,
  call_window_start TIME NOT NULL DEFAULT TIME '10:00',
  call_window_end TIME NOT NULL DEFAULT TIME '14:00',
  dial_timeout_minutes INTEGER NOT NULL DEFAULT 20,
  exhausted_reason TEXT,
  last_run_at TIMESTAMPTZ,
  exhausted_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (spreadsheet_id, sheet_name)
);

CREATE TABLE IF NOT EXISTS autodial_queue (
  id BIGSERIAL PRIMARY KEY,
  campaign_key TEXT NOT NULL REFERENCES autodial_campaigns(campaign_key) ON DELETE CASCADE,
  lead_key TEXT NOT NULL,
  sheet_row_number INTEGER,
  source_system TEXT NOT NULL DEFAULT 'xlsx_import',
  source_record_key TEXT NOT NULL,
  company_name TEXT,
  contact_name TEXT,
  phone_primary TEXT NOT NULL,
  phone_secondary TEXT,
  city TEXT,
  segment TEXT,
  lpr_role TEXT,
  lpr_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
  current_supplier TEXT,
  current_product TEXT,
  current_price TEXT,
  interest_level TEXT,
  objection_code TEXT,
  objection_text TEXT,
  preferred_channel TEXT NOT NULL DEFAULT 'phone',
  manager_owner TEXT,
  followup_count INTEGER NOT NULL DEFAULT 0,
  max_touch_limit INTEGER NOT NULL DEFAULT 3,
  do_not_call BOOLEAN NOT NULL DEFAULT FALSE,
  final_reason TEXT,
  notes_short TEXT,
  dial_status TEXT NOT NULL DEFAULT 'pending' CHECK (dial_status IN ('pending', 'dialing', 'retry_pending', 'final', 'exhausted', 'dnc')),
  attempt_cycle_date DATE NOT NULL DEFAULT CURRENT_DATE,
  attempt_count_today INTEGER NOT NULL DEFAULT 0,
  attempt_count_total INTEGER NOT NULL DEFAULT 0,
  connected_count_total INTEGER NOT NULL DEFAULT 0,
  last_attempt_at TIMESTAMPTZ,
  last_attempt_result TEXT,
  next_call_at TIMESTAMPTZ,
  locked_by_job TEXT,
  locked_until TIMESTAMPTZ,
  last_call_log_at TIMESTAMPTZ,
  last_updated_by TEXT NOT NULL DEFAULT 'autodial_dispatcher',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (campaign_key, lead_key)
);

CREATE TABLE IF NOT EXISTS autodial_attempts (
  id BIGSERIAL PRIMARY KEY,
  campaign_key TEXT NOT NULL REFERENCES autodial_campaigns(campaign_key) ON DELETE CASCADE,
  queue_id BIGINT REFERENCES autodial_queue(id) ON DELETE SET NULL,
  lead_key TEXT NOT NULL,
  event_key TEXT NOT NULL UNIQUE,
  attempt_no INTEGER NOT NULL,
  sheet_row_number INTEGER,
  request_status TEXT NOT NULL DEFAULT 'requested',
  result_status TEXT,
  is_live_connect BOOLEAN NOT NULL DEFAULT FALSE,
  request_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  provider_response JSONB NOT NULL DEFAULT '{}'::jsonb,
  call_log_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  eleven_conv_id TEXT,
  n8n_execution_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_autodial_campaigns_status_day
  ON autodial_campaigns (status, current_day);

CREATE INDEX IF NOT EXISTS idx_autodial_queue_campaign_status_next
  ON autodial_queue (campaign_key, dial_status, next_call_at, attempt_count_today, sheet_row_number);

CREATE INDEX IF NOT EXISTS idx_autodial_queue_locked
  ON autodial_queue (campaign_key, locked_until);

CREATE INDEX IF NOT EXISTS idx_autodial_attempts_campaign_created
  ON autodial_attempts (campaign_key, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_autodial_attempts_lead
  ON autodial_attempts (lead_key, created_at DESC);

CREATE OR REPLACE FUNCTION set_autodial_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_autodial_campaigns_updated_at ON autodial_campaigns;
CREATE TRIGGER trg_autodial_campaigns_updated_at
BEFORE UPDATE ON autodial_campaigns
FOR EACH ROW
EXECUTE FUNCTION set_autodial_updated_at();

DROP TRIGGER IF EXISTS trg_autodial_queue_updated_at ON autodial_queue;
CREATE TRIGGER trg_autodial_queue_updated_at
BEFORE UPDATE ON autodial_queue
FOR EACH ROW
EXECUTE FUNCTION set_autodial_updated_at();

DROP TRIGGER IF EXISTS trg_autodial_attempts_updated_at ON autodial_attempts;
CREATE TRIGGER trg_autodial_attempts_updated_at
BEFORE UPDATE ON autodial_attempts
FOR EACH ROW
EXECUTE FUNCTION set_autodial_updated_at();
