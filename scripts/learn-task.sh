#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TASK_FILE=""
USE_LATEST="false"
SOURCE="manual"

LESSONS_FILE="$BASE_DIR/knowledge/lessons-learned.md"
IMPROVEMENTS_FILE="$BASE_DIR/knowledge/improvement-log.md"
DECISIONS_FILE="$BASE_DIR/knowledge/decision-log.md"

usage() {
  echo "Uso:"
  echo "  ./scripts/learn-task.sh --task /caminho/task.md"
  echo "  ./scripts/learn-task.sh --latest"
  echo ""
  echo "Flags opcionais:"
  echo "  --source <manual|execute-task.sh|pipeline>"
}

extract_request_text() {
  local file="$1"
  awk '
    /^## Request/ { capture=1; next }
    /^## / && capture { exit }
    capture { print }
  ' "$file"
}

extract_first_line() {
  local text="$1"
  printf '%s\n' "$text" | awk 'NF { print; exit }'
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
    --source)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      SOURCE="$2"
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

mkdir -p "$BASE_DIR/knowledge"
touch "$LESSONS_FILE" "$IMPROVEMENTS_FILE" "$DECISIONS_FILE"

TIMESTAMP_UTC="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
TASK_BASENAME="$(basename "$TASK_FILE")"

CATEGORY="$(awk -F': ' '/^- CATEGORY: /{value=$2} END{print value}' "$TASK_FILE")"
PRIORITY="$(awk -F': ' '/^- PRIORITY: /{value=$2} END{print value}' "$TASK_FILE")"
LAST_STATUS="$(awk -F': ' '/^- Status: /{value=$2} END{print value}' "$TASK_FILE")"
ERROR_COUNT="$(grep -c '\[ERROR\]' "$TASK_FILE" || true)"

REQUEST_TEXT="$(extract_request_text "$TASK_FILE")"
REQUEST_SUMMARY="$(extract_first_line "$REQUEST_TEXT")"

[[ -n "$CATEGORY" ]] || CATEGORY="general"
[[ -n "$PRIORITY" ]] || PRIORITY="P3"
[[ -n "$LAST_STATUS" ]] || LAST_STATUS="UNKNOWN"
[[ -n "$REQUEST_SUMMARY" ]] || REQUEST_SUMMARY="(no request summary)"

LESSON_NOTE="Execution completed without error markers."
if [[ "$ERROR_COUNT" != "0" ]]; then
  LESSON_NOTE="Execution produced error markers; improve evidence and validation before next run."
fi

IMPROVEMENT_NOTE="Keep same workflow and increase evidence quality."
if [[ "$CATEGORY" == "ci-cd" ]]; then
  IMPROVEMENT_NOTE="Strengthen pipeline diagnostics and mandatory pre-checks."
elif [[ "$CATEGORY" == "observability" ]]; then
  IMPROVEMENT_NOTE="Expand observability checklist and add validation evidence templates."
elif [[ "$CATEGORY" == "release" ]]; then
  IMPROVEMENT_NOTE="Enforce release checklist completeness before gate requests."
elif [[ "$CATEGORY" == "access-gcp" ]]; then
  IMPROVEMENT_NOTE="Improve least-privilege request template and approval traceability."
fi

cat >> "$LESSONS_FILE" <<EOF

## $TIMESTAMP_UTC - Lesson from $TASK_BASENAME
- Source: $SOURCE
- Category: $CATEGORY
- Priority: $PRIORITY
- Last Status: $LAST_STATUS
- Request Summary: $REQUEST_SUMMARY
- Insight: $LESSON_NOTE
EOF

cat >> "$IMPROVEMENTS_FILE" <<EOF

## $TIMESTAMP_UTC - Improvement from $TASK_BASENAME
- Source: $SOURCE
- Category: $CATEGORY
- Priority: $PRIORITY
- Proposal: $IMPROVEMENT_NOTE
- Next Action: review with Manager Agent before enforcing changes
EOF

cat >> "$DECISIONS_FILE" <<EOF

## $TIMESTAMP_UTC - Learning Decision ($TASK_BASENAME)
- Decision: keep learning loop active for executed tasks
- Context: category=$CATEGORY priority=$PRIORITY status=$LAST_STATUS
- Rationale: improve repeatability and operational memory
- Source: $SOURCE
EOF

echo "Learning update concluído:"
echo "  Task: $TASK_FILE"
echo "  Lessons: $LESSONS_FILE"
echo "  Improvements: $IMPROVEMENTS_FILE"
echo "  Decisions: $DECISIONS_FILE"
