#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$BASE_DIR/outputs/checklists"
mkdir -p "$OUT_DIR"

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/generate-env-approval-checklist.sh <regression|prerelease|stage|preprod|prod> [task_id]"
  exit 1
fi

ENV_NAME="$1"
TASK_ID="${2:-N/A}"

case "$ENV_NAME" in
  regression|prerelease|stage|preprod|prod)
    ;;
  *)
    echo "Ambiente invalido: $ENV_NAME"
    exit 1
    ;;
esac

TS="$(date +%Y%m%d-%H%M%S)"
OUT_FILE="$OUT_DIR/${ENV_NAME}-approval-${TS}.md"

cat > "$OUT_FILE" <<EOF2
# Environment Approval Checklist - ${ENV_NAME}

## Metadata
- Task ID: ${TASK_ID}
- Environment: ${ENV_NAME}
- Generated At: ${TS}
- Manager Approval: Pending

## Scope and Objective
- [ ] Objective is clear and measurable
- [ ] Scope is validated with stakeholders
- [ ] Rollback strategy is documented

## Quality and Tests
- [ ] Unit/integration tests passed
- [ ] Validation command output attached
- [ ] Regressions reviewed

## Security and Compliance
- [ ] Sensitive data/secrets are not exposed
- [ ] Least privilege principle validated
- [ ] Audit trail updated with approver identity

## Observability and Operations
- [ ] Logs/metrics/traces contract validated
- [ ] Alerts/monitoring reviewed
- [ ] Runbook/troubleshooting updated

## Evidence
- [ ] Evidence links attached
- [ ] PR/commit references attached
- [ ] Jira/task status synchronized if enabled

## Decision
- [ ] GO
- [ ] NO-GO

## Approval Record
- Approved by:
- Approval note:
- Date:
EOF2

echo "Checklist gerado em: $OUT_FILE"
