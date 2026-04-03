#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Uso:"
  echo "  ./scripts/plan-task.sh \"descrição da tarefa\""
  exit 1
fi

TASK="$*"
LOWER="$(echo "$TASK" | tr '[:upper:]' '[:lower:]')"

CATEGORY="general"
SPEC="none"
AGENT="analysis"
PRIORITY="P3"

# Classificação
if [[ "$LOWER" == *"firestore"* ]] || [[ "$LOWER" == *"acesso"* ]] || [[ "$LOWER" == *"iam"* ]]; then
  CATEGORY="access-gcp"
  SPEC="jira-analysis"
  AGENT="analysis"
  PRIORITY="P2"

elif [[ "$LOWER" == *"pipeline"* ]] || [[ "$LOWER" == *"sonar"* ]] || [[ "$LOWER" == *"build"* ]]; then
  CATEGORY="ci-cd"
  SPEC="jira-analysis"
  AGENT="analysis"
  PRIORITY="P2"

elif [[ "$LOWER" == *"observability"* ]] || [[ "$LOWER" == *"datadog"* ]]; then
  CATEGORY="observability"
  SPEC="observability"
  AGENT="execution"
  PRIORITY="P2"

elif [[ "$LOWER" == *"release"* ]] || [[ "$LOWER" == *"deploy"* ]]; then
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
