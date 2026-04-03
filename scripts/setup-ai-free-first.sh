#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE="$BASE_DIR/config/ai-providers.env"
EXAMPLE_FILE="$BASE_DIR/config/ai-providers.env.example"

OPENROUTER_KEY="${OPENROUTER_API_KEY:-}"
GROQ_KEY="${GROQ_API_KEY:-}"
HF_KEY="${HF_API_KEY:-}"
RUN_REAL_TESTS="false"

usage() {
  echo "Uso:"
  echo "  ./scripts/setup-ai-free-first.sh [--openrouter-key <key>] [--groq-key <key>] [--hf-key <key>] [--run-real-tests]"
  echo ""
  echo "Observações:"
  echo "  - Sem chaves, o setup prepara o ambiente e valida em dry-run."
  echo "  - Com --run-real-tests, testes reais só rodam para provedores com chave."
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --openrouter-key)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      OPENROUTER_KEY="$2"
      shift 2
      ;;
    --groq-key)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      GROQ_KEY="$2"
      shift 2
      ;;
    --hf-key)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      HF_KEY="$2"
      shift 2
      ;;
    --run-real-tests)
      RUN_REAL_TESTS="true"
      shift
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

if [[ ! -f "$CONFIG_FILE" ]]; then
  if [[ ! -f "$EXAMPLE_FILE" ]]; then
    echo "Erro: arquivo de exemplo não encontrado: $EXAMPLE_FILE"
    exit 1
  fi
  cp "$EXAMPLE_FILE" "$CONFIG_FILE"
fi

set_kv() {
  local key="$1"
  local value="$2"
  if rg -q "^${key}=" "$CONFIG_FILE"; then
    sed -i "s|^${key}=.*|${key}=\"${value}\"|" "$CONFIG_FILE"
  else
    echo "${key}=\"${value}\"" >> "$CONFIG_FILE"
  fi
}

set_kv "AI_ROUTER_ENABLED" "true"
set_kv "AI_ROUTER_MODE" "recommendation"
set_kv "AI_FREE_FIRST" "true"
set_kv "AI_ALLOW_PAID_FALLBACK" "false"

set_kv "AI_PROVIDER_OPENROUTER_ENABLED" "true"
set_kv "AI_PROVIDER_GROQ_ENABLED" "true"
set_kv "AI_PROVIDER_HF_ENABLED" "true"

if [[ -n "$OPENROUTER_KEY" ]]; then
  set_kv "AI_PROVIDER_OPENROUTER_API_KEY" "$OPENROUTER_KEY"
fi
if [[ -n "$GROQ_KEY" ]]; then
  set_kv "AI_PROVIDER_GROQ_API_KEY" "$GROQ_KEY"
fi
if [[ -n "$HF_KEY" ]]; then
  set_kv "AI_PROVIDER_HF_API_KEY" "$HF_KEY"
fi

echo "Setup free-first aplicado em:"
echo "  $CONFIG_FILE"
echo ""

echo "Status de providers:"
"$BASE_DIR/scripts/ai-hub-check.sh"

echo ""
echo "Teste dry-run (openrouter):"
"$BASE_DIR/scripts/ai-hub-call.sh" openrouter "Quick health check from iac-platform" true

if [[ "$RUN_REAL_TESTS" == "true" ]]; then
  echo ""
  echo "Testes reais (somente com chave configurada):"

  OR_KEY_SET="$(awk -F= '/^AI_PROVIDER_OPENROUTER_API_KEY=/{gsub(/"/, "", $2); print $2}' "$CONFIG_FILE")"
  GROQ_KEY_SET="$(awk -F= '/^AI_PROVIDER_GROQ_API_KEY=/{gsub(/"/, "", $2); print $2}' "$CONFIG_FILE")"
  HF_KEY_SET="$(awk -F= '/^AI_PROVIDER_HF_API_KEY=/{gsub(/"/, "", $2); print $2}' "$CONFIG_FILE")"

  if [[ -n "${OR_KEY_SET}" ]]; then
    echo "- OpenRouter real test"
    "$BASE_DIR/scripts/ai-hub-call.sh" openrouter "Return: OPENROUTER_OK" false || true
  else
    echo "- OpenRouter: chave ausente (pulado)"
  fi

  if [[ -n "${GROQ_KEY_SET}" ]]; then
    echo "- Groq real test"
    "$BASE_DIR/scripts/ai-hub-call.sh" groq "Return: GROQ_OK" false || true
  else
    echo "- Groq: chave ausente (pulado)"
  fi

  if [[ -n "${HF_KEY_SET}" ]]; then
    echo "- HuggingFace real test"
    "$BASE_DIR/scripts/ai-hub-call.sh" huggingface "Return: HF_OK" false || true
  else
    echo "- HuggingFace: chave ausente (pulado)"
  fi
fi

echo ""
echo "Próximo passo recomendado:"
echo "  ./scripts/ai-hub-call.sh openrouter \"Resuma a task X\" false"
