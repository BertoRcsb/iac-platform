"""Task schema validation helpers."""

from __future__ import annotations

from .constants import PRIORITIES, TASK_SCHEMA_VERSION, TASK_STATES


class TaskSchemaError(ValueError):
    """Raised when task payload violates schema expectations."""


def validate_task_payload(payload: dict) -> None:
    required_top = [
        "schema_version",
        "task_id",
        "state",
        "created_at",
        "updated_at",
        "source",
        "request",
        "classification",
        "plan",
        "routing",
        "execution",
        "review",
        "learning",
        "history",
    ]
    for key in required_top:
        if key not in payload:
            raise TaskSchemaError(f"Missing required key: {key}")

    if payload["schema_version"] != TASK_SCHEMA_VERSION:
        raise TaskSchemaError(
            f"Unsupported schema version: {payload['schema_version']} (expected {TASK_SCHEMA_VERSION})"
        )

    state = payload["state"]
    if state not in TASK_STATES:
        raise TaskSchemaError(f"Invalid state '{state}'. Valid states: {TASK_STATES}")

    category = (payload.get("classification") or {}).get("category", "general")
    if not category:
        raise TaskSchemaError("Classification category cannot be empty")

    priority = (payload.get("classification") or {}).get("priority", "P3")
    if priority not in PRIORITIES:
        raise TaskSchemaError(f"Invalid priority '{priority}'. Valid priorities: {PRIORITIES}")

    source = payload.get("source") or {}
    if "type" not in source or "reference" not in source:
        raise TaskSchemaError("Source must contain 'type' and 'reference'")

    context = payload.get("context")
    if context is not None and not isinstance(context, dict):
        raise TaskSchemaError("Context must be an object when present")

    if not isinstance(payload.get("history"), list):
        raise TaskSchemaError("History must be a list")
