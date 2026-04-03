"""Domain entities for Agent OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .constants import TASK_SCHEMA_VERSION


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class Task:
    task_id: str
    state: str
    request: str
    source_type: str
    source_reference: str
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    schema_version: str = TASK_SCHEMA_VERSION
    classification: dict[str, Any] = field(default_factory=lambda: {"category": "general", "priority": "P3", "risks": []})
    plan: dict[str, Any] = field(default_factory=lambda: {"summary": "", "steps": [], "approval_required": True})
    routing: dict[str, Any] = field(default_factory=lambda: {"provider": "none", "model": "none", "profile": "balanced", "reason": ""})
    execution: dict[str, Any] = field(
        default_factory=lambda: {
            "dry_run": True,
            "approved": False,
            "status": "PENDING",
            "logs": [],
            "approval_logs": [],
        }
    )
    review: dict[str, Any] = field(default_factory=lambda: {"status": "PENDING", "findings": [], "conclusion": ""})
    learning: dict[str, Any] = field(
        default_factory=lambda: {
            "status": "PENDING",
            "shared_doc": "",
            "scientific_method": {},
        }
    )
    context: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "task_id": self.task_id,
            "state": self.state,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": {
                "type": self.source_type,
                "reference": self.source_reference,
            },
            "request": self.request,
            "classification": self.classification,
            "plan": self.plan,
            "routing": self.routing,
            "execution": self.execution,
            "review": self.review,
            "learning": self.learning,
            "context": self.context,
            "history": self.history,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Task":
        source = data.get("source") or {}
        return Task(
            schema_version=data.get("schema_version", TASK_SCHEMA_VERSION),
            task_id=data["task_id"],
            state=data["state"],
            created_at=data.get("created_at", utc_now()),
            updated_at=data.get("updated_at", utc_now()),
            source_type=source.get("type", "unknown"),
            source_reference=source.get("reference", ""),
            request=data.get("request", ""),
            classification=data.get("classification") or {"category": "general", "priority": "P3", "risks": []},
            plan=data.get("plan") or {"summary": "", "steps": [], "approval_required": True},
            routing=data.get("routing") or {"provider": "none", "model": "none", "profile": "balanced", "reason": ""},
            execution=data.get("execution")
            or {"dry_run": True, "approved": False, "status": "PENDING", "logs": [], "approval_logs": []},
            review=data.get("review") or {"status": "PENDING", "findings": [], "conclusion": ""},
            learning=data.get("learning") or {"status": "PENDING", "shared_doc": "", "scientific_method": {}},
            context=data.get("context") or {},
            history=data.get("history") or [],
        )

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_history(self, from_state: str, to_state: str, actor: str, reason: str) -> None:
        self.history.append(
            {
                "timestamp": utc_now(),
                "from": from_state,
                "to": to_state,
                "actor": actor,
                "reason": reason,
            }
        )
        self.touch()
