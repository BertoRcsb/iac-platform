#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASKS_DIR="$BASE_DIR/tasks/incoming"
CONFIG_FILE_DEFAULT="$BASE_DIR/config/jira-intake.env"
CONFIG_FILE="${JIRA_INTAKE_CONFIG:-$CONFIG_FILE_DEFAULT}"
AI_CONFIG_FILE_DEFAULT="$BASE_DIR/config/ai-providers.env"
AI_CONFIG_FILE="${AI_PROVIDERS_CONFIG:-$AI_CONFIG_FILE_DEFAULT}"

CLASSIFY_SCRIPT="$BASE_DIR/scripts/classify-task.sh"
PLAN_SCRIPT="$BASE_DIR/scripts/plan-task.sh"
EXECUTE_SCRIPT="$BASE_DIR/scripts/execute-task.sh"
AI_ROUTER_SCRIPT="$BASE_DIR/scripts/ai-router.sh"

# Safe defaults for local usage.
JIRA_API_ENABLED="false"
JIRA_BASE_URL=""
JIRA_EMAIL=""
JIRA_API_TOKEN=""
AUTO_ACTIONS_ENABLED="false"
AUTO_ACTIONS_LOCAL_ONLY="true"
DRY_RUN="true"
REQUIRE_MANAGER_APPROVAL="true"
AI_ROUTER_ENABLED="true"

LINK_INPUT=""
TEXT_INPUT=""
FILE_INPUT=""
APPLY_ACTIONS_REQUESTED="false"

usage() {
  echo "Uso:"
  echo "  ./scripts/intake-task.sh --text \"descrição da tarefa\""
  echo "  ./scripts/intake-task.sh --link \"https://.../browse/ABC-123\""
  echo "  ./scripts/intake-task.sh --link \"https://.../browse/ABC-123\" --text \"contexto colado\""
  echo "  ./scripts/intake-task.sh --file /caminho/entrada.txt"
  echo ""
  echo "Flag opcional:"
  echo "  --apply-actions   chama execute-task.sh após intake (respeita DRY_RUN/config)"
}

extract_issue_key() {
  local text="$1"
  printf '%s' "$text" \
    | tr '[:lower:]' '[:upper:]' \
    | grep -oE '[A-Z][A-Z0-9]+-[0-9]+' \
    | head -n 1 || true
}

sanitize_html() {
  printf '%s' "$1" \
    | sed -E 's/<[^>]+>/ /g' \
    | tr '\n' ' ' \
    | sed -E 's/[[:space:]]+/ /g' \
    | sed -E 's/^ //; s/ $//'
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --link)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      LINK_INPUT="$2"
      shift 2
      ;;
    --text)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      TEXT_INPUT="$2"
      shift 2
      ;;
    --file)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      FILE_INPUT="$2"
      shift 2
      ;;
    --apply-actions)
      APPLY_ACTIONS_REQUESTED="true"
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

if [[ -z "$LINK_INPUT" ]] && [[ -z "$TEXT_INPUT" ]] && [[ -z "$FILE_INPUT" ]]; then
  echo "Erro: informe ao menos uma fonte (--link, --text ou --file)."
  usage
  exit 1
fi

if [[ -n "$FILE_INPUT" ]] && { [[ -n "$LINK_INPUT" ]] || [[ -n "$TEXT_INPUT" ]]; }; then
  echo "Erro: --file não pode ser combinado com --link/--text."
  usage
  exit 1
fi

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$CONFIG_FILE"
fi

if [[ -f "$AI_CONFIG_FILE" ]]; then
  # shellcheck source=/dev/null
  source "$AI_CONFIG_FILE"
fi

if [[ ! -x "$CLASSIFY_SCRIPT" ]] || [[ ! -x "$PLAN_SCRIPT" ]]; then
  echo "Erro: scripts obrigatórios não encontrados/executáveis:"
  echo "  - $CLASSIFY_SCRIPT"
  echo "  - $PLAN_SCRIPT"
  exit 1
fi

SOURCE_TYPE=""
SOURCE_REF=""
JIRA_ISSUE_KEY=""
JIRA_FETCH_STATUS="NOT_APPLICABLE"
REQUEST_TEXT=""

if [[ -n "$FILE_INPUT" ]]; then
  if [[ ! -f "$FILE_INPUT" ]]; then
    echo "Erro: arquivo não encontrado: $FILE_INPUT"
    exit 1
  fi
  SOURCE_TYPE="text-file"
  SOURCE_REF="$FILE_INPUT"
  REQUEST_TEXT="$(cat "$FILE_INPUT")"
elif [[ -n "$LINK_INPUT" ]] && [[ -n "$TEXT_INPUT" ]]; then
  SOURCE_TYPE="jira-link-plus-text"
  SOURCE_REF="$LINK_INPUT"
  JIRA_ISSUE_KEY="$(extract_issue_key "$LINK_INPUT")"
  REQUEST_TEXT="$TEXT_INPUT"
else
  if [[ -n "$TEXT_INPUT" ]]; then
    SOURCE_TYPE="pasted-text"
    SOURCE_REF="inline"
    REQUEST_TEXT="$TEXT_INPUT"
  else
    SOURCE_TYPE="jira-link"
    SOURCE_REF="$LINK_INPUT"
    JIRA_ISSUE_KEY="$(extract_issue_key "$LINK_INPUT")"
    REQUEST_TEXT="$LINK_INPUT"
  fi
fi

if [[ -n "$LINK_INPUT" ]] && [[ "$JIRA_API_ENABLED" == "true" ]]; then
  if [[ -z "$JIRA_ISSUE_KEY" ]]; then
    JIRA_FETCH_STATUS="ISSUE_KEY_NOT_FOUND"
  elif [[ -z "$JIRA_BASE_URL" ]] || [[ -z "$JIRA_EMAIL" ]] || [[ -z "$JIRA_API_TOKEN" ]]; then
    JIRA_FETCH_STATUS="MISSING_JIRA_CREDENTIALS"
  elif ! command -v curl >/dev/null 2>&1; then
    JIRA_FETCH_STATUS="CURL_NOT_AVAILABLE"
  else
    API_BASE="${JIRA_BASE_URL%/}"
    API_URL="$API_BASE/rest/api/3/issue/$JIRA_ISSUE_KEY?fields=summary,description,priority,issuetype,status,labels&expand=renderedFields"
    if RESPONSE="$(curl -fsS -u "$JIRA_EMAIL:$JIRA_API_TOKEN" -H "Accept: application/json" "$API_URL" 2>/dev/null)"; then
      if command -v jq >/dev/null 2>&1; then
        SUMMARY="$(printf '%s' "$RESPONSE" | jq -r '.fields.summary // empty')"
        DESC_HTML="$(printf '%s' "$RESPONSE" | jq -r '.renderedFields.description // empty')"
        DESC_TEXT="$(sanitize_html "$DESC_HTML")"
        FETCHED_TEXT="$SUMMARY"
        if [[ -n "$DESC_TEXT" ]]; then
          FETCHED_TEXT="$FETCHED_TEXT"$'\n\n'"$DESC_TEXT"
        fi
        if [[ -n "${FETCHED_TEXT//[[:space:]]/}" ]]; then
          REQUEST_TEXT="$FETCHED_TEXT"
          if [[ -n "$TEXT_INPUT" ]]; then
            REQUEST_TEXT="$REQUEST_TEXT"$'\n\n'"Additional Context:"$'\n'"$TEXT_INPUT"
          fi
        fi
        JIRA_FETCH_STATUS="SUCCESS"
      else
        JIRA_FETCH_STATUS="JQ_NOT_AVAILABLE"
      fi
    else
      JIRA_FETCH_STATUS="FETCH_FAILED"
    fi
  fi
elif [[ -n "$LINK_INPUT" ]] && [[ "$JIRA_API_ENABLED" != "true" ]]; then
  JIRA_FETCH_STATUS="DISABLED_BY_CONFIG"
fi

if [[ -z "${REQUEST_TEXT//[[:space:]]/}" ]]; then
  echo "Erro: não foi possível obter conteúdo para análise."
  exit 1
fi

CLASS_OUTPUT="$("$CLASSIFY_SCRIPT" "$REQUEST_TEXT")"
CATEGORY="$(printf '%s\n' "$CLASS_OUTPUT" | awk -F= '/^CATEGORY=/{print $2}')"
PRIORITY="$(printf '%s\n' "$CLASS_OUTPUT" | awk -F= '/^PRIORITY=/{print $2}')"
PLAN_OUTPUT="$("$PLAN_SCRIPT" "$REQUEST_TEXT")"

ROUTER_AGENT="analysis"
case "$CATEGORY" in
  observability) ROUTER_AGENT="execution" ;;
  release) ROUTER_AGENT="release" ;;
  documentation) ROUTER_AGENT="documentation" ;;
  *) ROUTER_AGENT="analysis" ;;
esac

ROUTER_OUTPUT="AI_ROUTER_ENABLED=false
AI_ROUTER_SELECTED_PROVIDER=none
AI_ROUTER_SELECTED_MODEL=none
AI_ROUTER_SELECTION_REASON=router_not_available"
if [[ "$AI_ROUTER_ENABLED" == "true" ]] && [[ -x "$AI_ROUTER_SCRIPT" ]]; then
  if ROUTER_OUTPUT="$("$AI_ROUTER_SCRIPT" --task "$REQUEST_TEXT" --category "$CATEGORY" --priority "$PRIORITY" --agent "$ROUTER_AGENT" 2>&1)"; then
    :
  else
    ROUTER_OUTPUT="AI_ROUTER_ENABLED=true
AI_ROUTER_SELECTED_PROVIDER=none
AI_ROUTER_SELECTED_MODEL=none
AI_ROUTER_SELECTION_REASON=router_error"
  fi
fi

ROUTER_PROVIDER="$(printf '%s\n' "$ROUTER_OUTPUT" | awk -F= '/^AI_ROUTER_SELECTED_PROVIDER=/{print $2; exit}')"
[[ -n "$ROUTER_PROVIDER" ]] || ROUTER_PROVIDER="none"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TASKS_DIR"

if [[ -n "$JIRA_ISSUE_KEY" ]]; then
  ISSUE_KEY_SAFE="$(printf '%s' "$JIRA_ISSUE_KEY" | tr '[:upper:]' '[:lower:]')"
  TASK_FILE="$TASKS_DIR/task-${ISSUE_KEY_SAFE}-${TIMESTAMP}.md"
else
  TASK_FILE="$TASKS_DIR/task-${TIMESTAMP}.md"
fi

CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "$TASK_FILE" <<TASK
# AI Task Intake

## Source
- Type: $SOURCE_TYPE
- Reference: $SOURCE_REF
- Jira Issue Key: ${JIRA_ISSUE_KEY:-N/A}
- Jira Fetch Status: $JIRA_FETCH_STATUS
- Created At (UTC): $CREATED_AT

## Request
$REQUEST_TEXT

## Classification
- CATEGORY: ${CATEGORY:-unknown}
- PRIORITY: ${PRIORITY:-unknown}

## Auto Analysis
\`\`\`text
$PLAN_OUTPUT
\`\`\`

## AI Routing
\`\`\`text
$ROUTER_OUTPUT
\`\`\`

## Execution
- Status: PENDING_APPROVAL
- Auto Actions Requested at Intake: $APPLY_ACTIONS_REQUESTED
- Auto Actions Enabled by Config: $AUTO_ACTIONS_ENABLED
- Dry Run Mode: $DRY_RUN
- Manager Approval Required: $REQUIRE_MANAGER_APPROVAL
- Router Suggested Provider: $ROUTER_PROVIDER
- Next Step: ./scripts/execute-task.sh --task "$TASK_FILE"

## Notes
- Generated by scripts/intake-task.sh
- Intake phase does not deploy or provision infrastructure.
TASK

echo "Task intake concluído:"
echo "  $TASK_FILE"
echo ""
echo "Resumo:"
echo "  CATEGORY=$CATEGORY"
echo "  PRIORITY=$PRIORITY"
echo "  JIRA_FETCH_STATUS=$JIRA_FETCH_STATUS"
echo "  APPLY_ACTIONS_REQUESTED=$APPLY_ACTIONS_REQUESTED"
echo "  ROUTER_PROVIDER=$ROUTER_PROVIDER"

if [[ "$APPLY_ACTIONS_REQUESTED" == "true" ]]; then
  if [[ ! -x "$EXECUTE_SCRIPT" ]]; then
    echo ""
    echo "Aviso: execute-task.sh não encontrado/executável."
  else
    echo ""
    echo "Executando fase de execução via execute-task.sh..."
    "$EXECUTE_SCRIPT" --task "$TASK_FILE"
  fi
fi
