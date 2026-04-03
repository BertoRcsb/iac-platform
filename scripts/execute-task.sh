#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG_FILE_DEFAULT="$BASE_DIR/config/jira-intake.env"
CONFIG_FILE="${JIRA_INTAKE_CONFIG:-$CONFIG_FILE_DEFAULT}"

CLASSIFY_SCRIPT="$BASE_DIR/scripts/classify-task.sh"
LEARNING_SCRIPT="$BASE_DIR/scripts/learn-task.sh"

# Safe defaults: explicit execution required.
AUTO_ACTIONS_ENABLED="false"
AUTO_ACTIONS_LOCAL_ONLY="true"
DRY_RUN="true"
REQUIRE_MANAGER_APPROVAL="true"
AUTO_LEARNING_ENABLED="true"
AUTO_LEARNING_ON_SIMULATION="true"

TASK_FILE=""
USE_LATEST="false"
FORCE_APPLY="false"
FORCE_DRY_RUN="false"
MANAGER_APPROVED="false"

ACTIONS_LOG=""

usage() {
  echo "Uso:"
  echo "  ./scripts/execute-task.sh --task /caminho/task.md"
  echo "  ./scripts/execute-task.sh --latest"
  echo ""
  echo "Flags opcionais:"
  echo "  --apply    executa ações reais (somente se AUTO_ACTIONS_ENABLED=true e DRY_RUN=false)"
  echo "  --manager-approved  confirma aprovação humana para permitir --apply"
  echo "  --dry-run  força simulação"
}

append_log() {
  local text="$1"
  if [[ -n "$ACTIONS_LOG" ]]; then
    ACTIONS_LOG+=$'\n'
  fi
  ACTIONS_LOG+="$text"
}

run_local_action() {
  local label="$1"
  shift
  local output=""

  if [[ "$EFFECTIVE_DRY_RUN" == "true" ]]; then
    echo "[DRY-RUN] $label"
    echo "Command: $*"
    echo ""
    return 0
  fi

  if output="$("$@" 2>&1)"; then
    echo "[OK] $label"
    echo "$output"
    echo ""
  else
    echo "[ERROR] $label"
    echo "$output"
    echo ""
  fi
}

append_action() {
  local label="$1"
  shift
  local step_output
  step_output="$(run_local_action "$label" "$@")"
  append_log "$step_output"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --task)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      TASK_FILE="$2"
      shift 2
      ;;
    --latest)
      USE_LATEST="true"
      shift
      ;;
    --apply)
      FORCE_APPLY="true"
      shift
      ;;
    --manager-approved)
      MANAGER_APPROVED="true"
      shift
      ;;
    --dry-run)
      FORCE_DRY_RUN="true"
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

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

if [[ "$USE_LATEST" == "true" ]] && [[ -n "$TASK_FILE" ]]; then
  echo "Erro: use apenas --task ou --latest."
  exit 1
fi

if [[ "$USE_LATEST" == "true" ]]; then
  TASK_FILE="$(ls -1t "$BASE_DIR/tasks/incoming"/task-*.md 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$TASK_FILE" ]]; then
  echo "Erro: informe --task <arquivo> ou --latest."
  usage
  exit 1
fi

if [[ ! -f "$TASK_FILE" ]]; then
  echo "Erro: task file não encontrado: $TASK_FILE"
  exit 1
fi

CATEGORY="$(awk -F': ' '/^- CATEGORY: /{print $2; exit}' "$TASK_FILE" || true)"
PRIORITY="$(awk -F': ' '/^- PRIORITY: /{print $2; exit}' "$TASK_FILE" || true)"
REQUEST_TEXT="$(awk '
  /^## Request/ { capture=1; next }
  /^## / && capture { exit }
  capture { print }
' "$TASK_FILE")"

if [[ -z "$CATEGORY" ]] && [[ -x "$CLASSIFY_SCRIPT" ]]; then
  CLASS_OUTPUT="$("$CLASSIFY_SCRIPT" "$REQUEST_TEXT")"
  CATEGORY="$(printf '%s\n' "$CLASS_OUTPUT" | awk -F= '/^CATEGORY=/{print $2}')"
  PRIORITY="$(printf '%s\n' "$CLASS_OUTPUT" | awk -F= '/^PRIORITY=/{print $2}')"
fi

if [[ -z "$CATEGORY" ]]; then
  CATEGORY="general"
fi
if [[ -z "$PRIORITY" ]]; then
  PRIORITY="P3"
fi

if [[ "$FORCE_DRY_RUN" == "true" ]]; then
  EFFECTIVE_DRY_RUN="true"
else
  APPLY_ALLOWED="true"
  if [[ "$FORCE_APPLY" != "true" ]]; then
    APPLY_ALLOWED="false"
    append_log "[INFO] Running in dry-run because --apply was not provided."
  fi
  if [[ "$AUTO_ACTIONS_ENABLED" != "true" ]]; then
    APPLY_ALLOWED="false"
    append_log "[INFO] Running in dry-run because AUTO_ACTIONS_ENABLED is false."
  fi
  if [[ "$DRY_RUN" == "true" ]]; then
    APPLY_ALLOWED="false"
    append_log "[INFO] Running in dry-run because DRY_RUN is true in config."
  fi
  if [[ "$REQUIRE_MANAGER_APPROVAL" == "true" ]] && [[ "$MANAGER_APPROVED" != "true" ]]; then
    APPLY_ALLOWED="false"
    append_log "[INFO] Running in dry-run because manager approval was not confirmed (--manager-approved)."
  fi

  if [[ "$APPLY_ALLOWED" == "true" ]]; then
    EFFECTIVE_DRY_RUN="false"
  else
    EFFECTIVE_DRY_RUN="true"
  fi
fi

if [[ "$AUTO_ACTIONS_LOCAL_ONLY" != "true" ]]; then
  append_log "[BLOCKED] AUTO_ACTIONS_LOCAL_ONLY must remain true in this repository."
fi

append_log "Execution Context:"
append_log "- CATEGORY: $CATEGORY"
append_log "- PRIORITY: $PRIORITY"
append_log "- FORCE_APPLY: $FORCE_APPLY"
append_log "- MANAGER_APPROVED: $MANAGER_APPROVED"
append_log "- AUTO_ACTIONS_ENABLED: $AUTO_ACTIONS_ENABLED"
append_log "- DRY_RUN(config): $DRY_RUN"
append_log "- EFFECTIVE_DRY_RUN: $EFFECTIVE_DRY_RUN"
append_log "- REQUIRE_MANAGER_APPROVAL: $REQUIRE_MANAGER_APPROVAL"
append_log ""

if [[ "$AUTO_ACTIONS_LOCAL_ONLY" == "true" ]]; then
  case "$CATEGORY" in
    observability)
      append_action \
        "Generate observability checklist" \
        "$BASE_DIR/scripts/generate-checklist.sh" \
        "observability-$(date +%Y%m%d-%H%M%S)"
      append_action \
        "Generate priority report" \
        "$BASE_DIR/scripts/generate-priority-report.sh"
      ;;
    ci-cd)
      append_action \
        "Generate CI/CD checklist" \
        "$BASE_DIR/scripts/generate-checklist.sh" \
        "cicd-$(date +%Y%m%d-%H%M%S)"
      append_action \
        "Generate priority report" \
        "$BASE_DIR/scripts/generate-priority-report.sh"
      ;;
    release)
      append_action \
        "Generate release notes skeleton" \
        "$BASE_DIR/scripts/generate-release.sh" \
        "release-$(date +%Y%m%d-%H%M%S)"
      append_action \
        "Request approval (record)" \
        "$BASE_DIR/scripts/request-approval.sh" \
        "Promotion gate review for task $(basename "$TASK_FILE")"
      ;;
    access-gcp)
      append_action \
        "Generate access checklist" \
        "$BASE_DIR/scripts/generate-checklist.sh" \
        "access-$(date +%Y%m%d-%H%M%S)"
      append_action \
        "Request approval (record)" \
        "$BASE_DIR/scripts/request-approval.sh" \
        "Access request review for task $(basename "$TASK_FILE")"
      ;;
    *)
      append_action \
        "Generate general checklist" \
        "$BASE_DIR/scripts/generate-checklist.sh" \
        "general-$(date +%Y%m%d-%H%M%S)"
      ;;
  esac
fi

if [[ -z "$ACTIONS_LOG" ]]; then
  ACTIONS_LOG="No actions executed."
fi

RUN_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
STATUS="SIMULATED"
if [[ "$EFFECTIVE_DRY_RUN" == "false" ]]; then
  STATUS="EXECUTED_LOCAL"
fi

CMD_LINE="./scripts/execute-task.sh --task \"$TASK_FILE\""
if [[ "$FORCE_APPLY" == "true" ]]; then
  CMD_LINE="$CMD_LINE --apply"
fi
if [[ "$MANAGER_APPROVED" == "true" ]]; then
  CMD_LINE="$CMD_LINE --manager-approved"
fi
if [[ "$FORCE_DRY_RUN" == "true" ]]; then
  CMD_LINE="$CMD_LINE --dry-run"
fi

cat >> "$TASK_FILE" <<EOF

## Execution Log ($RUN_AT)
- Status: $STATUS
- Command: $CMD_LINE
\`\`\`text
$ACTIONS_LOG
\`\`\`
EOF

echo "Execução concluída para task:"
echo "  $TASK_FILE"
echo "Resumo:"
echo "  CATEGORY=$CATEGORY"
echo "  PRIORITY=$PRIORITY"
echo "  EFFECTIVE_DRY_RUN=$EFFECTIVE_DRY_RUN"
if [[ "$EFFECTIVE_DRY_RUN" == "true" ]]; then
  echo "  Dica: para executar de fato localmente, ajuste config e rode com --apply."
fi

if [[ "$AUTO_LEARNING_ENABLED" == "true" ]]; then
  SHOULD_LEARN="false"
  if [[ "$EFFECTIVE_DRY_RUN" == "false" ]] || [[ "$AUTO_LEARNING_ON_SIMULATION" == "true" ]]; then
    SHOULD_LEARN="true"
  fi

  if [[ "$SHOULD_LEARN" == "true" ]]; then
    if [[ -x "$LEARNING_SCRIPT" ]]; then
      echo ""
      echo "Executando ciclo de aprendizado..."
      if LEARN_OUTPUT="$("$LEARNING_SCRIPT" --task "$TASK_FILE" --source "execute-task.sh" 2>&1)"; then
        echo "$LEARN_OUTPUT"
      else
        echo "Aviso: falha ao executar learn-task.sh"
        echo "$LEARN_OUTPUT"
      fi
    else
      echo ""
      echo "Aviso: learn-task.sh não encontrado/executável; aprendizado automático ignorado."
    fi
  fi
fi
