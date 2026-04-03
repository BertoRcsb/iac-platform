"""LLM adapter implementations and unified interface."""

from __future__ import annotations

from dataclasses import dataclass

from app.agent_os.domain.classifiers import extract_risks
from app.agent_os.domain.interfaces import LLMGateway


@dataclass
class RuleBasedLLMAdapter(LLMGateway):
    """Deterministic adapter used as safe default for planning and review."""

    def generate_plan(self, task_text: str, category: str) -> dict[str, object]:
        plans = {
            "observability": [
                "Use platform-observability-core as baseline",
                "Apply template to service Dockerfile and entrypoint",
                "Validate logs/metrics/tracing contract",
                "Prepare PR with evidence checklist",
            ],
            "ci-cd": [
                "Collect failing pipeline evidence",
                "Validate credentials/tokens and permissions",
                "Check build and Sonar configuration",
                "Propose fix with rollback strategy",
            ],
            "access-gcp": [
                "Identify affected project/environment",
                "Audit current IAM permissions",
                "Apply least-privilege role set",
                "Validate access and capture approval evidence",
            ],
            "release": [
                "Prepare release scope and notes",
                "Validate risk checklist and rollback path",
                "Request explicit manager approval",
                "Advance only through approved promotion gate",
            ],
            "documentation": [
                "Gather source decisions and artifacts",
                "Draft concise technical summary",
                "Review against standards",
                "Publish and link references",
            ],
        }
        steps = plans.get(category, ["Analyze scope", "Define constraints", "Propose safe implementation"])
        return {
            "summary": f"Plan generated for category '{category}' with explicit validation and approval gates.",
            "steps": steps,
        }

    def summarize(self, text: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        return first_line[:240] if first_line else "No summary available"

    def review_change(self, task_text: str, execution_logs: list[str]) -> dict[str, object]:
        findings: list[str] = []
        joined = "\n".join(execution_logs).lower()
        if "error" in joined:
            findings.append("Execution logs contain error markers; keep task BLOCKED until resolved")
        if "approval" not in joined:
            findings.append("Approval evidence not found in execution logs")
        conclusion = "PASS"
        if findings:
            conclusion = "REQUIRES_ATTENTION"
        return {
            "findings": findings,
            "conclusion": conclusion,
        }

    def extract_risks(self, task_text: str, category: str, priority: str) -> list[str]:
        return extract_risks(task_text, category, priority)


@dataclass
class OpenRouterAdapter(RuleBasedLLMAdapter):
    provider_name: str = "openrouter"


@dataclass
class GroqAdapter(RuleBasedLLMAdapter):
    provider_name: str = "groq"


@dataclass
class OpenAIAdapter(RuleBasedLLMAdapter):
    provider_name: str = "openai"


@dataclass
class ClaudeAdapter(RuleBasedLLMAdapter):
    provider_name: str = "claude"


@dataclass
class GeminiAdapter(RuleBasedLLMAdapter):
    provider_name: str = "gemini"


@dataclass
class HuggingFaceAdapter(RuleBasedLLMAdapter):
    provider_name: str = "huggingface"


def build_adapter(provider: str) -> RuleBasedLLMAdapter:
    mapping = {
        "openrouter": OpenRouterAdapter,
        "groq": GroqAdapter,
        "openai": OpenAIAdapter,
        "claude": ClaudeAdapter,
        "gemini": GeminiAdapter,
        "huggingface": HuggingFaceAdapter,
    }
    adapter_cls = mapping.get(provider, RuleBasedLLMAdapter)
    return adapter_cls()
