"""Unified CLI for Agent OS."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.agent_os.application.services import AgentService, ServiceError
from app.agent_os.domain.state_machine import InvalidStateTransitionError
from app.agent_os.infrastructure.config import load_agent_settings, load_jira_settings, load_provider_settings
from app.agent_os.infrastructure.file_repo import TaskRepository
from app.agent_os.infrastructure.llm_adapters import RuleBasedLLMAdapter
from app.agent_os.infrastructure.logging import StructuredLogger


def bool_arg(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")


def emit(reasoning: str, decision: str, data: dict | None = None) -> None:
    print("Reasoning Summary")
    print(reasoning)
    print("")
    print("Decision")
    print(decision)
    if data is not None:
        print("")
        print("Data")
        print(json.dumps(data, indent=2, ensure_ascii=True))


def build_service(base_dir: Path) -> AgentService:
    settings = load_agent_settings(base_dir)
    providers = load_provider_settings(base_dir)
    jira = load_jira_settings(base_dir)
    repo = TaskRepository(base_dir)
    llm = RuleBasedLLMAdapter()
    logger = StructuredLogger(base_dir)
    return AgentService(
        base_dir=base_dir,
        repo=repo,
        settings=settings,
        provider_settings=providers,
        jira_settings=jira,
        llm=llm,
        logger=logger,
    )


def source_from_input(input_text: str) -> tuple[str, str]:
    if input_text.startswith("http://") or input_text.startswith("https://"):
        return "link", input_text
    return "text", "inline"


def cmd_new(service: AgentService, args: argparse.Namespace) -> None:
    source_type, source_reference = source_from_input(args.input)
    result = service.new_task(
        request=args.input,
        source_type=source_type,
        source_reference=source_reference,
        template_id=args.template,
        team_profile=args.team,
    )
    emit(
        reasoning="Task creation initializes immutable request context and starts lifecycle in NEW state.",
        decision=f"Task created. Next step: ./scripts/agentctl plan --task {result['task_id']}",
        data=result,
    )


def cmd_plan(service: AgentService, args: argparse.Namespace) -> None:
    result = service.plan_task(task_ref=args.task, latest=args.latest)
    emit(
        reasoning="Planning classifies category/priority, extracts risks, and builds a validation-first plan before any execution.",
        decision=f"Task planned. Next step: ./scripts/agentctl route --task {result['task_id']}",
        data=result,
    )


def cmd_route(service: AgentService, args: argparse.Namespace) -> None:
    result = service.route_task(task_ref=args.task, latest=args.latest)
    decision = f"Provider routed to {result['provider']} ({result['model']})."
    if result["provider"] == "none":
        decision += " Configure provider keys or local ollama and rerun route."
    emit(
        reasoning="Routing is provider-agnostic in domain rules and uses free-first policy with optional paid fallback.",
        decision=decision,
        data=result,
    )


def cmd_execute(service: AgentService, args: argparse.Namespace) -> None:
    dry_run = args.dry_run
    result = service.execute_task(
        task_ref=args.task,
        latest=args.latest,
        manager_approved=args.manager_approved,
        auto_approve=args.auto_approve,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
        dry_run=dry_run,
    )
    emit(
        reasoning="Execution enforces approval gates and records structured logs before moving task to REVIEW stage.",
        decision=result["next_command"],
        data=result,
    )


def cmd_review(service: AgentService, args: argparse.Namespace) -> None:
    result = service.review_task(task_ref=args.task, latest=args.latest, blocked=args.blocked, notes=args.notes)
    emit(
        reasoning="Review validates execution evidence and closes task only when findings are acceptable.",
        decision=result["next_command"],
        data=result,
    )


def cmd_learn(service: AgentService, args: argparse.Namespace) -> None:
    result = service.learn_task(task_ref=args.task, latest=args.latest, source="agentctl")
    emit(
        reasoning="Learning publishes scientific-method documentation so solutions can be reused and improved by other people.",
        decision=f"Scientific learning document updated at {result['shared_doc']}",
        data=result,
    )


def cmd_status(service: AgentService, args: argparse.Namespace) -> None:
    result = service.status_task(task_ref=args.task, latest=args.latest)
    emit(
        reasoning="Status provides lifecycle observability for safe and explicit operations.",
        decision=f"Current state: {result['state']}",
        data=result,
    )


def cmd_spec_pack(service: AgentService, args: argparse.Namespace) -> None:
    result = service.spec_pack_task(task_ref=args.task, latest=args.latest, feature_name=args.feature)
    emit(
        reasoning=(
            "Spec pack generation converts task planning into spec-driven artifacts "
            "(spec/plan/tasks/checklist) for faster and safer implementation."
        ),
        decision=result["next_command"],
        data=result,
    )


def cmd_catalog(service: AgentService, args: argparse.Namespace) -> None:
    data = service.catalog()
    emit(
        reasoning="Catalog exposes the team profiles and task templates for fast and consistent operations.",
        decision="Select a template and run: ./scripts/agentctl run --input \"...\" --template <id> --team <profile>",
        data=data,
    )


def cmd_spec_analyze(service: AgentService, args: argparse.Namespace) -> None:
    result = service.spec_analyze_task(task_ref=args.task, latest=args.latest)
    emit(
        reasoning=(
            "Spec analysis runs quality gates on generated artifacts "
            "(required files, required sections, clean-architecture and actionable tasks)."
        ),
        decision=result["next_command"],
        data=result,
    )


def cmd_gate_check(service: AgentService, args: argparse.Namespace) -> None:
    result = service.gate_check(
        task_ref=args.task,
        latest=args.latest,
        manager_approved=args.manager_approved,
        auto_approve=args.auto_approve,
        approved_by=args.approved_by,
        dry_run=args.dry_run,
    )
    overall = result["gate_check"]["overall"]
    decision = result["next_command"] if overall == "GO" else "Fix failing items before execution."
    emit(
        reasoning="GO/NO-GO checklist validates readiness, approval evidence, and execution safety before execution.",
        decision=decision,
        data=result,
    )


def cmd_doctor(service: AgentService, args: argparse.Namespace) -> None:
    checks = service.doctor()
    data = {
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "message": check.message,
                "suggested_action": check.suggested_action,
            }
            for check in checks
        ]
    }
    issues = [check for check in checks if check.status in {"WARN", "ERROR"}]
    if issues:
        decision = "Fix WARN/ERROR items before production usage. Use suggested_action for each item."
    else:
        decision = "Environment looks healthy for local usage."
    emit(
        reasoning="Doctor verifies configuration, binaries, provider prerequisites, and writable paths.",
        decision=decision,
        data=data,
    )


def cmd_jira_authorize(service: AgentService, args: argparse.Namespace) -> None:
    result = service.authorize_jira_issue(args.issue)
    emit(
        reasoning="Authorization allowlist prevents unintended execution in non-approved Jira cards.",
        decision=f"Issue {result['issue_key']} authorized. You can now run jira-run with execution flags if needed.",
        data=result,
    )


def cmd_jira_run(service: AgentService, args: argparse.Namespace) -> None:
    result = service.jira_run(
        issue_ref=args.issue,
        context=args.context,
        template_id=args.template,
        team_profile=args.team,
        manager_approved=args.manager_approved,
        auto_approve=args.auto_approve,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
    )
    decision = result.get("next_command", "./scripts/agentctl status --latest")
    emit(
        reasoning="Jira run fetches card details via API, converts them into task context, and follows the same approval-gated lifecycle.",
        decision=decision,
        data=result,
    )


def cmd_jira_transitions(service: AgentService, args: argparse.Namespace) -> None:
    result = service.jira_transitions(args.issue)
    emit(
        reasoning="Transitions listing checks what Jira statuses are currently available for the issue before moving it.",
        decision="Use one transition name exactly as listed with: ./scripts/agentctl jira-transition --issue <key> --to-status \"<name>\" ...",
        data=result,
    )


def cmd_jira_comment(service: AgentService, args: argparse.Namespace) -> None:
    result = service.jira_comment(
        issue_ref=args.issue,
        comment=args.comment,
        manager_approved=args.manager_approved,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
        dry_run=args.dry_run,
    )
    emit(
        reasoning="Jira comment action is guarded by allowlist and approval identity, with optional dry-run simulation.",
        decision=result["next_command"],
        data=result,
    )


def cmd_jira_transition(service: AgentService, args: argparse.Namespace) -> None:
    result = service.jira_transition(
        issue_ref=args.issue,
        to_status=args.to_status,
        manager_approved=args.manager_approved,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
        dry_run=args.dry_run,
    )
    emit(
        reasoning="Jira transition action enforces allowlist, approver identity, and allowed transition policy.",
        decision=result["next_command"],
        data=result,
    )


def cmd_jira_comment_template(service: AgentService, args: argparse.Namespace) -> None:
    result = service.jira_comment_template(
        mode=args.mode,
        issue_ref=args.issue,
        task_ref=args.task,
        latest_task=args.latest,
        extra=args.extra,
        post=args.post,
        manager_approved=args.manager_approved,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
        dry_run=args.dry_run,
    )
    decision = result.get("next_command", "./scripts/agentctl jira-run --issue <key>")
    emit(
        reasoning="Template mode standardizes Jira communication with reusable structures and optional secure posting.",
        decision=decision,
        data=result,
    )


def cmd_run(service: AgentService, args: argparse.Namespace) -> None:
    source_type, source_reference = source_from_input(args.input)
    result = service.run_pipeline(
        input_text=args.input,
        source_type=source_type,
        source_reference=source_reference,
        manager_approved=args.manager_approved,
        auto_approve=args.auto_approve,
        approved_by=args.approved_by,
        approval_note=args.approval_note,
        template_id=args.template,
        team_profile=args.team,
    )

    decision = result.get("next_command", "./scripts/agentctl status --latest")
    data = {
        "task_id": result["task_id"],
        "state": result["state"],
        "category": result["category"],
        "priority": result["priority"],
        "risks": result["risks"],
        "plan_steps": result["plan_steps"],
        "workflow": result.get("workflow", ""),
        "spec_pack_path": result.get("spec_pack_path", ""),
        "spec_pack_quality": result.get("spec_pack_quality", ""),
        "approval_required": result["approval_required"],
        "approved_by": result.get("approved_by", ""),
        "provider": result["provider"],
        "model": result["model"],
        "template": result.get("template", ""),
        "team_profile": result.get("team_profile", ""),
        "next_command": decision,
    }
    if "shared_doc" in result:
        data["shared_doc"] = result["shared_doc"]

    emit(
        reasoning=(
            "Run orchestrates intake, planning, and routing. "
            "Execution only advances when approval conditions are explicitly met."
        ),
        decision=decision,
        data=data,
    )


def cmd_review_code(service: AgentService, args: argparse.Namespace) -> None:
    result = service.review_code(target=args.path)
    emit(
        reasoning=(
            "Code review inspects risk patterns, shell safety, and maintainability signals before any automatic fix."
        ),
        decision=result["next_command"],
        data=result,
    )


def cmd_debug_auto(service: AgentService, args: argparse.Namespace) -> None:
    result = service.debug_auto(command=args.validation_command, target=args.path, apply_refactor=args.apply_refactor)
    outcome = "Debug succeeded with stable validation." if result["after"]["returncode"] == 0 else "Debug still failing after validation."
    emit(
        reasoning=(
            "Auto debug runs baseline tests, applies safe refactors when requested, and only accepts changes after re-test."
        ),
        decision=f"{outcome} Next step: {result['next_command']}",
        data=result,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agentctl", description="Unified Agent OS CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_new = sub.add_parser("new", help="Create a new task")
    p_new.add_argument("--input", required=True, help="Task input text or link")
    p_new.add_argument("--template", help="Optional team-mode template id")
    p_new.add_argument("--team", help="Optional team profile id")

    p_plan = sub.add_parser("plan", help="Classify and plan a task")
    p_plan.add_argument("--task", help="Task id or task.json path")
    p_plan.add_argument("--latest", action="store_true", help="Use latest task")

    p_route = sub.add_parser("route", help="Route task to provider")
    p_route.add_argument("--task", help="Task id or task.json path")
    p_route.add_argument("--latest", action="store_true", help="Use latest task")

    p_execute = sub.add_parser("execute", help="Execute a planned task")
    p_execute.add_argument("--task", help="Task id or task.json path")
    p_execute.add_argument("--latest", action="store_true", help="Use latest task")
    p_execute.add_argument("--manager-approved", action="store_true", help="Confirm manager approval")
    p_execute.add_argument("--auto-approve", action="store_true", help="Auto transition PLANNED->APPROVED")
    p_execute.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_execute.add_argument("--approval-note", default="", help="Approval rationale/context")
    p_execute.add_argument("--dry-run", type=bool_arg, default=None, help="Override dry-run true/false")

    p_review = sub.add_parser("review", help="Review execution and close task")
    p_review.add_argument("--task", help="Task id or task.json path")
    p_review.add_argument("--latest", action="store_true", help="Use latest task")
    p_review.add_argument("--blocked", action="store_true", help="Force BLOCKED conclusion")
    p_review.add_argument("--notes", default="", help="Extra review notes")

    p_learn = sub.add_parser("learn", help="Generate learning documentation")
    p_learn.add_argument("--task", help="Task id or task.json path")
    p_learn.add_argument("--latest", action="store_true", help="Use latest task")

    p_status = sub.add_parser("status", help="Show task status")
    p_status.add_argument("--task", help="Task id or task.json path")
    p_status.add_argument("--latest", action="store_true", help="Use latest task")

    p_spec = sub.add_parser("spec-pack", help="Generate spec-driven pack (spec/plan/tasks/checklist)")
    p_spec.add_argument("--task", help="Task id or task.json path")
    p_spec.add_argument("--latest", action="store_true", help="Use latest task")
    p_spec.add_argument("--feature", default="", help="Optional custom feature name")

    p_spec_analyze = sub.add_parser("spec-analyze", help="Analyze spec pack quality gates")
    p_spec_analyze.add_argument("--task", help="Task id or task.json path")
    p_spec_analyze.add_argument("--latest", action="store_true", help="Use latest task")

    p_gate = sub.add_parser("gate-check", help="Run GO/NO-GO checklist before execution")
    p_gate.add_argument("--task", help="Task id or task.json path")
    p_gate.add_argument("--latest", action="store_true", help="Use latest task")
    p_gate.add_argument("--manager-approved", action="store_true", help="Include manager approval evidence in check")
    p_gate.add_argument("--auto-approve", action="store_true", help="Include auto approval evidence in check")
    p_gate.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_gate.add_argument("--dry-run", type=bool_arg, default=None, help="Override dry-run true/false for gate check")

    sub.add_parser("catalog", help="List team profiles and task templates")
    sub.add_parser("doctor", help="Run environment diagnostics")

    p_jira_authorize = sub.add_parser("jira-authorize", help="Authorize Jira issue key for execution")
    p_jira_authorize.add_argument("--issue", required=True, help="Jira issue key or URL")

    p_jira_run = sub.add_parser("jira-run", help="Fetch Jira issue and run lifecycle")
    p_jira_run.add_argument("--issue", required=True, help="Jira issue key or URL")
    p_jira_run.add_argument("--context", default="", help="Additional context from human")
    p_jira_run.add_argument("--template", help="Optional team-mode template id")
    p_jira_run.add_argument("--team", help="Optional team profile id")
    p_jira_run.add_argument("--manager-approved", action="store_true", help="Allow execution and closure")
    p_jira_run.add_argument("--auto-approve", action="store_true", help="Auto approve execution gate")
    p_jira_run.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_jira_run.add_argument("--approval-note", default="", help="Approval rationale/context")

    p_jira_transitions = sub.add_parser("jira-transitions", help="List available Jira transitions for an issue")
    p_jira_transitions.add_argument("--issue", required=True, help="Jira issue key or URL")

    p_jira_comment = sub.add_parser("jira-comment", help="Create Jira comment (external action)")
    p_jira_comment.add_argument("--issue", required=True, help="Jira issue key or URL")
    p_jira_comment.add_argument("--comment", required=True, help="Comment text")
    p_jira_comment.add_argument("--manager-approved", action="store_true", help="Confirm manager approval")
    p_jira_comment.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_jira_comment.add_argument("--approval-note", default="", help="Approval rationale/context")
    p_jira_comment.add_argument("--dry-run", type=bool_arg, default=None, help="Override dry-run true/false")

    p_jira_transition = sub.add_parser("jira-transition", help="Transition Jira issue status (external action)")
    p_jira_transition.add_argument("--issue", required=True, help="Jira issue key or URL")
    p_jira_transition.add_argument("--to-status", required=True, help="Target transition name in Jira")
    p_jira_transition.add_argument("--manager-approved", action="store_true", help="Confirm manager approval")
    p_jira_transition.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_jira_transition.add_argument("--approval-note", default="", help="Approval rationale/context")
    p_jira_transition.add_argument("--dry-run", type=bool_arg, default=None, help="Override dry-run true/false")

    p_jira_comment_template = sub.add_parser("jira-comment-template", help="Build Jira comment from standard template")
    p_jira_comment_template.add_argument("--mode", default="execution-complete", help="Template mode")
    p_jira_comment_template.add_argument("--issue", default="", help="Jira issue key or URL")
    p_jira_comment_template.add_argument("--task", help="Task id or task.json path")
    p_jira_comment_template.add_argument("--latest", action="store_true", help="Use latest task")
    p_jira_comment_template.add_argument("--extra", default="", help="Additional context text")
    p_jira_comment_template.add_argument("--post", action="store_true", help="Post template comment via Jira adapter")
    p_jira_comment_template.add_argument("--manager-approved", action="store_true", help="Confirm manager approval")
    p_jira_comment_template.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_jira_comment_template.add_argument("--approval-note", default="", help="Approval rationale/context")
    p_jira_comment_template.add_argument("--dry-run", type=bool_arg, default=None, help="Override dry-run true/false")

    p_run = sub.add_parser("run", help="Run end-to-end flow from input")
    p_run.add_argument("--input", required=True, help="Task input text or link")
    p_run.add_argument("--manager-approved", action="store_true", help="Allow execution and closure")
    p_run.add_argument("--auto-approve", action="store_true", help="Auto approve execution gate")
    p_run.add_argument("--approved-by", default="", help="Approval identity for audit trail")
    p_run.add_argument("--approval-note", default="", help="Approval rationale/context")
    p_run.add_argument("--template", help="Optional team-mode template id")
    p_run.add_argument("--team", help="Optional team profile id")

    p_review_code = sub.add_parser("review-code", help="Review code quality and risk patterns")
    p_review_code.add_argument("--path", default=".", help="Target file or directory")

    p_debug_auto = sub.add_parser("debug-auto", help="Run command, test, and optionally apply safe refactor")
    p_debug_auto.add_argument("--command", dest="validation_command", default="./scripts/agentctl-test.sh", help="Validation command")
    p_debug_auto.add_argument("--path", default=".", help="Target file or directory for refactor candidates")
    p_debug_auto.add_argument("--apply-refactor", action="store_true", help="Apply safe auto-refactors before re-test")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    base_dir = Path(__file__).resolve().parents[2]
    service = build_service(base_dir)

    try:
        handlers = {
            "new": cmd_new,
            "plan": cmd_plan,
            "route": cmd_route,
            "execute": cmd_execute,
            "review": cmd_review,
            "learn": cmd_learn,
            "status": cmd_status,
            "spec-pack": cmd_spec_pack,
            "spec-analyze": cmd_spec_analyze,
            "gate-check": cmd_gate_check,
            "catalog": cmd_catalog,
            "doctor": cmd_doctor,
            "jira-authorize": cmd_jira_authorize,
            "jira-run": cmd_jira_run,
            "jira-transitions": cmd_jira_transitions,
            "jira-comment": cmd_jira_comment,
            "jira-transition": cmd_jira_transition,
            "jira-comment-template": cmd_jira_comment_template,
            "run": cmd_run,
            "review-code": cmd_review_code,
            "debug-auto": cmd_debug_auto,
        }
        handler = handlers[args.command]
        handler(service, args)
        return 0
    except ServiceError as exc:
        emit(
            reasoning="Command could not proceed due to lifecycle or approval constraints.",
            decision=f"{exc.message}. Suggested action: {exc.suggested_action}",
        )
        return 2
    except InvalidStateTransitionError as exc:
        emit(
            reasoning="State machine rejected the transition to protect workflow consistency.",
            decision=f"{exc}. Suggested action: inspect current state with ./scripts/agentctl status --task <task>",
        )
        return 2
    except FileNotFoundError as exc:
        emit(
            reasoning="Referenced resource was not found in the workspace.",
            decision=(
                f"{exc}. Suggested action: use ./scripts/agentctl status --latest "
                "or create a task with ./scripts/agentctl new --input \"...\""
            ),
        )
        return 2
    except Exception as exc:  # noqa: BLE001
        emit(
            reasoning="Unexpected runtime error occurred while processing command.",
            decision=f"Error: {exc}. Suggested action: run ./scripts/agentctl doctor",
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
