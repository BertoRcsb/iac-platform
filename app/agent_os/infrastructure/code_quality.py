"""Code review and debug helpers."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Finding:
    severity: str
    file: str
    rule: str
    message: str
    suggestion: str


@dataclass
class CommandResult:
    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass
class RefactorAction:
    file: Path
    description: str


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def _iter_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    candidates: list[Path] = []
    for path in target.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", "node_modules", "__pycache__"} for part in path.parts):
            continue
        if path.suffix in {".py", ".sh", ".tf", ".md", ".json"}:
            candidates.append(path)
    return candidates


def review_code(base_dir: Path, target_path: Path) -> dict:
    findings: list[Finding] = []
    files = _iter_files(target_path)

    for file in files:
        rel = str(file.relative_to(base_dir)) if file.is_relative_to(base_dir) else str(file)
        text = _read_text(file)
        if not text:
            continue

        if file.suffix == ".py":
            if "except Exception" in text:
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        file=rel,
                        rule="broad-exception",
                        message="Broad exception handler may hide root causes",
                        suggestion="Prefer specific exceptions where possible",
                    )
                )
            if re.search(r"subprocess\..*shell\s*=\s*True", text):
                findings.append(
                    Finding(
                        severity="HIGH",
                        file=rel,
                        rule="subprocess-shell-true",
                        message="subprocess with shell=True may increase command injection risk",
                        suggestion="Use argument list and shell=False",
                    )
                )

        if file.suffix == ".sh":
            first_lines = "\n".join(text.splitlines()[:8])
            if "set -euo pipefail" not in first_lines:
                findings.append(
                    Finding(
                        severity="MEDIUM",
                        file=rel,
                        rule="shell-strict-mode",
                        message="Shell script missing strict mode in header",
                        suggestion="Add: set -euo pipefail below shebang",
                    )
                )
            if "rm -rf /" in text:
                findings.append(
                    Finding(
                        severity="HIGH",
                        file=rel,
                        rule="dangerous-rm",
                        message="Potentially destructive rm command detected",
                        suggestion="Require explicit allowlist and confirmation",
                    )
                )

        todo_pattern = re.compile(r"(^|\\s)(TODO|FIXME)[:\\s]", re.IGNORECASE)
        if any(todo_pattern.search(line) for line in text.splitlines()):
            findings.append(
                Finding(
                    severity="LOW",
                    file=rel,
                    rule="todo-fixme",
                    message="Pending TODO/FIXME markers found",
                    suggestion="Convert TODO into tracked issue or resolved action",
                )
            )

    critical = [f for f in findings if f.severity == "HIGH"]
    medium = [f for f in findings if f.severity == "MEDIUM"]
    low = [f for f in findings if f.severity == "LOW"]

    return {
        "target": str(target_path),
        "summary": {
            "high": len(critical),
            "medium": len(medium),
            "low": len(low),
            "total": len(findings),
        },
        "findings": [f.__dict__ for f in findings],
    }


def run_command(base_dir: Path, command: str) -> CommandResult:
    proc = subprocess.run(
        ["bash", "-lc", command],
        cwd=base_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    return CommandResult(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _ensure_trailing_newline(content: str) -> str:
    return content if content.endswith("\n") else content + "\n"


def apply_safe_refactors(base_dir: Path, target_path: Path) -> tuple[list[RefactorAction], dict[Path, str]]:
    files = _iter_files(target_path)
    actions: list[RefactorAction] = []
    backups: dict[Path, str] = {}

    for file in files:
        text = _read_text(file)
        if not text:
            continue

        original = text
        updated = text

        if file.suffix == ".sh":
            lines = updated.splitlines()
            if lines and lines[0].startswith("#!/"):
                header = "\n".join(lines[:8])
                if "set -euo pipefail" not in header:
                    lines.insert(1, "set -euo pipefail")
                    updated = "\n".join(lines)
                    actions.append(RefactorAction(file=file, description="Added strict shell mode"))

        # universal whitespace-safe cleanup
        cleaned_lines = [line.rstrip() for line in updated.splitlines()]
        candidate = _ensure_trailing_newline("\n".join(cleaned_lines))
        if candidate != updated:
            updated = candidate
            actions.append(RefactorAction(file=file, description="Normalized trailing whitespace/newline"))

        if updated != original:
            backups[file] = original
            file.write_text(updated, encoding="utf-8")

    return actions, backups


def rollback_refactors(backups: dict[Path, str]) -> None:
    for file, content in backups.items():
        file.write_text(content, encoding="utf-8")


def write_debug_scientific_doc(
    base_dir: Path,
    name: str,
    hypothesis: str,
    command_before: CommandResult,
    command_after: CommandResult,
    applied_actions: list[RefactorAction],
) -> Path:
    shared_dir = base_dir / "knowledge" / "shared"
    shared_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    output = shared_dir / f"debug-{timestamp}-{name}.md"

    evidence_before = (command_before.stdout + "\n" + command_before.stderr).strip()[:4000]
    evidence_after = (command_after.stdout + "\n" + command_after.stderr).strip()[:4000]
    actions = "\n".join(f"- {a.file}: {a.description}" for a in applied_actions) or "- No refactor applied"

    output.write_text(
        "\n".join(
            [
                f"# Scientific Debug Resolution - {name}",
                "",
                "## Problem",
                f"Command failed or presented risk: `{command_before.command}`",
                "",
                "## Hypothesis",
                hypothesis,
                "",
                "## Experiment Method",
                "1. Run baseline command",
                "2. Apply safe refactor candidates",
                "3. Re-run command and compare",
                "",
                "## Refactors Applied",
                actions,
                "",
                "## Evidence (Before)",
                "```text",
                evidence_before,
                "```",
                "",
                "## Evidence (After)",
                "```text",
                evidence_after,
                "```",
                "",
                "## Analysis",
                "Comparison indicates whether refactor reduced failure/risk while preserving behavior.",
                "",
                "## Conclusion",
                "Accepted only when post-refactor command remains stable (or improves) without introducing new failures.",
                "",
                "## Reproducibility",
                f"- Baseline command: `{command_before.command}`",
                f"- Validation command: `{command_after.command}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    return output
