# apps

Deployable applications in the monorepo.

| App | Stack | Workspace name | In pnpm/turbo? |
|---|---|---|---|
| [flask/](flask/README.md) | Flask (Python) | `app.flask.*` | yes |
| [microservices/market-bots](microservices/market-bots/README.md) | Python (unpinned deps) | `app.microservices.market-bots` | yes |
| [next/maze-runner](next/maze-runner/README.md) | Next.js 12 (Pages Router) | `app.next.maze-runner` | yes |
| solid/ | *(empty placeholder — no files)* | — | n/a |
| svelte/ | *(empty placeholder — no files)* | — | n/a |

`apps/solid` and `apps/svelte` contain no files at all; presumed reserved for future apps, unverified.

See [../architecture.md](../architecture.md) and [../known-issues.md](../known-issues.md) for the workspace-glob exclusion bug and the two-port-mechanism inconsistency that affects the Flask apps.
