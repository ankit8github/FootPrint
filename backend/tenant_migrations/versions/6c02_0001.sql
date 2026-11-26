-- Phase 6C-02, additive synthetic research model. Not the candidate PV1 DDL.
-- Executed as fp6_owner, never by runtime. Schema ownership is explicit.
CREATE SCHEMA fp6_auth AUTHORIZATION fp6_owner;
CREATE SCHEMA fp6_data AUTHORIZATION fp6_owner;
CREATE SCHEMA fp6_reference AUTHORIZATION fp6_owner;
CREATE SCHEMA IF NOT EXISTS fp6_context AUTHORIZATION fp6_owner;
CREATE SCHEMA IF NOT EXISTS fp6_ledger AUTHORIZATION fp6_owner;
REVOKE ALL ON SCHEMA fp6_auth, fp6_data, fp6_reference, fp6_context, fp6_ledger FROM PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE fp6_owner REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;

-- The transaction id also rejects stale session-level settings accidentally left
-- by a caller. It is a pool safety fence, not an authentication credential.
CREATE OR REPLACE FUNCTION fp6_context.owner_id() RETURNS uuid
LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = pg_catalog AS $$
DECLARE value text;
BEGIN
  IF current_setting('app.owner_xid', true) IS DISTINCT FROM pg_current_xact_id()::text
  THEN RETURN NULL; END IF;
  value := current_setting('app.owner_id', true);
  IF value IS NULL OR value !~ '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
  THEN RETURN NULL; END IF;
  RETURN value::uuid;
END $$;
REVOKE ALL ON FUNCTION fp6_context.owner_id() FROM PUBLIC;
GRANT USAGE ON SCHEMA fp6_context TO fp6_runtime;
GRANT EXECUTE ON FUNCTION fp6_context.owner_id() TO fp6_runtime;

CREATE DOMAIN fp6_data.domain_name AS varchar(68) CHECK (VALUE IN (
 'fictional-cafe.test','fictional-clinic.test','fictional-date.test',
 'fictional-duplicate.test','fictional-library.test','fictional-museum.test',
 'fictional-news.test','fictional-notes.test','fictional-parcel.test',
 'fictional-postcard.test','fictional-shop.test','fictional-shopper.test','fictional-studio.test'));
CREATE DOMAIN fp6_data.issue_code AS varchar(40) CHECK (VALUE IN (
 'OK','EMAIL_UNCLASSIFIED','DUPLICATE_RECORD','INVALID_TIMESTAMP','INVALID_URL',
 'INVALID_RECORD','INVALID_JSON','JSON_LIMIT','MALFORMED_MIME','UNSUPPORTED_ENCODING',
 'MISSING_SENDER','ORIGIN_CONFLICT','HTML_ONLY_IGNORED','UNAVAILABLE_HISTORY',
 'NOT_APPROVED_SYNTHETIC','FILE_LIMIT','BATCH_LIMIT','RECORD_LIMIT','UNSUPPORTED_FILE',
 'PARSER_TIMEOUT','PARSER_FAILED','NO_SUPPORTED_FEATURE','QUOTED_CONTEXT',
 'UNTRUSTED_INSTRUCTIONS','MULTIPLE_COMMERCIAL_REFERENCES','FEATURE_LIMIT'));
CREATE DOMAIN fp6_data.relation_type AS varchar(16)
 CHECK (VALUE IN ('visited','likely_account','transaction','marketing'));
CREATE DOMAIN fp6_data.feature_code AS varchar(40) CHECK (VALUE IN (
 'ACCOUNT_REQUEST','ACCOUNT_PREFERENCES_CHANGED','PAID_RECEIPT_CLAIM',
 'CANCELLED_BEFORE_PAYMENT_CLAIM','UNPAID_INVOICE_CLAIM','NEWSLETTER_CUE',
 'QUOTED_CONTEXT','UNTRUSTED_INSTRUCTIONS','VISIT_RECORDED'));

CREATE TABLE fp6_auth.users (
 owner_id uuid PRIMARY KEY,
 state varchar(10) NOT NULL CHECK (state IN ('active','disabled','deleted')),
 auth_epoch integer NOT NULL CHECK (auth_epoch BETWEEN 1 AND 1000000),
 created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE fp6_auth.identity_links (
 owner_id uuid NOT NULL REFERENCES fp6_auth.users,
 issuer_config varchar(20) NOT NULL CHECK (issuer_config = 'synthetic-idp-v1'),
 subject_lookup bytea NOT NULL CHECK (octet_length(subject_lookup) = 32),
 subject_ciphertext bytea NOT NULL CHECK (octet_length(subject_ciphertext) BETWEEN 32 AND 512),
 nonce bytea NOT NULL CHECK (octet_length(nonce) = 12),
 key_version smallint NOT NULL CHECK (key_version = 1),
 PRIMARY KEY (issuer_config, subject_lookup),
 UNIQUE (owner_id, issuer_config)
);
CREATE TABLE fp6_auth.sessions (
 digest bytea PRIMARY KEY CHECK (octet_length(digest) = 32),
 owner_id uuid NOT NULL REFERENCES fp6_auth.users,
 auth_epoch integer NOT NULL CHECK (auth_epoch BETWEEN 1 AND 1000000),
 created_at timestamptz NOT NULL,
 last_seen_at timestamptz NOT NULL,
 idle_expires_at timestamptz NOT NULL,
 absolute_expires_at timestamptz NOT NULL,
 strength varchar(16) NOT NULL CHECK (strength IN ('synthetic_mfa')),
 revoked boolean NOT NULL DEFAULT false,
 CHECK (created_at <= last_seen_at AND last_seen_at < idle_expires_at
        AND idle_expires_at <= absolute_expires_at),
 CHECK (absolute_expires_at <= created_at + interval '12 hours')
);
-- Only bootstrap exception. No dynamic SQL and no footprint reference; fixed
-- search_path prevents object shadowing. No table SELECT is granted to auth.
CREATE FUNCTION fp6_auth.lookup_session(candidate bytea)
RETURNS TABLE (owner_id uuid, auth_epoch integer, strength varchar)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $$
 SELECT s.owner_id, s.auth_epoch, s.strength FROM fp6_auth.sessions s
 JOIN fp6_auth.users u ON u.owner_id = s.owner_id AND u.auth_epoch = s.auth_epoch
 WHERE octet_length(candidate) = 32 AND s.digest = candidate
 AND u.state = 'active' AND NOT s.revoked
 AND s.idle_expires_at > statement_timestamp()
 AND s.absolute_expires_at > statement_timestamp()
$$;
REVOKE ALL ON FUNCTION fp6_auth.lookup_session(bytea) FROM PUBLIC;
GRANT USAGE ON SCHEMA fp6_auth TO fp6_auth;
GRANT EXECUTE ON FUNCTION fp6_auth.lookup_session(bytea) TO fp6_auth;

CREATE TABLE fp6_data.tenant_state (
 owner_id uuid PRIMARY KEY REFERENCES fp6_auth.users,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 lifecycle varchar(16) NOT NULL CHECK (lifecycle IN ('active','pending_delete','disabled')),
 UNIQUE (owner_id, consent_epoch, revision)
);
CREATE TABLE fp6_data.consents (
 owner_id uuid NOT NULL REFERENCES fp6_data.tenant_state,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 event_id uuid NOT NULL,
 decision varchar(10) NOT NULL CHECK (decision IN ('accepted','withdrawn','expired')),
 purpose varchar(20) NOT NULL CHECK (purpose = 'synthetic-test-only'),
 policy_version varchar(24) NOT NULL CHECK (policy_version = 'synthetic-policy-v1'),
 notice_version varchar(24) NOT NULL CHECK (notice_version = 'synthetic-notice-v1'),
 accepted_at timestamptz NOT NULL,
 expires_at timestamptz NOT NULL,
 PRIMARY KEY (owner_id, consent_epoch), UNIQUE (owner_id, event_id),
 CHECK (expires_at > accepted_at)
);
CREATE TABLE fp6_data.collections (
 owner_id uuid NOT NULL REFERENCES fp6_data.tenant_state,
 collection_id uuid NOT NULL,
 current_generation integer NOT NULL CHECK (current_generation BETWEEN 1 AND 1000000),
 lifecycle varchar(16) NOT NULL CHECK (lifecycle IN ('active','pending_delete','unavailable')),
 expires_at timestamptz NOT NULL,
 schema_version varchar(32) NOT NULL CHECK (schema_version = 'minimized-evidence-v1'),
 parser_version varchar(32) NOT NULL CHECK (parser_version = 'phase2-normalized-v1'),
 feature_version varchar(32) NOT NULL CHECK (feature_version = 'email_features_v1'),
 context_version varchar(32) NOT NULL CHECK (context_version = 'email_context_v1'),
 fusion_version varchar(32) NOT NULL CHECK (fusion_version = 'relationship_fusion_v1'),
 assessment_version varchar(32) NOT NULL CHECK (assessment_version = 'sensitivity_rules_v1'),
 explanation_version varchar(32) NOT NULL CHECK (explanation_version = 'phase4-explanations-v1'),
 PRIMARY KEY (owner_id, collection_id), UNIQUE (owner_id)
);
CREATE TABLE fp6_data.generations (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL,
 generation integer NOT NULL CHECK (generation BETWEEN 1 AND 1000000),
 PRIMARY KEY (owner_id, collection_id, generation),
 FOREIGN KEY (owner_id, collection_id) REFERENCES fp6_data.collections
);
ALTER TABLE fp6_data.collections ADD CONSTRAINT current_generation_fk
 FOREIGN KEY (owner_id, collection_id, current_generation)
 REFERENCES fp6_data.generations DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE fp6_data.import_sources (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, source_id uuid NOT NULL,
 ordinal smallint NOT NULL CHECK (ordinal BETWEEN 1 AND 20),
 adapter varchar(24) NOT NULL CHECK (adapter IN ('email_eml_v1','browser_chrome_json_v1')),
 record_count integer NOT NULL CHECK (record_count BETWEEN 0 AND 10000),
 lifecycle varchar(16) NOT NULL CHECK (lifecycle IN ('active','pending_delete')),
 PRIMARY KEY (owner_id, collection_id, source_id),
 UNIQUE (owner_id, collection_id, ordinal),
 UNIQUE (owner_id, collection_id, source_id, adapter, record_count),
 FOREIGN KEY (owner_id, collection_id) REFERENCES fp6_data.collections
);
CREATE TABLE fp6_data.observations (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, observation_id uuid NOT NULL,
 source_id uuid NOT NULL, record_index integer NOT NULL CHECK (record_index BETWEEN 0 AND 9999),
 source_count integer NOT NULL CHECK (source_count BETWEEN 1 AND 10000),
 adapter varchar(24) NOT NULL,
 kind varchar(40) NOT NULL CHECK (kind IN ('site_visit_observed','registration_email_detected',
 'transaction_email_detected','marketing_email_detected','account_notification_detected',
 'unclassified_observation')),
 domain fp6_data.domain_name,
 occurred_at timestamptz,
 time_status varchar(8) NOT NULL CHECK (time_status IN ('valid','invalid','missing')),
 attribution varchar(20) NOT NULL CHECK (attribution IN ('browser_record','unverified_sender')),
 issue_code fp6_data.issue_code,
 PRIMARY KEY (owner_id, collection_id, observation_id),
 UNIQUE (owner_id, collection_id, source_id, record_index),
 UNIQUE (owner_id, collection_id, observation_id, adapter),
 UNIQUE (owner_id, collection_id, observation_id, domain),
 FOREIGN KEY (owner_id, collection_id, source_id, adapter, source_count)
 REFERENCES fp6_data.import_sources (owner_id, collection_id, source_id, adapter, record_count),
 CHECK (record_index < source_count),
 CHECK ((time_status = 'valid') = (occurred_at IS NOT NULL)),
 CHECK (occurred_at IS NULL OR (occurred_at >= '1970-01-01Z'::timestamptz
        AND occurred_at < '2101-01-01Z'::timestamptz)),
 CHECK ((adapter = 'browser_chrome_json_v1' AND kind = 'site_visit_observed'
         AND attribution = 'browser_record' AND domain IS NOT NULL
         AND time_status = 'valid' AND issue_code IS NULL)
     OR (adapter = 'email_eml_v1' AND kind <> 'site_visit_observed'
         AND attribution = 'unverified_sender'
         AND ((issue_code IS NULL AND domain IS NOT NULL)
           OR (issue_code IS NOT NULL AND domain IS NULL AND kind = 'unclassified_observation'))))
);
CREATE TABLE fp6_data.observation_features (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, observation_id uuid NOT NULL,
 adapter varchar(24) NOT NULL, feature fp6_data.feature_code NOT NULL,
 PRIMARY KEY (owner_id, collection_id, observation_id, feature),
 FOREIGN KEY (owner_id, collection_id, observation_id, adapter)
 REFERENCES fp6_data.observations (owner_id, collection_id, observation_id, adapter),
 CHECK ((adapter = 'browser_chrome_json_v1' AND feature = 'VISIT_RECORDED')
     OR (adapter = 'email_eml_v1' AND feature <> 'VISIT_RECORDED'))
);
CREATE TABLE fp6_data.context_evidence (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, observation_id uuid NOT NULL,
 required_feature fp6_data.feature_code NOT NULL CHECK (required_feature = 'ACCOUNT_REQUEST'),
 code varchar(40) NOT NULL CHECK (code = 'CLINIC_APPOINTMENT_PORTAL_CONTEXT'),
 PRIMARY KEY (owner_id, collection_id, observation_id),
 FOREIGN KEY (owner_id, collection_id, observation_id, required_feature)
 REFERENCES fp6_data.observation_features
);
CREATE TABLE fp6_data.excluded_rows (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, source_id uuid NOT NULL,
 record_index integer NOT NULL CHECK (record_index BETWEEN 0 AND 9999),
 source_count integer NOT NULL CHECK (source_count BETWEEN 1 AND 10000),
 adapter varchar(24) NOT NULL, code fp6_data.issue_code NOT NULL,
 PRIMARY KEY (owner_id, collection_id, source_id, record_index),
 FOREIGN KEY (owner_id, collection_id, source_id, adapter, source_count)
 REFERENCES fp6_data.import_sources (owner_id, collection_id, source_id, adapter, record_count),
 CHECK (record_index < source_count)
);
CREATE TABLE fp6_data.evidence_groups (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, group_id uuid NOT NULL,
 primary_observation_id uuid NOT NULL,
 PRIMARY KEY (owner_id, collection_id, group_id),
 FOREIGN KEY (owner_id, collection_id, primary_observation_id) REFERENCES fp6_data.observations
);
CREATE TABLE fp6_data.evidence_equivalence (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, group_id uuid NOT NULL,
 observation_id uuid NOT NULL,
 PRIMARY KEY (owner_id, collection_id, group_id, observation_id),
 UNIQUE (owner_id, collection_id, observation_id),
 FOREIGN KEY (owner_id, collection_id, group_id) REFERENCES fp6_data.evidence_groups,
 FOREIGN KEY (owner_id, collection_id, observation_id) REFERENCES fp6_data.observations
);
ALTER TABLE fp6_data.evidence_groups ADD CONSTRAINT primary_member_fk
 FOREIGN KEY (owner_id, collection_id, group_id, primary_observation_id)
 REFERENCES fp6_data.evidence_equivalence DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE fp6_data.commercial_groups (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, group_id uuid NOT NULL,
 domain fp6_data.domain_name NOT NULL,
 PRIMARY KEY (owner_id, collection_id, group_id),
 UNIQUE (owner_id, collection_id, group_id, domain),
 FOREIGN KEY (owner_id, collection_id) REFERENCES fp6_data.collections
);
CREATE TABLE fp6_data.commercial_alias_members (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, group_id uuid NOT NULL,
 domain fp6_data.domain_name NOT NULL, observation_id uuid NOT NULL,
 required_feature fp6_data.feature_code NOT NULL CHECK (required_feature IN
 ('PAID_RECEIPT_CLAIM','CANCELLED_BEFORE_PAYMENT_CLAIM','UNPAID_INVOICE_CLAIM')),
 PRIMARY KEY (owner_id, collection_id, group_id, observation_id),
 FOREIGN KEY (owner_id, collection_id, group_id, domain)
 REFERENCES fp6_data.commercial_groups (owner_id, collection_id, group_id, domain),
 FOREIGN KEY (owner_id, collection_id, observation_id, domain)
 REFERENCES fp6_data.observations (owner_id, collection_id, observation_id, domain),
 FOREIGN KEY (owner_id, collection_id, observation_id, required_feature)
 REFERENCES fp6_data.observation_features
);
CREATE TABLE fp6_data.findings (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL,
 kind varchar(12) NOT NULL CHECK (kind IN ('relationship','unresolved')),
 domain fp6_data.domain_name, relationship_type fp6_data.relation_type,
 issue_code fp6_data.issue_code,
 PRIMARY KEY (owner_id, collection_id, generation, finding_id),
 UNIQUE (owner_id, collection_id, generation, domain, relationship_type),
 UNIQUE (owner_id, collection_id, generation, finding_id, domain, relationship_type),
 FOREIGN KEY (owner_id, collection_id, generation) REFERENCES fp6_data.generations,
 CHECK ((kind = 'relationship' AND domain IS NOT NULL AND relationship_type IS NOT NULL
         AND issue_code IS NULL)
     OR (kind = 'unresolved' AND domain IS NULL AND relationship_type IS NULL
         AND issue_code IS NOT NULL))
);
CREATE TABLE fp6_data.finding_evidence (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL, observation_id uuid NOT NULL,
 evidence_role varchar(16) NOT NULL CHECK (evidence_role IN ('primary','corroborating','context')),
 PRIMARY KEY (owner_id, collection_id, generation, finding_id, observation_id),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id) REFERENCES fp6_data.findings,
 FOREIGN KEY (owner_id, collection_id, observation_id) REFERENCES fp6_data.observations
);
CREATE TABLE fp6_data.assessments (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL,
 evidence_state varchar(8) NOT NULL CHECK (evidence_state IN ('observed','inferred','unknown')),
 confidence varchar(12) NOT NULL CHECK (confidence IN ('high','medium','low','insufficient')),
 priority varchar(10) NOT NULL CHECK (priority IN ('sensitive','medium','low','unknown')),
 rule_id varchar(24) NOT NULL CHECK (rule_id IN ('clinic_account','account',
 'conflicting_transaction','paid_receipt','unpaid_invoice','visit','marketing','unknown','invalid_support')),
 retention_status varchar(7) NOT NULL CHECK (retention_status = 'unknown'),
 data_sale_status varchar(7) NOT NULL CHECK (data_sale_status = 'unknown'),
 evaluated_at timestamptz NOT NULL,
 PRIMARY KEY (owner_id, collection_id, generation, finding_id),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id) REFERENCES fp6_data.findings
);
CREATE TABLE fp6_data.rationale_evidence (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL, observation_id uuid NOT NULL,
 code varchar(32) NOT NULL CHECK (code IN ('ACCOUNT_RELATIONSHIP','HEALTH_CONTEXT',
 'TRANSACTION_INDICATION','VISIT_ONLY','MARKETING_ONLY','AMBIGUOUS_EVIDENCE')),
 PRIMARY KEY (owner_id, collection_id, generation, finding_id, code, observation_id),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id) REFERENCES fp6_data.assessments,
 FOREIGN KEY (owner_id, collection_id, generation, finding_id, observation_id)
 REFERENCES fp6_data.finding_evidence
);
CREATE TABLE fp6_data.assessment_limitations (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL,
 code varchar(40) NOT NULL CHECK (code IN ('SOURCE_RECORD_ONLY','UNVERIFIED_SENDER',
 'UNKNOWN_CLAIMS','NO_PERSONAL_HEALTH_INFERENCE','CONTRADICTORY_PAYMENT_CLAIMS',
 'UNPAID_INVOICE','UNKNOWN_EVENT_TIME','DUPLICATES_NOT_INDEPENDENT',
 'INSUFFICIENT_CATEGORY_CONTEXT','INVALID_SUPPORT')),
 PRIMARY KEY (owner_id, collection_id, generation, finding_id, code),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id) REFERENCES fp6_data.assessments
);
CREATE TABLE fp6_data.unknown_claims (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL,
 claim varchar(32) NOT NULL CHECK (claim IN ('sender_authenticity','current_account',
 'payment_completed','payment_credentials_retained','company_retention','data_sale','breach_status')),
 evidence_state varchar(7) NOT NULL CHECK (evidence_state = 'unknown'),
 confidence varchar(12) NOT NULL CHECK (confidence = 'insufficient'),
 PRIMARY KEY (owner_id, collection_id, generation, finding_id, claim),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id) REFERENCES fp6_data.assessments
);

-- Reference projections only: no URL, live verification, directory governance or
-- editable runtime catalog. Only the migrator can add synthetic eligibility.
CREATE TABLE fp6_reference.organizations (
 domain fp6_data.domain_name PRIMARY KEY,
 realm varchar(9) NOT NULL CHECK (realm = 'synthetic'),
 UNIQUE (domain, realm)
);
CREATE TABLE fp6_reference.directory_versions (
 directory_id uuid NOT NULL, version integer NOT NULL CHECK (version BETWEEN 1 AND 1000000),
 domain fp6_data.domain_name NOT NULL, realm varchar(9) NOT NULL CHECK (realm = 'synthetic'),
 state varchar(12) NOT NULL CHECK (state IN ('needs_review','active','revoked')),
 expires_at timestamptz NOT NULL,
 PRIMARY KEY (directory_id, version),
 UNIQUE (directory_id, version, domain, realm),
 FOREIGN KEY (domain, realm) REFERENCES fp6_reference.organizations (domain, realm)
);
CREATE TABLE fp6_reference.action_eligibility (
 directory_id uuid NOT NULL, version integer NOT NULL,
 domain fp6_data.domain_name NOT NULL, relationship_type fp6_data.relation_type NOT NULL,
 realm varchar(9) NOT NULL CHECK (realm = 'synthetic'),
 PRIMARY KEY (directory_id, version, domain, relationship_type, realm),
 FOREIGN KEY (directory_id, version, domain, realm)
 REFERENCES fp6_reference.directory_versions (directory_id, version, domain, realm)
);
CREATE TABLE fp6_data.user_actions (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL, generation integer NOT NULL,
 finding_id uuid NOT NULL, domain fp6_data.domain_name NOT NULL,
 relationship_type fp6_data.relation_type NOT NULL,
 directory_id uuid NOT NULL, directory_version integer NOT NULL,
 realm varchar(9) NOT NULL CHECK (realm = 'synthetic'),
 status varchar(12) NOT NULL CHECK (status IN ('not_started','opened')),
 PRIMARY KEY (owner_id, collection_id, generation, finding_id, directory_id, directory_version),
 FOREIGN KEY (owner_id, collection_id, generation, finding_id, domain, relationship_type)
 REFERENCES fp6_data.findings
 (owner_id, collection_id, generation, finding_id, domain, relationship_type),
 FOREIGN KEY (directory_id, directory_version, domain, relationship_type, realm)
 REFERENCES fp6_reference.action_eligibility
);
CREATE TABLE fp6_data.deletion_requests (
 owner_id uuid NOT NULL REFERENCES fp6_data.tenant_state,
 request_id uuid NOT NULL, collection_id uuid, source_id uuid,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 operation varchar(16) NOT NULL CHECK (operation IN ('source','collection','withdrawal','account','expiry')),
 state varchar(20) NOT NULL CHECK (state IN ('pending','live_data_removed','completed')),
 affected_count integer NOT NULL CHECK (affected_count BETWEEN 0 AND 10000),
 PRIMARY KEY (owner_id, request_id),
 UNIQUE (owner_id, request_id, consent_epoch, revision),
 FOREIGN KEY (owner_id, collection_id) REFERENCES fp6_data.collections,
 FOREIGN KEY (owner_id, collection_id, source_id) REFERENCES fp6_data.import_sources,
 CHECK ((operation = 'source' AND collection_id IS NOT NULL AND source_id IS NOT NULL)
     OR (operation = 'collection' AND collection_id IS NOT NULL AND source_id IS NULL)
     OR (operation IN ('withdrawal','account','expiry') AND source_id IS NULL))
);
CREATE TABLE fp6_data.outbox (
 owner_id uuid NOT NULL, event_id uuid NOT NULL, request_id uuid NOT NULL,
 consent_epoch integer NOT NULL, revision bigint NOT NULL,
 state varchar(12) NOT NULL CHECK (state IN ('pending','acknowledged')),
 journal_sequence bigint CHECK (journal_sequence > 0),
 PRIMARY KEY (owner_id, event_id), UNIQUE (owner_id, request_id),
 FOREIGN KEY (owner_id, request_id, consent_epoch, revision)
 REFERENCES fp6_data.deletion_requests (owner_id, request_id, consent_epoch, revision),
 CHECK ((state = 'acknowledged') = (journal_sequence IS NOT NULL))
);
CREATE TABLE fp6_data.idempotency_records (
 owner_id uuid NOT NULL REFERENCES fp6_data.tenant_state,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 key uuid NOT NULL,
 operation varchar(16) NOT NULL CHECK (operation IN ('save','source','collection','withdrawal','account','expiry','action')),
 request_hmac bytea NOT NULL CHECK (octet_length(request_hmac) = 32),
 request_id uuid,
 state varchar(12) NOT NULL CHECK (state IN ('pending','completed')),
 PRIMARY KEY (owner_id, consent_epoch, key),
 FOREIGN KEY (owner_id, request_id, consent_epoch, revision)
 REFERENCES fp6_data.deletion_requests (owner_id, request_id, consent_epoch, revision)
);
-- Minimal local ledger projection, NOT the independently durable 6D journal.
-- No FK back to deletable data. A test downgrade must retain these rows.
CREATE TABLE IF NOT EXISTS fp6_ledger.deletion_journal (
 owner_id uuid NOT NULL, event_id uuid NOT NULL,
 journal_sequence bigint NOT NULL CHECK (journal_sequence > 0),
 operation varchar(16) NOT NULL CHECK (operation IN ('source','collection','withdrawal','account','expiry')),
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 PRIMARY KEY (owner_id, event_id), UNIQUE (owner_id, journal_sequence)
);

-- Central exhaustive policy installation, including lifecycle and journal rows.
DO $$ DECLARE item record;
BEGIN
 FOR item IN SELECT schemaname, tablename FROM pg_catalog.pg_tables
 WHERE schemaname IN ('fp6_data','fp6_ledger') LOOP
   EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', item.schemaname, item.tablename);
   EXECUTE format('ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY', item.schemaname, item.tablename);
   EXECUTE format('DROP POLICY IF EXISTS tenant_owner ON %I.%I', item.schemaname, item.tablename);
   EXECUTE format('CREATE POLICY tenant_owner ON %I.%I TO fp6_runtime USING '
    || '(owner_id = fp6_context.owner_id()) WITH CHECK (owner_id = fp6_context.owner_id())',
    item.schemaname, item.tablename);
 END LOOP;
END $$;
-- Block owner adoption even within an otherwise empty object. Keys never cascade.
CREATE OR REPLACE FUNCTION fp6_context.immutable_owner() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 IF NEW.owner_id IS DISTINCT FROM OLD.owner_id THEN
  RAISE EXCEPTION 'immutable owner' USING ERRCODE = '23514';
 END IF;
 RETURN NEW;
END $$;
DO $$ DECLARE item record;
BEGIN
 FOR item IN SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname = 'fp6_data' LOOP
  EXECUTE format('CREATE TRIGGER immutable_owner BEFORE UPDATE ON fp6_data.%I '
   || 'FOR EACH ROW EXECUTE FUNCTION fp6_context.immutable_owner()', item.tablename);
 END LOOP;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA fp6_context FROM PUBLIC;
GRANT USAGE ON SCHEMA fp6_data, fp6_ledger, fp6_reference TO fp6_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA fp6_data TO fp6_runtime;
REVOKE UPDATE, DELETE ON fp6_data.consents, fp6_data.observations,
 fp6_data.observation_features, fp6_data.context_evidence, fp6_data.excluded_rows FROM fp6_runtime;
-- Membership identities are replaced through delete/insert, never moved to a
-- different group by UPDATE; deferred lower bounds then inspect the old group.
REVOKE UPDATE ON fp6_data.evidence_equivalence, fp6_data.commercial_alias_members FROM fp6_runtime;
GRANT SELECT, INSERT ON fp6_ledger.deletion_journal TO fp6_runtime;
GRANT SELECT ON ALL TABLES IN SCHEMA fp6_reference TO fp6_runtime;
-- No grants at all to restore. No security-definer footprint access or worker bypass.

-- Serialize source/row budget checks on an owned parent, including concurrent
-- inserts. No SECURITY DEFINER, unscoped scans or cross-owner lock acquisition.
CREATE OR REPLACE FUNCTION fp6_context.source_budget() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 -- A real row version change also makes Repeatable Read reject stale snapshots.
 UPDATE fp6_data.collections SET lifecycle=lifecycle
 WHERE owner_id = NEW.owner_id AND collection_id = NEW.collection_id;
 IF (SELECT COALESCE(sum(record_count),0) FROM fp6_data.import_sources
     WHERE owner_id = NEW.owner_id AND collection_id = NEW.collection_id
       AND source_id <> NEW.source_id) + NEW.record_count > 10000 THEN
  RAISE EXCEPTION 'source budget' USING ERRCODE = '23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER source_budget BEFORE INSERT OR UPDATE ON fp6_data.import_sources
 FOR EACH ROW EXECUTE FUNCTION fp6_context.source_budget();
CREATE OR REPLACE FUNCTION fp6_context.row_slot() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 UPDATE fp6_data.import_sources SET lifecycle=lifecycle WHERE owner_id = NEW.owner_id
 AND collection_id = NEW.collection_id AND source_id = NEW.source_id;
 IF TG_TABLE_NAME = 'observations' THEN
  IF EXISTS (SELECT 1 FROM fp6_data.excluded_rows WHERE owner_id = NEW.owner_id
      AND collection_id = NEW.collection_id AND source_id = NEW.source_id
      AND record_index = NEW.record_index) THEN
   RAISE EXCEPTION 'occupied row' USING ERRCODE = '23514';
  END IF;
 ELSE
  IF EXISTS (SELECT 1 FROM fp6_data.observations WHERE owner_id = NEW.owner_id
      AND collection_id = NEW.collection_id AND source_id = NEW.source_id
      AND record_index = NEW.record_index) THEN
   RAISE EXCEPTION 'occupied row' USING ERRCODE = '23514';
  END IF;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER row_slot BEFORE INSERT ON fp6_data.observations
 FOR EACH ROW EXECUTE FUNCTION fp6_context.row_slot();
CREATE TRIGGER row_slot BEFORE INSERT ON fp6_data.excluded_rows
 FOR EACH ROW EXECUTE FUNCTION fp6_context.row_slot();

CREATE OR REPLACE FUNCTION fp6_context.group_bounds() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
DECLARE o uuid; c uuid; g uuid; members integer;
BEGIN
 IF TG_OP = 'DELETE' THEN o := OLD.owner_id; c := OLD.collection_id; g := OLD.group_id;
 ELSE o := NEW.owner_id; c := NEW.collection_id; g := NEW.group_id; END IF;
 IF o IS DISTINCT FROM fp6_context.owner_id() THEN
  RAISE EXCEPTION 'missing group owner context' USING ERRCODE='23514';
 END IF;
 UPDATE fp6_data.collections SET lifecycle=lifecycle WHERE owner_id=o AND collection_id=c;
 IF TG_TABLE_NAME IN ('evidence_groups','evidence_equivalence') THEN
  IF NOT EXISTS (SELECT 1 FROM fp6_data.evidence_groups
   WHERE owner_id=o AND collection_id=c AND group_id=g) THEN RETURN NULL; END IF;
  SELECT count(*) INTO members FROM fp6_data.evidence_equivalence
   WHERE owner_id=o AND collection_id=c AND group_id=g;
  IF members < 2 THEN RAISE EXCEPTION 'equivalence bounds' USING ERRCODE='23514'; END IF;
 ELSE
  IF NOT EXISTS (SELECT 1 FROM fp6_data.commercial_groups
   WHERE owner_id=o AND collection_id=c AND group_id=g) THEN RETURN NULL; END IF;
  SELECT count(*) INTO members FROM fp6_data.commercial_alias_members
   WHERE owner_id=o AND collection_id=c AND group_id=g;
  IF members < 1 THEN RAISE EXCEPTION 'alias bounds' USING ERRCODE='23514'; END IF;
 END IF;
 RETURN NULL;
END $$;
CREATE CONSTRAINT TRIGGER group_bounds AFTER INSERT OR UPDATE ON fp6_data.evidence_groups
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fp6_context.group_bounds();
CREATE CONSTRAINT TRIGGER group_bounds AFTER INSERT OR UPDATE OR DELETE ON fp6_data.evidence_equivalence
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fp6_context.group_bounds();
CREATE CONSTRAINT TRIGGER group_bounds AFTER INSERT OR UPDATE ON fp6_data.commercial_groups
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fp6_context.group_bounds();
CREATE CONSTRAINT TRIGGER group_bounds AFTER INSERT OR UPDATE OR DELETE ON fp6_data.commercial_alias_members
 DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION fp6_context.group_bounds();
CREATE OR REPLACE FUNCTION fp6_context.alias_budget() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 UPDATE fp6_data.collections SET lifecycle=lifecycle
  WHERE owner_id=NEW.owner_id AND collection_id=NEW.collection_id;
 IF (SELECT count(*) FROM fp6_data.commercial_alias_members
  WHERE owner_id=NEW.owner_id AND collection_id=NEW.collection_id
    AND observation_id=NEW.observation_id AND group_id<>NEW.group_id) >= 8 THEN
  RAISE EXCEPTION 'alias budget' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER alias_budget BEFORE INSERT OR UPDATE ON fp6_data.commercial_alias_members
 FOR EACH ROW EXECUTE FUNCTION fp6_context.alias_budget();
CREATE OR REPLACE FUNCTION fp6_context.context_eligible() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 IF EXISTS (SELECT 1 FROM fp6_data.observations
  WHERE owner_id=NEW.owner_id AND collection_id=NEW.collection_id
   AND observation_id=NEW.observation_id AND issue_code IS NOT NULL) THEN
  RAISE EXCEPTION 'ineligible context' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER context_eligible BEFORE INSERT ON fp6_data.context_evidence
 FOR EACH ROW EXECUTE FUNCTION fp6_context.context_eligible();
