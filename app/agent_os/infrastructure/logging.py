"""Structured logging for agent runs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class RunEvent:
    run_id: str
    task_id: str
    agent: str
    status: str
    duration_ms: int
    details: dict


class StructuredLogger:
    def __init__(self, base_dir: Path) -> None:
        self.log_file = base_dir / "outputs" / "reports" / "agentctl-runs.ndjson"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: RunEvent) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "run_id": event.run_id,
            "task_id": event.task_id,
            "agent": event.agent,
            "status": event.status,
            "duration_ms": event.duration_ms,
            "details": event.details,
        }
        with self.log_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")
