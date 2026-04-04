"""Application use-cases for agent lifecycle orchestration."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from app.agent_os.domain.classifiers import classify_task
from app.agent_os.domain.models import Task, utc_now
from app.agent_os.domain.state_machine import InvalidStateTransitionError, assert_transition, is_at_least
from app.agent_os.domain.team_templates import (
    available_task_templates,
    available_team_profiles,
    apply_team_context,
    get_task_template,
)
from app.agent_os.infrastructure.config import AgentSettings, JiraSettings, ProviderSettings
from app.agent_os.infrastructure.code_quality import (
    apply_safe_refactors,
    review_code,
    rollback_refactors,
    run_command,
    write_debug_scientific_doc,
)
from app.agent_os.infrastructure.doctor import DoctorCheck, run_doctor
from app.agent_os.infrastructure.file_repo import TaskRepository
from app.agent_os.infrastructure.jira_client import (
    JiraClientError,
    authorize_jira_issue,
    ensure_jira_issue_authorized,
    fetch_jira_issue,
)
from app.agent_os.infrastructure.llm_adapters import RuleBasedLLMAdapter
from app.agent_os.infrastructure.logging import RunEvent, StructuredLogger
from app.agent_os.infrastructure.provider_router import RoutingDecision, decide_provider


@dataclass
class ServiceError(Exception):
    message: str
    suggested_action: str


class AgentService:
    def __init__(
        self,
        base_dir: Path,
        repo: TaskRepository,
        settings: AgentSettings,
        provider_settings: ProviderSettings,
        jira_settings: JiraSettings,
        llm: RuleBasedLLMAdapter,
        logger: StructuredLogger,
    ) -> None:
        self.base_dir = base_dir
        self.repo = repo
        self.settings = settings
        self.provider_settings = provider_settings
        self.jira_settings = jira_settings
        self.llm = llm
        self.logger = logger

    def _log_event(self, run_id: str, task_id: str, agent: str, status: str, start: float, details: dict[str, Any]) -> None:
        duration_ms = int((perf_counter() - start) * 1000)
        self.logger.log(
            RunEvent(
                run_id=run_id,
                task_id=task_id,
                agent=agent,
                status=status,
                duration_ms=duration_ms,
                details=details,
            )
        )

    def _transition(self, task: Task, to_state: str, actor: str, reason: str) -> None:
        if task.state == to_state:
            return
        transition = assert_transition(task.state, to_state, reason)
        task.add_history(transition.from_state, transition.to_state, actor=actor, reason=reason)
        task.state = transition.to_state

    def _resolve_task(self, task_ref: str | None, latest: bool) -> tuple[Path, Task]:
        task_file = self.repo.resolve(task_ref, latest=latest)
        task = self.repo.load(task_file)
        return task_file, task

    def _validation_command_for(self, category: str) -> str:
        mapping = {
            "ci-cd": "./scripts/agentctl-test.sh",
            "observability": "./scripts/agentctl-test.sh",
            "access-gcp": "./scripts/agentctl doctor",
            "release": "./scripts/agentctl doctor",
            "documentation": "./scripts/agentctl review-code --path .",
            "general": "./scripts/agentctl doctor",
        }
        return mapping.get(category, "./scripts/agentctl doctor")

    def _gate_check_task(
        self,
        task: Task,
        manager_approved: bool = False,
        auto_approve: bool = False,
        approved_by: str = "",
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        effective_dry_run = self.settings.dry_run if dry_run is None else dry_run
        approval_required = bool(task.plan.get("approval_required", True) or self.settings.require_manager_approval)
        current_approved = bool(task.execution.get("approved", False))

        items: list[dict[str, str]] = []

        state_ok = task.state in {"PLANNED", "APPROVED", "EXECUTING", "REVIEW", "DONE", "BLOCKED"}
        items.append(
            {
                "name": "state-ready",
                "status": "PASS" if state_ok else "FAIL",
                "message": f"Task state is {task.state}",
                "suggested_action": "Run planning first until state=PLANNED",
            }
        )

        category = str(task.classification.get("category", "")).strip()
        priority = str(task.classification.get("priority", "")).strip()
        class_ok = bool(category and priority)
        items.append(
            {
                "name": "classification-ready",
                "status": "PASS" if class_ok else "FAIL",
                "message": f"category={category or 'missing'} priority={priority or 'missing'}",
                "suggested_action": "Run: ./scripts/agentctl plan --task <task_id>",
            }
        )

        risks = task.classification.get("risks", [])
        risks_ok = isinstance(risks, list) and len(risks) > 0
        items.append(
            {
                "name": "risks-identified",
                "status": "PASS" if risks_ok else "FAIL",
                "message": f"risks_count={len(risks) if isinstance(risks, list) else 0}",
                "suggested_action": "Run plan again with enough context and risk extraction",
            }
        )

        steps = task.plan.get("steps", [])
        steps_ok = isinstance(steps, list) and len(steps) > 0
        items.append(
            {
                "name": "plan-steps-defined",
                "status": "PASS" if steps_ok else "FAIL",
                "message": f"steps_count={len(steps) if isinstance(steps, list) else 0}",
                "suggested_action": "Ensure plan generation created actionable steps",
            }
        )

        validation_command = str(task.plan.get("validation_command", "")).strip()
        validation_ok = bool(validation_command)
        items.append(
            {
                "name": "validation-command",
                "status": "PASS" if validation_ok else "FAIL",
                "message": validation_command or "validation command missing",
                "suggested_action": "Re-run planning to generate a validation command",
            }
        )

        approval_evidence = current_approved or manager_approved or auto_approve or not approval_required
        items.append(
            {
                "name": "approval-gate",
                "status": "PASS" if approval_evidence else "FAIL",
                "message": (
                    "Approval present"
                    if approval_evidence
                    else "Manager approval required before execution"
                ),
                "suggested_action": f"Run: ./scripts/agentctl execute --task {task.task_id} --manager-approved --approved-by <name>",
            }
        )

        identity_required = manager_approved or auto_approve
        approver = approved_by.strip()
        identity_ok = (not identity_required) or bool(approver)
        items.append(
            {
                "name": "approval-identity",
                "status": "PASS" if identity_ok else "FAIL",
                "message": approver if approver else "approved_by missing",
                "suggested_action": "Provide --approved-by '<manager-name>' for audit trail",
            }
        )

        dry_status = "PASS" if effective_dry_run else "WARN"
        dry_message = "DRY_RUN enabled (safe mode)" if effective_dry_run else "DRY_RUN disabled (real local execution)"
        items.append(
            {
                "name": "execution-safety",
                "status": dry_status,
                "message": dry_message,
                "suggested_action": "Set DRY_RUN=true for safer simulation if needed",
            }
        )

        has_fail = any(item["status"] == "FAIL" for item in items)
        overall = "NO_GO" if has_fail else "GO"
        return {
            "overall": overall,
            "approval_required": approval_required,
            "effective_dry_run": effective_dry_run,
            "items": items,
            "checked_at": utc_now(),
        }

    def new_task(
        self,
        request: str,
        source_type: str,
        source_reference: str,
        template_id: str | None = None,
        team_profile: str | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        try:
            enriched_request, context = apply_team_context(request, template_id=template_id, team_profile=team_profile)
        except ValueError as exc:
            raise ServiceError(
                message=str(exc),
                suggested_action="Run ./scripts/agentctl catalog to list valid templates and team profiles",
            ) from exc

        task_file = self.repo.create(request=enriched_request, source_type=source_type, source_reference=source_reference)
        task = self.repo.load(task_file)
        task.context = context
        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="intake",
            status="CREATED",
            start=start,
            details={
                "task_file": str(task_file),
                "state": task.state,
                "template": template_id or "",
                "team_profile": team_profile or "",
            },
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "template": template_id or "",
            "team_profile": team_profile or "",
        }

    def plan_task(self, task_ref: str | None, latest: bool = False) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)

        if task.state == "NEW":
            self._transition(task, "TRIAGED", actor="plan", reason="Task triaged during planning")
        if task.state == "TRIAGED":
            pass
        elif not is_at_least(task.state, "PLANNED"):
            raise ServiceError(
                message=f"Task state '{task.state}' cannot be planned",
                suggested_action="Move task back to TRIAGED or create a new task",
            )

        classification = classify_task(task.request)
        template_meta = (task.context or {}).get("template") if isinstance(task.context, dict) else None
        template = get_task_template(str(template_meta.get("id"))) if isinstance(template_meta, dict) else None

        category = template.category if template else classification.category
        priority = template.priority if template else classification.priority
        risks = self.llm.extract_risks(task.request, category, priority)
        if template:
            risks = list(dict.fromkeys([*template.default_risks, *risks]))

        plan = self.llm.generate_plan(task.request, category)
        steps = list(plan.get("steps", []))
        if template:
            steps = list(dict.fromkeys([*template.plan_steps, *steps]))
        team_profile = (task.context or {}).get("team_profile") if isinstance(task.context, dict) else None
        team_checks = []
        if isinstance(team_profile, dict):
            team_checks = [str(item) for item in team_profile.get("default_checks", []) if isinstance(item, str)]
        if team_checks:
            steps = list(dict.fromkeys([*steps, *team_checks]))

        task.classification = {
            "category": category,
            "priority": priority,
            "risks": risks,
        }
        task.plan = {
            "summary": str(plan.get("summary", "")),
            "steps": steps,
            "approval_required": True,
            "validation_command": self._validation_command_for(category),
        }
        if template:
            task.plan["workflow"] = template.recommended_workflow

        if task.state == "TRIAGED":
            self._transition(task, "PLANNED", actor="plan", reason="Planning completed")

        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="analysis",
            status="PLANNED",
            start=start,
            details={"category": category, "priority": priority},
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "category": category,
            "priority": priority,
            "risks": risks,
            "plan_steps": task.plan["steps"],
            "workflow": task.plan.get("workflow", ""),
        }

    def route_task(self, task_ref: str | None, latest: bool = False) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)

        if not is_at_least(task.state, "PLANNED"):
            raise ServiceError(
                message=f"Task state '{task.state}' must be PLANNED before routing",
                suggested_action="Run: ./scripts/agentctl plan --task <task_ref>",
            )

        decision: RoutingDecision = decide_provider(task.classification.get("category", "general"), self.settings, self.provider_settings)
        task.routing = {
            "provider": decision.provider,
            "model": decision.model,
            "profile": decision.profile,
            "reason": decision.reason,
            "candidates": decision.candidates,
        }

        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="router",
            status="ROUTED",
            start=start,
            details={"provider": decision.provider, "model": decision.model},
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "provider": decision.provider,
            "model": decision.model,
            "profile": decision.profile,
            "candidates": decision.candidates,
        }

    def execute_task(
        self,
        task_ref: str | None,
        latest: bool = False,
        manager_approved: bool = False,
        auto_approve: bool = False,
        approved_by: str = "",
        approval_note: str = "",
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)

        effective_dry_run = self.settings.dry_run if dry_run is None else dry_run
        gate = self._gate_check_task(
            task=task,
            manager_approved=manager_approved,
            auto_approve=auto_approve,
            approved_by=approved_by,
            dry_run=effective_dry_run,
        )
        task.execution["last_gate_check"] = gate

        if task.state == "PLANNED":
            if not (auto_approve or manager_approved or not self.settings.require_manager_approval):
                approval_log = {
                    "timestamp": utc_now(),
                    "status": "WAITING_FOR_MANAGER_APPROVAL",
                    "message": "Execution blocked until explicit manager approval",
                    "required_fields": ["approved_by"],
                }
                task.execution.setdefault("approval_logs", []).append(approval_log)
                self.repo.save(task, task_file)
                self._log_event(
                    run_id,
                    task.task_id,
                    agent="execution",
                    status="WAITING_APPROVAL",
                    start=start,
                    details=approval_log,
                )
                raise ServiceError(
                    message="Manager approval required before execution",
                    suggested_action=f"Run: ./scripts/agentctl execute --task {task.task_id} --manager-approved --approved-by <manager> --auto-approve",
                )

            if gate["overall"] != "GO":
                self.repo.save(task, task_file)
                failed = next((item for item in gate["items"] if item["status"] == "FAIL"), None)
                message = failed["message"] if failed else "Execution gate failed"
                suggested = failed["suggested_action"] if failed else f"Run: ./scripts/agentctl gate-check --task {task.task_id}"
                raise ServiceError(
                    message=f"GO/NO-GO blocked execution: {message}",
                    suggested_action=suggested,
                )
            approver = approved_by.strip() or ("system-policy" if not self.settings.require_manager_approval else "manager-unknown")
            task.execution["approved"] = True
            task.execution["approved_by"] = approver
            approval_log = {
                "timestamp": utc_now(),
                "status": "APPROVED",
                "approved_by": approver,
                "approval_note": approval_note.strip(),
                "mode": "auto-approve" if auto_approve else "manager-approved",
            }
            task.execution.setdefault("approval_logs", []).append(approval_log)
            self._transition(task, "APPROVED", actor="manager", reason="Approval granted for execution")

        if task.state not in {"APPROVED", "EXECUTING", "REVIEW", "DONE", "BLOCKED"}:
            raise ServiceError(
                message=f"Task state '{task.state}' cannot be executed",
                suggested_action="Run planning first: ./scripts/agentctl plan --task <task_ref>",
            )

        if task.state in {"DONE", "BLOCKED"}:
            return {
                "run_id": run_id,
                "task_file": str(task_file),
                "task_id": task.task_id,
                "state": task.state,
                "execution_status": task.execution.get("status", "PENDING"),
                "next_command": "./scripts/agentctl status --task <task_ref>",
            }

        if task.state == "REVIEW":
            return {
                "run_id": run_id,
                "task_file": str(task_file),
                "task_id": task.task_id,
                "state": task.state,
                "execution_status": task.execution.get("status", "PENDING"),
                "next_command": f"./scripts/agentctl review --task {task.task_id}",
            }

        if task.state == "APPROVED":
            self._transition(task, "EXECUTING", actor="execution", reason="Execution started")

        logs = task.execution.setdefault("logs", [])
        logs.append(f"Execution started at {utc_now()}")
        logs.append(f"Category={task.classification.get('category', 'general')}")
        logs.append(
            "Approval evidence: manager_approved={manager} auto_approve={auto}".format(
                manager=str(manager_approved).lower(),
                auto=str(auto_approve).lower(),
            )
        )
        if effective_dry_run:
            logs.append("DRY_RUN enabled: no external side effects were executed")
            task.execution["status"] = "SIMULATED"
        else:
            logs.append("Execution completed in local mode")
            task.execution["status"] = "EXECUTED_LOCAL"

        task.execution["dry_run"] = effective_dry_run

        if task.state == "EXECUTING":
            self._transition(task, "REVIEW", actor="execution", reason="Execution finished and sent to review")

        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="execution",
            status=task.execution["status"],
            start=start,
            details={
                "state": task.state,
                "dry_run": effective_dry_run,
                "approved_by": task.execution.get("approved_by", ""),
            },
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "execution_status": task.execution["status"],
            "dry_run": effective_dry_run,
            "approved_by": task.execution.get("approved_by", ""),
            "gate_check": gate,
            "next_command": f"./scripts/agentctl review --task {task.task_id}",
        }

    def review_task(self, task_ref: str | None, latest: bool = False, blocked: bool = False, notes: str = "") -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)

        if task.state not in {"REVIEW", "DONE", "BLOCKED"}:
            raise ServiceError(
                message=f"Task state '{task.state}' must be REVIEW before final review",
                suggested_action=f"Run: ./scripts/agentctl execute --task {task.task_id} --manager-approved --approved-by <manager> --auto-approve",
            )

        if task.state in {"DONE", "BLOCKED"}:
            return {
                "run_id": run_id,
                "task_file": str(task_file),
                "task_id": task.task_id,
                "state": task.state,
                "conclusion": task.review.get("conclusion", ""),
                "next_command": f"./scripts/agentctl learn --task {task.task_id}",
            }

        review = self.llm.review_change(task.request, task.execution.get("logs", []))
        findings = list(review.get("findings", []))
        if notes:
            findings.append(f"Manual note: {notes}")

        requires_attention = blocked or bool(findings)
        conclusion = "REQUIRES_ATTENTION" if requires_attention else "PASS"

        task.review = {
            "status": "COMPLETED",
            "findings": findings,
            "conclusion": conclusion,
        }

        next_state = "BLOCKED" if requires_attention else "DONE"
        self._transition(task, next_state, actor="review", reason=f"Review conclusion: {conclusion}")

        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="review",
            status=conclusion,
            start=start,
            details={"findings_count": len(findings), "state": task.state},
        )
        shared_doc = ""
        if self.settings.auto_learning_enabled and task.state in {"DONE", "BLOCKED"}:
            learned = self.learn_task(str(task_file), source="review-auto")
            shared_doc = learned.get("shared_doc", "")
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "conclusion": conclusion,
            "findings": findings,
            "next_command": f"./scripts/agentctl status --task {task.task_id}" if shared_doc else f"./scripts/agentctl learn --task {task.task_id}",
            "shared_doc": shared_doc,
        }

    def learn_task(self, task_ref: str | None, latest: bool = False, source: str = "agentctl") -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)

        if task.learning.get("status") == "COMPLETED" and task.learning.get("shared_doc"):
            return {
                "run_id": run_id,
                "task_file": str(task_file),
                "task_id": task.task_id,
                "state": task.state,
                "shared_doc": task.learning["shared_doc"],
            }

        shared_dir = self.base_dir / "knowledge" / "shared"
        shared_dir.mkdir(parents=True, exist_ok=True)

        summary = self.llm.summarize(task.request)
        hypothesis = "Applying standardized workflow and explicit gates reduces regression risk."
        experiment = "Run intake -> plan -> route -> execute -> review with structured logs and approval checks."
        evidence = "\n".join(task.execution.get("logs", [])[-5:]) or "No execution logs available"
        analysis = "Findings reviewed and recorded with explicit state transitions."
        conclusion = (
            "Workflow reached stable conclusion and is reproducible." if task.state == "DONE" else "Workflow requires additional evidence before closure."
        )

        scientific_doc = shared_dir / f"{task.task_id}-scientific-method.md"
        scientific_doc.write_text(
            "\n".join(
                [
                    f"# Scientific Resolution - {task.task_id}",
                    "",
                    "## Problem",
                    summary,
                    "",
                    "## Hypothesis",
                    hypothesis,
                    "",
                    "## Experiment Method",
                    experiment,
                    "",
                    "## Evidence",
                    evidence,
                    "",
                    "## Analysis",
                    analysis,
                    "",
                    "## Conclusion",
                    conclusion,
                    "",
                    "## Reproducibility Steps",
                    "1. Recreate task using agentctl new/run.",
                    "2. Execute with explicit approval gates.",
                    "3. Compare outputs and logs against this document.",
                    "",
                    "## Shared Learning",
                    "This document is designed to be shared with other teams for learning and reuse.",
                    "",
                    f"Generated at: {utc_now()}",
                    f"Source: {source}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        lessons_file = self.base_dir / "knowledge" / "lessons-learned.md"
        improvements_file = self.base_dir / "knowledge" / "improvement-log.md"
        decisions_file = self.base_dir / "knowledge" / "decision-log.md"
        for file in (lessons_file, improvements_file, decisions_file):
            file.parent.mkdir(parents=True, exist_ok=True)
            if not file.exists():
                file.write_text(f"# {file.stem.replace('-', ' ').title()}\n", encoding="utf-8")

        with lessons_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - {task.task_id}\n"
                f"- Category: {task.classification.get('category')}\n"
                f"- Priority: {task.classification.get('priority')}\n"
                f"- Scientific doc: {scientific_doc.relative_to(self.base_dir)}\n"
            )

        with improvements_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - {task.task_id}\n"
                "- Improvement method: scientific hypothesis + evidence + reproducibility\n"
                "- Next step: refine checklist and automation based on evidence\n"
            )

        with decisions_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - {task.task_id}\n"
                "- Decision: Keep scientific documentation mandatory for each resolution\n"
                "- Rationale: Shared organizational learning and repeatability\n"
            )

        task.learning = {
            "status": "COMPLETED",
            "shared_doc": str(scientific_doc.relative_to(self.base_dir)),
            "scientific_method": {
                "problem": summary,
                "hypothesis": hypothesis,
                "experiment": experiment,
                "analysis": analysis,
                "conclusion": conclusion,
            },
        }

        self.repo.save(task, task_file)
        self._log_event(
            run_id,
            task.task_id,
            agent="documentation",
            status="LEARNED",
            start=start,
            details={"shared_doc": str(scientific_doc.relative_to(self.base_dir))},
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "shared_doc": str(scientific_doc.relative_to(self.base_dir)),
        }

    def status_task(self, task_ref: str | None, latest: bool = False) -> dict[str, Any]:
        task_file, task = self._resolve_task(task_ref, latest)
        template = (task.context or {}).get("template") if isinstance(task.context, dict) else {}
        team_profile = (task.context or {}).get("team_profile") if isinstance(task.context, dict) else {}
        return {
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "category": task.classification.get("category"),
            "priority": task.classification.get("priority"),
            "risks": task.classification.get("risks", []),
            "workflow": task.plan.get("workflow", ""),
            "validation_command": task.plan.get("validation_command", ""),
            "provider": task.routing.get("provider"),
            "model": task.routing.get("model"),
            "approval_required": task.plan.get("approval_required", True),
            "approved_by": task.execution.get("approved_by", ""),
            "execution_status": task.execution.get("status"),
            "review_conclusion": task.review.get("conclusion"),
            "shared_doc": task.learning.get("shared_doc"),
            "template": template.get("id", ""),
            "team_profile": team_profile.get("id", ""),
            "last_gate_check": task.execution.get("last_gate_check", {}),
        }

    def catalog(self) -> dict[str, Any]:
        return {
            "team_profiles": available_team_profiles(),
            "templates": available_task_templates(),
        }

    def gate_check(
        self,
        task_ref: str | None,
        latest: bool = False,
        manager_approved: bool = False,
        auto_approve: bool = False,
        approved_by: str = "",
        dry_run: bool | None = None,
    ) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        task_file, task = self._resolve_task(task_ref, latest)
        gate = self._gate_check_task(
            task=task,
            manager_approved=manager_approved,
            auto_approve=auto_approve,
            approved_by=approved_by,
            dry_run=dry_run,
        )
        task.execution["last_gate_check"] = gate
        self.repo.save(task, task_file)
        self._log_event(
            run_id=run_id,
            task_id=task.task_id,
            agent="gate",
            status=gate["overall"],
            start=start,
            details={"state": task.state, "overall": gate["overall"]},
        )
        next_command = (
            f"./scripts/agentctl execute --task {task.task_id} --manager-approved --approved-by <manager>"
            if gate["overall"] == "GO" and task.state == "PLANNED"
            else f"./scripts/agentctl status --task {task.task_id}"
        )
        return {
            "run_id": run_id,
            "task_file": str(task_file),
            "task_id": task.task_id,
            "state": task.state,
            "gate_check": gate,
            "next_command": next_command,
        }

    def authorize_jira_issue(self, issue_ref: str) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())
        try:
            issue_key, allowlist_path = authorize_jira_issue(issue_ref, self.jira_settings, self.base_dir)
        except JiraClientError as exc:
            raise ServiceError(
                message=str(exc),
                suggested_action="Use a valid Jira key format like INF-33",
            ) from exc

        self._log_event(
            run_id=run_id,
            task_id=issue_key,
            agent="manager",
            status="AUTHORIZED",
            start=start,
            details={"allowlist_file": str(allowlist_path)},
        )
        return {
            "run_id": run_id,
            "issue_key": issue_key,
            "allowlist_file": str(allowlist_path),
        }

    def jira_run(
        self,
        issue_ref: str,
        context: str = "",
        template_id: str | None = None,
        team_profile: str | None = None,
        manager_approved: bool = False,
        auto_approve: bool = False,
        approved_by: str = "",
        approval_note: str = "",
    ) -> dict[str, Any]:
        try:
            issue = fetch_jira_issue(issue_ref, self.jira_settings)
        except JiraClientError as exc:
            raise ServiceError(
                message=f"Jira fetch failed: {exc}",
                suggested_action="Check config/jira-intake.env and run ./scripts/agentctl doctor",
            ) from exc

        should_execute = manager_approved or auto_approve
        if should_execute:
            try:
                ensure_jira_issue_authorized(issue.key, self.jira_settings, self.base_dir)
            except JiraClientError as exc:
                raise ServiceError(
                    message=str(exc),
                    suggested_action=f"Authorize first: ./scripts/agentctl jira-authorize --issue {issue.key}",
                ) from exc

        parts = [
            f"JIRA: {issue.url}",
            f"Issue Key: {issue.key}",
            f"Summary: {issue.summary}",
            f"Status: {issue.status or 'unknown'}",
            f"Priority: {issue.priority or 'unknown'}",
            f"Type: {issue.issue_type or 'unknown'}",
        ]
        if issue.labels:
            parts.append("Labels: " + ", ".join(issue.labels))
        if issue.description:
            parts += ["", "Description:", issue.description]
        if context.strip():
            parts += ["", "Additional Context:", context.strip()]

        input_text = "\n".join(parts)
        result = self.run_pipeline(
            input_text=input_text,
            source_type="jira-api",
            source_reference=issue.url,
            manager_approved=manager_approved,
            auto_approve=auto_approve,
            approved_by=approved_by,
            approval_note=approval_note,
            template_id=template_id,
            team_profile=team_profile,
        )
        result.update(
            {
                "jira_issue_key": issue.key,
                "jira_issue_url": issue.url,
                "jira_summary": issue.summary,
            }
        )
        return result

    def review_code(self, target: str = ".") -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())

        target_path = (self.base_dir / target).resolve() if not Path(target).is_absolute() else Path(target)
        if not target_path.exists():
            raise ServiceError(
                message=f"Target path not found: {target}",
                suggested_action="Use --path with an existing file/directory",
            )

        report = review_code(self.base_dir, target_path)
        details = {
            "target": str(target_path),
            "summary": report["summary"],
        }
        self._log_event(
            run_id=run_id,
            task_id="code-review",
            agent="reviewer",
            status="COMPLETED",
            start=start,
            details=details,
        )

        if report["summary"]["high"] > 0 or report["summary"]["medium"] > 0:
            next_command = "./scripts/agentctl debug-auto --path . --apply-refactor"
        else:
            next_command = "./scripts/agentctl run --input \"Nova tarefa\""

        return {
            "run_id": run_id,
            "target": str(target_path),
            "summary": report["summary"],
            "findings": report["findings"],
            "next_command": next_command,
        }

    def debug_auto(
        self,
        command: str,
        target: str = ".",
        apply_refactor: bool = False,
    ) -> dict[str, Any]:
        start = perf_counter()
        run_id = str(uuid.uuid4())

        target_path = (self.base_dir / target).resolve() if not Path(target).is_absolute() else Path(target)
        if not target_path.exists():
            raise ServiceError(
                message=f"Target path not found: {target}",
                suggested_action="Use --path with an existing file/directory",
            )

        before = run_command(self.base_dir, command)
        review = review_code(self.base_dir, target_path)

        actions = []
        backups: dict[Path, str] = {}
        after = before
        rollback = False

        should_refactor = apply_refactor and (
            before.returncode != 0
            or review["summary"]["high"] > 0
            or review["summary"]["medium"] > 0
        )

        if should_refactor:
            actions, backups = apply_safe_refactors(self.base_dir, target_path)
            after = run_command(self.base_dir, command)
            if after.returncode != 0:
                rollback_refactors(backups)
                rollback = True
                after = run_command(self.base_dir, command)

        scientific_doc = write_debug_scientific_doc(
            base_dir=self.base_dir,
            name="auto-debug",
            hypothesis=(
                "Safe, test-validated refactors can reduce break risk without changing intended behavior."
            ),
            command_before=before,
            command_after=after,
            applied_actions=actions,
        )

        lessons_file = self.base_dir / "knowledge" / "lessons-learned.md"
        improvements_file = self.base_dir / "knowledge" / "improvement-log.md"
        decisions_file = self.base_dir / "knowledge" / "decision-log.md"
        for file in (lessons_file, improvements_file, decisions_file):
            file.parent.mkdir(parents=True, exist_ok=True)
            if not file.exists():
                file.write_text(f"# {file.stem.replace('-', ' ').title()}\n", encoding="utf-8")

        with lessons_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - auto-debug\n"
                f"- Command: {command}\n"
                f"- Before return code: {before.returncode}\n"
                f"- After return code: {after.returncode}\n"
                f"- Scientific doc: {scientific_doc.relative_to(self.base_dir)}\n"
            )

        with improvements_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - auto-debug\n"
                "- Improvement method: test-first refactor with rollback guard\n"
                "- Next action: keep expanding deterministic safe-refactor rules\n"
            )

        with decisions_file.open("a", encoding="utf-8") as handle:
            handle.write(
                f"\n## {utc_now()} - auto-debug\n"
                "- Decision: accept refactor changes only when validation command remains stable\n"
                "- Rationale: prevent regressions and preserve system integrity\n"
            )

        status = "PASSED" if after.returncode == 0 else "FAILED"
        self._log_event(
            run_id=run_id,
            task_id="auto-debug",
            agent="debugger",
            status=status,
            start=start,
            details={
                "command": command,
                "before_returncode": before.returncode,
                "after_returncode": after.returncode,
                "refactor_actions": len(actions),
                "rollback": rollback,
                "scientific_doc": str(scientific_doc.relative_to(self.base_dir)),
            },
        )

        suggested = (
            "./scripts/agentctl review-code --path ."
            if after.returncode == 0
            else "./scripts/agentctl debug-auto --command './scripts/agentctl-test.sh' --path . --apply-refactor"
        )

        return {
            "run_id": run_id,
            "command": command,
            "before": {
                "returncode": before.returncode,
                "stdout": before.stdout[-2000:],
                "stderr": before.stderr[-2000:],
            },
            "after": {
                "returncode": after.returncode,
                "stdout": after.stdout[-2000:],
                "stderr": after.stderr[-2000:],
            },
            "review_summary": review["summary"],
            "applied_refactors": [
                {"file": str(action.file.relative_to(self.base_dir)), "description": action.description}
                for action in actions
            ],
            "rollback": rollback,
            "scientific_doc": str(scientific_doc.relative_to(self.base_dir)),
            "next_command": suggested,
        }

    def doctor(self) -> list[DoctorCheck]:
        return run_doctor(self.base_dir)

    def run_pipeline(
        self,
        input_text: str,
        source_type: str,
        source_reference: str,
        manager_approved: bool = False,
        auto_approve: bool = False,
        approved_by: str = "",
        approval_note: str = "",
        template_id: str | None = None,
        team_profile: str | None = None,
    ) -> dict[str, Any]:
        created = self.new_task(
            input_text,
            source_type,
            source_reference,
            template_id=template_id,
            team_profile=team_profile,
        )
        task_ref = created["task_file"]

        planned = self.plan_task(task_ref)
        routed = self.route_task(task_ref)

        outcome: dict[str, Any] = {
            "task_file": task_ref,
            "task_id": created["task_id"],
            "state": planned["state"],
            "category": planned["category"],
            "priority": planned["priority"],
            "risks": planned["risks"],
            "plan_steps": planned["plan_steps"],
            "workflow": planned.get("workflow", ""),
            "provider": routed["provider"],
            "model": routed["model"],
            "approval_required": True,
            "approved_by": "",
            "next_command": f"./scripts/agentctl execute --task {created['task_id']} --manager-approved --approved-by <manager> --auto-approve",
            "template": created.get("template", ""),
            "team_profile": created.get("team_profile", ""),
        }

        if manager_approved or auto_approve:
            executed = self.execute_task(
                task_ref,
                manager_approved=manager_approved,
                auto_approve=auto_approve,
                approved_by=approved_by,
                approval_note=approval_note,
            )
            reviewed = self.review_task(task_ref)
            learned = self.learn_task(task_ref)
            outcome.update(
                {
                    "state": reviewed["state"],
                    "execution_status": executed["execution_status"],
                    "approved_by": executed.get("approved_by", ""),
                    "review_conclusion": reviewed["conclusion"],
                    "shared_doc": learned["shared_doc"],
                    "next_command": f"./scripts/agentctl status --task {created['task_id']}",
                }
            )

        return outcome
