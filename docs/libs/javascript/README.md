# libs/javascript

JavaScript/TypeScript packages. **None of these are recognized by the pnpm workspace** — `pnpm-workspace.yaml` only globs `libs/*/*` (2 levels), and every package below lives at `libs/javascript/<framework>/<name>` (3 levels). See [../../known-issues.md](../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).

| Group | Docs |
|---|---|
| `node/` | [node/README.md](node/README.md) — Node scripts/libraries, plus the `dots-js` git submodule |
| `react/` | [react/README.md](react/README.md) — a mix of Next.js 12 and old create-react-app packages |
| `svelte/resume-builder` | [svelte/resume-builder/README.md](svelte/resume-builder/README.md) — Svelte 5 + Vite 5 + Storybook 8, the only modern frontend stack in the repo |

None of these packages depend on or are depended on by anything else in the repo (standalone leaves) — see [../../architecture.md](../../architecture.md#dependency-graph).
