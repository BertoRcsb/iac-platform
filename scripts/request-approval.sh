#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/request-approval.sh \"descrição do gate/aprovação\""
  exit 1
fi

echo "APPROVAL REQUIRED"
echo "Context: $*"
echo "Status: WAITING_FOR_MANAGER_APPROVAL"
