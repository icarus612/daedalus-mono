#!/usr/bin/env bash
# smart-lint.sh - Intelligent project-aware code quality checks for Claude Code
#
# SYNOPSIS
#   smart-lint.sh [options]
#
# DESCRIPTION
#   Automatically detects project type and runs ALL quality checks.
#   Every issue found is blocking - code must be 100% clean to proceed.
#
# OPTIONS
#   --debug       Enable debug output
#   --fast        Skip slow checks (import cycles, security scans)
#
# EXIT CODES
#   0 - Success (all checks passed - everything is ✅ GREEN)
#   1 - General error (missing dependencies, etc.)
#   2 - ANY issues found - ALL must be fixed
#
# CONFIGURATION
#   Project-specific overrides can be placed in .claude-hooks-config.sh
#   See inline documentation for all available options.

# Don't use set -e - we need to control exit codes carefully
set +e

# ============================================================================
# COLOR DEFINITIONS AND UTILITIES
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Debug mode
CLAUDE_HOOKS_DEBUG="${CLAUDE_HOOKS_DEBUG:-0}"

# Logging functions
log_debug() {
    [[ "$CLAUDE_HOOKS_DEBUG" == "1" ]] && echo -e "${CYAN}[DEBUG]${NC} $*" >&2
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*" >&2
}

# Performance timing
time_start() {
    if [[ "$CLAUDE_HOOKS_DEBUG" == "1" ]]; then
        echo $(($(date +%s%N)/1000000))
    fi
}

time_end() {
    if [[ "$CLAUDE_HOOKS_DEBUG" == "1" ]]; then
        local start=$1
        local end=$(($(date +%s%N)/1000000))
        local duration=$((end - start))
        log_debug "Execution time: ${duration}ms"
    fi
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# find_pruned <maxdepth|""> <find-expr...>
# find with build-artifact/dependency dirs pruned. These never contain
# first-party code, so neither detection nor lint discovery should look
# inside them. Repos can extend the list via CLAUDE_HOOKS_PRUNE_EXTRA
# (space-separated dir names) in .claude-hooks-config.sh.
find_pruned() {
    local depth="$1"
    shift

    local names=(node_modules .git vendor target .godot .venv venv env __pycache__ dist build out result .next .turbo .workflows)
    # shellcheck disable=SC2206 # intentional word-splitting
    [[ -n "${CLAUDE_HOOKS_PRUNE_EXTRA:-}" ]] && names+=(${CLAUDE_HOOKS_PRUNE_EXTRA})

    local prune=() n
    for n in "${names[@]}"; do
        prune+=(-name "$n" -o)
    done
    prune=("${prune[@]:0:$(( ${#prune[@]} - 1 ))}")  # drop trailing -o

    local depth_args=()
    [[ -n "$depth" ]] && depth_args=(-maxdepth "$depth")

    find . "${depth_args[@]}" \( "${prune[@]}" \) -prune -o \( "$@" \) -print 2>/dev/null
}

# ============================================================================
# PROJECT DETECTION
# ============================================================================

detect_project_type() {
    local project_type="unknown"
    local types=()

    # Detection depth: 6 levels normally. A README.md below the root marks
    # nested sub-projects (monorepo convention) — lift the depth cap so
    # arbitrarily deep projects are still detected.
    local depth="6"
    if [[ -n "$(find_pruned "" -mindepth 2 -name README.md -type f | head -n 1)" ]]; then
        depth=""
        log_debug "Nested README.md found — monorepo mode, detection depth uncapped"
    fi

    # Go project
    if [[ -n "$(find_pruned "$depth" \( -name go.mod -o -name go.sum -o -name '*.go' \) -type f | head -n 1)" ]]; then
        types+=("go")
    fi

    # Python project
    if [[ -n "$(find_pruned "$depth" \( -name pyproject.toml -o -name setup.py -o -name requirements.txt -o -name '*.py' \) -type f | head -n 1)" ]]; then
        types+=("python")
    fi

    # JavaScript/TypeScript project
    if [[ -n "$(find_pruned "$depth" \( -name package.json -o -name tsconfig.json -o -name '*.js' -o -name '*.ts' -o -name '*.jsx' -o -name '*.tsx' \) -type f | head -n 1)" ]]; then
        types+=("javascript")
    fi

    # Rust project
    if [[ -n "$(find_pruned "$depth" \( -name Cargo.toml -o -name '*.rs' \) -type f | head -n 1)" ]]; then
        types+=("rust")
    fi

    # Nix project
    if [[ -n "$(find_pruned "$depth" \( -name flake.nix -o -name default.nix -o -name shell.nix \) -type f | head -n 1)" ]]; then
        types+=("nix")
    fi
    
    # Return primary type or "mixed" if multiple
    if [[ ${#types[@]} -eq 1 ]]; then
        project_type="${types[0]}"
    elif [[ ${#types[@]} -gt 1 ]]; then
        project_type="mixed:$(IFS=,; echo "${types[*]}")"
    fi
    
    log_debug "Detected project type: $project_type"
    echo "$project_type"
}

# Get list of modified files (if available from git)
get_modified_files() {
    if [[ -d .git ]] && command_exists git; then
        # Get files modified in the last commit or currently staged/modified
        git diff --name-only HEAD 2>/dev/null || true
        git diff --cached --name-only 2>/dev/null || true
    fi
}

# Check if we should skip a file
should_skip_file() {
    local file="$1"
    
    # Check .claude-hooks-ignore if it exists
    if [[ -f ".claude-hooks-ignore" ]]; then
        while IFS= read -r pattern; do
            # Skip comments and empty lines
            [[ -z "$pattern" || "$pattern" =~ ^[[:space:]]*# ]] && continue
            
            # Check if file matches pattern
            if [[ "$file" == $pattern ]]; then
                log_debug "Skipping $file due to .claude-hooks-ignore pattern: $pattern"
                return 0
            fi
        done < ".claude-hooks-ignore"
    fi
    
    # Check for inline skip comments
    if [[ -f "$file" ]] && head -n 5 "$file" 2>/dev/null | grep -q "claude-hooks-disable"; then
        log_debug "Skipping $file due to inline claude-hooks-disable comment"
        return 0
    fi
    
    return 1
}

# ============================================================================
# HOOK-MODE SCOPING (TARGET_FILE)
# ============================================================================
#
# Everything below exists to answer one question — given the single file that
# triggered this run, should it be linted at all, and if so by which one
# linter? Hook mode never runs detect_project_type(); these helpers replace
# it with a direct, per-file dispatch.

# target_lintable_ext <file> — true if the extension is one this hook knows
# how to lint. Anything else (markdown, JSON, a lockfile, ...) exits clean
# before any linter runs.
target_lintable_ext() {
    case "${1##*.}" in
        py|go|js|jsx|ts|tsx|rs|nix) return 0 ;;
        *) return 1 ;;
    esac
}

# find_nearest_manifest <file> <manifest-name> — walk up from the file's
# directory looking for <manifest-name> (go.mod, Cargo.toml, ...), printing
# the first directory that has one. Empty output + non-zero exit means none
# was found above the file. Shared by the Go and Rust scoped linters so a
# hook-mode run touches only the module/crate that owns the file, never
# every module/crate in the repo.
find_nearest_manifest() {
    local start_dir manifest_name dir
    start_dir=$(dirname "$1")
    manifest_name="$2"
    dir=$(cd "$start_dir" 2>/dev/null && pwd) || return 1
    while [[ "$dir" != "/" ]]; do
        [[ -f "$dir/$manifest_name" ]] && { echo "$dir"; return 0; }
        dir=$(dirname "$dir")
    done
    return 1
}

# should_skip_target <file> <repo-root> — the hook-mode early clean-exit
# gate. True (skip) when the file is gone, lives outside this repo, is
# ignored, or has no lintable extension. This is the fix for the single
# largest source of this script's old cost: a write to a markdown file, a
# progress log, or a path outside the repo used to trigger a full repo-wide
# sweep; now it prints one line and the caller exits 0 immediately.
should_skip_target() {
    local file="$1"
    local repo_root="$2"

    if [[ ! -e "$file" ]]; then
        log_info "Skip (does not exist): $file"
        return 0
    fi

    local abs_file
    abs_file=$(cd "$(dirname "$file")" 2>/dev/null && printf '%s/%s' "$PWD" "$(basename "$file")") || abs_file=""
    if [[ -z "$abs_file" || "$abs_file" != "$repo_root"/* ]]; then
        log_info "Skip (outside repo): $file"
        return 0
    fi

    if should_skip_file "$file"; then
        log_info "Skip (ignored): $file"
        return 0
    fi

    if ! target_lintable_ext "$file"; then
        log_info "Skip (no lintable extension): $file"
        return 0
    fi

    return 1
}

# ============================================================================
# ERROR TRACKING
# ============================================================================

declare -a CLAUDE_HOOKS_SUMMARY=()
declare -i CLAUDE_HOOKS_ERROR_COUNT=0

add_error() {
    local message="$1"
    CLAUDE_HOOKS_ERROR_COUNT+=1
    CLAUDE_HOOKS_SUMMARY+=("${RED}❌${NC} $message")
}

print_summary() {
    if [[ $CLAUDE_HOOKS_ERROR_COUNT -gt 0 ]]; then
        # Only show failures when there are errors
        echo -e "\n${BLUE}═══ Summary ═══${NC}" >&2
        for item in "${CLAUDE_HOOKS_SUMMARY[@]}"; do
            echo -e "$item" >&2
        done
        
        echo -e "\n${RED}Found $CLAUDE_HOOKS_ERROR_COUNT issue(s) that MUST be fixed!${NC}" >&2
        echo -e "${RED}════════════════════════════════════════════${NC}" >&2
        echo -e "${RED}❌ ALL ISSUES ARE BLOCKING ❌${NC}" >&2
        echo -e "${RED}════════════════════════════════════════════${NC}" >&2
        echo -e "${RED}Fix EVERYTHING above until all checks are ✅ GREEN${NC}" >&2
    fi
}

# ============================================================================
# CONFIGURATION LOADING
# ============================================================================

load_config() {
    # Default configuration
    export CLAUDE_HOOKS_ENABLED="${CLAUDE_HOOKS_ENABLED:-true}"
    export CLAUDE_HOOKS_FAIL_FAST="${CLAUDE_HOOKS_FAIL_FAST:-false}"
    export CLAUDE_HOOKS_SHOW_TIMING="${CLAUDE_HOOKS_SHOW_TIMING:-false}"
    
    # Language enables
    export CLAUDE_HOOKS_GO_ENABLED="${CLAUDE_HOOKS_GO_ENABLED:-true}"
    export CLAUDE_HOOKS_PYTHON_ENABLED="${CLAUDE_HOOKS_PYTHON_ENABLED:-true}"
    export CLAUDE_HOOKS_JS_ENABLED="${CLAUDE_HOOKS_JS_ENABLED:-true}"
    export CLAUDE_HOOKS_RUST_ENABLED="${CLAUDE_HOOKS_RUST_ENABLED:-true}"
    export CLAUDE_HOOKS_NIX_ENABLED="${CLAUDE_HOOKS_NIX_ENABLED:-true}"
    
    # Project-specific overrides
    if [[ -f ".claude-hooks-config.sh" ]]; then
        source ".claude-hooks-config.sh" || {
            log_error "Failed to load .claude-hooks-config.sh"
            exit 2
        }
    fi
    
    # Quick exit if hooks are disabled
    if [[ "$CLAUDE_HOOKS_ENABLED" != "true" ]]; then
        log_info "Claude hooks are disabled"
        exit 0
    fi
}

# ============================================================================
# GO LINTING
# ============================================================================

lint_go() {
    if [[ "${CLAUDE_HOOKS_GO_ENABLED:-true}" != "true" ]]; then
        log_debug "Go linting disabled"
        return 0
    fi
    
    log_info "Running Go formatting and linting..."
    
    # Check if Makefile exists with fmt and lint targets
    if [[ -f "Makefile" ]]; then
        local has_fmt=$(grep -E "^fmt:" Makefile 2>/dev/null || echo "")
        local has_lint=$(grep -E "^lint:" Makefile 2>/dev/null || echo "")
        
        if [[ -n "$has_fmt" && -n "$has_lint" ]]; then
            log_info "Using Makefile targets"
            
            local fmt_output
            if ! fmt_output=$(make fmt 2>&1); then
                add_error "Go formatting failed (make fmt)"
                echo "$fmt_output" >&2
            fi
            
            local lint_output
            if ! lint_output=$(make lint 2>&1); then
                add_error "Go linting failed (make lint)"
                echo "$lint_output" >&2
            fi
        else
            # Fallback to per-module linting
            lint_go_modules
        fi
    else
        # No Makefile, lint per-module
        lint_go_modules
    fi
}

# Monorepo-aware Go linting: discover every go.mod and lint each module from
# its own directory. A single-module repo (go.mod at the root) behaves exactly
# like the old root-level run.
lint_go_modules() {
    log_info "Using direct Go tools"

    local gomods
    gomods=$(find_pruned "" -name go.mod -type f)

    if [[ -z "$gomods" ]]; then
        # .go files exist but no module anywhere — vet/lint need a module.
        log_info "Go files but no go.mod found — skipping Go checks"
        return 0
    fi

    local mod dir
    while IFS= read -r mod; do
        dir=$(dirname "$mod")
        log_info "Go module: $dir"

        # Format check, scoped to the module
        local unformatted_files=$(cd "$dir" && gofmt -l . 2>/dev/null | grep -v vendor/ || true)

        if [[ -n "$unformatted_files" ]]; then
            local fmt_output
            if ! fmt_output=$(cd "$dir" && gofmt -w . 2>&1); then
                add_error "Go formatting failed ($dir)"
                echo "$fmt_output" >&2
            fi
        fi

        # Linting, from inside the module
        if command_exists golangci-lint; then
            local lint_output
            if ! lint_output=$(cd "$dir" && golangci-lint run --timeout=2m 2>&1); then
                add_error "golangci-lint found issues ($dir)"
                echo "$lint_output" >&2
            fi
        elif command_exists go; then
            local vet_output
            if ! vet_output=$(cd "$dir" && go vet ./... 2>&1); then
                add_error "go vet found issues ($dir)"
                echo "$vet_output" >&2
            fi
        else
            log_error "No Go linting tools available - install golangci-lint or go"
        fi
    done <<< "$gomods"
}

# Hook-mode Go: format just the triggering file, vet just the module that
# owns it. Never touches a module the edit didn't happen in.
lint_go_scoped() {
    local file="$1"

    if [[ "${CLAUDE_HOOKS_GO_ENABLED:-true}" != "true" ]]; then
        log_debug "Go linting disabled"
        return 0
    fi

    log_info "Running Go formatting and linting (scoped to $file)..."

    local unformatted
    unformatted=$(gofmt -l "$file" 2>/dev/null || true)
    if [[ -n "$unformatted" ]]; then
        local fmt_output
        if ! fmt_output=$(gofmt -w "$file" 2>&1); then
            add_error "Go formatting failed ($file)"
            echo "$fmt_output" >&2
        fi
    fi

    local mod_dir
    mod_dir=$(find_nearest_manifest "$file" "go.mod") || {
        log_info "No go.mod found above $file — skipping go vet"
        return 0
    }

    log_info "Go module: $mod_dir"
    if command_exists golangci-lint; then
        local lint_output
        if ! lint_output=$(cd "$mod_dir" && golangci-lint run --timeout=2m 2>&1); then
            add_error "golangci-lint found issues ($mod_dir)"
            echo "$lint_output" >&2
        fi
    elif command_exists go; then
        local vet_output
        if ! vet_output=$(cd "$mod_dir" && go vet ./... 2>&1); then
            add_error "go vet found issues ($mod_dir)"
            echo "$vet_output" >&2
        fi
    else
        log_error "No Go linting tools available - install golangci-lint or go"
    fi
}

# ============================================================================
# OTHER LANGUAGE LINTERS
# ============================================================================

lint_python() {
    if [[ "${CLAUDE_HOOKS_PYTHON_ENABLED:-true}" != "true" ]]; then
        log_debug "Python linting disabled"
        return 0
    fi

    log_info "Running Python linters..."

    # Common exclusions for Python linting
    local exclude_dirs=".venv,venv,.env,env,node_modules,.git,__pycache__,build,dist,.eggs,*.egg-info,.workflows"

    # Black formatting
    if command_exists black; then
        local black_output
        if ! black_output=$(black . --check --exclude "($exclude_dirs)" 2>&1); then
            # Apply formatting and capture any errors
            local format_output
            if ! format_output=$(black . --exclude "($exclude_dirs)" 2>&1); then
                add_error "Python formatting failed"
                echo "$format_output" >&2
            fi
        fi
    fi

    # Linting - always use flake8
    if command_exists flake8; then
        # Black formats to 88 cols; flake8 defaults to 79 and flags black's
        # output (plus E203, which black produces intentionally). When the
        # repo has no flake8 config of its own, run with black-compatible
        # settings so the two tools don't fight. A repo config always wins.
        local flake8_args=()
        if [[ ! -f ".flake8" ]] && ! grep -qs '^\[flake8\]' setup.cfg tox.ini; then
            flake8_args+=(--max-line-length=88 --extend-ignore=E203)
        fi

        local flake8_output
        if ! flake8_output=$(flake8 . --exclude="$exclude_dirs" "${flake8_args[@]}" 2>&1); then
            add_error "Flake8 found issues"
            echo "$flake8_output" >&2
        fi
    fi

    return 0
}

# Hook-mode Python: black + flake8 on the single triggering file only. No
# ruff step — the installed base this was upstreamed from does not run ruff
# in its PostToolUse path (only black + flake8), so there is nothing to
# scope here; ruff stays a separate, unpinned gate elsewhere (see plan R7).
lint_python_scoped() {
    local file="$1"

    if [[ "${CLAUDE_HOOKS_PYTHON_ENABLED:-true}" != "true" ]]; then
        log_debug "Python linting disabled"
        return 0
    fi

    log_info "Running Python linters (scoped to $file)..."

    if command_exists black; then
        local black_output
        if ! black_output=$(black --check "$file" 2>&1); then
            local format_output
            if ! format_output=$(black "$file" 2>&1); then
                add_error "Python formatting failed ($file)"
                echo "$format_output" >&2
            fi
        fi
    fi

    if command_exists flake8; then
        # Same black-compatible defaults the repo-wide path computes, only
        # applied when the repo has no flake8 config of its own.
        local flake8_args=()
        if [[ ! -f ".flake8" ]] && ! grep -qs '^\[flake8\]' setup.cfg tox.ini; then
            flake8_args+=(--max-line-length=88 --extend-ignore=E203)
        fi

        local flake8_output
        if ! flake8_output=$(flake8 "$file" "${flake8_args[@]}" 2>&1); then
            add_error "Flake8 found issues ($file)"
            echo "$flake8_output" >&2
        fi
    fi

    return 0
}

lint_javascript() {
    if [[ "${CLAUDE_HOOKS_JS_ENABLED:-true}" != "true" ]]; then
        log_debug "JavaScript linting disabled"
        return 0
    fi

    log_info "Running JavaScript/TypeScript linters..."

    # Detect package manager (prefer pnpm)
    local pkg_manager="pnpm"
    if ! command_exists pnpm; then
        if command_exists npm; then
            pkg_manager="npm"
        else
            log_error "No package manager found (pnpm or npm)"
            return 0
        fi
    fi

    local ran_any_js_check=false
    local repo_root="$PWD"

    # ESLint — a root package.json lint script owns the whole workspace
    # (turbo/pnpm -r orchestration); running members again would double-lint.
    # Without one, discover nested packages and run each one's own lint
    # script from its directory (monorepo-aware).
    local lint_dirs=()
    if [[ -f "package.json" ]] && grep -q '"lint"' package.json 2>/dev/null; then
        lint_dirs=(".")
    else
        local pkg
        while IFS= read -r pkg; do
            grep -q '"lint"' "$pkg" 2>/dev/null && lint_dirs+=("$(dirname "$pkg")")
        done < <(find_pruned "" -mindepth 2 -name package.json -type f)
    fi

    local dir
    for dir in "${lint_dirs[@]}"; do
        # Missing deps are an environment gap, not a lint failure — skip
        # loudly instead of phantom-blocking on "eslint: not found".
        if [[ ! -d "$dir/node_modules" && ! -d "node_modules" ]]; then
            log_info "Skipping lint in $dir (node_modules not installed)"
            continue
        fi
        ran_any_js_check=true
        local eslint_output
        if ! eslint_output=$(cd "$dir" && $pkg_manager run lint 2>&1); then
            add_error "ESLint found issues ($dir)"
            echo "$eslint_output" >&2
        fi
    done

    # Prettier — MUST use the project's own install when present. A global or
    # pnpx-fetched prettier resolves to a different version than the project's
    # pin and the two fight over formatting (each --write flips files back and
    # forth on every hook run). pnpx also downloads registry-latest on the fly.
    # A root prettier config owns the whole tree; otherwise discover nested
    # package configs and run prettier from each package dir (prettier
    # resolves config per-file, so scoped runs are safe).
    local prettier_dirs=()
    if [[ -f ".prettierrc" ]] || [[ -f "prettier.config.js" ]] || [[ -f ".prettierrc.json" ]]; then
        prettier_dirs=(".")
    else
        local cfg
        while IFS= read -r cfg; do
            prettier_dirs+=("$(dirname "$cfg")")
        done < <(find_pruned "" -mindepth 2 \( -name .prettierrc -o -name prettier.config.js -o -name .prettierrc.json \) -type f)
    fi

    for dir in "${prettier_dirs[@]}"; do
        local prettier_cmd=""
        if [[ -x "$dir/node_modules/.bin/prettier" ]]; then
            prettier_cmd="$repo_root/$dir/node_modules/.bin/prettier"
        elif [[ -x "$repo_root/node_modules/.bin/prettier" ]]; then
            prettier_cmd="$repo_root/node_modules/.bin/prettier"
        else
            # No project-local prettier: SKIP. Do NOT fall back to a global or
            # pnpx-fetched binary. Two reasons, both observed in practice:
            #
            #   1. pnpx downloads registry-latest, which drifts from the
            #      project's pin. Prettier does not treat formatting changes as
            #      semver-breaking, so 3.6.2 and 3.9.6 format the same union
            #      type differently and each rejects the other's output.
            #   2. The --write below targets the whole DIRECTORY, not one file.
            #      So a single disagreement rewrites every file in the tree —
            #      a fresh worktree (deps not yet installed) silently reformats
            #      files the edit never touched.
            #
            # Skipping is strictly safer: the project's own `lint` script still
            # catches formatting, just without a wrong-version rewrite first.
            log_info "No project-local prettier in ${dir} — skipping (refusing to format with an unpinned version)"
            continue
        fi

        # Scope to the edited file when the hook gave us one. `.` is only for
        # manual CLI runs — see TARGET_FILE at the bottom of this file.
        local prettier_target="."
        if [[ -n "${TARGET_FILE:-}" ]]; then
            local abs_target abs_dir
            abs_target=$(cd "$(dirname "$TARGET_FILE")" 2>/dev/null && printf '%s/%s' "$PWD" "$(basename "$TARGET_FILE")") || abs_target=""
            abs_dir=$(cd "$dir" 2>/dev/null && pwd) || abs_dir=""
            # Skip dirs the edited file doesn't live under, so a monorepo runs
            # prettier once, in the right workspace, instead of once per config.
            if [[ -z "$abs_target" || -z "$abs_dir" || "$abs_target" != "$abs_dir"/* ]]; then
                continue
            fi
            prettier_target="${abs_target#"$abs_dir"/}"
            # Prettier exits non-zero on a file it has no parser for (.env,
            # images, lockfiles); that is not a formatting failure.
            if ! (cd "$dir" && $prettier_cmd --check "$prettier_target" >/dev/null 2>&1) \
               && (cd "$dir" && $prettier_cmd --check "$prettier_target" 2>&1 | grep -qiE "no parser|ignored"); then
                continue
            fi
        fi

        ran_any_js_check=true
        local prettier_output
        if ! prettier_output=$(cd "$dir" && $prettier_cmd --check "$prettier_target" 2>&1); then
            # Apply formatting and capture any errors
            local format_output
            if ! format_output=$(cd "$dir" && $prettier_cmd --write "$prettier_target" 2>&1); then
                add_error "Prettier formatting failed ($dir)"
                echo "$format_output" >&2
            fi
        fi
    done

    # JS/TS files exist but nothing was checked — say so instead of silently
    # passing. Root-level configs drive this hook; nested-only package
    # configs (per-package lint scripts, per-package .prettierrc) are not
    # discovered.
    if [[ "$ran_any_js_check" == false ]]; then
        log_info "JS/TS detected but no root package.json lint script or prettier config — skipped JS checks"
    fi

    return 0
}

lint_rust() {
    if [[ "${CLAUDE_HOOKS_RUST_ENABLED:-true}" != "true" ]]; then
        log_debug "Rust linting disabled"
        return 0
    fi
    
    log_info "Running Rust linters..."

    if ! command_exists cargo; then
        log_info "Cargo not found, skipping Rust checks"
        return 0
    fi

    # Monorepo-aware: find every Cargo.toml and lint each crate from its own
    # directory. Only top-most manifests are used — a Cargo.toml nested under
    # another discovered one is a workspace member, and cargo covers it when
    # run from the workspace root. Single-crate repos behave as before.
    local manifests
    manifests=$(find_pruned "" -name Cargo.toml -type f | sort)

    if [[ -z "$manifests" ]]; then
        log_info "Rust files but no Cargo.toml found — skipping Rust checks"
        return 0
    fi

    local crate_roots=() manifest dir root nested
    while IFS= read -r manifest; do
        dir=$(dirname "$manifest")

        # Skip workspace members: sort order guarantees ancestors come first
        nested=false
        for root in "${crate_roots[@]}"; do
            if [[ "$dir/" == "$root/"* ]]; then
                nested=true
                break
            fi
        done
        [[ "$nested" == true ]] && continue
        crate_roots+=("$dir")

        log_info "Rust crate: $dir"

        local fmt_output
        if ! fmt_output=$(cd "$dir" && cargo fmt -- --check 2>&1); then
            # Apply formatting and capture any errors
            local format_output
            if ! format_output=$(cd "$dir" && cargo fmt 2>&1); then
                add_error "Rust formatting failed ($dir)"
                echo "$format_output" >&2
            fi
        fi

        local clippy_output
        if ! clippy_output=$(cd "$dir" && cargo clippy --quiet -- -D warnings 2>&1); then
            add_error "Clippy found issues ($dir)"
            echo "$clippy_output" >&2
        fi
    done <<< "$manifests"

    return 0
}

# Hook-mode Rust: fmt/clippy scoped to the crate containing the file. Cargo
# has no single-file fmt/clippy mode, so the crate is the finest scope
# available — never every crate in the repo.
lint_rust_scoped() {
    local file="$1"

    if [[ "${CLAUDE_HOOKS_RUST_ENABLED:-true}" != "true" ]]; then
        log_debug "Rust linting disabled"
        return 0
    fi

    if ! command_exists cargo; then
        log_info "Cargo not found, skipping Rust checks"
        return 0
    fi

    local crate_dir
    crate_dir=$(find_nearest_manifest "$file" "Cargo.toml") || {
        log_info "No Cargo.toml found above $file — skipping Rust checks"
        return 0
    }

    log_info "Rust crate: $crate_dir (scoped to $file)"

    local fmt_output
    if ! fmt_output=$(cd "$crate_dir" && cargo fmt -- --check 2>&1); then
        local format_output
        if ! format_output=$(cd "$crate_dir" && cargo fmt 2>&1); then
            add_error "Rust formatting failed ($crate_dir)"
            echo "$format_output" >&2
        fi
    fi

    local clippy_output
    if ! clippy_output=$(cd "$crate_dir" && cargo clippy --quiet -- -D warnings 2>&1); then
        add_error "Clippy found issues ($crate_dir)"
        echo "$clippy_output" >&2
    fi

    return 0
}

lint_nix() {
    if [[ "${CLAUDE_HOOKS_NIX_ENABLED:-true}" != "true" ]]; then
        log_debug "Nix linting disabled"
        return 0
    fi
    
    log_info "Running Nix linters..."
    
    # Find all .nix files
    local nix_files=$(find_pruned "" -name '*.nix' -type f | grep -v '/nix/store/' | head -20)
    
    if [[ -z "$nix_files" ]]; then
        log_debug "No Nix files found"
        return 0
    fi
    
    # Check formatting with nixpkgs-fmt or alejandra
    if command_exists nixpkgs-fmt; then
        local fmt_output
        if ! fmt_output=$(echo "$nix_files" | xargs nixpkgs-fmt --check 2>&1); then
            # Apply formatting and capture any errors
            local format_output
            if ! format_output=$(echo "$nix_files" | xargs nixpkgs-fmt 2>&1); then
                add_error "Nix formatting failed"
                echo "$format_output" >&2
            fi
        fi
    elif command_exists alejandra; then
        local fmt_output
        if ! fmt_output=$(echo "$nix_files" | xargs alejandra --check 2>&1); then
            # Apply formatting and capture any errors
            local format_output
            if ! format_output=$(echo "$nix_files" | xargs alejandra 2>&1); then
                add_error "Nix formatting failed"
                echo "$format_output" >&2
            fi
        fi
    fi
    
    # Static analysis with statix
    if command_exists statix; then
        local statix_output
        if ! statix_output=$(statix check 2>&1); then
            add_error "Statix found issues"
            echo "$statix_output" >&2
        fi
    fi
    
    return 0
}

# Hook-mode Nix: format-check just the triggering file. statix is a
# whole-project static analyzer with no per-file scope, so it is skipped in
# hook mode rather than run repo-wide for a single-file edit.
lint_nix_scoped() {
    local file="$1"

    if [[ "${CLAUDE_HOOKS_NIX_ENABLED:-true}" != "true" ]]; then
        log_debug "Nix linting disabled"
        return 0
    fi

    log_info "Running Nix formatting (scoped to $file)..."

    if command_exists nixpkgs-fmt; then
        local fmt_output
        if ! fmt_output=$(nixpkgs-fmt --check "$file" 2>&1); then
            local format_output
            if ! format_output=$(nixpkgs-fmt "$file" 2>&1); then
                add_error "Nix formatting failed ($file)"
                echo "$format_output" >&2
            fi
        fi
    elif command_exists alejandra; then
        local fmt_output
        if ! fmt_output=$(alejandra --check "$file" 2>&1); then
            local format_output
            if ! format_output=$(alejandra "$file" 2>&1); then
                add_error "Nix formatting failed ($file)"
                echo "$format_output" >&2
            fi
        fi
    fi

    return 0
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Parse command line options
FAST_MODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            export CLAUDE_HOOKS_DEBUG=1
            shift
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        *)
            # A bare path scopes the run to one file (CLI equivalent of the
            # hook payload below).
            if [[ -e "$1" ]]; then
                TARGET_FILE="$1"
                shift
            else
                echo "Unknown option: $1" >&2
                exit 2
            fi
            ;;
    esac
done

# PostToolUse fires once per edit, so scope formatters to the file that
# triggered it rather than the whole tree. Repo-wide `--write .` means one
# disagreement rewrites files the edit never touched, and on a large repo it can
# exhaust Node's heap outright. Falls back to repo-wide when invoked manually
# with no path (CLI mode), which is what `--fast` and ad-hoc runs expect.
if [[ -z "${TARGET_FILE:-}" ]] && [[ ! -t 0 ]]; then
    _hook_input=$(cat 2>/dev/null || true)
    if [[ -n "$_hook_input" ]] && command_exists jq && echo "$_hook_input" | jq . >/dev/null 2>&1; then
        TARGET_FILE=$(echo "$_hook_input" | jq -r '.tool_input.file_path // empty')
    fi
fi
export TARGET_FILE="${TARGET_FILE:-}"

# Hook mode: bail out immediately — before the header, before config
# loading, before any project detection, before touching a single linter —
# when the triggering file cannot need linting at all (gone, outside this
# repo, ignored, or an extension no linter here understands). This is the
# fix for the cost this script used to impose on every edit, including
# non-code writes and writes to paths outside the repo entirely.
if [[ -n "$TARGET_FILE" ]]; then
    REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
    if should_skip_target "$TARGET_FILE" "$REPO_ROOT"; then
        exit 0
    fi
fi

# Print header
echo "" >&2
echo "🔍 Style Check - Validating code formatting..." >&2
echo "────────────────────────────────────────────" >&2

# Load configuration
load_config

# Start timing
START_TIME=$(time_start)

# Main execution
main() {
    if [[ -n "$TARGET_FILE" ]]; then
        # Hook mode: lint only the file/module/crate the edit touched. No
        # detect_project_type() sweep at all — the extension alone decides
        # which single linter runs.
        case "${TARGET_FILE##*.}" in
            py)            lint_python_scoped "$TARGET_FILE" ;;
            go)             lint_go_scoped "$TARGET_FILE" ;;
            js|jsx|ts|tsx)  lint_javascript ;;
            rs)             lint_rust_scoped "$TARGET_FILE" ;;
            nix)            lint_nix_scoped "$TARGET_FILE" ;;
        esac
    else
        # CLI mode: unchanged repo-wide sweep.
        PROJECT_TYPE=$(detect_project_type)
        log_info "Project type: $PROJECT_TYPE"

        # Handle mixed project types
        if [[ "$PROJECT_TYPE" == mixed:* ]]; then
            local types="${PROJECT_TYPE#mixed:}"
            IFS=',' read -ra TYPE_ARRAY <<< "$types"

            for type in "${TYPE_ARRAY[@]}"; do
                case "$type" in
                    "go") lint_go ;;
                    "python") lint_python ;;
                    "javascript") lint_javascript ;;
                    "rust") lint_rust ;;
                    "nix") lint_nix ;;
                esac

                # Fail fast if configured
                if [[ "$CLAUDE_HOOKS_FAIL_FAST" == "true" && $CLAUDE_HOOKS_ERROR_COUNT -gt 0 ]]; then
                    break
                fi
            done
        else
            # Single project type
            case "$PROJECT_TYPE" in
                "go") lint_go ;;
                "python") lint_python ;;
                "javascript") lint_javascript ;;
                "rust") lint_rust ;;
                "nix") lint_nix ;;
                "unknown")
                    log_info "No recognized project type, skipping checks"
                    ;;
            esac
        fi
    fi

    # Show timing if enabled
    time_end "$START_TIME"
    
    # Print summary
    print_summary
    
    # Return exit code - any issues mean failure
    if [[ $CLAUDE_HOOKS_ERROR_COUNT -gt 0 ]]; then
        return 2
    else
        return 0
    fi
}

# Run main function
main
exit_code=$?

# Final message and exit
if [[ $exit_code -eq 2 ]]; then
    echo -e "\n${RED}🛑 FAILED - Fix all issues above! 🛑${NC}" >&2
    echo -e "${YELLOW}📋 NEXT STEPS:${NC}" >&2
    echo -e "${YELLOW}  1. Fix the issues listed above${NC}" >&2
    echo -e "${YELLOW}  2. Verify the fix by running the lint command again${NC}" >&2
    echo -e "${YELLOW}  3. Continue with your original task${NC}" >&2
    exit 2
else
    echo -e "\n${GREEN}✅ Style check passed - all clean!${NC}" >&2
    exit 0
fi