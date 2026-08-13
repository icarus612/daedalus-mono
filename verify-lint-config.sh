#!/usr/bin/env bash
# verify-lint-config.sh
#
# Contract test for Packet C — 1.3: Root tool & language-version config.
#
# Verifies, purely from the outside, that the root tool-config files behave as specified:
#   ruff.toml, .editorconfig, .python-version, .nvmrc, eslint.config.js, .prettierrc,
#   and package.json's engines.node + eslint/@eslint/js/prettier devDependencies.
#
# This script is blind to how those files are implemented — it only exercises the
# documented, externally-observable behavior (CLI exit codes / reported findings against
# disposable fixtures). It does not read or depend on any file's literal content beyond
# what the contract specifies.
#
# Usage: ./verify-lint-config.sh   (run from anywhere; resolves repo root from its own path)

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/verify-lint-config.XXXXXX")"
# ESLint v9+ flat config's --config resolution ignores any file outside the config file's
# base path ("File ignored because outside of base path") — a fixture under system $TMPDIR
# would silently lint nothing, making every assertion against it a false pass rather than
# real signal. So JS/ESLint fixtures live inside the repo tree instead, in a throwaway
# subdirectory next to this script, removed by the same cleanup trap. Only the ESLint
# fixtures need this; ruff and prettier have no such base-path restriction, so their
# fixtures stay in the external $SCRATCH tmpdir.
ESLINT_SCRATCH="$(mktemp -d "$REPO_ROOT/.verify-lint-config-eslint-fixtures.XXXXXX")"
trap 'rm -rf "$SCRATCH" "$ESLINT_SCRATCH"' EXIT

FAILURES=0

fail() {
  echo "FAIL: $1" >&2
  FAILURES=$((FAILURES + 1))
}

pass() {
  echo "PASS: $1"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "required command '$1' is not on PATH — cannot run this check"
    return 1
  fi
  return 0
}

echo "== Packet C (1.3) root tool & language-version config =="
echo "repo root: $REPO_ROOT"
echo "scratch:   $SCRATCH"
echo

# ---------------------------------------------------------------------------
# 0. All six files exist at root
# ---------------------------------------------------------------------------

for f in ruff.toml .editorconfig .python-version .nvmrc eslint.config.js .prettierrc; do
  if [[ -f "$REPO_ROOT/$f" ]]; then
    pass "root $f exists"
  else
    fail "root $f is missing"
  fi
done

if [[ -f "$REPO_ROOT/package.json" ]]; then
  pass "root package.json exists"
else
  fail "root package.json is missing"
fi

# ---------------------------------------------------------------------------
# 1. .python-version and .nvmrc content markers
# ---------------------------------------------------------------------------

if [[ -f "$REPO_ROOT/.python-version" ]]; then
  content="$(tr -d '[:space:]' <"$REPO_ROOT/.python-version")"
  if [[ "$content" == "3.11" ]]; then
    pass ".python-version contains exactly 3.11"
  else
    fail ".python-version does not contain exactly '3.11' (got: '$content')"
  fi
fi

if [[ -f "$REPO_ROOT/.nvmrc" ]]; then
  content="$(tr -d '[:space:]' <"$REPO_ROOT/.nvmrc")"
  if [[ "$content" == "24" ]]; then
    pass ".nvmrc contains exactly 24"
  else
    fail ".nvmrc does not contain exactly '24' (got: '$content')"
  fi
fi

# ---------------------------------------------------------------------------
# 2. package.json: engines.node + devDependencies (via jq)
# ---------------------------------------------------------------------------

if require_cmd jq && [[ -f "$REPO_ROOT/package.json" ]]; then
  node_engine="$(jq -r '.engines.node // empty' "$REPO_ROOT/package.json" 2>/dev/null)"
  if [[ -n "$node_engine" ]]; then
    pass "package.json .engines.node is set ('$node_engine')"
  else
    fail "package.json .engines.node is missing or empty"
  fi

  has_devdeps="$(jq -r '(.devDependencies // {}) | (has("eslint") and has("@eslint/js") and has("prettier"))' "$REPO_ROOT/package.json" 2>/dev/null)"
  if [[ "$has_devdeps" == "true" ]]; then
    pass "package.json devDependencies has eslint, @eslint/js, and prettier"
  else
    fail "package.json devDependencies is missing one of: eslint, @eslint/js, prettier"
  fi
fi

# ---------------------------------------------------------------------------
# 3. ruff: check + format against root ruff.toml
# ---------------------------------------------------------------------------

RUFF_TOML="$REPO_ROOT/ruff.toml"

if require_cmd ruff && [[ -f "$RUFF_TOML" ]]; then
  PY_CLEAN="$SCRATCH/clean.py"
  cat >"$PY_CLEAN" <<'EOF'
"""Compliant fixture module."""


def add(a: int, b: int) -> int:
    return a + b
EOF

  PY_LINT_VIOLATION="$SCRATCH/bad_lint.py"
  cat >"$PY_LINT_VIOLATION" <<'EOF'
"""Fixture with an unused import (select-covered F rule)."""

import os


def add(a: int, b: int) -> int:
    return a + b
EOF

  PY_FORMAT_VIOLATION="$SCRATCH/bad_format.py"
  cat >"$PY_FORMAT_VIOLATION" <<'EOF'
def add(a,b):
    return a+b
EOF

  # ruff check: clean fixture passes
  if out="$(ruff check --config "$RUFF_TOML" "$PY_CLEAN" 2>&1)"; then
    pass "ruff check: clean Python fixture passes with exit 0"
  else
    fail "ruff check: clean Python fixture was rejected (config error or false positive): $out"
  fi

  # ruff check: violation fixture is reported, and rule selection (F) is honored
  out="$(ruff check --config "$RUFF_TOML" "$PY_LINT_VIOLATION" 2>&1)"
  rc=$?
  if [[ $rc -ne 0 ]] && grep -q "F401" <<<"$out"; then
    pass "ruff check: unused-import violation is reported as F401 (rule selection honored)"
  else
    fail "ruff check: unused-import fixture was not reported as F401 (exit=$rc): $out"
  fi

  # ruff format --check: clean fixture is already canonically formatted
  if out="$(ruff format --check --config "$RUFF_TOML" "$PY_CLEAN" 2>&1)"; then
    pass "ruff format --check: clean Python fixture passes with exit 0"
  else
    fail "ruff format --check: clean Python fixture was flagged as needing reformatting: $out"
  fi

  # ruff format --check: badly formatted fixture is flagged
  if out="$(ruff format --check --config "$RUFF_TOML" "$PY_FORMAT_VIOLATION" 2>&1)"; then
    fail "ruff format --check: badly formatted fixture was NOT flagged (expected non-zero exit)"
  else
    pass "ruff format --check: badly formatted fixture is correctly flagged"
  fi
fi

# ---------------------------------------------------------------------------
# 4. eslint: --config eslint.config.js against JS fixtures
# ---------------------------------------------------------------------------

ESLINT_CONFIG="$REPO_ROOT/eslint.config.js"

if require_cmd pnpm && [[ -f "$ESLINT_CONFIG" ]]; then
  JS_CLEAN="$ESLINT_SCRATCH/clean.mjs"
  cat >"$JS_CLEAN" <<'EOF'
export function add(a, b) {
  return a + b;
}
EOF

  JS_UNUSED_VIOLATION="$ESLINT_SCRATCH/bad_unused.mjs"
  cat >"$JS_UNUSED_VIOLATION" <<'EOF'
export function add(a, b) {
  const unusedVar = 42;
  return a + b;
}
EOF

  JS_CONSOLE="$ESLINT_SCRATCH/console_info.mjs"
  cat >"$JS_CONSOLE" <<'EOF'
export function logInfo(message) {
  console.info(message);
}
EOF

  # clean fixture: no configuration error, no errors reported
  json="$(cd "$REPO_ROOT" && pnpm exec eslint --config "$ESLINT_CONFIG" --format json "$JS_CLEAN" 2>&1)"
  if err_count="$(jq -r '.[0].errorCount // "null"' <<<"$json" 2>/dev/null)" && [[ "$err_count" != "null" ]]; then
    if [[ "$err_count" == "0" ]]; then
      pass "eslint: clean JS fixture reports no errors (no configuration error)"
    else
      fail "eslint: clean JS fixture unexpectedly reported $err_count error(s): $json"
    fi
  else
    fail "eslint: could not parse JSON output for clean JS fixture (possible configuration error): $json"
  fi

  # unused-var fixture: no-unused-vars is reported
  json="$(cd "$REPO_ROOT" && pnpm exec eslint --config "$ESLINT_CONFIG" --format json "$JS_UNUSED_VIOLATION" 2>&1)"
  if rule_ids="$(jq -r '.[0].messages[]?.ruleId // empty' <<<"$json" 2>/dev/null)"; then
    if grep -q "no-unused-vars" <<<"$rule_ids"; then
      pass "eslint: unused-var fixture is reported via no-unused-vars"
    else
      fail "eslint: unused-var fixture did not report no-unused-vars. messages: $rule_ids raw: $json"
    fi
  else
    fail "eslint: could not parse JSON output for unused-var fixture: $json"
  fi

  # console.info fixture: neither no-console nor no-undef must be flagged (no-undef would
  # fire if console isn't declared as a known global — the whole point of merging
  # globals.node/globals.browser into languageOptions.globals)
  json="$(cd "$REPO_ROOT" && pnpm exec eslint --config "$ESLINT_CONFIG" --format json "$JS_CONSOLE" 2>&1)"
  if rule_ids="$(jq -r '.[0].messages[]?.ruleId // empty' <<<"$json" 2>/dev/null)"; then
    if grep -q "no-console" <<<"$rule_ids"; then
      fail "eslint: console.info(...) fixture was flagged by no-console (should be absent from rule set): $rule_ids"
    elif grep -q "no-undef" <<<"$rule_ids"; then
      fail "eslint: console.info(...) fixture was flagged by no-undef (console must be a declared global): $rule_ids"
    else
      pass "eslint: console.info(...) fixture is NOT flagged by no-console or no-undef"
    fi
  else
    fail "eslint: could not parse JSON output for console.info fixture: $json"
  fi
fi

# ---------------------------------------------------------------------------
# 5. prettier: --check --config .prettierrc against JS fixtures
# ---------------------------------------------------------------------------

PRETTIERRC="$REPO_ROOT/.prettierrc"

if require_cmd pnpm && [[ -f "$PRETTIERRC" ]]; then
  PRETTIER_CLEAN="$SCRATCH/clean_fmt.js"
  cat >"$PRETTIER_CLEAN" <<'EOF'
function add(a, b) {
  return a + b;
}
EOF

  # Object literal that fits on one line only if the line is allowed to exceed 88 chars;
  # prettier reflows object expressions that don't fit within printWidth onto multiple lines.
  PRETTIER_WIDTH_VIOLATION="$SCRATCH/bad_width.js"
  cat >"$PRETTIER_WIDTH_VIOLATION" <<'EOF'
const config = { alpha: 1, beta: 2, gamma: 3, delta: 4, epsilon: 5, zeta: 6, eta: 7, theta: 8 };
EOF

  PRETTIER_QUOTE_VIOLATION="$SCRATCH/bad_quote.js"
  cat >"$PRETTIER_QUOTE_VIOLATION" <<'EOF'
const greeting = 'hello';
EOF

  if (cd "$REPO_ROOT" && pnpm exec prettier --check --config "$PRETTIERRC" "$PRETTIER_CLEAN") >/dev/null 2>&1; then
    pass "prettier --check: clean JS fixture passes with exit 0"
  else
    fail "prettier --check: clean JS fixture was flagged as needing reformatting"
  fi

  if (cd "$REPO_ROOT" && pnpm exec prettier --check --config "$PRETTIERRC" "$PRETTIER_WIDTH_VIOLATION") >/dev/null 2>&1; then
    fail "prettier --check: fixture exceeding printWidth=88 was NOT flagged (expected non-zero exit)"
  else
    pass "prettier --check: fixture exceeding printWidth=88 is correctly flagged"
  fi

  if (cd "$REPO_ROOT" && pnpm exec prettier --check --config "$PRETTIERRC" "$PRETTIER_QUOTE_VIOLATION") >/dev/null 2>&1; then
    fail "prettier --check: single-quote fixture was NOT flagged (expected non-zero exit; singleQuote is false)"
  else
    pass "prettier --check: single-quote fixture is correctly flagged (singleQuote: false honored)"
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo
if [[ $FAILURES -eq 0 ]]; then
  echo "PASS: all Packet C (1.3) root tool & language-version config checks passed"
  exit 0
else
  echo "FAIL: $FAILURES check(s) failed — see FAIL lines above"
  exit 1
fi
