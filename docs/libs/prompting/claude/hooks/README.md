# Claude Code Hooks

Automated code-quality checks that run after Claude Code modifies files, enforcing project standards with zero tolerance for errors. Wired up by the bundle's [`settings.json`](../README.md) as `PostToolUse` (smart-lint, smart-test) and `Stop` (ntfy-notifier) hooks, with all paths assuming the bundle lives at `~/claude-code/`.

## Hooks

### `smart-lint.sh`
Project-aware linting that detects the language and runs the appropriate checks:
- **Go**: `gofmt`, `golangci-lint` (enforces forbidden patterns like `time.Sleep`, `panic()`, `interface{}`)
- **Python**: `black`, `ruff` or `flake8`
- **JavaScript/TypeScript**: `eslint`, `prettier`
- **Rust**: `cargo fmt`, `cargo clippy`
- **Nix**: `nixpkgs-fmt`/`alejandra`, `statix`

Features: automatic project-type detection, prefers project Makefile targets (`make lint`), only checks modified files, `--fast` mode to skip slow checks, `--debug` output. Exit code 2 means issues were found and ALL must be fixed; it also exits 2 on success with a "continue" message so Claude resumes its original task instead of stopping.

### `smart-test.sh`
Runs tests relevant to the file Claude just edited: focused tests for the file, package-level tests (optional race detection), optionally the full suite and integration tests. Configured via:
- `CLAUDE_HOOKS_TEST_ON_EDIT` (default `true`)
- `CLAUDE_HOOKS_TEST_MODES` — comma-separated `focused,package,all,integration`
- `CLAUDE_HOOKS_ENABLE_RACE` (default `true`)
- `CLAUDE_HOOKS_FAIL_ON_MISSING_TESTS` (default `false`)

Uses `gotestsum` for Go when available.

### `ntfy-notifier.sh`
Push notifications via the ntfy service for Claude Code events (`notification`/`stop`). Includes terminal context (tmux/terminal window name) for identification. Requires `~/.config/claude-code-ntfy/config.yaml` with `ntfy_topic` (and optional `ntfy_server`).

### `common-helpers.sh`
Shared colors, logging, and utility functions sourced by the other hooks — not a hook itself.

## Configuration

### Global settings
Environment variables:

```bash
CLAUDE_HOOKS_ENABLED=false      # Disable all hooks
CLAUDE_HOOKS_DEBUG=1            # Enable debug output
```

### Per-project settings
Create `claude-code-hooks-config.sh` in your project root (start from the example file `claude-hooks-config.sh` in this directory):

```bash
CLAUDE_HOOKS_GO_ENABLED=false
CLAUDE_HOOKS_PYTHON_ENABLED=false
CLAUDE_HOOKS_FAIL_FAST=true
CLAUDE_HOOKS_MAX_FILES=500
```

### Excluding files
Create `claude-code-hooks-ignore` in your project root using gitignore-style glob patterns (see the example file `claude-hooks-ignore` in this directory):

```
vendor/**
node_modules/**
*.pb.go
*_generated.go
```

Add `// claude-hooks-disable` to the top of any file to skip hooks for it.

## Usage

```bash
./smart-lint.sh           # Auto-runs after Claude edits
./smart-lint.sh --debug   # Debug mode
./smart-lint.sh --fast    # Skip slow checks
```

### Exit codes
- `0`: All checks passed
- `1`: General error (missing dependencies)
- `2`: Issues found — must fix ALL (also used on success to force "continue")

## Dependencies

Hooks work best with these tools installed and degrade gracefully when they're missing: `golangci-lint`, `gotestsum` (Go); `black`, `ruff` (Python); `eslint`, `prettier` (JS/TS); `cargo fmt`/`clippy` (Rust); `nixpkgs-fmt`/`alejandra`, `statix` (Nix).

## Note vs. the old in-tree README

The previous README claimed the hooks are "automatically installed by Nix home-manager" and referenced `example-claude-hooks-config.sh` / `example-claude-hooks-ignore`; there is no Nix machinery in this package, and the example files are named `claude-hooks-config.sh` / `claude-hooks-ignore`.
