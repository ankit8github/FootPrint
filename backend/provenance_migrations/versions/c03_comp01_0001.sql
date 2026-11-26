-- Synthetic-only candidate. Never run through an application connection.
-- Independent graph: requires intact 6c02_0001, with no existing generations.
LOCK TABLE fp6_data.generations IN ACCESS EXCLUSIVE MODE;
-- Do not infer historical bindings. Use a physical constraint validation, not
-- a tenant-filtered SELECT or an assumption about FK-validation visibility.
ALTER TABLE fp6_data.generations ADD CONSTRAINT provenance_requires_empty
 CHECK (false) NOT VALID;
ALTER TABLE fp6_data.generations VALIDATE CONSTRAINT provenance_requires_empty;
ALTER TABLE fp6_data.generations DROP CONSTRAINT provenance_requires_empty;

CREATE TABLE fp6_reference.implementation_packages (
 package_revision varchar(16) PRIMARY KEY,
 manifest_sha256 varchar(64) NOT NULL,
 worker_sha256 varchar(64) NOT NULL,
 pure_sha256 varchar(64) NOT NULL,
 UNIQUE (package_revision, manifest_sha256, worker_sha256, pure_sha256),
 CONSTRAINT recognized_immutable_package CHECK (
  manifest_sha256 = '7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055'
  AND (
   (package_revision = 'historical-v1'
    AND worker_sha256 = '69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064'
    AND pure_sha256 = '73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5')
   OR
   (package_revision = 'indexed-r1'
    AND worker_sha256 = 'f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a'
    AND pure_sha256 = '5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7')
  )
 )
);
INSERT INTO fp6_reference.implementation_packages VALUES
 ('historical-v1',
  '7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055',
  '69fcc47c8b0890c488900b4afe875aa7ce19faa6e257a691ad371fd53edff064',
  '73dbb73013b2a8ff0c364312adb6820b02a6de9ccb0d60ffd7adc9bc8cd58bb5'),
 ('indexed-r1',
  '7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055',
  'f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a',
  '5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7');
ALTER TABLE fp6_reference.implementation_packages ENABLE ROW LEVEL SECURITY;
ALTER TABLE fp6_reference.implementation_packages FORCE ROW LEVEL SECURITY;
CREATE POLICY package_read ON fp6_reference.implementation_packages
 FOR SELECT TO fp6_runtime, fp6_owner USING (true);
REVOKE ALL ON fp6_reference.implementation_packages FROM PUBLIC;
GRANT SELECT ON fp6_reference.implementation_packages TO fp6_runtime;

CREATE TABLE fp6_data.generation_implementations (
 owner_id uuid NOT NULL, collection_id uuid NOT NULL,
 generation integer NOT NULL CHECK (generation BETWEEN 1 AND 1000000),
 -- This schema revision has ONE server-selected implementation. A caller
 -- cannot select historical-v1 or inject hashes, even through direct SQL.
 package_revision varchar(16) NOT NULL CHECK (package_revision = 'indexed-r1'),
 manifest_sha256 varchar(64) NOT NULL,
 worker_sha256 varchar(64) NOT NULL,
 pure_sha256 varchar(64) NOT NULL,
 PRIMARY KEY (owner_id, collection_id, generation),
 CONSTRAINT exact_package FOREIGN KEY
  (package_revision, manifest_sha256, worker_sha256, pure_sha256)
  REFERENCES fp6_reference.implementation_packages
  (package_revision, manifest_sha256, worker_sha256, pure_sha256),
 CONSTRAINT bound_generation FOREIGN KEY (owner_id, collection_id, generation)
  REFERENCES fp6_data.generations DEFERRABLE INITIALLY DEFERRED
);
ALTER TABLE fp6_data.generation_implementations ENABLE ROW LEVEL SECURITY;
ALTER TABLE fp6_data.generation_implementations FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_owner ON fp6_data.generation_implementations TO fp6_runtime
 USING (owner_id = fp6_context.owner_id())
 WITH CHECK (owner_id = fp6_context.owner_id());
REVOKE ALL ON fp6_data.generation_implementations FROM PUBLIC;
GRANT SELECT, INSERT ON fp6_data.generation_implementations TO fp6_runtime;

CREATE FUNCTION fp6_context.immutable_implementation() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 RAISE EXCEPTION 'immutable implementation identity' USING ERRCODE = '42501';
END $$;
CREATE TRIGGER immutable_implementation BEFORE UPDATE OR DELETE
 ON fp6_reference.implementation_packages
 FOR EACH ROW EXECUTE FUNCTION fp6_context.immutable_implementation();
CREATE TRIGGER immutable_implementation_truncate BEFORE TRUNCATE
 ON fp6_reference.implementation_packages
 FOR EACH STATEMENT EXECUTE FUNCTION fp6_context.immutable_implementation();
CREATE TRIGGER immutable_implementation BEFORE UPDATE OR DELETE
 ON fp6_data.generation_implementations
 FOR EACH ROW EXECUTE FUNCTION fp6_context.immutable_implementation();
CREATE TRIGGER immutable_implementation_truncate BEFORE TRUNCATE
 ON fp6_data.generation_implementations
 FOR EACH STATEMENT EXECUTE FUNCTION fp6_context.immutable_implementation();

CREATE FUNCTION fp6_context.bind_implementation() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog AS $$
BEGIN
 IF TG_OP = 'UPDATE' THEN
  IF ROW(NEW.owner_id,NEW.collection_id,NEW.generation)
   IS DISTINCT FROM ROW(OLD.owner_id,OLD.collection_id,OLD.generation) THEN
   RAISE EXCEPTION 'immutable generation identity' USING ERRCODE = '42501';
  END IF;
  RETURN NEW;
 END IF;
 INSERT INTO fp6_data.generation_implementations VALUES
  (NEW.owner_id, NEW.collection_id, NEW.generation, 'indexed-r1',
   '7485ac86c2cd9502e1414d68df7a930ae531b209706d44b8161a736ec7e24055',
   'f4170b61857e2ae673332e4d57cd01cab5214ede7f4c3b3abef390221258670a',
   '5e980c1c1856226ef6b2ce35b9b4eb651d5860139ba6041a4ffe76ffb262d1e7');
 RETURN NEW;
END $$;
REVOKE ALL ON FUNCTION fp6_context.immutable_implementation() FROM PUBLIC;
REVOKE ALL ON FUNCTION fp6_context.bind_implementation() FROM PUBLIC;
CREATE TRIGGER bind_implementation BEFORE INSERT OR UPDATE ON fp6_data.generations
 FOR EACH ROW EXECUTE FUNCTION fp6_context.bind_implementation();

-- Immediate reverse FK makes even an in-transaction generation INSERT carry
-- its binding. The deferred bound_generation FK closes the cycle at commit.
-- Validation intentionally refuses any pre-existing unbound generation.
ALTER TABLE fp6_data.generations ADD CONSTRAINT implementation_required
 FOREIGN KEY (owner_id, collection_id, generation)
 REFERENCES fp6_data.generation_implementations;
