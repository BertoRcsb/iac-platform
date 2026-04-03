#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REPORT="$BASE_DIR/outputs/reports/priority-report.md"
mkdir -p "$(dirname "$REPORT")"

cat > "$REPORT" <<EOF2
# Priority Report

## Purpose
This report should list:
- highest priority tasks
- blocked items
- tasks awaiting approval
- risks requiring escalation

## Current State
Manual population required in current version.
EOF2

echo "Relatório gerado em: $REPORT"
