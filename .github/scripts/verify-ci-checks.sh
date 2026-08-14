#!/usr/bin/env bash
# verify-ci-checks.sh
#
# Contract test for Lane 5, Packet 1 — 5.1: workspace-membership guard.
#
# Verifies, purely from the outside, that .github/scripts/verify-workspace-membership.sh
# behaves per its documented CLI contract:
#
#   verify-workspace-membership.sh <dir> [<dir> ...]
#
#   - exits 0 and prints "workspace membership OK" (plus a package count) to stdout when
#     every package.json found under the given dir(s) (excluding pnpm-workspace.yaml's
#     dynamically-read `!`-negated globs) names a package that appears in
#     `pnpm exec turbo run build lint test --dry=json`'s package graph.
#   - exits 1 and lists the missing package name(s) to stderr otherwise.
#   - is read-only: no side effects.
#
# This script is blind to verify-workspace-membership.sh's own implementation and to the
# three workflow YAML files that call it — it only exercises the documented, externally
# observable CLI contract (exit codes / stdout / stderr) against the real repo tree and
# against a disposable, isolated fixture. It does not read or depend on any file's literal
# content beyond what the contract specifies.
#
# Usage: ./verify-ci-checks.sh   (run from anywhere; resolves repo root from its own path)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_SCRIPT="$REPO_ROOT/.github/scripts/verify-workspace-membership.sh"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/verify-ci-checks.XXXXXX")"
trap 'rm -rf "$SCRATCH"' EXIT

FAILURES=0

fail() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

pass() {
  echo "PASS: $1"
}

echo "== Lane 5 Packet 1 (5.1) verify-workspace-membership.sh contract =="
echo "repo root: $REPO_ROOT"
echo "target:    $TARGET_SCRIPT"
echo "scratch:   $SCRATCH"
echo

# ---------------------------------------------------------------------------
# 0. Script must exist and be executable/runnable before anything else
# ---------------------------------------------------------------------------

if [[ ! -f "$TARGET_SCRIPT" ]]; then
  fail "$TARGET_SCRIPT does not exist — cannot run any contract checks"
  echo
  echo "FAIL: $FAILURES check(s) failed — see FAIL lines above"
  exit 1
fi

if [[ ! -x "$TARGET_SCRIPT" ]]; then
  # Not fatal on its own (CI chmod's it before invoking) — but note it, then
  # invoke via `bash "$TARGET_SCRIPT"` below so the rest of the checks can still run.
  echo "NOTE: $TARGET_SCRIPT is not marked executable; invoking via 'bash' instead of directly."
fi

run_target() {
  if [[ -x "$TARGET_SCRIPT" ]]; then
    "$TARGET_SCRIPT" "$@"
  else
    bash "$TARGET_SCRIPT" "$@"
  fi
}

# ---------------------------------------------------------------------------
# 1. Positive, real-repo case: JavaScript workspace dirs
# ---------------------------------------------------------------------------

out="$(cd "$REPO_ROOT" && run_target libs/javascript apps/next 2>&1)"
rc=$?
if [[ $rc -eq 0 ]]; then
  pass "verify-workspace-membership.sh libs/javascript apps/next exits 0"
else
  fail "verify-workspace-membership.sh libs/javascript apps/next exited $rc (expected 0). output: $out"
fi
if grep -qi "OK" <<<"$out"; then
  pass "verify-workspace-membership.sh libs/javascript apps/next reports OK"
else
  fail "verify-workspace-membership.sh libs/javascript apps/next did not report OK. output: $out"
fi

# ---------------------------------------------------------------------------
# 2. Positive, real-repo case: Python workspace dirs
# ---------------------------------------------------------------------------

out="$(cd "$REPO_ROOT" && run_target apps/flask apps/microservices libs/python 2>&1)"
rc=$?
if [[ $rc -eq 0 ]]; then
  pass "verify-workspace-membership.sh apps/flask apps/microservices libs/python exits 0"
else
  fail "verify-workspace-membership.sh apps/flask apps/microservices libs/python exited $rc (expected 0). output: $out"
fi
if grep -qi "OK" <<<"$out"; then
  pass "verify-workspace-membership.sh apps/flask apps/microservices libs/python reports OK"
else
  fail "verify-workspace-membership.sh apps/flask apps/microservices libs/python did not report OK. output: $out"
fi

# ---------------------------------------------------------------------------
# 3. Negative, isolated-fixture case: a package.json whose name is absent from
#    turbo's graph, living entirely outside the real workspace dirs.
# ---------------------------------------------------------------------------

FAKE_NAME="zzz-contract-tester-fixture-not-in-workspace"
FIXTURE_DIR="$SCRATCH/fake-package"
mkdir -p "$FIXTURE_DIR"
cat >"$FIXTURE_DIR/package.json" <<EOF
{
  "name": "$FAKE_NAME",
  "version": "0.0.0-fixture",
  "private": true
}
EOF

# Capture stdout and stderr separately so we can assert stderr specifically.
stdout_file="$SCRATCH/negative.stdout"
stderr_file="$SCRATCH/negative.stderr"
( cd "$REPO_ROOT" && run_target "$FIXTURE_DIR" >"$stdout_file" 2>"$stderr_file" )
rc=$?

if [[ $rc -eq 1 ]]; then
  pass "verify-workspace-membership.sh on isolated fake-name fixture exits 1"
else
  fail "verify-workspace-membership.sh on isolated fake-name fixture exited $rc (expected 1). stdout: $(cat "$stdout_file") stderr: $(cat "$stderr_file")"
fi

if grep -qF "$FAKE_NAME" "$stderr_file"; then
  pass "verify-workspace-membership.sh reports the missing fake package name on stderr"
else
  fail "verify-workspace-membership.sh did not report '$FAKE_NAME' on stderr. stderr: $(cat "$stderr_file")"
fi

# Sanity: the fixture must never mutate the real repo tree.
if [[ -z "$(cd "$REPO_ROOT" && git status --porcelain 2>/dev/null)" ]]; then
  pass "repo working tree is clean after negative-fixture run (no side effects)"
else
  fail "repo working tree is NOT clean after negative-fixture run — script may have side effects"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
if [[ $FAILURES -eq 0 ]]; then
  echo "PASS: all Lane 5 Packet 1 (5.1) verify-workspace-membership.sh contract checks passed"
  exit 0
else
  echo "FAIL: $FAILURES check(s) failed — see FAIL lines above"
  exit 1
fi
