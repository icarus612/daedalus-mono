# libs/prompting

Portable AI coding-assistant configuration bundles — not application code. Each is meant to be dropped into *other* projects to carry house rules for that assistant. Both are recognized by the pnpm workspace.

| Package | Docs | Assistant |
|---|---|---|
| `claude` | [claude/README.md](claude/README.md) | Claude Code (`CLAUDE.md`, `hooks/`, `commands/{check,next,prompt}.md`) |
| `gemini` | [gemini/README.md](gemini/README.md) | Gemini CLI (`GEMINI.md`, `hooks/`, `commands/{check,next,prompt}.md`) |

See [../../conventions.md](../../conventions.md#ai-assistant-claude-code--gemini-cli-prompting-conventions) for the house rules these bundles encode.
