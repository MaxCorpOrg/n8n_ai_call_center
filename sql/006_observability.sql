-- 006_observability.sql
-- Additive-only: missing indexes, audit log, retention config, SLA views.
-- Safe to apply multiple times (all IF NOT EXISTS / OR REPLACE).

-- ═══════════════════════════════════════════════════════════
-- 1. Missing indexes for time-based queries
-- ═══════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_call_events_created_at
  ON call_events (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_call_events_task_created
  ON call_events (task_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_call_tasks_status_created
  ON call_tasks (status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_assistant_action_log_created_at
  ON assistant_action_log (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_assistant_action_log_type_status
  ON assistant_action_log (action_type, status);

CREATE INDEX IF NOT EXISTS idx_memory_facts_updated_at
  ON memory_facts (updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_call_sessions_started_at
  ON call_sessions (started_at DESC);

CREATE INDEX IF NOT EXISTS idx_call_sessions_outcome
  ON call_sessions (outcome, started_at DESC);

CREATE INDEX IF NOT EXISTS idx_autodial_queue_dial_status
  ON autodial_queue (dial_status);

CREATE INDEX IF NOT EXISTS idx_autodial_attempts_result
  ON autodial_attempts (result_status, created_at DESC);

-- ═══════════════════════════════════════════════════════════
-- 2. Audit log table (tracks INSERT/UPDATE/DELETE on key tables)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  operation TEXT NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
  record_id TEXT,
  old_data JSONB,
  new_data JSONB,
  changed_by TEXT NOT NULL DEFAULT CURRENT_USER,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_table_created
  ON audit_log (table_name, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_log_record
  ON audit_log (table_name, record_id);

-- Generic audit trigger function
CREATE OR REPLACE FUNCTION fn_audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO audit_log (table_name, operation, record_id, new_data)
    VALUES (TG_TABLE_NAME, 'INSERT', NEW.id::TEXT, to_jsonb(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO audit_log (table_name, operation, record_id, old_data, new_data)
    VALUES (TG_TABLE_NAME, 'UPDATE', NEW.id::TEXT, to_jsonb(OLD), to_jsonb(NEW));
    RETURN NEW;
  ELSIF TG_OP = 'DELETE' THEN
    INSERT INTO audit_log (table_name, operation, record_id, old_data)
    VALUES (TG_TABLE_NAME, 'DELETE', OLD.id::TEXT, to_jsonb(OLD));
    RETURN OLD;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach to key tables (only on UPDATE/DELETE — INSERT is high-volume, skip for performance)
DROP TRIGGER IF EXISTS trg_audit_call_tasks ON call_tasks;
CREATE TRIGGER trg_audit_call_tasks
AFTER UPDATE OR DELETE ON call_tasks
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

DROP TRIGGER IF EXISTS trg_audit_agent_profiles ON agent_profiles;
CREATE TRIGGER trg_audit_agent_profiles
AFTER INSERT OR UPDATE OR DELETE ON agent_profiles
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

DROP TRIGGER IF EXISTS trg_audit_autodial_campaigns ON autodial_campaigns;
CREATE TRIGGER trg_audit_autodial_campaigns
AFTER UPDATE OR DELETE ON autodial_campaigns
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

DROP TRIGGER IF EXISTS trg_audit_compliance_rules ON compliance_rules;
CREATE TRIGGER trg_audit_compliance_rules
AFTER INSERT OR UPDATE OR DELETE ON compliance_rules
FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();

-- ═══════════════════════════════════════════════════════════
-- 3. Data retention configuration
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS data_retention_config (
  table_name TEXT PRIMARY KEY,
  retention_days INTEGER NOT NULL,
  date_column TEXT NOT NULL DEFAULT 'created_at',
  archive_before_delete BOOLEAN NOT NULL DEFAULT FALSE,
  last_cleanup_at TIMESTAMPTZ,
  rows_deleted_last INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Default retention policies
INSERT INTO data_retention_config (table_name, retention_days, date_column, archive_before_delete)
VALUES
  ('audit_log', 90, 'created_at', FALSE),
  ('assistant_action_log', 180, 'created_at', TRUE),
  ('call_events', 365, 'created_at', TRUE),
  ('autodial_attempts', 180, 'created_at', FALSE)
ON CONFLICT (table_name) DO NOTHING;

-- Cleanup function (call from cron or n8n schedule)
CREATE OR REPLACE FUNCTION fn_apply_retention()
RETURNS TABLE (table_cleaned TEXT, rows_removed BIGINT) AS $$
DECLARE
  rec RECORD;
  sql_text TEXT;
  removed BIGINT;
BEGIN
  FOR rec IN SELECT * FROM data_retention_config LOOP
    sql_text := format(
      'DELETE FROM %I WHERE %I < NOW() - interval ''%s days''',
      rec.table_name, rec.date_column, rec.retention_days
    );
    EXECUTE sql_text;
    GET DIAGNOSTICS removed = ROW_COUNT;

    UPDATE data_retention_config
    SET last_cleanup_at = NOW(), rows_deleted_last = removed, updated_at = NOW()
    WHERE data_retention_config.table_name = rec.table_name;

    table_cleaned := rec.table_name;
    rows_removed := removed;
    RETURN NEXT;
  END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════
-- 4. SLA / Operational views
-- ═══════════════════════════════════════════════════════════

-- Daily call summary
CREATE OR REPLACE VIEW v_daily_call_summary AS
SELECT
  date_trunc('day', cs.started_at)::DATE AS call_date,
  COUNT(*) AS total_calls,
  COUNT(*) FILTER (WHERE cs.direction = 'inbound') AS inbound,
  COUNT(*) FILTER (WHERE cs.direction = 'outbound') AS outbound,
  COUNT(*) FILTER (WHERE cs.outcome IS NOT NULL) AS completed,
  COUNT(*) FILTER (WHERE cs.ended_at IS NOT NULL) AS with_duration,
  ROUND(AVG(EXTRACT(EPOCH FROM (cs.ended_at - cs.started_at)))::NUMERIC, 1) AS avg_duration_sec,
  COUNT(*) FILTER (WHERE cs.outcome = 'qualified') AS qualified,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE cs.outcome = 'qualified') / NULLIF(COUNT(*), 0), 1
  ) AS qualification_rate_pct
FROM call_sessions cs
WHERE cs.started_at >= NOW() - INTERVAL '90 days'
GROUP BY 1
ORDER BY 1 DESC;

-- Quality metrics
CREATE OR REPLACE VIEW v_quality_metrics AS
SELECT
  date_trunc('week', qr.created_at)::DATE AS week_start,
  COUNT(*) AS reviews_count,
  ROUND(AVG(qr.score_total), 1) AS avg_score,
  ROUND(MIN(qr.score_total), 1) AS min_score,
  ROUND(MAX(qr.score_total), 1) AS max_score,
  ROUND(AVG(qr.score_opening), 1) AS avg_opening,
  ROUND(AVG(qr.score_objection_handling), 1) AS avg_objections,
  ROUND(AVG(qr.score_compliance), 1) AS avg_compliance
FROM call_quality_reviews qr
GROUP BY 1
ORDER BY 1 DESC;

-- Autodial campaign dashboard
CREATE OR REPLACE VIEW v_autodial_dashboard AS
SELECT
  c.campaign_key,
  c.status AS campaign_status,
  c.daily_success_count,
  c.daily_success_limit,
  COUNT(q.id) AS total_leads,
  COUNT(q.id) FILTER (WHERE q.dial_status = 'pending') AS pending,
  COUNT(q.id) FILTER (WHERE q.dial_status = 'dialing') AS dialing,
  COUNT(q.id) FILTER (WHERE q.dial_status = 'final') AS final,
  COUNT(q.id) FILTER (WHERE q.dial_status = 'exhausted') AS exhausted,
  COUNT(q.id) FILTER (WHERE q.dial_status = 'dnc') AS do_not_call,
  ROUND(
    100.0 * COUNT(q.id) FILTER (WHERE q.connected_count_total > 0) / NULLIF(COUNT(q.id), 0), 1
  ) AS connect_rate_pct,
  c.last_run_at
FROM autodial_campaigns c
LEFT JOIN autodial_queue q ON q.campaign_key = c.campaign_key
GROUP BY c.campaign_key, c.status, c.daily_success_count, c.daily_success_limit, c.last_run_at;

-- Error rate (last 24h)
CREATE OR REPLACE VIEW v_error_rate_24h AS
SELECT
  action_type,
  COUNT(*) AS total,
  COUNT(*) FILTER (WHERE status = 'error') AS errors,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE status = 'error') / NULLIF(COUNT(*), 0), 1
  ) AS error_rate_pct
FROM assistant_action_log
WHERE created_at >= NOW() - INTERVAL '24 hours'
GROUP BY action_type
ORDER BY errors DESC;
