#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE_DEFAULT="$BASE_DIR/config/ai-providers.env"
CONFIG_FILE="${AI_PROVIDERS_CONFIG:-$CONFIG_FILE_DEFAULT}"

TASK_TEXT=""
CATEGORY="general"
PRIORITY="P3"
AGENT="analysis"
PROFILE=""

# Defaults (overridable by config file)
AI_ROUTER_ENABLED="true"
AI_ROUTER_MODE="recommendation"
AI_FREE_FIRST="true"
AI_ALLOW_PAID_FALLBACK="false"

AI_PROVIDER_OLLAMA_ENABLED="true"
AI_PROVIDER_OLLAMA_MODEL_FAST="llama3.1:8b"
AI_PROVIDER_OLLAMA_MODEL_REASONING="qwen2.5:14b"
AI_PROVIDER_OLLAMA_MODEL_WRITING="mistral:7b"

AI_PROVIDER_GROQ_ENABLED="false"
AI_PROVIDER_GROQ_API_KEY=""
AI_PROVIDER_GROQ_MODEL_FAST="llama-3.1-8b-instant"
AI_PROVIDER_GROQ_MODEL_REASONING="llama-3.3-70b-versatile"
AI_PROVIDER_GROQ_MODEL_WRITING="llama-3.3-70b-versatile"

AI_PROVIDER_GEMINI_ENABLED="false"
AI_PROVIDER_GEMINI_API_KEY=""
AI_PROVIDER_GEMINI_MODEL_FAST="gemini-2.0-flash"
AI_PROVIDER_GEMINI_MODEL_REASONING="gemini-2.5-pro"
AI_PROVIDER_GEMINI_MODEL_WRITING="gemini-2.0-flash"

AI_PROVIDER_OPENROUTER_ENABLED="false"
AI_PROVIDER_OPENROUTER_API_KEY=""
AI_PROVIDER_OPENROUTER_MODEL_FAST="meta-llama/llama-3.1-8b-instruct:free"
AI_PROVIDER_OPENROUTER_MODEL_REASONING="deepseek/deepseek-r1:free"
AI_PROVIDER_OPENROUTER_MODEL_WRITING="qwen/qwen2.5-7b-instruct:free"

AI_PROVIDER_HF_ENABLED="false"
AI_PROVIDER_HF_API_KEY=""
AI_PROVIDER_HF_MODEL_FAST="Qwen/Qwen2.5-7B-Instruct"
AI_PROVIDER_HF_MODEL_REASONING="mistralai/Mistral-7B-Instruct-v0.3"
AI_PROVIDER_HF_MODEL_WRITING="Qwen/Qwen2.5-7B-Instruct"

AI_PROVIDER_OPENAI_ENABLED="false"
AI_PROVIDER_OPENAI_API_KEY=""
AI_PROVIDER_OPENAI_MODEL_FAST="gpt-4o-mini"
AI_PROVIDER_OPENAI_MODEL_REASONING="o4-mini"
AI_PROVIDER_OPENAI_MODEL_WRITING="gpt-4o-mini"

AI_PROVIDER_CLAUDE_ENABLED="false"
AI_PROVIDER_CLAUDE_API_KEY=""
AI_PROVIDER_CLAUDE_MODEL_FAST="claude-3-5-haiku-latest"
AI_PROVIDER_CLAUDE_MODEL_REASONING="claude-3-7-sonnet-latest"
AI_PROVIDER_CLAUDE_MODEL_WRITING="claude-3-5-haiku-latest"

usage() {
  echo "Uso:"
  echo "  ./scripts/ai-router.sh --task \"texto\" [--category observability] [--priority P2]"
  echo ""
  echo "Flags:"
  echo "  --task <texto>"
  echo "  --category <general|observability|ci-cd|release|access-gcp|documentation>"
  echo "  --priority <P1|P2|P3|P4>"
  echo "  --agent <analysis|execution|review|documentation|release|intake>"
  echo "  --profile <reasoning|writing|balanced|fast>   # opcional, override automático"
}

normalize() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed \
      -e 's/[áàâãä]/a/g' \
      -e 's/[éèêë]/e/g' \
      -e 's/[íìîï]/i/g' \
      -e 's/[óòôõö]/o/g' \
      -e 's/[úùûü]/u/g' \
      -e 's/ç/c/g'
}

provider_enabled() {
  case "$1" in
    ollama) [[ "$AI_PROVIDER_OLLAMA_ENABLED" == "true" ]] && command -v ollama >/dev/null 2>&1 ;;
    groq) [[ "$AI_PROVIDER_GROQ_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_GROQ_API_KEY" ]] ;;
    gemini) [[ "$AI_PROVIDER_GEMINI_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_GEMINI_API_KEY" ]] ;;
    openrouter) [[ "$AI_PROVIDER_OPENROUTER_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_OPENROUTER_API_KEY" ]] ;;
    huggingface) [[ "$AI_PROVIDER_HF_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_HF_API_KEY" ]] ;;
    openai) [[ "$AI_PROVIDER_OPENAI_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_OPENAI_API_KEY" ]] ;;
    claude) [[ "$AI_PROVIDER_CLAUDE_ENABLED" == "true" ]] && [[ -n "$AI_PROVIDER_CLAUDE_API_KEY" ]] ;;
    *) return 1 ;;
  esac
}

provider_model() {
  local provider="$1"
  local profile="$2"
  case "$provider:$profile" in
    ollama:reasoning) echo "$AI_PROVIDER_OLLAMA_MODEL_REASONING" ;;
    ollama:writing) echo "$AI_PROVIDER_OLLAMA_MODEL_WRITING" ;;
    ollama:fast|ollama:balanced) echo "$AI_PROVIDER_OLLAMA_MODEL_FAST" ;;
    groq:reasoning) echo "$AI_PROVIDER_GROQ_MODEL_REASONING" ;;
    groq:writing) echo "$AI_PROVIDER_GROQ_MODEL_WRITING" ;;
    groq:fast|groq:balanced) echo "$AI_PROVIDER_GROQ_MODEL_FAST" ;;
    gemini:reasoning) echo "$AI_PROVIDER_GEMINI_MODEL_REASONING" ;;
    gemini:writing) echo "$AI_PROVIDER_GEMINI_MODEL_WRITING" ;;
    gemini:fast|gemini:balanced) echo "$AI_PROVIDER_GEMINI_MODEL_FAST" ;;
    openrouter:reasoning) echo "$AI_PROVIDER_OPENROUTER_MODEL_REASONING" ;;
    openrouter:writing) echo "$AI_PROVIDER_OPENROUTER_MODEL_WRITING" ;;
    openrouter:fast|openrouter:balanced) echo "$AI_PROVIDER_OPENROUTER_MODEL_FAST" ;;
    huggingface:reasoning) echo "$AI_PROVIDER_HF_MODEL_REASONING" ;;
    huggingface:writing) echo "$AI_PROVIDER_HF_MODEL_WRITING" ;;
    huggingface:fast|huggingface:balanced) echo "$AI_PROVIDER_HF_MODEL_FAST" ;;
    openai:reasoning) echo "$AI_PROVIDER_OPENAI_MODEL_REASONING" ;;
    openai:writing) echo "$AI_PROVIDER_OPENAI_MODEL_WRITING" ;;
    openai:fast|openai:balanced) echo "$AI_PROVIDER_OPENAI_MODEL_FAST" ;;
    claude:reasoning) echo "$AI_PROVIDER_CLAUDE_MODEL_REASONING" ;;
    claude:writing) echo "$AI_PROVIDER_CLAUDE_MODEL_WRITING" ;;
    claude:fast|claude:balanced) echo "$AI_PROVIDER_CLAUDE_MODEL_FAST" ;;
    *) echo "unknown-model" ;;
  esac
}

build_candidates() {
  local profile="$1"
  local free_chain=""
  local paid_chain=""
  case "$profile" in
    reasoning)
      free_chain="ollama,groq,gemini,openrouter,huggingface"
      paid_chain="claude,openai"
      ;;
    writing)
      free_chain="ollama,gemini,openrouter,huggingface,groq"
      paid_chain="claude,openai"
      ;;
    fast)
      free_chain="ollama,groq,gemini,openrouter,huggingface"
      paid_chain="openai,claude"
      ;;
    *)
      free_chain="ollama,groq,gemini,openrouter,huggingface"
      paid_chain="openai,claude"
      ;;
  esac

  if [[ "$AI_FREE_FIRST" == "true" ]]; then
    if [[ "$AI_ALLOW_PAID_FALLBACK" == "true" ]]; then
      echo "$free_chain,$paid_chain"
    else
      echo "$free_chain"
    fi
  else
    if [[ "$AI_ALLOW_PAID_FALLBACK" == "true" ]]; then
      echo "$paid_chain,$free_chain"
    else
      echo "$free_chain"
    fi
  fi
}

first_line() {
  printf '%s\n' "$1" | awk 'NF { print; exit }'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      TASK_TEXT="$2"
      shift 2
      ;;
    --category)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      CATEGORY="$2"
      shift 2
      ;;
    --priority)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      PRIORITY="$2"
      shift 2
      ;;
    --agent)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      AGENT="$2"
      shift 2
      ;;
    --profile)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      PROFILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento inválido: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

if [[ "$AI_ROUTER_ENABLED" != "true" ]]; then
  echo "AI_ROUTER_ENABLED=false"
  echo "AI_ROUTER_SELECTED_PROVIDER=none"
  echo "AI_ROUTER_SELECTED_MODEL=none"
  echo "AI_ROUTER_SELECTION_REASON=router_disabled"
  echo "AI_ROUTER_NOTE=No provider selected."
  exit 0
fi

if [[ -z "${TASK_TEXT//[[:space:]]/}" ]]; then
  TASK_TEXT="(task text not provided)"
fi

NORM_CATEGORY="$(normalize "$CATEGORY")"
NORM_AGENT="$(normalize "$AGENT")"

if [[ -z "$PROFILE" ]]; then
  case "$NORM_CATEGORY" in
    observability|ci-cd|release|access-gcp) PROFILE="reasoning" ;;
    documentation) PROFILE="writing" ;;
    *) PROFILE="balanced" ;;
  esac
fi

if [[ "$NORM_AGENT" == "documentation" ]]; then
  PROFILE="writing"
fi

CANDIDATES="$(build_candidates "$PROFILE")"
SELECTED_PROVIDER="none"
SELECTED_MODEL="none"
SELECTION_REASON="no_enabled_provider"

IFS=',' read -r -a CANDIDATE_ARRAY <<< "$CANDIDATES"
for provider in "${CANDIDATE_ARRAY[@]}"; do
  if provider_enabled "$provider"; then
    SELECTED_PROVIDER="$provider"
    SELECTED_MODEL="$(provider_model "$provider" "$PROFILE")"
    SELECTION_REASON="first_enabled_candidate"
    break
  fi
done

TASK_SUMMARY="$(first_line "$TASK_TEXT")"
TASK_SUMMARY="${TASK_SUMMARY:0:200}"

NEXT_STEP="No execution command generated."
case "$SELECTED_PROVIDER" in
  ollama)
    NEXT_STEP="ollama run $SELECTED_MODEL \"<PROMPT_FROM_TASK>\""
    ;;
  groq)
    NEXT_STEP="Use provider adapter with GROQ API (not executed automatically)."
    ;;
  gemini)
    NEXT_STEP="Use provider adapter with Gemini API (not executed automatically)."
    ;;
  openrouter)
    NEXT_STEP="Use provider adapter with OpenRouter API (not executed automatically)."
    ;;
  huggingface)
    NEXT_STEP="Use provider adapter with Hugging Face API (not executed automatically)."
    ;;
  openai)
    NEXT_STEP="Use provider adapter with OpenAI API (not executed automatically)."
    ;;
  claude)
    NEXT_STEP="Use provider adapter with Claude API (not executed automatically)."
    ;;
esac

echo "AI_ROUTER_ENABLED=true"
echo "AI_ROUTER_MODE=$AI_ROUTER_MODE"
echo "AI_ROUTER_CATEGORY=$CATEGORY"
echo "AI_ROUTER_PRIORITY=$PRIORITY"
echo "AI_ROUTER_AGENT=$AGENT"
echo "AI_ROUTER_PROFILE=$PROFILE"
echo "AI_ROUTER_FREE_FIRST=$AI_FREE_FIRST"
echo "AI_ROUTER_ALLOW_PAID_FALLBACK=$AI_ALLOW_PAID_FALLBACK"
echo "AI_ROUTER_CANDIDATES=$CANDIDATES"
echo "AI_ROUTER_SELECTED_PROVIDER=$SELECTED_PROVIDER"
echo "AI_ROUTER_SELECTED_MODEL=$SELECTED_MODEL"
echo "AI_ROUTER_SELECTION_REASON=$SELECTION_REASON"
echo "AI_ROUTER_TASK_SUMMARY=$TASK_SUMMARY"
echo "AI_ROUTER_NEXT_STEP=$NEXT_STEP"
echo "AI_ROUTER_NOTE=Recommendation only. No external API call was executed."
