#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/classify-task.sh \"descrição da tarefa\""
  exit 1
fi

TEXT="$(printf '%s' "$*" | tr '[:upper:]' '[:lower:]')"

CATEGORY="general"
PRIORITY="P3"

if [[ "$TEXT" == *"acesso"* ]] || [[ "$TEXT" == *"iam"* ]] || [[ "$TEXT" == *"firestore"* ]]; then
  CATEGORY="access-gcp"
  PRIORITY="P2"
elif [[ "$TEXT" == *"pipeline"* ]] || [[ "$TEXT" == *"sonar"* ]] || [[ "$TEXT" == *"build"* ]]; then
  CATEGORY="ci-cd"
  PRIORITY="P2"
elif [[ "$TEXT" == *"observability"* ]] || [[ "$TEXT" == *"datadog"* ]]; then
  CATEGORY="observability"
  PRIORITY="P2"
elif [[ "$TEXT" == *"release"* ]] || [[ "$TEXT" == *"deploy"* ]]; then
  CATEGORY="release"
  PRIORITY="P2"
elif [[ "$TEXT" == *"documenta"* ]] || [[ "$TEXT" == *"readme"* ]]; then
  CATEGORY="documentation"
  PRIORITY="P3"
fi

echo "CATEGORY=$CATEGORY"
echo "PRIORITY=$PRIORITY"
