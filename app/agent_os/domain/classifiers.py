"""Task classification and risk heuristics."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassificationResult:
    category: str
    priority: str


def normalize_text(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "à": "a",
            "â": "a",
            "ã": "a",
            "ä": "a",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "í": "i",
            "ì": "i",
            "î": "i",
            "ï": "i",
            "ó": "o",
            "ò": "o",
            "ô": "o",
            "õ": "o",
            "ö": "o",
            "ú": "u",
            "ù": "u",
            "û": "u",
            "ü": "u",
            "ç": "c",
        }
    )
    return text.lower().translate(replacements)


def contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def classify_task(task_text: str) -> ClassificationResult:
    text = normalize_text(task_text)

    if contains_any(text, ["firestore", "acesso", "access", "iam", "permission", "permissao", "credentials", "role"]):
        return ClassificationResult(category="access-gcp", priority="P2")

    if contains_any(text, ["pipeline", "sonar", "build", "compilacao", "ci/cd", "cicd"]):
        return ClassificationResult(category="ci-cd", priority="P2")

    if contains_any(
        text,
        ["observability", "observabilidade", "datadog", "telemetry", "telemetria", "logs", "metrics", "tracing"],
    ):
        return ClassificationResult(category="observability", priority="P2")

    if contains_any(text, ["release", "deploy", "deployment", "promocao", "promotion", "rollback", "gate"]):
        return ClassificationResult(category="release", priority="P2")

    if contains_any(text, ["documentation", "documenta", "docs", "readme"]):
        return ClassificationResult(category="documentation", priority="P3")

    return ClassificationResult(category="general", priority="P3")


def extract_risks(task_text: str, category: str, priority: str) -> list[str]:
    text = normalize_text(task_text)
    risks: list[str] = []

    if priority == "P1":
        risks.append("Critical urgency may cause rushed decisions")
    if category in {"release", "ci-cd", "access-gcp"}:
        risks.append("High operational impact if validation is incomplete")
    if contains_any(text, ["prod", "production", "producao"]):
        risks.append("Production context requires explicit approval evidence")
    if contains_any(text, ["security", "seguranca", "secret", "token", "credential"]):
        risks.append("Security-sensitive scope detected")
    if re.search(r"\b(hotfix|urgent|urgente)\b", text):
        risks.append("Urgent scope detected; enforce rollback and checklist")

    if not risks:
        risks.append("No critical risk keywords detected; keep standard validation")

    return risks
