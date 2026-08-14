#!/usr/bin/env bash
# verify-workspace-membership.sh
#
# Read-only diagnostic: proves every package.json found under the given directories
# (minus pnpm-workspace.yaml's own `!`-negated legacy exclusions) is actually visible to
# turbo's task graph. Guards against the C1 pattern from plan lint-import-audit-08-12-26 —
# a workspace glob in pnpm-workspace.yaml too shallow to see a real package directory.
#
# Usage: verify-workspace-membership.sh <dir> [<dir> ...]
#
# Exit 0: every discovered package.json's declared name is present in turbo's package
#         graph. Prints a one-line "workspace membership OK: ..." summary to stdout.
# Exit 1: at least one discovered package.json's declared name is missing from turbo's
#         package graph. Prints an explanation plus the missing names to stderr.
#
# No side effects — never writes, installs, or mutates anything.

set -uo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: $(basename "$0") <dir> [<dir> ...]" >&2
  exit 1
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"
if [[ -z "$REPO_ROOT" ]]; then
  echo "verify-workspace-membership.sh: not inside a git repository" >&2
  exit 1
fi
cd "$REPO_ROOT" || exit 1

WORKSPACE_FILE="pnpm-workspace.yaml"
if [[ ! -f "$WORKSPACE_FILE" ]]; then
  echo "verify-workspace-membership.sh: $WORKSPACE_FILE not found at repo root ($REPO_ROOT)" >&2
  exit 1
fi

# Step 2: dynamically read the `!`-negated glob lines (the D7 legacy exclusions) — never
# hardcode the excluded package names, so this keeps working if the exclusion list changes.
mapfile -t EXCLUDED_DIRS < <(
  grep -E "^[[:space:]]*-[[:space:]]*['\"]?!" "$WORKSPACE_FILE" |
    sed -E "s/^[[:space:]]*-[[:space:]]*['\"]?!//; s/['\"][[:space:]]*(#.*)?\$//"
)

is_excluded() {
  local candidate_dir="$1"
  local excluded
  for excluded in "${EXCLUDED_DIRS[@]}"; do
    [[ -z "$excluded" ]] && continue
    if [[ "$candidate_dir" == "$excluded" || "$candidate_dir" == "$excluded"/* ]]; then
      return 0
    fi
  done
  return 1
}

# Step 3: collect the expected set — every package.json's declared name, under each <dir>
# argument, skipping excluded directories.
EXPECTED=()
for dir in "$@"; do
  if [[ ! -d "$dir" ]]; then
    echo "verify-workspace-membership.sh: directory not found: $dir" >&2
    exit 1
  fi
  while IFS= read -r manifest; do
    [[ -z "$manifest" ]] && continue
    pkg_dir="$(dirname "$manifest")"
    if is_excluded "$pkg_dir"; then
      continue
    fi
    pkg_name="$(jq -r '.name' "$manifest")"
    if [[ -n "$pkg_name" && "$pkg_name" != "null" ]]; then
      EXPECTED+=("$pkg_name")
    fi
  done < <(find "$dir" -name package.json -not -path '*/node_modules/*')
done

# Step 4: run the single turbo dry-run and collect its package graph into the actual set.
TURBO_DRY_JSON="$(pnpm exec turbo run build lint test --dry=json 2>/dev/null)"
if [[ -z "$TURBO_DRY_JSON" ]]; then
  echo "verify-workspace-membership.sh: 'pnpm exec turbo run build lint test --dry=json' produced no output" >&2
  exit 1
fi

mapfile -t ACTUAL < <(echo "$TURBO_DRY_JSON" | jq -r '.packages[]?')

# Step 5: compute expected - actual.
declare -A ACTUAL_SET=()
for pkg in "${ACTUAL[@]}"; do
  ACTUAL_SET["$pkg"]=1
done

MISSING=()
declare -A SEEN_EXPECTED=()
for pkg in "${EXPECTED[@]}"; do
  [[ -n "${SEEN_EXPECTED[$pkg]:-}" ]] && continue
  SEEN_EXPECTED["$pkg"]=1
  if [[ -z "${ACTUAL_SET[$pkg]:-}" ]]; then
    MISSING+=("$pkg")
  fi
done

if [[ ${#MISSING[@]} -eq 0 ]]; then
  echo "workspace membership OK: ${#EXPECTED[@]} package(s) visible to turbo under $*"
  exit 0
fi

{
  echo "workspace membership FAILED — this is the C1 pattern from lint-import-audit-08-12-26:"
  echo "a workspace glob in $WORKSPACE_FILE too shallow to see the package directory below."
  echo "The following package(s) have a package.json under $* but are not visible to"
  echo "'pnpm exec turbo run build lint test --dry=json':"
  for pkg in "${MISSING[@]}"; do
    echo "  - $pkg"
  done
} >&2

exit 1
