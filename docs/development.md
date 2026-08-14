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
| `dev` | `gotestsum --watch ./...` (e.g. `lib.golang.err`) | `py-dev` — `uv run python main.py`, or for Flask apps `FLASK_APP=main.py uv run python -m flask run --port=<fixed port>` (`maze-runner`→5001, `pokedex`→5002, `weather-fortcast`→5003, `market-bots`→5004); libraries with no `main.py` just exit 0 | `next dev` for Next apps; framework-specific dev servers elsewhere (`vite`/`storybook` for the one Svelte package) — several `libs/javascript/**` packages still have no real `dev` script (Phase 3 pending) |
| `build` | `go build ./...` (run from inside the module directory — see [`installation.md`](./installation.md)'s Go caveat) | `py-build` — `uv sync` (syncs the shared root `.venv` from the root `uv.lock`) | `next build` for Next apps, `vite build` for the Svelte package; two packages (`lib.bash.cli-tools`, `lib.javascript.node.build-scripts`) declare no `build` script at all — `turbo build` treats this as a no-op, not a failure (a minor, standing convention gap, not Phase-3-pending work) |
| `lint` | `go vet ./... && test -z "$(gofmt -l .)"` | `py-lint` — `uv run ruff format --check .` then `uv run ruff check .`; `ruff` resolved from the root `uv` workspace's `[dependency-groups] dev` list, no runtime install | whatever each package's own `lint` script defines (mostly `eslint .`); every package has a real lint script except the two deliberately-excluded legacy CRA packages (`markdown-builder`, `quote-builder`, D7) — `turbo lint` is 34/34 green repo-wide |
| `test` | `go test ./...` | `py-test` — `uv run pytest` if the package has a `tests/` directory, else a no-op (exit 0) | not standardized per-package today (varies by project; several packages' `test` script is `exit 1` as a deliberate "not implemented" marker) |
| `install` *(lifecycle hook, not a turbo task)* | n/a — no install step | n/a — no per-package install hook any more; the whole workspace installs via `uv sync`, a separate explicit step, not a pnpm lifecycle hook | handled by pnpm itself from `pnpm-lock.yaml` |

## Notes

- **`console.info` is never flagged** by the shared root `eslint.config.js` — this is a deliberate,
  standing repo convention (see the config's own comment at the top of the file), not an oversight;
  `no-console` is left out of the rule set on purpose. Do not add it back or route around
  `console.info` calls to satisfy a stricter config.
- Go's `lint` script is what `.github/workflows/lint-go.yml`'s `gofmt`/`go vet` steps mirror at CI
  scope — see that workflow for how it's invoked repo-wide.
- Python's `build`/`lint`/`dev`/`test` scripts all live in `libs/bash/build-tools/py-scripts/py-*`
  (`py-build`, `py-lint`, `py-dev`, `py-test` — there is no `py-install` any more) and are consumed
  by every Python package via a `"lib.bash.build-tools": "workspace:*"` devDependency — one place to
  change the incantation for every Python project at once, matching the `package.json`-shim pattern
  triple-m also uses.
