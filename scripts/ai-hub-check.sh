#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HUB_DIR="$BASE_DIR/tools/ai-hub"
ENV_FILE="${AI_PROVIDERS_CONFIG:-$BASE_DIR/config/ai-providers.env}"

if [[ ! -d "$HUB_DIR" ]]; then
  echo "Erro: módulo tools/ai-hub não encontrado."
  exit 1
fi

cd "$HUB_DIR"
npm run check -- --env "$ENV_FILE"
