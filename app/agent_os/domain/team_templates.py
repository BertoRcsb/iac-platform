"""Team mode templates and DevOps flow catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TeamProfile:
    profile_id: str
    name: str
    focus: str
    default_checks: list[str]


@dataclass(frozen=True)
class TaskTemplate:
    template_id: str
    name: str
    description: str
    category: str
    priority: str
    plan_steps: list[str]
    default_risks: list[str]
    recommended_workflow: str


TEAM_PROFILES: dict[str, TeamProfile] = {
    "platform-core": TeamProfile(
        profile_id="platform-core",
        name="Platform Core",
        focus="Platform standards, architecture, and governance.",
        default_checks=[
            "Validate standards and architecture alignment",
            "Confirm approval gate and evidence",
            "Publish reusable learning note",
        ],
    ),
    "sre": TeamProfile(
        profile_id="sre",
        name="SRE",
        focus="Reliability, incident handling, and operational safety.",
        default_checks=[
            "Confirm rollback strategy",
            "Validate impact and blast radius",
            "Record incident timeline and evidence",
        ],
    ),
    "devops": TeamProfile(
        profile_id="devops",
        name="DevOps",
        focus="CI/CD, delivery pipeline, and release reliability.",
        default_checks=[
            "Validate pipeline integrity",
            "Confirm quality gates and tests",
            "Document release readiness",
        ],
    ),
    "security": TeamProfile(
        profile_id="security",
        name="Security",
        focus="Access governance and security hardening.",
        default_checks=[
            "Apply least privilege",
            "Ensure no exposed secrets",
            "Record approval and audit trail",
        ],
    ),
}


TASK_TEMPLATES: dict[str, TaskTemplate] = {
    "pipeline-failure": TaskTemplate(
        template_id="pipeline-failure",
        name="Pipeline Failure",
        description="Use when CI/CD or Sonar/build pipeline failed.",
        category="ci-cd",
        priority="P2",
        plan_steps=[
            "Collect failing stage logs and error evidence",
            "Validate credentials, tokens, and permissions",
            "Check build and quality gate configs",
            "Propose fix with rollback and validation command",
        ],
        default_risks=[
            "Delivery blocked while pipeline remains unstable",
            "Rushed fixes can bypass quality gates",
        ],
        recommended_workflow="incident-analysis",
    ),
    "observability-rollout": TaskTemplate(
        template_id="observability-rollout",
        name="Observability Rollout",
        description="Apply observability standard to a service.",
        category="observability",
        priority="P2",
        plan_steps=[
            "Apply platform-observability-core baseline",
            "Validate Dockerfile and entrypoint contract",
            "Validate logs, metrics, and tracing",
            "Prepare PR with evidence checklist",
        ],
        default_risks=[
            "Telemetry contract drift across services",
            "Runtime mismatch can break service startup",
        ],
        recommended_workflow="service-standardization",
    ),
    "access-request": TaskTemplate(
        template_id="access-request",
        name="Access Request",
        description="Access, IAM, and permission issue workflow.",
        category="access-gcp",
        priority="P2",
        plan_steps=[
            "Identify project/environment and required role",
            "Audit current IAM bindings",
            "Apply least-privilege role update",
            "Validate access and collect approval evidence",
        ],
        default_risks=[
            "Over-privileged role grants security exposure",
            "Missing approval can violate governance policy",
        ],
        recommended_workflow="task-triage",
    ),
    "release-gate": TaskTemplate(
        template_id="release-gate",
        name="Release Gate",
        description="Promotion gate preparation and approval.",
        category="release",
        priority="P2",
        plan_steps=[
            "Prepare release notes and scope",
            "Run regression and gate validation",
            "Request explicit manager approval",
            "Advance only after recorded approval evidence",
        ],
        default_risks=[
            "Promotion without approval evidence",
            "Insufficient validation before environment advancement",
        ],
        recommended_workflow="release-flow",
    ),
    "learning-doc": TaskTemplate(
        template_id="learning-doc",
        name="Learning Documentation",
        description="Capture and share a reusable scientific learning record.",
        category="documentation",
        priority="P3",
        plan_steps=[
            "Collect problem context and constraints",
            "Capture hypothesis and experiment method",
            "Write evidence and analysis",
            "Publish reproducibility steps for team reuse",
        ],
        default_risks=[
            "Knowledge loss if documentation is incomplete",
        ],
        recommended_workflow="continuous-learning-loop",
    ),
}


def get_team_profile(profile_id: str | None) -> TeamProfile | None:
    if not profile_id:
        return None
    return TEAM_PROFILES.get(profile_id)


def get_task_template(template_id: str | None) -> TaskTemplate | None:
    if not template_id:
        return None
    return TASK_TEMPLATES.get(template_id)


def available_team_profiles() -> list[dict[str, object]]:
    return [
        {
            "id": profile.profile_id,
            "name": profile.name,
            "focus": profile.focus,
            "default_checks": profile.default_checks,
        }
        for profile in TEAM_PROFILES.values()
    ]


def available_task_templates() -> list[dict[str, object]]:
    return [
        {
            "id": template.template_id,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "priority": template.priority,
            "plan_steps": template.plan_steps,
            "recommended_workflow": template.recommended_workflow,
        }
        for template in TASK_TEMPLATES.values()
    ]


def apply_team_context(input_text: str, template_id: str | None, team_profile: str | None) -> tuple[str, dict[str, object]]:
    template = get_task_template(template_id)
    profile = get_team_profile(team_profile)

    if template_id and template is None:
        raise ValueError(f"Unknown template: {template_id}")
    if team_profile and profile is None:
        raise ValueError(f"Unknown team profile: {team_profile}")

    if not template and not profile:
        return input_text, {}

    tags: list[str] = []
    context: dict[str, object] = {}
    if template:
        context["template"] = {
            "id": template.template_id,
            "name": template.name,
            "category": template.category,
            "priority": template.priority,
            "recommended_workflow": template.recommended_workflow,
        }
        tags.append(f"template={template.template_id}")
    if profile:
        context["team_profile"] = {
            "id": profile.profile_id,
            "name": profile.name,
            "focus": profile.focus,
            "default_checks": profile.default_checks,
        }
        tags.append(f"team={profile.profile_id}")

    enriched = f"{input_text}\n\n[TeamMode {' '.join(tags)}]"
    return enriched, context
