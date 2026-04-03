"""State machine rules for task lifecycle."""

from __future__ import annotations

from dataclasses import dataclass

from .constants import STATE_ORDER, STATE_TRANSITIONS, TASK_STATES


class InvalidStateTransitionError(ValueError):
    """Raised when a transition is not valid for the task lifecycle."""


@dataclass(frozen=True)
class StateTransition:
    from_state: str
    to_state: str
    reason: str


def ensure_valid_state(state: str) -> None:
    if state not in TASK_STATES:
        valid = ", ".join(TASK_STATES)
        raise ValueError(f"Invalid state '{state}'. Valid states: {valid}")


def can_transition(from_state: str, to_state: str) -> bool:
    ensure_valid_state(from_state)
    ensure_valid_state(to_state)
    if from_state == to_state:
        return True
    return to_state in STATE_TRANSITIONS[from_state]


def assert_transition(from_state: str, to_state: str, reason: str) -> StateTransition:
    if not can_transition(from_state, to_state):
        raise InvalidStateTransitionError(
            f"Invalid transition {from_state} -> {to_state}. "
            f"Allowed: {sorted(STATE_TRANSITIONS[from_state])}"
        )
    return StateTransition(from_state=from_state, to_state=to_state, reason=reason)


def is_at_least(current_state: str, target_state: str) -> bool:
    ensure_valid_state(current_state)
    ensure_valid_state(target_state)
    return STATE_ORDER[current_state] >= STATE_ORDER[target_state]
