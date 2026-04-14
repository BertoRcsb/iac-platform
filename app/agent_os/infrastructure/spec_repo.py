"""Repository for spec-driven documentation packs."""

from __future__ import annotations

import re
from pathlib import Path


class SpecPackRepository:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.features_root = self.base_dir / "specs" / "features"
        self.features_root.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        raw = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
        compact = "-".join(part for part in raw.split("-") if part)
        return compact[:48] or "feature"

    def next_feature_prefix(self) -> str:
        pattern = re.compile(r"^(\d{3})-")
        max_id = 0
        for entry in self.features_root.iterdir():
            if not entry.is_dir():
                continue
            match = pattern.match(entry.name)
            if match:
                max_id = max(max_id, int(match.group(1)))
        return f"{max_id + 1:03d}"

    def create_feature_dir(self, hint: str) -> Path:
        prefix = self.next_feature_prefix()
        feature_name = self._slugify(hint)
        feature_dir = self.features_root / f"{prefix}-{feature_name}"
        feature_dir.mkdir(parents=True, exist_ok=False)
        (feature_dir / "checklists").mkdir(parents=True, exist_ok=True)
        return feature_dir

    def write_documents(self, feature_dir: Path, docs: dict[str, str]) -> list[str]:
        written: list[str] = []
        for rel_path, content in docs.items():
            path = feature_dir / rel_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            written.append(str(path.relative_to(self.base_dir)))
        return written
