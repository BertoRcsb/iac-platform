#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/plan-task.sh \"descrição da tarefa\""
  exit 1
fi

TASK="$*"

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

NORM="$(normalize_text "$TASK")"

CATEGORY="general"
SPEC="none"
AGENT="analysis"
PRIORITY="P3"

# Classificação
if contains_any "$NORM" "firestore" "acesso" "access" "iam" "permission" "permissao" "credentials" "credencial" "role" "papel"; then
  CATEGORY="access-gcp"
  SPEC="jira-analysis"
  AGENT="analysis"
  PRIORITY="P2"

elif contains_any "$NORM" "pipeline" "sonar" "build" "compilacao" "ci/cd" "cicd" "deploy pipeline"; then
  CATEGORY="ci-cd"
  SPEC="jira-analysis"
  AGENT="analysis"
  PRIORITY="P2"

elif contains_any "$NORM" "observability" "observabilidade" "datadog" "telemetry" "telemetria" "logs" "log" "metrics" "metricas" "tracing" "rastreio"; then
  CATEGORY="observability"
  SPEC="observability"
  AGENT="execution"
  PRIORITY="P2"

elif contains_any "$NORM" "release" "deploy" "deployment" "promocao" "promotion" "go-live" "rollback" "gate"; then
  CATEGORY="release"
  SPEC="release-management"
  AGENT="release"
  PRIORITY="P2"
fi

echo "========================================"
echo "AI TASK PLAN"
echo "========================================"

echo "Task:"
echo "  $TASK"
echo ""

echo "Classification:"
echo "  CATEGORY: $CATEGORY"
echo "  PRIORITY: $PRIORITY"
echo ""

echo "Suggested Spec:"
echo "  $SPEC"
echo ""

echo "Responsible Agent:"
echo "  $AGENT"
echo ""

echo "Suggested Plan:"
echo "----------------------------------------"

case "$CATEGORY" in

  observability)
    echo "1. Use platform-observability-core"
    echo "2. Apply template to service"
    echo "3. Validate Dockerfile and entrypoint"
    echo "4. Prepare PR"
    ;;

  ci-cd)
    echo "1. Analyze pipeline failure"
    echo "2. Check credentials and tokens"
    echo "3. Validate config (Sonar, build)"
    echo "4. Propose fix"
    ;;

  access-gcp)
    echo "1. Identify correct project"
    echo "2. Check IAM"
    echo "3. Apply least privilege role"
    echo "4. Validate access"
    ;;

  release)
    echo "1. Prepare release notes"
    echo "2. Validate changes"
    echo "3. Request approval"
    echo "4. Follow promotion gates"
    ;;

  *)
    echo "1. Analyze task"
    echo "2. Define scope"
    echo "3. Suggest solution"
    ;;
esac

echo ""
echo "Approval Required: YES"
echo "Next Step: Review plan before execution"
