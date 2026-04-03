#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/classify-task.sh \"descrição da tarefa\""
  exit 1
fi

normalize_text() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed \
      -e 's/[áàâãä]/a/g' \
      -e 's/[éèêë]/e/g' \
      -e 's/[íìîï]/i/g' \
      -e 's/[óòôõö]/o/g' \
      -e 's/[úùûü]/u/g' \
      -e 's/ç/c/g'
}

contains_any() {
  local text="$1"
  shift
  local term
  for term in "$@"; do
    if [[ "$text" == *"$term"* ]]; then
      return 0
    fi
  done
  return 1
}

TEXT="$(normalize_text "$*")"

CATEGORY="general"
PRIORITY="P3"

if contains_any "$TEXT" "firestore" "acesso" "access" "iam" "permission" "permissao" "credentials" "credencial" "role" "papel"; then
  CATEGORY="access-gcp"
  PRIORITY="P2"
elif contains_any "$TEXT" "pipeline" "sonar" "build" "compilacao" "ci/cd" "cicd" "deploy pipeline"; then
  CATEGORY="ci-cd"
  PRIORITY="P2"
elif contains_any "$TEXT" "observability" "observabilidade" "datadog" "telemetry" "telemetria" "logs" "log" "metrics" "metricas" "tracing" "rastreio"; then
  CATEGORY="observability"
  PRIORITY="P2"
elif contains_any "$TEXT" "release" "deploy" "deployment" "promocao" "promotion" "go-live" "rollback" "gate"; then
  CATEGORY="release"
  PRIORITY="P2"
elif contains_any "$TEXT" "documenta" "documentation" "docs" "readme"; then
  CATEGORY="documentation"
  PRIORITY="P3"
fi

echo "CATEGORY=$CATEGORY"
echo "PRIORITY=$PRIORITY"
