"""Jira API integration helpers (read-only intake)."""

from __future__ import annotations

import base64
import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from app.agent_os.infrastructure.config import JiraSettings


class JiraClientError(RuntimeError):
    """Raised when Jira API integration fails."""


ISSUE_KEY_REGEX = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class JiraIssue:
    key: str
    url: str
    summary: str
    description: str
    status: str
    priority: str
    issue_type: str
    labels: list[str]


def extract_issue_key(value: str) -> str:
    match = ISSUE_KEY_REGEX.search(value or "")
    if not match:
        return ""
    return match.group(1).upper()


def strip_html(value: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", value or "")
    compact = re.sub(r"\s+", " ", no_tags).strip()
    return compact


def _adf_text(node: dict) -> str:
    node_type = str(node.get("type", ""))
    if node_type == "text":
        return str(node.get("text", ""))
    content = node.get("content")
    if isinstance(content, list):
        parts = [_adf_text(item) for item in content if isinstance(item, dict)]
        if node_type in {"paragraph", "heading"}:
            return "".join(parts) + "\n"
        if node_type == "listItem":
            return "- " + "".join(parts) + "\n"
        return "".join(parts)
    return ""


def _description_from_payload(payload: dict) -> str:
    rendered = (payload.get("renderedFields") or {}).get("description")
    if isinstance(rendered, str) and rendered.strip():
        return strip_html(rendered)
    adf = ((payload.get("fields") or {}).get("description")) or {}
    if isinstance(adf, dict):
        return re.sub(r"\n{3,}", "\n\n", _adf_text(adf)).strip()
    return ""


def fetch_jira_issue(issue_ref: str, settings: JiraSettings, timeout_sec: int = 20) -> JiraIssue:
    if not settings.enabled:
        raise JiraClientError("JIRA_API_ENABLED=false")
    if not settings.base_url or not settings.email or not settings.api_token:
        raise JiraClientError("Jira credentials are missing in config/jira-intake.env")

    key = extract_issue_key(issue_ref)
    if not key:
        raise JiraClientError("Could not extract Jira issue key from input")

    base = settings.base_url.rstrip("/")
    api_url = (
        f"{base}/rest/api/3/issue/{key}"
        "?fields=summary,description,priority,issuetype,status,labels&expand=renderedFields"
    )

    auth_raw = f"{settings.email}:{settings.api_token}".encode("utf-8")
    auth_header = "Basic " + base64.b64encode(auth_raw).decode("ascii")
    request = urllib.request.Request(
        api_url,
        headers={
            "Accept": "application/json",
            "Authorization": auth_header,
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise JiraClientError(f"Jira API HTTP error {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise JiraClientError(f"Jira API connection error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise JiraClientError("Invalid JSON response from Jira API") from exc

    fields = payload.get("fields") or {}
    summary = str(fields.get("summary") or "").strip()
    description = _description_from_payload(payload)
    status = str((fields.get("status") or {}).get("name") or "").strip()
    priority = str((fields.get("priority") or {}).get("name") or "").strip()
    issue_type = str((fields.get("issuetype") or {}).get("name") or "").strip()
    labels = [str(item) for item in (fields.get("labels") or []) if isinstance(item, str)]
    issue_url = f"{base}/browse/{key}"

    return JiraIssue(
        key=key,
        url=issue_url,
        summary=summary,
        description=description,
        status=status,
        priority=priority,
        issue_type=issue_type,
        labels=labels,
    )


def load_jira_allowlist(path: Path) -> set[str]:
    if not path.exists():
        return set()
    allowed: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key = extract_issue_key(line)
        if key:
            allowed.add(key)
    return allowed


def ensure_jira_issue_authorized(issue_key: str, settings: JiraSettings, base_dir: Path) -> None:
    if not settings.require_issue_allowlist:
        return
    allowlist_path = Path(settings.allowlist_file)
    if not allowlist_path.is_absolute():
        allowlist_path = base_dir / settings.allowlist_file
    allowed = load_jira_allowlist(allowlist_path)
    if issue_key.upper() not in allowed:
        raise JiraClientError(
            f"Jira issue '{issue_key}' is not authorized in allowlist: {allowlist_path}"
        )


def authorize_jira_issue(issue_ref: str, settings: JiraSettings, base_dir: Path) -> tuple[str, Path]:
    issue_key = extract_issue_key(issue_ref)
    if not issue_key:
        raise JiraClientError("Could not extract Jira issue key")
    allowlist_path = Path(settings.allowlist_file)
    if not allowlist_path.is_absolute():
        allowlist_path = base_dir / settings.allowlist_file
    allowlist_path.parent.mkdir(parents=True, exist_ok=True)

    existing = load_jira_allowlist(allowlist_path)
    if issue_key not in existing:
        with allowlist_path.open("a", encoding="utf-8") as handle:
            handle.write(issue_key + "\n")
    return issue_key, allowlist_path
