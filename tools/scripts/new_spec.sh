#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TEMPLATE="${REPO_ROOT}/agents/shared/templates/spec-template.md"
DEST_DIR="${REPO_ROOT}/docs/specs"

if [ "$#" -lt 1 ]; then
  echo "Usage: $(basename "$0") <name>" >&2
  exit 1
fi

slugify() {
  echo "$1" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//'
}

name="$*"
slug="$(slugify "${name}")"

if [ -z "${slug}" ]; then
  echo "Invalid name after slugify. Provide a name with letters or numbers." >&2
  exit 1
fi

mkdir -p "${DEST_DIR}"
out_file="${DEST_DIR}/${slug}.md"

if [ -e "${out_file}" ]; then
  echo "File already exists: ${out_file}" >&2
  exit 1
fi

cp "${TEMPLATE}" "${out_file}"
echo "Created ${out_file}"
