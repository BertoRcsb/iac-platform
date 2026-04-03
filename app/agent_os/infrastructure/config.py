"""Configuration loader for Agent OS."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class AgentSettings:
    profile: str = "local"
    dry_run: bool = True
    require_manager_approval: bool = True
    ai_free_first: bool = True
    ai_allow_paid_fallback: bool = False
    max_llm_calls_per_task: int = 8
    max_cost_usd_per_task: float = 2.0
    auto_learning_enabled: bool = True
    auto_learning_on_simulation: bool = True
    default_provider_profile: str = "balanced"


@dataclass
class ProviderSettings:
    ollama_enabled: bool = True
    openrouter_enabled: bool = False
    openrouter_api_key: str = ""
    groq_enabled: bool = False
    groq_api_key: str = ""
    gemini_enabled: bool = False
    gemini_api_key: str = ""
    openai_enabled: bool = False
    openai_api_key: str = ""
    claude_enabled: bool = False
    claude_api_key: str = ""
    hf_enabled: bool = False
    hf_api_key: str = ""


@dataclass
class JiraSettings:
    enabled: bool = False
    base_url: str = ""
    email: str = ""
    api_token: str = ""
    require_issue_allowlist: bool = True
    allowlist_file: str = "config/jira-issue-allowlist.txt"


def parse_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        data[key] = value
    return data


def load_agent_settings(base_dir: Path) -> AgentSettings:
    env_path = base_dir / "config" / "agentctl.env"
    raw = parse_env_file(env_path)

    return AgentSettings(
        profile=raw.get("PROFILE", "local"),
        dry_run=parse_bool(raw.get("DRY_RUN"), True),
        require_manager_approval=parse_bool(raw.get("REQUIRE_MANAGER_APPROVAL"), True),
        ai_free_first=parse_bool(raw.get("AI_FREE_FIRST"), True),
        ai_allow_paid_fallback=parse_bool(raw.get("AI_ALLOW_PAID_FALLBACK"), False),
        max_llm_calls_per_task=int(raw.get("MAX_LLM_CALLS_PER_TASK", "8")),
        max_cost_usd_per_task=float(raw.get("MAX_COST_USD_PER_TASK", "2.0")),
        auto_learning_enabled=parse_bool(raw.get("AUTO_LEARNING_ENABLED"), True),
        auto_learning_on_simulation=parse_bool(raw.get("AUTO_LEARNING_ON_SIMULATION"), True),
        default_provider_profile=raw.get("DEFAULT_PROVIDER_PROFILE", "balanced"),
    )


def load_provider_settings(base_dir: Path) -> ProviderSettings:
    env_path = base_dir / "config" / "ai-providers.env"
    raw = parse_env_file(env_path)

    return ProviderSettings(
        ollama_enabled=parse_bool(raw.get("AI_PROVIDER_OLLAMA_ENABLED"), True),
        openrouter_enabled=parse_bool(raw.get("AI_PROVIDER_OPENROUTER_ENABLED"), False),
        openrouter_api_key=raw.get("AI_PROVIDER_OPENROUTER_API_KEY", ""),
        groq_enabled=parse_bool(raw.get("AI_PROVIDER_GROQ_ENABLED"), False),
        groq_api_key=raw.get("AI_PROVIDER_GROQ_API_KEY", ""),
        gemini_enabled=parse_bool(raw.get("AI_PROVIDER_GEMINI_ENABLED"), False),
        gemini_api_key=raw.get("AI_PROVIDER_GEMINI_API_KEY", ""),
        openai_enabled=parse_bool(raw.get("AI_PROVIDER_OPENAI_ENABLED"), False),
        openai_api_key=raw.get("AI_PROVIDER_OPENAI_API_KEY", ""),
        claude_enabled=parse_bool(raw.get("AI_PROVIDER_CLAUDE_ENABLED"), False),
        claude_api_key=raw.get("AI_PROVIDER_CLAUDE_API_KEY", ""),
        hf_enabled=parse_bool(raw.get("AI_PROVIDER_HF_ENABLED"), False),
        hf_api_key=raw.get("AI_PROVIDER_HF_API_KEY", ""),
    )


def load_jira_settings(base_dir: Path) -> JiraSettings:
    env_path = base_dir / "config" / "jira-intake.env"
    raw = parse_env_file(env_path)
    return JiraSettings(
        enabled=parse_bool(raw.get("JIRA_API_ENABLED"), False),
        base_url=raw.get("JIRA_BASE_URL", ""),
        email=raw.get("JIRA_EMAIL", ""),
        api_token=raw.get("JIRA_API_TOKEN", ""),
        require_issue_allowlist=parse_bool(raw.get("JIRA_REQUIRE_ISSUE_ALLOWLIST"), True),
        allowlist_file=raw.get("JIRA_ISSUE_ALLOWLIST_FILE", "config/jira-issue-allowlist.txt"),
    )
