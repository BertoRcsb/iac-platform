#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HUB_DIR="$BASE_DIR/tools/ai-hub"
ENV_FILE="${AI_PROVIDERS_CONFIG:-$BASE_DIR/config/ai-providers.env}"

if [[ $# -lt 2 ]]; then
  echo "Uso:"
  echo "  ./scripts/ai-hub-call.sh <provider> \"prompt\" [dry-run:true|false]"
  echo "Exemplo:"
  echo "  ./scripts/ai-hub-call.sh openrouter \"Summarize this task\" true"
  exit 1
fi

PROVIDER="$1"
PROMPT="$2"
DRY_RUN="${3:-true}"

if [[ ! -d "$HUB_DIR" ]]; then
  echo "Erro: módulo tools/ai-hub não encontrado."
  exit 1
fi

cd "$HUB_DIR"
npm run call -- --provider "$PROVIDER" --prompt "$PROMPT" --dry-run "$DRY_RUN" --env "$ENV_FILE"
