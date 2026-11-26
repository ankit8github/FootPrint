"""Partial seed-reference codec only; durable projection stopped at C03-COMP-01.

Only original whole-envelope catalog seeds are accepted. UUIDs are independent
of minimized values. No result mapping, survivor publication, SQL projection,
database write or serving entry is implemented by this stopped module.
"""

import hashlib
from dataclasses import dataclass
from uuid import UUID, uuid4

from experiments.admission_registry import SyntheticRegistry
from experiments.minimized_contract import MinimizedBatch, canonical, parse_json


class ProvenanceRejected(Exception):
    def __init__(self) -> None:
        super().__init__("PROVENANCE_REJECTED")


@dataclass(frozen=True, slots=True)
class Scope:
    owner: UUID
    collection: UUID
    generation: int

    def check(self) -> None:
        if (
            type(self) is not Scope
            or any(type(v) is not UUID or v.int == 0 for v in (self.owner, self.collection))
            or type(self.generation) is not int
            or not 1 <= self.generation <= 1_000_000
        ):
            raise ProvenanceRejected()


@dataclass(frozen=True, slots=True)
class Binding:
    scope: Scope
    kind: str
    local: str
    identity: UUID


@dataclass(frozen=True, slots=True)
class Seed:
    scope: Scope
    raw: bytes
    origin_digest: str
    bindings: tuple[Binding, ...]


def _keys(batch: MinimizedBatch) -> list[tuple[str, str]]:
    return (
        [("source", s.source_id) for s in batch.sources]
        + [("observation", o.id) for o in batch.observations]
        + [("excluded", e.event_id) for e in batch.excluded]
        + [("duplicate_group", str(i)) for i in range(len(batch.duplicate_groups))]
        + [("commercial_group", g.alias) for g in batch.commercial_groups]
    )


def seed_catalog(raw: bytes, scope: Scope) -> Seed:
    scope.check()
    if type(raw) is not bytes:
        raise ProvenanceRejected()
    batch = MinimizedBatch.model_validate(parse_json(raw))
    SyntheticRegistry().admit(batch)
    payload = canonical(batch)
    return Seed(
        scope,
        payload,
        hashlib.sha256(payload).hexdigest(),
        tuple(Binding(scope, kind, local, uuid4()) for kind, local in _keys(batch)),
    )


def validate_seed(seed: Seed, expected: Scope) -> MinimizedBatch:
    try:
        expected.check()
        if type(seed) is not Seed or type(seed.scope) is not Scope or seed.scope != expected:
            raise ProvenanceRejected()
        seed.scope.check()
        if (
            type(seed.raw) is not bytes
            or hashlib.sha256(seed.raw).hexdigest() != seed.origin_digest
        ):
            raise ProvenanceRejected()
        batch = MinimizedBatch.model_validate(parse_json(seed.raw))
        SyntheticRegistry().admit(batch)
        if canonical(batch) != seed.raw or type(seed.bindings) is not tuple:
            raise ProvenanceRejected()
        expected_keys = _keys(batch)
        if len(seed.bindings) != len(expected_keys):
            raise ProvenanceRejected()
        identities: set[UUID] = set()
        for binding, (kind, local) in zip(seed.bindings, expected_keys, strict=True):
            if (
                type(binding) is not Binding
                or type(binding.scope) is not Scope
                or binding.scope != expected
                or binding.kind != kind
                or binding.local != local
                or type(binding.identity) is not UUID
                or binding.identity.int == 0
                or binding.identity in identities
            ):
                raise ProvenanceRejected()
            identities.add(binding.identity)
        return batch
    except Exception:
        raise ProvenanceRejected() from None
