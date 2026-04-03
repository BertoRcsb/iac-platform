"""Provider routing adapter independent from business logic."""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from .config import AgentSettings, ProviderSettings


@dataclass
class RoutingDecision:
    provider: str
    model: str
    profile: str
    reason: str
    candidates: list[str]


def _has_provider(provider: str, settings: ProviderSettings) -> bool:
    if provider == "ollama":
        return settings.ollama_enabled and shutil.which("ollama") is not None
    if provider == "openrouter":
        return settings.openrouter_enabled and bool(settings.openrouter_api_key)
    if provider == "groq":
        return settings.groq_enabled and bool(settings.groq_api_key)
    if provider == "gemini":
        return settings.gemini_enabled and bool(settings.gemini_api_key)
    if provider == "openai":
        return settings.openai_enabled and bool(settings.openai_api_key)
    if provider == "claude":
        return settings.claude_enabled and bool(settings.claude_api_key)
    if provider == "huggingface":
        return settings.hf_enabled and bool(settings.hf_api_key)
    return False


def _model_for(provider: str, profile: str) -> str:
    model_map = {
        "ollama": {
            "reasoning": "qwen2.5:14b",
            "writing": "mistral:7b",
            "fast": "llama3.1:8b",
            "balanced": "llama3.1:8b",
        },
        "openrouter": {
            "reasoning": "deepseek/deepseek-r1:free",
            "writing": "qwen/qwen2.5-7b-instruct:free",
            "fast": "meta-llama/llama-3.1-8b-instruct:free",
            "balanced": "meta-llama/llama-3.1-8b-instruct:free",
        },
        "groq": {
            "reasoning": "llama-3.3-70b-versatile",
            "writing": "llama-3.3-70b-versatile",
            "fast": "llama-3.1-8b-instant",
            "balanced": "llama-3.1-8b-instant",
        },
        "gemini": {
            "reasoning": "gemini-2.5-pro",
            "writing": "gemini-2.0-flash",
            "fast": "gemini-2.0-flash",
            "balanced": "gemini-2.0-flash",
        },
        "openai": {
            "reasoning": "o4-mini",
            "writing": "gpt-4o-mini",
            "fast": "gpt-4o-mini",
            "balanced": "gpt-4o-mini",
        },
        "claude": {
            "reasoning": "claude-3-7-sonnet-latest",
            "writing": "claude-3-5-haiku-latest",
            "fast": "claude-3-5-haiku-latest",
            "balanced": "claude-3-5-haiku-latest",
        },
        "huggingface": {
            "reasoning": "mistralai/Mistral-7B-Instruct-v0.3",
            "writing": "Qwen/Qwen2.5-7B-Instruct",
            "fast": "Qwen/Qwen2.5-7B-Instruct",
            "balanced": "Qwen/Qwen2.5-7B-Instruct",
        },
    }
    return model_map.get(provider, {}).get(profile, "unknown-model")


def decide_provider(category: str, agent_settings: AgentSettings, provider_settings: ProviderSettings) -> RoutingDecision:
    if category in {"observability", "ci-cd", "release", "access-gcp"}:
        profile = "reasoning"
    elif category == "documentation":
        profile = "writing"
    else:
        profile = agent_settings.default_provider_profile or "balanced"

    free_chain = ["ollama", "openrouter", "groq", "gemini", "huggingface"]
    paid_chain = ["openai", "claude"]

    if agent_settings.ai_free_first:
        candidates = free_chain + (paid_chain if agent_settings.ai_allow_paid_fallback else [])
    else:
        candidates = paid_chain + free_chain if agent_settings.ai_allow_paid_fallback else free_chain

    for provider in candidates:
        if _has_provider(provider, provider_settings):
            return RoutingDecision(
                provider=provider,
                model=_model_for(provider, profile),
                profile=profile,
                reason="first_enabled_candidate",
                candidates=candidates,
            )

    return RoutingDecision(
        provider="none",
        model="none",
        profile=profile,
        reason="no_enabled_provider",
        candidates=candidates,
    )
