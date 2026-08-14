# prompting/gemini

A portable Gemini configuration bundle — a partial port of the [claude bundle](../claude/README.md) with the same house rules and slash commands, rebranded for Gemini (`GEMINI.md`, `GEMINI_HOOKS_*` variables). See [../../../conventions.md](../../../conventions.md#ai-assistant-claude-code--gemini-cli-prompting-conventions).

**Path:** `libs/prompting/gemini`
**Workspace name:** `lib.prompting.gemini` (scripts are no-op echoes; nothing builds)

## Contents (verified against the tree)

```
.
├── GEMINI.md                    # House rules, first-person Gemini phrasing (177 lines)
├── commands/
│   ├── check.md                 # Same check workflow as the claude bundle
│   ├── next.md                  # Same research → plan → implement workflow
│   └── prompt.md                # Same prompt synthesizer
├── hooks/
│   ├── gemini-hooks-config.sh   # Example per-project config (GEMINI_HOOKS_* vars)
│   └── smart-test.sh            # Test-runner hook (Gemini-branded port)
└── package.json
```

## Differences from the claude bundle (verified)

- **No `settings.json`** — nothing wires the hooks to any tool automatically.
- **Hooks are incomplete**: only `smart-test.sh` and the example config exist. There is no `smart-lint.sh`, no `ntfy-notifier.sh`, and — critically — no `common-helpers.sh`, even though `hooks/smart-test.sh` does `source "${SCRIPT_DIR}/common-helpers.sh"`. As shipped, `smart-test.sh` fails at startup unless a copy of `common-helpers.sh` (from `../claude/hooks/`) is placed alongside it.
- `GEMINI.md` is a light rewrite of `CLAUDE.md` (first-person phrasing, adds a "Project Locations" section, drops a few lines); the substance — pnpm-only, blocking checks, research→plan→implement, Go forbidden patterns — is identical.
- `gemini-hooks-config.sh` documents smart-lint settings (`GEMINI_HOOKS_GO_ENABLED`, ...) for a `smart-lint.sh` that does not exist in this bundle.

## Note vs. the old in-tree README

The previous README mirrored the claude bundle's structure listing and claimed files this package does not contain (`settings.json`, `default.nix`, `hooks/smart-lint.sh`, `hooks/ntfy-notifier.sh`, `hooks/common-helpers.sh`, a hooks README). This page reflects what is actually present.
