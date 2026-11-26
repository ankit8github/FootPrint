-- REVIEW TEXT ONLY. Not an Alembic revision; no application imports or runner.
-- Core of the proposed fresh-synthetic fp6_live contract, not the complete typed
-- projection. Requires approved roles, the exact PR14 global package catalog,
-- empty old fp6_data storage and a reviewed complete DDL inventory first.
-- NEVER run against a nonempty legacy graph. No old trigger/FK/hash is changed.

CREATE SCHEMA fp6_live AUTHORIZATION fp6_owner;
REVOKE ALL ON SCHEMA fp6_live FROM PUBLIC;

-- New global build facts; deliberately no fabricated digest/seed row. The full
-- migration must make this catalog immutable, FORCE RLS and SELECT-only to runtime.
CREATE TABLE fp6_reference.isolation_profiles (
 profile_id varchar(32) PRIMARY KEY,
 manifest_sha256 varchar(64) NOT NULL,
 runtime_sha256 varchar(64) NOT NULL,
 runner_sha256 varchar(64) NOT NULL,
 filter_sha256 varchar(64) NOT NULL,
 UNIQUE(profile_id,manifest_sha256,runtime_sha256,runner_sha256,filter_sha256)
);

CREATE TABLE fp6_live.controls (
 owner_id uuid PRIMARY KEY REFERENCES fp6_auth.users,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 generation_highwater integer NOT NULL CHECK (generation_highwater BETWEEN 0 AND 1000000),
 lifecycle varchar(16) NOT NULL CHECK (lifecycle IN ('active','pending_delete','disabled'))
);
CREATE TABLE fp6_live.collections (
 owner_id uuid NOT NULL REFERENCES fp6_live.controls,
 collection_id uuid NOT NULL,
 current_generation integer NOT NULL CHECK (current_generation BETWEEN 1 AND 1000000),
 lifecycle varchar(16) NOT NULL CHECK (lifecycle IN ('active','pending_delete','unavailable')),
 expires_at timestamptz NOT NULL,
 PRIMARY KEY(owner_id,collection_id), UNIQUE(owner_id)
 -- The seven unchanged semantic/explanation CHECK columns from 6c02.collections
 -- must be included in the complete reviewed DDL; this kernel is not deployable.
);
CREATE TABLE fp6_live.generations (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL,
 generation integer NOT NULL CHECK (generation BETWEEN 1 AND 1000000),
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 expected_revision bigint NOT NULL CHECK (expected_revision BETWEEN 0 AND 1000000000),
 execution_id uuid NOT NULL,
 package_revision varchar(16) NOT NULL CHECK (package_revision='indexed-r1'),
 manifest_sha256 varchar(64) NOT NULL,
 worker_sha256 varchar(64) NOT NULL,
 pure_sha256 varchar(64) NOT NULL,
 isolation_profile varchar(32) NOT NULL,
 isolation_manifest_sha256 varchar(64) NOT NULL,
 runtime_sha256 varchar(64) NOT NULL,
 runner_sha256 varchar(64) NOT NULL,
 filter_sha256 varchar(64) NOT NULL,
 PRIMARY KEY(owner_id,collection_id,generation), UNIQUE(owner_id,execution_id),
 FOREIGN KEY(owner_id,collection_id) REFERENCES fp6_live.collections,
 CONSTRAINT exact_live_package FOREIGN KEY
  (package_revision,manifest_sha256,worker_sha256,pure_sha256)
  REFERENCES fp6_reference.implementation_packages
  (package_revision,manifest_sha256,worker_sha256,pure_sha256),
 CONSTRAINT exact_isolation_profile FOREIGN KEY
  (isolation_profile,isolation_manifest_sha256,runtime_sha256,runner_sha256,filter_sha256)
  REFERENCES fp6_reference.isolation_profiles
  (profile_id,manifest_sha256,runtime_sha256,runner_sha256,filter_sha256)
);
ALTER TABLE fp6_live.collections ADD CONSTRAINT current_bound_generation
 FOREIGN KEY(owner_id,collection_id,current_generation)
 REFERENCES fp6_live.generations DEFERRABLE INITIALLY DEFERRED;

-- Pending target IDs are opaque control identities, not observations or payloads.
-- No foreign key back to a deletable collection, generation or source.
CREATE TABLE fp6_live.erasure_intents (
 owner_id uuid NOT NULL REFERENCES fp6_live.controls,
 event_id uuid NOT NULL, collection_id uuid, source_id uuid,
 consent_epoch integer NOT NULL CHECK (consent_epoch BETWEEN 1 AND 1000000),
 revision bigint NOT NULL CHECK (revision BETWEEN 0 AND 1000000000),
 operation varchar(16) NOT NULL CHECK
  (operation IN ('source','collection','withdrawal','account','expiry')),
 state varchar(20) NOT NULL CHECK (state IN ('pending','live_data_removed','completed')),
 PRIMARY KEY(owner_id,event_id), UNIQUE(owner_id,event_id,consent_epoch,revision),
 CHECK ((operation='source' AND collection_id IS NOT NULL AND source_id IS NOT NULL)
  OR (operation='collection' AND collection_id IS NOT NULL AND source_id IS NULL)
  OR (operation IN ('withdrawal','account','expiry') AND source_id IS NULL))
);
CREATE TABLE fp6_live.erasure_outbox (
 owner_id uuid NOT NULL, event_id uuid NOT NULL,
 consent_epoch integer NOT NULL, revision bigint NOT NULL,
 state varchar(12) NOT NULL CHECK (state IN ('pending','acknowledged')),
 journal_sequence bigint CHECK (journal_sequence>0),
 PRIMARY KEY(owner_id,event_id),
 FOREIGN KEY(owner_id,event_id,consent_epoch,revision)
  REFERENCES fp6_live.erasure_intents(owner_id,event_id,consent_epoch,revision),
 CHECK ((state='acknowledged')=(journal_sequence IS NOT NULL))
);

-- The controller must already hold the owner lock. This trigger independently
-- locks/rechecks the same owner before any generation identity becomes visible.
CREATE FUNCTION fp6_live.check_generation_insert() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE state_row fp6_live.controls%ROWTYPE;
BEGIN
 IF NEW.owner_id IS DISTINCT FROM fp6_context.owner_id() THEN
  RAISE EXCEPTION 'owner context required' USING ERRCODE='42501';
 END IF;
 SELECT * INTO STRICT state_row FROM fp6_live.controls
  WHERE owner_id=NEW.owner_id FOR UPDATE;
 IF NEW.consent_epoch<>state_row.consent_epoch
  OR NEW.expected_revision<>state_row.revision
  OR NEW.generation<>state_row.generation_highwater+1
  OR NOT (state_row.lifecycle='active' OR
   (current_user='fp6_purger' AND state_row.lifecycle='pending_delete'
    AND EXISTS (SELECT 1 FROM fp6_live.erasure_intents i
     WHERE i.owner_id=NEW.owner_id AND i.collection_id=NEW.collection_id
      AND i.consent_epoch=NEW.consent_epoch AND i.revision=NEW.expected_revision
      AND i.operation='source' AND i.state='pending'))) THEN
  RAISE EXCEPTION 'stale generation' USING ERRCODE='23514';
 END IF;
 UPDATE fp6_live.controls SET generation_highwater=NEW.generation WHERE owner_id=NEW.owner_id;
 RETURN NEW;
END $$;
CREATE TRIGGER check_generation_insert BEFORE INSERT ON fp6_live.generations
 FOR EACH ROW EXECUTE FUNCTION fp6_live.check_generation_insert();

CREATE FUNCTION fp6_live.protect_generation() RETURNS trigger
LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP<>'DELETE' THEN
  RAISE EXCEPTION 'immutable live generation' USING ERRCODE='42501';
 END IF;
 IF current_user<>'fp6_purger' OR OLD.owner_id IS DISTINCT FROM fp6_context.owner_id() THEN
  RAISE EXCEPTION 'purger required' USING ERRCODE='42501';
 END IF;
 PERFORM 1 FROM fp6_live.controls WHERE owner_id=OLD.owner_id
  AND lifecycle='pending_delete' FOR UPDATE;
 IF NOT FOUND OR NOT EXISTS (
  SELECT 1 FROM fp6_live.erasure_intents i JOIN fp6_live.controls t USING(owner_id)
  WHERE i.owner_id=OLD.owner_id AND i.state='pending'
   AND i.consent_epoch=t.consent_epoch AND i.revision=t.revision
   AND (i.collection_id=OLD.collection_id OR i.operation IN ('withdrawal','account','expiry'))
   AND (i.operation<>'source' OR NOT EXISTS (
    SELECT 1 FROM fp6_live.collections c WHERE c.owner_id=OLD.owner_id
     AND c.collection_id=OLD.collection_id AND c.current_generation=OLD.generation))) THEN
  RAISE EXCEPTION 'valid fenced intent required' USING ERRCODE='42501';
 END IF;
 RETURN OLD;
END $$;
CREATE TRIGGER protect_generation BEFORE UPDATE OR DELETE ON fp6_live.generations
 FOR EACH ROW EXECUTE FUNCTION fp6_live.protect_generation();
CREATE TRIGGER protect_generation_truncate BEFORE TRUNCATE ON fp6_live.generations
 FOR EACH STATEMENT EXECUTE FUNCTION fp6_live.protect_generation();

-- Apply these explicit policies/grants to EVERY new personal table after its
-- complete typed CREATE TABLE; no dynamic table discovery or wildcard grants.
ALTER TABLE fp6_live.generations ENABLE ROW LEVEL SECURITY;
ALTER TABLE fp6_live.generations FORCE ROW LEVEL SECURITY;
CREATE POLICY live_owner ON fp6_live.generations TO fp6_runtime,fp6_purger
 USING(owner_id=fp6_context.owner_id()) WITH CHECK(owner_id=fp6_context.owner_id());
REVOKE ALL ON fp6_live.generations FROM PUBLIC;
GRANT SELECT,INSERT ON fp6_live.generations TO fp6_runtime;
GRANT SELECT,INSERT,DELETE ON fp6_live.generations TO fp6_purger;
REVOKE ALL ON FUNCTION fp6_live.check_generation_insert(),fp6_live.protect_generation() FROM PUBLIC;

-- Required complete-migration additions, deliberately NOT fabricated here:
-- explicit controls/collection update guards, active-generation read views,
-- unchanged typed source/observation/group/finding/support/assessment/action
-- tables, per-table RLS/grants, bounded intents/outbox/idempotency, monotonic
-- protected highwater, signed-in principal/consent/policy/expiry commit checks,
-- per-target purge authorization, auth erasure permissions and online/offline
-- verification. No caller-GUC "allow_delete" flag or trigger-disable escape.
