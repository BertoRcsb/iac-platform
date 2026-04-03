#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$BASE_DIR/outputs/checklists"
mkdir -p "$OUT_DIR"

NAME="${1:-general-checklist}"
OUT_FILE="$OUT_DIR/$NAME.md"

cat > "$OUT_FILE" <<EOF2
# Checklist: $NAME

- [ ] Objective clearly defined
- [ ] Scope confirmed
- [ ] Risks identified
- [ ] Required approvals identified
- [ ] Documentation updated
- [ ] Validation evidence collected
EOF2

echo "Checklist gerado em: $OUT_FILE"
