"""Faithful retained model state, before any Pydantic serializer can omit it."""

from typing import cast

from app.contracts import Contract
from experiments.minimized_contract import (
    MAX_BODY,
    MAX_ROWS,
    AdmissionEnvelope,
    CommercialGroup,
    Context,
    EmailObservation,
    Excluded,
    HistoryObservation,
    MinimizedBatch,
    Source,
)

MODELS = (
    AdmissionEnvelope,
    MinimizedBatch,
    Source,
    EmailObservation,
    HistoryObservation,
    Excluded,
    Context,
    CommercialGroup,
)


def model_input(model: AdmissionEnvelope | MinimizedBatch) -> dict[str, object]:
    """Reject unexpected state, then copy retained fields without serializing input.

    This cannot reconstruct data already discarded by an earlier constructor.
    It is not a sandbox against code modifying classes or the Python interpreter.
    """
    remaining = MAX_BODY

    def visit(value: object, depth: int) -> object:
        nonlocal remaining
        remaining -= 1
        if remaining < 0 or depth > 8:
            raise ValueError("invalid evidence")
        if type(value) in MODELS:
            assert isinstance(value, Contract)
            state = object.__getattribute__(value, "__dict__")
            fields = set(type(value).model_fields)
            supplied = object.__getattribute__(value, "__pydantic_fields_set__")
            if (
                type(state) is not dict
                or any(type(key) is not str for key in state)
                or set(state) != fields
                or type(supplied) is not set
                or any(type(key) is not str for key in supplied)
                or supplied != fields
                or object.__getattribute__(value, "__pydantic_extra__") is not None
                or object.__getattribute__(value, "__pydantic_private__") is not None
            ):
                raise ValueError("invalid evidence")
            return {key: visit(state[key], depth + 1) for key in state}
        if type(value) is list:
            if len(value) > MAX_ROWS:
                raise ValueError("invalid evidence")
            return [visit(child, depth + 1) for child in value]
        if type(value) is str:
            remaining -= len(value)
            if remaining < 0:
                raise ValueError("invalid evidence")
            return value
        if value is None or type(value) is int:
            return value
        # No bool/int coercion, model subclasses, arbitrary mappings or objects.
        raise ValueError("invalid evidence")

    try:
        if type(model) not in (AdmissionEnvelope, MinimizedBatch):
            raise ValueError("invalid evidence")
        return cast(dict[str, object], visit(model, 1))
    except Exception:
        # Never reflect object representations, field names or serializer details.
        raise ValueError("invalid evidence") from None
