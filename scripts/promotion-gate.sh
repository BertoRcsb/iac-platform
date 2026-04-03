#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/promotion-gate.sh <regression|prerelease|stage|preprod|prod>"
  exit 1
fi

GATE="$1"

case "$GATE" in
  regression|prerelease|stage|preprod|prod)
    echo "Gate: $GATE"
    echo "Validation required"
    echo "Approval required"
    echo "Advancement blocked until explicit manager approval"
    ;;
  *)
    echo "Gate inválido: $GATE"
    exit 1
    ;;
esac
