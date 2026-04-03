#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$BASE_DIR/outputs/releases"
mkdir -p "$OUT_DIR"

NAME="${1:-release-note}"
OUT_FILE="$OUT_DIR/$NAME.md"

cat > "$OUT_FILE" <<EOF2
# Release Notes: $NAME

## Summary
- Pending definition

## Changes
- Pending collection

## Risks
- Pending analysis

## Validation
- Pending evidence
EOF2

echo "Release note gerada em: $OUT_FILE"
