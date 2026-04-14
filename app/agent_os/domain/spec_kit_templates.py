"""Spec-driven document templates inspired by GitHub Spec Kit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecPackInput:
    task_id: str
    request: str
    state: str
    category: str
    priority: str
    risks: list[str]
    plan_summary: str
    plan_steps: list[str]
    workflow: str
    validation_command: str
    source_reference: str


def _lines(items: list[str], fallback: str) -> list[str]:
    if items:
        return [f"- {item}" for item in items]
    return [f"- {fallback}"]


def render_spec_md(feature_name: str, data: SpecPackInput) -> str:
    goals = _lines(data.plan_steps[:3], "Define measurable implementation goals")
    requirements = _lines(data.plan_steps, "Define functional requirements")
    risks = _lines(data.risks, "No explicit risks were captured yet")

    return "\n".join(
        [
            f"# Spec: {feature_name}",
            "",
            "## Context",
            f"- Task ID: `{data.task_id}`",
            f"- State at generation: `{data.state}`",
            f"- Source: `{data.source_reference or 'inline'}`",
            f"- Category/Priority: `{data.category}` / `{data.priority}`",
            "",
            "## Problem Statement",
            data.request.strip() or "Pending detailed problem statement.",
            "",
            "## Objectives (What/Why)",
            *goals,
            "",
            "## Non-Goals",
            "- Do not execute cloud/production changes directly from this repository.",
            "- Do not bypass manager approval or governance gates.",
            "",
            "## Functional Requirements",
            *requirements,
            "",
            "## Non-Functional Requirements",
            "- Performance: keep flow deterministic and avoid unnecessary network calls.",
            "- Reliability: all lifecycle transitions must remain explicit and auditable.",
            "- Security: enforce allowlist + approval identity for external actions.",
            "- Maintainability: preserve Clean Architecture boundaries (domain/application/infrastructure).",
            "",
            "## Risks",
            *risks,
            "",
            "## Acceptance Criteria",
            "- Plan and routing are generated with explicit next command.",
            "- GO/NO-GO gate can validate readiness before execution.",
            "- Review and learning outputs are generated and traceable.",
            "",
            "## Open Questions",
            "- Any unresolved dependency, environment, or access constraints?",
            "- Does this require Jira external action or local-only pilot mode?",
        ]
    ) + "\n"


def render_plan_md(feature_name: str, data: SpecPackInput) -> str:
    steps = _lines(data.plan_steps, "Define implementation tasks")
    workflow = data.workflow or "task-triage"
    validation = data.validation_command or "./scripts/agentctl-test.sh"

    return "\n".join(
        [
            f"# Plan: {feature_name}",
            "",
            "## Technical Context",
            f"- Workflow: `{workflow}`",
            f"- Validation command: `{validation}`",
            f"- Plan summary: {data.plan_summary or 'Pending plan summary'}",
            "",
            "## Clean Architecture Boundaries",
            "- Domain: rules, contracts, and deterministic policies only.",
            "- Application: orchestrate lifecycle/use-cases without framework coupling.",
            "- Infrastructure: adapters for files, Jira, providers, and external actions.",
            "",
            "## Implementation Strategy",
            "1. Keep lifecycle transitions explicit and idempotent.",
            "2. Apply local-first validation before any external mutation.",
            "3. Preserve audit trail (`run_id`, `task_id`, `approved_by`, evidence).",
            "",
            "## Planned Steps",
            *steps,
            "",
            "## Performance Strategy",
            "- Prefer deterministic local adapters by default.",
            "- Avoid duplicate execution; use state machine and idempotent commands.",
            "- Keep command outputs structured (`Reasoning Summary` + `Decision`).",
        ]
    ) + "\n"


def render_tasks_md(feature_name: str, data: SpecPackInput) -> str:
    task_items = data.plan_steps or ["Define actionable tasks from specification"]
    workflow = data.workflow or "task-triage"
    validation = data.validation_command or "./scripts/agentctl-test.sh"

    numbered = [f"- [ ] T{i + 1}: {item}" for i, item in enumerate(task_items)]
    return "\n".join(
        [
            f"# Tasks: {feature_name}",
            "",
            "## Execution Checklist",
            *numbered,
            "",
            "## Mandatory Gates",
            "- [ ] `./scripts/agentctl gate-check --task <task_id> --manager-approved --approved-by <manager>`",
            "- [ ] `./scripts/agentctl execute --task <task_id> --manager-approved --auto-approve --approved-by <manager>`",
            "- [ ] `./scripts/agentctl review --task <task_id>`",
            "- [ ] `./scripts/agentctl learn --task <task_id>`",
            "",
            "## Validation",
            f"- [ ] Run `{validation}`",
            f"- [ ] Confirm workflow alignment with `{workflow}`",
            "",
            "## Completion Criteria",
            "- [ ] Task closed as DONE or BLOCKED with explicit reason",
            "- [ ] Scientific learning document generated and shareable",
            "- [ ] Documentation and logs updated",
        ]
    ) + "\n"


def render_spec_checklist_md() -> str:
    return "\n".join(
        [
            "# Checklist: Spec Quality",
            "",
            "## Clarity",
            "- [ ] Problem and objective are explicit",
            "- [ ] Scope and non-goals are defined",
            "- [ ] Acceptance criteria are testable",
            "",
            "## Architecture",
            "- [ ] Domain/Application/Infrastructure responsibilities are separated",
            "- [ ] External actions are adapter-based and approval-gated",
            "",
            "## Quality",
            "- [ ] Risks documented",
            "- [ ] Validation command defined",
            "- [ ] Performance and reliability requirements stated",
            "",
            "## Governance",
            "- [ ] Approval path is explicit",
            "- [ ] Audit trail fields are present (`approved_by`, notes, evidence)",
        ]
    ) + "\n"


def required_spec_sections() -> list[str]:
    return [
        "## Context",
        "## Problem Statement",
        "## Objectives (What/Why)",
        "## Functional Requirements",
        "## Non-Functional Requirements",
        "## Acceptance Criteria",
    ]
