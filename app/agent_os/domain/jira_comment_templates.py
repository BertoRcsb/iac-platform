"""Jira comment templates for standardized communication."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class JiraCommentTemplate:
    mode: str
    title: str
    description: str


COMMENT_TEMPLATES: dict[str, JiraCommentTemplate] = {
    "analysis-start": JiraCommentTemplate(
        mode="analysis-start",
        title="Analysis Started",
        description="Task intake/analysis started with initial plan and risks.",
    ),
    "execution-approved": JiraCommentTemplate(
        mode="execution-approved",
        title="Execution Approved",
        description="Manager approved execution and audit identity recorded.",
    ),
    "execution-complete": JiraCommentTemplate(
        mode="execution-complete",
        title="Execution Complete",
        description="Execution completed and moved to review.",
    ),
    "blocked": JiraCommentTemplate(
        mode="blocked",
        title="Blocked",
        description="Task blocked due to validation or dependency issues.",
    ),
    "learning-published": JiraCommentTemplate(
        mode="learning-published",
        title="Learning Published",
        description="Scientific learning document generated for reuse.",
    ),
}


def available_comment_templates() -> list[dict[str, str]]:
    return [
        {
            "mode": item.mode,
            "title": item.title,
            "description": item.description,
        }
        for item in COMMENT_TEMPLATES.values()
    ]


def normalize_comment_mode(mode: str) -> str:
    value = (mode or "").strip().lower()
    if value in COMMENT_TEMPLATES:
        return value
    return "execution-complete"


def compose_jira_comment(mode: str, payload: dict[str, Any]) -> str:
    normalized = normalize_comment_mode(mode)
    template = COMMENT_TEMPLATES[normalized]

    task_id = str(payload.get("task_id", "N/A"))
    state = str(payload.get("state", "N/A"))
    category = str(payload.get("category", "N/A"))
    priority = str(payload.get("priority", "N/A"))
    approved_by = str(payload.get("approved_by", "")).strip() or "N/A"
    approval_note = str(payload.get("approval_note", "")).strip()
    workflow = str(payload.get("workflow", "")).strip()
    summary = str(payload.get("summary", "")).strip()
    decision = str(payload.get("decision", "")).strip()
    risks = payload.get("risks") or []
    extra = str(payload.get("extra", "")).strip()
    generated_at = str(payload.get("generated_at", ""))
    learning_doc = str(payload.get("shared_doc", "")).strip()

    lines = [
        "[AgentCtl Update]",
        f"Template: {template.mode} - {template.title}",
        "",
        f"Task ID: {task_id}",
        f"State: {state}",
        f"Category/Priority: {category} / {priority}",
    ]
    if workflow:
        lines.append(f"Workflow: {workflow}")

    if summary:
        lines += ["", "Reasoning Summary:", summary]
    if decision:
        lines += ["", "Decision:", decision]

    if isinstance(risks, list) and risks:
        lines += ["", "Risks:"]
        for item in risks[:6]:
            lines.append(f"- {item}")

    lines += ["", f"Approved By: {approved_by}"]
    if approval_note:
        lines.append(f"Approval Note: {approval_note}")
    if learning_doc:
        lines.append(f"Learning Doc: {learning_doc}")
    if extra:
        lines += ["", "Additional Context:", extra]
    if generated_at:
        lines += ["", f"Generated At (UTC): {generated_at}"]

    return "\n".join(lines).strip()
