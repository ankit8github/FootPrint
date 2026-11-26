"""Disabled synthetic indexing copy; original contract remains authoritative.

All inherited fields/validators and the reference method are copied unchanged,
except the final ordered alias membership lookup. No application imports this.
"""

from typing import Self

from pydantic import model_validator

from experiments.minimized_contract import (
    COMMERCIAL,
    MAX_ROWS,
    EmailObservation,
    MinimizedBatch,
    Observation,
)


class IndexedBatch(MinimizedBatch):
    @model_validator(mode="after")
    def references(self) -> Self:
        def require(condition: bool) -> None:
            if not condition:
                raise ValueError("invalid evidence")

        require(sum(s.record_count for s in self.sources) <= MAX_ROWS)
        sources = {s.source_id: s for s in self.sources}
        require(
            [s.source_id for s in self.sources] == [f"s{i + 1:04}" for i in range(len(sources))]
        )
        rows: set[str] = set()
        observations = {o.id: o for o in self.observations}
        require(len(observations) == len(self.observations))
        for row in [*self.observations, *self.excluded]:
            identifier = row.id if isinstance(row, Observation) else row.event_id
            source = sources.get(row.source_id)
            require(source is not None)
            assert source is not None
            require(row.record_index < source.record_count)
            require(identifier == f"{row.source_id}:r{row.record_index:05}")
            require(identifier not in rows)
            rows.add(identifier)
            if isinstance(row, Observation):
                require(row.adapter == source.adapter)
        require(len(rows) == sum(s.record_count for s in self.sources))
        # Duplicate membership is complete and direct: no unscoped/group fallback.
        grouped: set[str] = set()
        duplicates: set[str] = set()
        for group in self.duplicate_groups:
            require(len(set(group)) == len(group) and not grouped.intersection(group))
            grouped.update(group)
            primary = observations.get(group[0])
            require(primary is not None and primary.duplicate_of is None)
            assert primary is not None
            for member in group[1:]:
                copy = observations.get(member)
                require(copy is not None and copy.duplicate_of == primary.id)
                assert copy is not None
                require(
                    all(
                        getattr(copy, k) == getattr(primary, k)
                        for k in (
                            "adapter",
                            "kind",
                            "domain",
                            "occurred_at",
                            "time_status",
                            "features",
                            "order_keys",
                            "issue_code",
                            "attribution",
                        )
                    )
                )
                duplicates.add(member)
        require(duplicates == {o.id for o in self.observations if o.duplicate_of is not None})
        require(len({c.observation_id for c in self.contexts}) == len(self.contexts))
        for context in self.contexts:
            observation = observations.get(context.observation_id)
            require(isinstance(observation, EmailObservation))
            assert isinstance(observation, EmailObservation)
            require(observation.issue_code is None and "ACCOUNT_REQUEST" in observation.features)
        aliases = list(dict.fromkeys(alias for o in self.observations for alias in o.order_keys))
        require([g.alias for g in self.commercial_groups] == aliases)
        require(aliases == [f"order{i + 1:04}" for i in range(len(aliases))])
        # Batch-local ordered membership, including foreign-domain rows so the
        # unchanged domain check below still rejects them. Never retained or shared.
        alias_members: dict[str, list[Observation]] = {}
        for observation in self.observations:
            for alias in dict.fromkeys(observation.order_keys):
                alias_members.setdefault(alias, []).append(observation)
        for commercial in self.commercial_groups:
            members = alias_members.get(commercial.alias, [])
            require(commercial.members == [o.id for o in members])
            require(
                all(
                    isinstance(o, EmailObservation)
                    and o.domain == commercial.domain
                    and bool(COMMERCIAL.intersection(o.features))
                    for o in members
                )
            )
        return self
