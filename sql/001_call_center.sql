CREATE TABLE IF NOT EXISTS call_tasks (
  id BIGSERIAL PRIMARY KEY,
  external_id TEXT UNIQUE,
  lead_id TEXT,
  phone_e164 TEXT NOT NULL,
  contact_name TEXT,
  script_version TEXT,
  consent_source TEXT,
  status TEXT NOT NULL DEFAULT 'queued',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS call_events (
  id BIGSERIAL PRIMARY KEY,
  task_id BIGINT REFERENCES call_tasks(id) ON DELETE SET NULL,
  provider_call_id TEXT,
  event_type TEXT NOT NULL,
  direction TEXT,
  duration_seconds INTEGER,
  recording_url TEXT,
  transcript TEXT,
  summary TEXT,
  sentiment TEXT,
  raw_payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_call_tasks_phone ON call_tasks(phone_e164);
CREATE INDEX IF NOT EXISTS idx_call_events_provider_call_id ON call_events(provider_call_id);
CREATE INDEX IF NOT EXISTS idx_call_events_type_created ON call_events(event_type, created_at DESC);

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_call_tasks_updated_at ON call_tasks;
CREATE TRIGGER trg_call_tasks_updated_at
BEFORE UPDATE ON call_tasks
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();
