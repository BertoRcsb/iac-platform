#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MAKE_DIR="${REPO_ROOT}/agents-local"

usage() {
  cat <<USAGE
Usage: $(basename "$0") <command> [environment]

Commands:
  init <env>      Run terraform init
  validate <env>  Run terraform validate
  plan <env>      Run terraform plan
  apply <env>     Run terraform apply
  destroy <env>   Run terraform destroy
  verify <env>    Run fmt + init + validate + lint + sec + plan

Defaults:
  environment = lab

Examples:
  $(basename "$0") init
  $(basename "$0") validate lab
  $(basename "$0") plan gcp-client-whitelist
USAGE
}

if ! command -v make >/dev/null 2>&1; then
  echo "make is required but was not found." >&2
  exit 1
fi

if [ "$#" -lt 1 ]; then
  usage
  exit 1
fi

command="$1"
env_name="${2:-lab}"
env_dir="${REPO_ROOT}/environments/${env_name}"

if [ ! -d "${env_dir}" ]; then
  echo "Environment directory not found: ${env_dir}" >&2
  exit 1
fi

case "${command}" in
  init|validate|plan|apply|destroy|verify)
    make -C "${MAKE_DIR}" "${command}" ENV="${env_name}"
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    echo "Unknown command: ${command}" >&2
    usage
    exit 1
    ;;
esac
