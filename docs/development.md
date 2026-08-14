# Development

Every package in this monorepo — JS, Python, Go, even bash — carries a `package.json` with the same
four script names (convention #4/#5: the `package.json`-as-universal-task-shim). `turbo.json`
declares exactly these four as pipeline tasks: `dev`, `build`, `lint`, `test`. **`clean` is
root-only** — the root `package.json` has a `"clean": "turbo clean"` script, but `turbo.json`
declares no `clean` task, so it is not a per-package convention the way the other four are (verified:
`turbo.json` has no `"clean"` entry in `tasks`).

Run any of the four for one package by its dotted turbo name (convention #2):

```
pnpm turbo build --filter='lib.golang.err'
pnpm turbo lint --filter='lib.python.cli-tools'
```

or for everything, or everything in one language, using the per-language filter groups already used
throughout this repo's CI (`lib.javascript.*` + `app.next.*` for JS, `lib.python.*` + `app.flask.*` +
`app.microservices.*` for Python, `lib.golang.*` for Go):

```
pnpm turbo lint --filter='lib.golang.*'
```

## What each script does, per language

| Script | Go | Python | JS / Next |
|---|---|---|---|
| `dev` | `gotestsum --watch ./...` (e.g. `lib.golang.err`) | `py-dev` — runs `main.py` (Flask apps get a per-project fixed port, e.g. `maze-runner` → `5001`); libraries just exit 0 | `next dev` for Next apps; framework-specific dev servers elsewhere (`vite`/`storybook` for the one Svelte package) — several `libs/javascript/**` packages still have no real `dev` script (Phase 3 pending) |
| `build` | `go build ./...` (run from inside the module directory — see [`installation.md`](./installation.md)'s Go caveat) | `py-build` — ensures the package's own `.venv` exists, `poetry install`s it | `next build` for Next apps, `vite build` for the Svelte package; several packages still stub this as `echo 'No build configured'` (Phase 3 pending, subphases 3.1/3.4) |
| `lint` | `go vet ./... && test -z "$(gofmt -l .)"` | `py-lint` — **today**: `pip install -q ruff` at run time, then `ruff check .` (not yet a pinned dependency); **once Phase 2 subphases 2.5/2.6 land**: ruff resolved from the shared `uv` workspace, no runtime install | whatever each package's own `lint` script defines — several are still `echo 'No lint configured'` stubs pending 3.4 |
| `test` | `go test ./...` | not standardized per-package today (varies by project) | not standardized per-package today (varies by project; several packages' `test` script is `exit 1` as a deliberate "not implemented" marker) |
| `install` *(lifecycle hook, not a turbo task)* | n/a — no install step | `py-install` — fires automatically on every `pnpm install` because `install` is an npm/pnpm lifecycle hook name | handled by pnpm itself from `pnpm-lock.yaml` |

## Notes

- **`console.info` is never flagged** by the shared root `eslint.config.js` — this is a deliberate,
  standing repo convention (see the config's own comment at the top of the file), not an oversight;
  `no-console` is left out of the rule set on purpose. Do not add it back or route around
  `console.info` calls to satisfy a stricter config.
- Go's `lint` script is what `.github/workflows/lint-go.yml`'s `gofmt`/`go vet` steps mirror at CI
  scope — see that workflow for how it's invoked repo-wide.
- Python's `lint`/`build`/`dev`/`install` scripts all live in
  `libs/bash/build-tools/py-scripts/py-*` and are consumed by every Python package via a
  `"lib.bash.build-tools": "workspace:*"` devDependency — one place to change the incantation for
  every Python project at once, matching the `package.json`-shim pattern triple-m also uses.
