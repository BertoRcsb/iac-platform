"""Jira API integration helpers."""

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


@dataclass(frozen=True)
class JiraTransition:
    transition_id: str
    name: str


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

    payload = _request_json(settings, method="GET", url=api_url, payload=None, timeout_sec=timeout_sec)

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


def _basic_auth_header(settings: JiraSettings) -> str:
    auth_raw = f"{settings.email}:{settings.api_token}".encode("utf-8")
    return "Basic " + base64.b64encode(auth_raw).decode("ascii")


def _request_json(
    settings: JiraSettings,
    method: str,
    url: str,
    payload: dict | None,
    timeout_sec: int,
) -> dict:
    body: bytes | None = None
    headers = {
        "Accept": "application/json",
        "Authorization": _basic_auth_header(settings),
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout_sec) as response:  # noqa: S310
            raw = response.read().decode("utf-8") or "{}"
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail_raw = exc.read().decode("utf-8")
            parsed = json.loads(detail_raw)
            detail = str(parsed.get("errorMessages") or parsed.get("errors") or "").strip()
        except Exception:
            detail = ""
        suffix = f": {detail}" if detail else ""
        raise JiraClientError(f"Jira API HTTP error {exc.code}{suffix}") from exc
    except urllib.error.URLError as exc:
        raise JiraClientError(f"Jira API connection error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise JiraClientError("Invalid JSON response from Jira API") from exc


def _ensure_actions_enabled(settings: JiraSettings) -> None:
    if not settings.enabled:
        raise JiraClientError("JIRA_API_ENABLED=false")
    if not settings.actions_enabled:
        raise JiraClientError("JIRA_ACTIONS_ENABLED=false")
    if not settings.base_url or not settings.email or not settings.api_token:
        raise JiraClientError("Jira credentials are missing in config/jira-intake.env")


def list_jira_transitions(issue_ref: str, settings: JiraSettings, timeout_sec: int = 20) -> list[JiraTransition]:
    _ensure_actions_enabled(settings)
    issue_key = extract_issue_key(issue_ref)
    if not issue_key:
        raise JiraClientError("Could not extract Jira issue key")

    base = settings.base_url.rstrip("/")
    api_url = f"{base}/rest/api/3/issue/{issue_key}/transitions"
    payload = _request_json(settings, method="GET", url=api_url, payload=None, timeout_sec=timeout_sec)
    transitions_raw = payload.get("transitions") or []
    transitions: list[JiraTransition] = []
    for item in transitions_raw:
        if not isinstance(item, dict):
            continue
        transition_id = str(item.get("id") or "").strip()
        name = str(item.get("name") or "").strip()
        if transition_id and name:
            transitions.append(JiraTransition(transition_id=transition_id, name=name))
    return transitions


def _allowed_transition_names(settings: JiraSettings) -> set[str]:
    raw = settings.allowed_transition_names or ""
    values = {item.strip().lower() for item in raw.split(",") if item.strip()}
    return values


def transition_jira_issue(issue_ref: str, to_status: str, settings: JiraSettings, timeout_sec: int = 20) -> dict:
    _ensure_actions_enabled(settings)
    issue_key = extract_issue_key(issue_ref)
    if not issue_key:
        raise JiraClientError("Could not extract Jira issue key")
    target = (to_status or "").strip()
    if not target:
        raise JiraClientError("Target status is required")

    allowed = _allowed_transition_names(settings)
    if allowed and target.lower() not in allowed:
        raise JiraClientError(
            f"Transition '{target}' is not allowed by JIRA_ALLOWED_TRANSITIONS={settings.allowed_transition_names}"
        )

    transitions = list_jira_transitions(issue_key, settings, timeout_sec=timeout_sec)
    chosen = next((item for item in transitions if item.name.lower() == target.lower()), None)
    if not chosen:
        valid = ", ".join(item.name for item in transitions) or "none"
        raise JiraClientError(f"Transition '{target}' not available for {issue_key}. Available: {valid}")

    base = settings.base_url.rstrip("/")
    api_url = f"{base}/rest/api/3/issue/{issue_key}/transitions"
    _request_json(
        settings,
        method="POST",
        url=api_url,
        payload={"transition": {"id": chosen.transition_id}},
        timeout_sec=timeout_sec,
    )
    return {
        "issue_key": issue_key,
        "transition_id": chosen.transition_id,
        "transition_name": chosen.name,
    }


def add_jira_comment(issue_ref: str, comment: str, settings: JiraSettings, timeout_sec: int = 20) -> dict:
    _ensure_actions_enabled(settings)
    issue_key = extract_issue_key(issue_ref)
    if not issue_key:
        raise JiraClientError("Could not extract Jira issue key")
    text = (comment or "").strip()
    if not text:
        raise JiraClientError("Comment cannot be empty")

    base = settings.base_url.rstrip("/")
    api_url = f"{base}/rest/api/3/issue/{issue_key}/comment"
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [{"type": "text", "text": text}],
                }
            ],
        }
    }
    response = _request_json(settings, method="POST", url=api_url, payload=payload, timeout_sec=timeout_sec)
    comment_id = str(response.get("id") or "")
    return {
        "issue_key": issue_key,
        "comment_id": comment_id,
    }


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
