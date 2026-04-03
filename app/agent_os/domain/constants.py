"""Domain constants for Agent OS."""

from __future__ import annotations

from typing import Final

TASK_SCHEMA_VERSION: Final[str] = "1.0"

TASK_STATES: Final[list[str]] = [
    "NEW",
    "TRIAGED",
    "PLANNED",
    "APPROVED",
    "EXECUTING",
    "REVIEW",
    "DONE",
    "BLOCKED",
]

STATE_TRANSITIONS: Final[dict[str, set[str]]] = {
    "NEW": {"TRIAGED", "BLOCKED"},
    "TRIAGED": {"PLANNED", "BLOCKED"},
    "PLANNED": {"APPROVED", "BLOCKED"},
    "APPROVED": {"EXECUTING", "BLOCKED"},
    "EXECUTING": {"REVIEW", "BLOCKED"},
    "REVIEW": {"DONE", "BLOCKED"},
    "DONE": set(),
    "BLOCKED": {"TRIAGED", "PLANNED", "APPROVED", "EXECUTING", "REVIEW", "DONE"},
}

STATE_ORDER: Final[dict[str, int]] = {name: index for index, name in enumerate(TASK_STATES)}

CATEGORIES: Final[list[str]] = [
    "general",
    "access-gcp",
    "ci-cd",
    "observability",
    "release",
    "documentation",
]

PRIORITIES: Final[list[str]] = ["P1", "P2", "P3", "P4"]
