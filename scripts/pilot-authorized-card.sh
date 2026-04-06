#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$BASE_DIR"

ISSUE="${1:-ABC-123}"
REQUEST_TEXT="${2:-Pipeline falhou no Sonar e precisa de analise e plano seguro.}"
TEMPLATE="${TEMPLATE:-pipeline-failure}"
TEAM="${TEAM:-devops}"
APPROVED_BY="${APPROVED_BY:-pilot-manager}"
APPROVAL_NOTE="${APPROVAL_NOTE:-piloto local autorizado}"

TS="$(date +%Y%m%d-%H%M%S)"
REPORT_DIR="$BASE_DIR/outputs/reports"
REPORT_FILE="$REPORT_DIR/pilot-${ISSUE}-${TS}.log"
JIRA_ENV="$BASE_DIR/config/jira-intake.env"
mkdir -p "$REPORT_DIR"

env_get() {
  local key="$1"
  if [[ ! -f "$JIRA_ENV" ]]; then
    echo ""
    return 0
  fi
  awk -F'=' -v k="$key" '$1==k {v=$2; gsub(/"/, "", v); print v; exit}' "$JIRA_ENV"
}

log() {
  printf '%s\n' "$*" | tee -a "$REPORT_FILE"
}

run_and_capture() {
  local tmp
  tmp="$(mktemp)"
  log "$ $*"
  if "$@" >"$tmp" 2>&1; then
    cat "$tmp" | tee -a "$REPORT_FILE" >&2
    cat "$tmp"
    rm -f "$tmp"
    return 0
  fi
  cat "$tmp" | tee -a "$REPORT_FILE" >&2
  rm -f "$tmp"
  return 1
}

log "==============================================="
log "AgentCtl Pilot - Authorized Jira-like Card"
log "==============================================="
log "Issue: $ISSUE"
log "Template/Team: $TEMPLATE / $TEAM"
log "Report: $REPORT_FILE"
log ""

JIRA_API_ENABLED="$(env_get JIRA_API_ENABLED)"
JIRA_BASE_URL="$(env_get JIRA_BASE_URL)"
if [[ -z "$JIRA_BASE_URL" ]]; then
  JIRA_BASE_URL="https://example.atlassian.net"
fi

DRY_RUN_VALUE="$(awk -F'=' '$1=="DRY_RUN" {v=$2; gsub(/"/, "", v); print v; exit}' "$BASE_DIR/config/agentctl.env" 2>/dev/null || true)"
if [[ -z "$DRY_RUN_VALUE" ]]; then
  DRY_RUN_VALUE="true"
fi

log "Step 1/4 - Authorize card in allowlist"
run_and_capture ./scripts/agentctl jira-authorize --issue "$ISSUE" >/dev/null

log "Step 2/4 - Execute full pipeline in local safe mode"
if [[ "$JIRA_API_ENABLED" == "true" ]]; then
  RUN_OUTPUT="$(run_and_capture ./scripts/agentctl jira-run --issue "$ISSUE" --template "$TEMPLATE" --team "$TEAM" --manager-approved --auto-approve --approved-by "$APPROVED_BY" --approval-note "$APPROVAL_NOTE")"
else
  INPUT_TEXT="${JIRA_BASE_URL}/browse/${ISSUE}
${REQUEST_TEXT}"
  RUN_OUTPUT="$(run_and_capture ./scripts/agentctl run --input "$INPUT_TEXT" --template "$TEMPLATE" --team "$TEAM" --manager-approved --auto-approve --approved-by "$APPROVED_BY" --approval-note "$APPROVAL_NOTE")"
fi

TASK_ID="$(printf '%s\n' "$RUN_OUTPUT" | sed -n 's/.*"task_id": "\([^"]*\)".*/\1/p' | head -n 1)"
if [[ -z "$TASK_ID" ]]; then
  log "ERROR: task_id not found in pipeline output"
  exit 1
fi

log "Step 3/4 - Run GO/NO-GO report"
run_and_capture ./scripts/agentctl gate-check --task "$TASK_ID" --manager-approved --auto-approve --approved-by "$APPROVED_BY" >/dev/null

log "Step 4/4 - Capture final status"
run_and_capture ./scripts/agentctl status --task "$TASK_ID" >/dev/null

log ""
log "Pilot concluded"
log "Task ID: $TASK_ID"
log "DRY_RUN: $DRY_RUN_VALUE"
log "Report file: $REPORT_FILE"
log ""
log "Next suggested commands:"
log "  ./scripts/agentctl review-code --path ."
log "  ./scripts/agentctl debug-auto --command './scripts/agentctl-test.sh' --path . --apply-refactor"
