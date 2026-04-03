"""File-based repository for task persistence."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from app.agent_os.domain.models import Task
from app.agent_os.domain.task_schema import validate_task_payload


class TaskRepository:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.tasks_dir = self.base_dir / "tasks" / "incoming"
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _utc_slug(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    def _slugify(self, text: str) -> str:
        raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
        compact = "-".join(part for part in raw.split("-") if part)
        return compact[:32] or "task"

    def create(self, request: str, source_type: str, source_reference: str) -> Path:
        slug = self._slugify(request)
        digest = hashlib.sha1(request.encode("utf-8")).hexdigest()[:6]
        task_id = f"task-{self._utc_slug()}-{slug}-{digest}"

        task = Task(
            task_id=task_id,
            state="NEW",
            request=request,
            source_type=source_type,
            source_reference=source_reference,
        )

        task_dir = self.tasks_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=False)
        task_file = task_dir / "task.json"
        self.save_to_path(task, task_file)
        return task_file

    def list_task_files(self) -> list[Path]:
        return sorted(self.tasks_dir.glob("*/task.json"), key=lambda p: p.stat().st_mtime, reverse=True)

    def latest(self) -> Path:
        files = self.list_task_files()
        if not files:
            raise FileNotFoundError("No task.json found in tasks/incoming")
        return files[0]

    def resolve(self, ref: str | None, latest: bool = False) -> Path:
        if latest:
            return self.latest()
        if not ref:
            raise ValueError("Task reference is required. Use --task <path|task_id> or --latest")

        ref_path = Path(ref)
        if ref_path.exists():
            if ref_path.is_dir():
                candidate = ref_path / "task.json"
                if candidate.exists():
                    return candidate
            if ref_path.is_file():
                return ref_path

        candidate = self.tasks_dir / ref / "task.json"
        if candidate.exists():
            return candidate

        raise FileNotFoundError(f"Task reference not found: {ref}")

    def load(self, task_file: Path) -> Task:
        payload = json.loads(task_file.read_text(encoding="utf-8"))
        validate_task_payload(payload)
        return Task.from_dict(payload)

    def save_to_path(self, task: Task, task_file: Path) -> None:
        payload = task.to_dict()
        validate_task_payload(payload)
        task_file.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    def save(self, task: Task, task_file: Path) -> None:
        task.touch()
        self.save_to_path(task, task_file)
