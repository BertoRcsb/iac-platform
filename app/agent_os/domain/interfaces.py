"""Domain interfaces for LLM integration."""

from __future__ import annotations

from typing import Protocol


class LLMGateway(Protocol):
    def generate_plan(self, task_text: str, category: str) -> dict[str, object]:
        """Return plan summary and steps for a task."""

    def summarize(self, text: str) -> str:
        """Return concise summary text."""

    def review_change(self, task_text: str, execution_logs: list[str]) -> dict[str, object]:
        """Return findings and review conclusion."""

    def extract_risks(self, task_text: str, category: str, priority: str) -> list[str]:
        """Return risk list for a task."""
