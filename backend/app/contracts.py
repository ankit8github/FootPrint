"""Read-only v1 vocabulary, not an ingestion or classification implementation."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Adapter = Literal["email_eml_v1", "browser_chrome_json_v1"]
ObservationKind = Literal[
    "site_visit_observed",
    "registration_email_detected",
    "transaction_email_detected",
    "marketing_email_detected",
    "account_notification_detected",
    "unclassified_observation",
]
SummaryCode = Literal[
    "VISIT_RECORDED",
    "WELCOME_MESSAGE_PATTERN",
    "ORDER_CONFIRMATION_PATTERN",
    "MARKETING_PATTERN",
    "ACCOUNT_NOTIFICATION_PATTERN",
    "UNCLASSIFIED",
]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Observation(Contract):
    """Future minimized output. No arbitrary metadata or raw-content fields."""

    observation_id: UUID
    batch_id: UUID
    adapter: Adapter
    kind: ObservationKind
    domain: Annotated[str, Field(min_length=3, max_length=253)] | None
    occurred_at: AwareDatetime | None
    summary_code: SummaryCode


class Evidence(Contract):
    relationship_id: UUID
    observation_id: UUID
    evidence_role: Literal["primary", "corroborating", "context"]


class Assessment(Contract):
    relationship_id: UUID
    evidence_state: Literal["observed", "inferred"]
    confidence: Literal["high", "medium", "low", "insufficient"]
    review_priority: Literal["sensitive", "medium", "low", "unknown"]
    retention_status: Literal["unknown"] = "unknown"
    data_sale_status: Literal["unknown"] = "unknown"
    rationale_codes: Annotated[
        list[
            Literal[
                "TRANSACTION_INDICATION",
                "IDENTITY_CONTEXT",
                "HEALTH_CONTEXT",
                "ACCOUNT_RELATIONSHIP",
                "MARKETING_ONLY",
                "VISIT_ONLY",
                "AMBIGUOUS_EVIDENCE",
            ]
        ],
        Field(max_length=7),
    ]
    # No generated explanations or rules exist in Phase 0.
    limitations: tuple[Literal["PHASE0_NO_ANALYSIS"], ...] = ("PHASE0_NO_ANALYSIS",)
    ruleset_version: Literal["not_implemented"] = "not_implemented"


class Health(Contract):
    api_version: Literal["v1"] = "v1"
    status: Literal["ok"] = "ok"
    mode: Literal["synthetic_demo"] = "synthetic_demo"


class DemoSnapshot(Contract):
    api_version: Literal["v1"] = "v1"
    mode: Literal["synthetic_demo"] = "synthetic_demo"
    observations: Annotated[list[Observation], Field(max_length=0)] = Field(default_factory=list)
    evidence: Annotated[list[Evidence], Field(max_length=0)] = Field(default_factory=list)
    assessments: Annotated[list[Assessment], Field(max_length=0)] = Field(default_factory=list)
