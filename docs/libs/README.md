# libs

Shared libraries, grouped by language/category. Most are standalone leaves (no in-repo consumer) — see [../architecture.md](../architecture.md#dependency-graph).

| Category | Docs | Notes |
|---|---|---|
| `bash/` | [bash/README.md](bash/README.md) | build/CLI tooling shims, some run as CI scripts |
| `golang/` | [golang/README.md](golang/README.md) | independent Go modules under `github.com/dae-go/*` |
| `javascript/` | [javascript/README.md](javascript/README.md) | Node, React, and Svelte packages — **most are excluded from the pnpm workspace**, see below |
| `prompting/` | [prompting/README.md](prompting/README.md) | portable Claude Code / Gemini CLI configuration bundles |
| `python/` | [python/README.md](python/README.md) | Poetry libs, Flask utils, neural-network experiments — several excluded from the pnpm workspace |

**Read [../known-issues.md](../known-issues.md#workspace-glob-excludes-a-third-of-the-repo) first**: `pnpm-workspace.yaml` only globs 2 levels under `libs/`, so all of `libs/javascript/node/*`, `libs/javascript/react/*`, `libs/javascript/svelte/*`, `libs/python/neural-networks/*`, and `libs/python/tensorflow/open-ai-gym` are invisible to `pnpm install` / `turbo build|dev|lint|test` despite having valid `package.json` files.
