# prompting/claude

A portable Claude Code configuration bundle: house rules (`CLAUDE.md`), slash commands, quality-gate hooks, and a `settings.json`, meant to be dropped into other projects / the user's environment rather than consumed by this repo's build. See [../../../conventions.md](../../../conventions.md#ai-assistant-claude-code--gemini-cli-prompting-conventions).

**Path:** `libs/prompting/claude`
**Workspace name:** `lib.prompting.claude` (scripts are no-op echoes; nothing builds)

## Contents (verified against the tree)

```
.
├── CLAUDE.md                    # Development-partnership house rules (193 lines)
├── commands/
│   ├── check.md                 # /check — fix ALL lint/test issues, zero tolerance
│   ├── next.md                  # /next — research → plan → implement workflow
│   └── prompt.md                # /prompt — synthesize a full prompt from next.md + args
├── hooks/                       # Quality-gate scripts — see hooks/README.md
│   ├── common-helpers.sh
│   ├── smart-lint.sh
│   ├── smart-test.sh
│   ├── ntfy-notifier.sh
│   ├── claude-hooks-config.sh   # example per-project config
│   └── claude-hooks-ignore      # example ignore file
├── settings.json                # Claude Code settings (model, hooks, permissions)
└── package.json
```

## What each piece does

- **`CLAUDE.md`** — the "Development Partnership" rules: pnpm-only, mandatory research→plan→implement flow, blocking hook failures, Go-specific forbidden patterns (`interface{}`, `time.Sleep`, ...), TODO.md working-memory protocol.
- **`commands/*.md`** — Claude Code slash commands with `allowed-tools: all` frontmatter; `next.md` takes `$ARGUMENTS` as the feature to implement, `prompt.md` composes `next.md` with `$ARGUMENTS` into a copy-ready prompt.
- **`settings.json`** — sets `"model": "opus"`; registers `PostToolUse` hooks (`smart-lint.sh`, `smart-test.sh` on `Write|Edit|MultiEdit`) and a `Stop` hook (`ntfy-notifier.sh notification`); allow/deny permission lists (denies `rm`, `sudo`, `curl`, and a long list of destructive git commands).

## Installation assumption

`settings.json` references the hooks at `~/claude-code/hooks/...`, and `prompt.md` reads `~/claude-code/commands/next.md` — the bundle expects to be copied/checked out to `~/claude-code` (or have those paths adjusted).

## Known issues (verified)

- `settings.json` is not strict JSON: the `permissions.allow` array has a trailing comma after `"Bash(go test:*)"`, and `"Bash(grep:*)"` is listed twice.
- The old in-tree README described files that don't exist (`default.nix`, `example-claude-hooks-config.sh`, `example-claude-hooks-ignore`); the actual example files are `hooks/claude-hooks-config.sh` and `hooks/claude-hooks-ignore`.

## Related

- [hooks/README.md](hooks/README.md) — detailed hook documentation.
- [../gemini/README.md](../gemini/README.md) — partial port of this bundle for Gemini.
