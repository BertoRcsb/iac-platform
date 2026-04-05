"""Environment diagnostics for agentctl doctor command."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from app.agent_os.infrastructure.config import load_jira_settings


@dataclass
class DoctorCheck:
    name: str
    status: str
    message: str
    suggested_action: str


def run_doctor(base_dir: Path) -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    jira_settings = load_jira_settings(base_dir)

    required_paths = [
        base_dir / "config" / "agentctl.env",
        base_dir / "config" / "ai-providers.env",
        base_dir / "config" / "jira-intake.env",
    ]

    for path in required_paths:
        if path.exists():
            checks.append(
                DoctorCheck(
                    name=f"config:{path.name}",
                    status="OK",
                    message="Configuration file found",
                    suggested_action="None",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name=f"config:{path.name}",
                    status="WARN",
                    message="Configuration file missing",
                    suggested_action=f"Create from example: cp {path}.example {path}",
                )
            )

    binaries = ["python3", "terraform", "curl", "jq", "ollama"]
    for binary in binaries:
        found = shutil.which(binary)
        if found:
            checks.append(
                DoctorCheck(
                    name=f"binary:{binary}",
                    status="OK",
                    message=f"Found at {found}",
                    suggested_action="None",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name=f"binary:{binary}",
                    status="WARN",
                    message="Binary not found",
                    suggested_action=f"Install {binary} or disable dependent provider/workflow",
                )
            )

    writable_targets = [
        base_dir / "tasks" / "incoming",
        base_dir / "outputs" / "reports",
        base_dir / "knowledge",
    ]
    for target in writable_targets:
        try:
            target.mkdir(parents=True, exist_ok=True)
            probe = target / ".agentctl-write-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            checks.append(
                DoctorCheck(
                    name=f"permission:{target.relative_to(base_dir)}",
                    status="OK",
                    message="Writable",
                    suggested_action="None",
                )
            )
        except OSError as exc:
            checks.append(
                DoctorCheck(
                    name=f"permission:{target.relative_to(base_dir)}",
                    status="ERROR",
                    message=f"Not writable: {exc}",
                    suggested_action=f"Fix permissions: chmod/chown {target}",
                )
            )

    env_checks = [
        ("OPENROUTER_API_KEY", "Optional; needed for OpenRouter real calls"),
        ("GROQ_API_KEY", "Optional; needed for Groq real calls"),
    ]
    for var, note in env_checks:
        if os.getenv(var):
            status = "OK"
            message = "Environment variable is set"
            action = "None"
        else:
            status = "INFO"
            message = "Environment variable not set"
            action = f"Set {var} or configure key in config/ai-providers.env ({note})"
        checks.append(DoctorCheck(name=f"env:{var}", status=status, message=message, suggested_action=action))

    if jira_settings.enabled:
        if jira_settings.base_url and jira_settings.email and jira_settings.api_token:
            checks.append(
                DoctorCheck(
                    name="jira:api",
                    status="OK",
                    message="Jira API enabled with credentials",
                    suggested_action="None",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name="jira:api",
                    status="ERROR",
                    message="Jira API enabled but credentials are incomplete",
                    suggested_action="Set JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN in config/jira-intake.env",
                )
            )
    else:
        checks.append(
            DoctorCheck(
                name="jira:api",
                status="INFO",
                message="Jira API is disabled (JIRA_API_ENABLED=false)",
                suggested_action="Enable only when ready to read Jira cards via API",
            )
        )

    if jira_settings.require_issue_allowlist:
        allowlist_path = Path(jira_settings.allowlist_file)
        if not allowlist_path.is_absolute():
            allowlist_path = base_dir / jira_settings.allowlist_file
        if allowlist_path.exists():
            checks.append(
                DoctorCheck(
                    name="jira:allowlist",
                    status="OK",
                    message=f"Allowlist found at {allowlist_path}",
                    suggested_action="None",
                )
            )
        else:
            checks.append(
                DoctorCheck(
                    name="jira:allowlist",
                    status="WARN",
                    message=f"Allowlist file missing: {allowlist_path}",
                    suggested_action="Create file and authorize cards with ./scripts/agentctl jira-authorize --issue INF-33",
                )
            )

    if jira_settings.actions_enabled:
        checks.append(
            DoctorCheck(
                name="jira:actions",
                status="OK",
                message="Jira external actions enabled (comment/transition)",
                suggested_action="None",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                name="jira:actions",
                status="INFO",
                message="Jira external actions disabled (JIRA_ACTIONS_ENABLED=false)",
                suggested_action="Enable only when ready to apply comments/transitions via API",
            )
        )

    if jira_settings.auto_sync_on_review:
        checks.append(
            DoctorCheck(
                name="jira:auto-sync",
                status="OK",
                message="Auto-sync on review is enabled",
                suggested_action="None",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                name="jira:auto-sync",
                status="INFO",
                message="Auto-sync on review is disabled",
                suggested_action="Enable JIRA_AUTO_SYNC_ON_REVIEW=true when ready",
            )
        )

    return checks
