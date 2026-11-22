-- PV1 candidate PostgreSQL schema v0.1 (2026-11-22).
-- SYNTHETIC DATA ONLY. This schema is NOT a complete security architecture.
-- Application authorization / RLS, encryption, logging, migrations and backup deletion require Step 4 review.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE import_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  adapter text NOT NULL CHECK (adapter IN ('email_eml_v1','browser_chrome_json_v1')),
  source_label text NOT NULL,
  status text NOT NULL DEFAULT 'processing' CHECK (status IN ('processing','completed','failed')),
  imported_at timestamptz NOT NULL DEFAULT now(),
  record_count integer NOT NULL DEFAULT 0 CHECK (record_count >= 0),
  retention_policy text NOT NULL DEFAULT 'pending_security_review',
  UNIQUE (id, user_id)
);

CREATE TABLE observations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  batch_id uuid NOT NULL,
  kind text NOT NULL CHECK (kind IN (
    'site_visit_observed','registration_email_detected',
    'transaction_email_detected','marketing_email_detected',
    'account_notification_detected','unclassified_observation')),
  domain text,
  occurred_at timestamptz,
  summary_code text NOT NULL,
  safe_metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  dedupe_hash text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (batch_id,user_id) REFERENCES import_batches(id,user_id) ON DELETE CASCADE,
  UNIQUE (id,user_id),
  UNIQUE (batch_id,dedupe_hash)
);

CREATE TABLE organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name text NOT NULL,
  canonical_domain text NOT NULL UNIQUE,
  resolution_status text NOT NULL DEFAULT 'unresolved' CHECK (resolution_status IN ('reviewed','unresolved'))
);

CREATE TABLE relationships (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES organizations(id),
  relationship_type text NOT NULL CHECK (relationship_type IN ('visited','likely_account','transaction','marketing')),
  first_observed_at timestamptz,
  last_observed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (id,user_id),
  UNIQUE (user_id,organization_id,relationship_type)
);

CREATE TABLE relationship_evidence (
  user_id uuid NOT NULL,
  relationship_id uuid NOT NULL,
  observation_id uuid NOT NULL,
  evidence_role text NOT NULL CHECK (evidence_role IN ('primary','corroborating','context')),
  PRIMARY KEY (relationship_id,observation_id),
  FOREIGN KEY (relationship_id,user_id) REFERENCES relationships(id,user_id) ON DELETE CASCADE,
  FOREIGN KEY (observation_id,user_id) REFERENCES observations(id,user_id) ON DELETE CASCADE
);

CREATE TABLE assessments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  relationship_id uuid NOT NULL,
  evidence_state text NOT NULL CHECK (evidence_state IN ('observed','inferred','confirmed')),
  confidence text NOT NULL CHECK (confidence IN ('high','medium','low','insufficient')),
  review_priority text NOT NULL CHECK (review_priority IN ('sensitive','medium','low','unknown')),
  retention_status text NOT NULL DEFAULT 'unknown' CHECK (retention_status IN ('unknown','verified_retained','verified_not_retained')),
  data_sale_status text NOT NULL DEFAULT 'unknown' CHECK (data_sale_status IN ('unknown','verified_shared_or_sold','verified_not_shared_or_sold')),
  rationale_codes text[] NOT NULL DEFAULT '{}',
  limitations text[] NOT NULL DEFAULT '{}',
  ruleset_version text NOT NULL,
  evaluated_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (relationship_id,user_id) REFERENCES relationships(id,user_id) ON DELETE CASCADE
);

CREATE TABLE action_directory (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id),
  action_type text NOT NULL CHECK (action_type IN ('account_settings','privacy_settings','unsubscribe','deletion_request','instructions')),
  official_url text NOT NULL,
  verified_at timestamptz,
  verification_method text,
  status text NOT NULL DEFAULT 'needs_review' CHECK (status IN ('active','needs_review','unavailable'))
);

CREATE TABLE user_actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL,
  relationship_id uuid NOT NULL,
  action_id uuid NOT NULL REFERENCES action_directory(id),
  status text NOT NULL DEFAULT 'not_started' CHECK (status IN ('not_started','opened','user_reported_done','verified_external_response')),
  updated_at timestamptz NOT NULL DEFAULT now(),
  FOREIGN KEY (relationship_id,user_id) REFERENCES relationships(id,user_id) ON DELETE CASCADE
);

CREATE INDEX idx_import_batches_user ON import_batches(user_id,imported_at DESC);
CREATE INDEX idx_observations_batch ON observations(batch_id);
CREATE INDEX idx_observations_domain ON observations(user_id,domain);
CREATE INDEX idx_relationships_user ON relationships(user_id,organization_id);
CREATE INDEX idx_rel_evidence_observation ON relationship_evidence(observation_id);
CREATE INDEX idx_assessments_relationship ON assessments(relationship_id,evaluated_at DESC);
CREATE INDEX idx_actions_organization ON action_directory(organization_id,status);

-- Operational requirements, NOT solved by these DDL statements:
-- 1. Enforce tenant authorization in application and optionally RLS (no cross-user IDOR).
-- 2. Delete import inside transaction, recompute/retire related relationship assessments.
-- 3. Validate safe_metadata with an allowlist; JSONB must not become a secret dump.
-- 4. Establish backup/log/retention rules and encryption/key strategy prior to real-user beta.
-- 5. Enforce claim-specific evidence rules in application services; DB CHECKs cannot prove semantics.
