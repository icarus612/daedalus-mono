# Installation

One section per language. Every command below was run for real in a checkout of this branch; output
is quoted (trimmed for length) rather than assumed. See
[`package-management-strategy.md`](./package-management-strategy.md) for *why* each mechanism looks
the way it does.

## JavaScript / TypeScript

- **Manager:** pnpm, workspace-driven (`pnpm-workspace.yaml`). `packageManager` is pinned in root
  `package.json` (`"packageManager": "pnpm@9.1.0"`) — `pnpm/action-setup` and any local pnpm read
  that pin, no separate version file needed. Node's own version is pinned in `.nvmrc` (`24`) and
  mirrored in `package.json`'s `engines.node` (`>=24`).
- **Install:**
  ```
  pnpm install --frozen-lockfile
  ```
  installs every `libs/javascript/**` / `apps/next/**` package's `node_modules` from the single root
  `pnpm-lock.yaml`. No Python package declares an `install` lifecycle script any more, so this no
  longer touches Python at all — it installs JS dependencies only. Python packages are installed
  separately, via `uv sync` (see the Python section below), run as an explicit step after
  `pnpm install`, not as a side effect of it.
- **Run one package**, using its dotted turbo name (convention #2 — mirrors the path):
  ```
  $ pnpm exec turbo run build --filter='lib.javascript.svelte.resume-builder'
  lib.javascript.svelte.resume-builder:build: ✓ 112 modules transformed.
  lib.javascript.svelte.resume-builder:build: dist/style.css     0.23 kB │ gzip:  0.16 kB
  lib.javascript.svelte.resume-builder:build: dist/index.es.js  77.91 kB │ gzip: 23.14 kB
  lib.javascript.svelte.resume-builder:build: dist/index.umd.js  46.83 kB │ gzip: 17.42 kB
  lib.javascript.svelte.resume-builder:build: ✓ built in 592ms

   Tasks:    1 successful, 1 total
  ```
  (real `vite build` output, package verified end-to-end from this worktree's existing
  `node_modules`).

## Python

- **Manager:** a single root **`uv` workspace** — one `.venv`, one `uv.lock`, both committed at the
  repo root; `[tool.uv.workspace]` in the root `pyproject.toml` lists all 14 Python packages
  (every `apps/flask/*`, `apps/microservices/market-bots`, and `libs/python/*` project). Each package
  still keeps its own `pyproject.toml`, so per-package distributions and the `cp -R` mirroring
  (`build-maze-runner.yml`) still work — only dependency *resolution* is shared, not the manifests.
  Dev tooling (`ruff`, `pytest`) is pinned once at the root via `[dependency-groups] dev = [...]`
  rather than installed per package. `.python-version` still pins `3.11` at the root (D2). `uv 0.12.4`
  is installed and on `$PATH` in this environment. (This used to be per-package Poetry with no shared
  root virtualenv or lockfile; that mechanism has been fully replaced — see
  [`package-management-strategy.md`](./package-management-strategy.md) for the migration record.)
- **Install (verified):**
  ```
  $ uv sync
  Resolved 135 packages in 1ms
  Checked 124 packages in 1ms
  $ echo $?
  0
  $ .venv/bin/python -c "import cli_tools; print('ok')"
  ok
  ```
  `uv sync` is a single root-level command that resolves and installs the whole workspace — there is
  no more per-package `py-install`; `libs/bash/build-tools/py-scripts/` now contains only
  `py-build`/`py-lint`/`py-dev`/`py-test`, all of which shell to `uv sync`/`uv run` rather than
  `poetry`. `libs/python/cli-tools` is used above as the verified-working example.
- **Lint:** `ruff` is the canonical linter for this repo (D3) — `py-lint` now runs
  `uv run ruff format --check .` then `uv run ruff check .`, with `ruff` resolved from the root `uv`
  workspace's `[dependency-groups] dev` list; no runtime `pip install` any more. See
  [`development.md`](./development.md).

## Go

- **Manager:** none — `go.work` at the repo root (`go 1.24.2` floor) gives the six
  `libs/golang/*` modules local resolution of one another without per-module `replace` directives.
  No install step; `go build`/`go vet`/`go test` resolve directly against each module's own
  `go.mod` + the workspace.
- **Verified caveat (important — differs from what you might expect):** Go's workspace-mode pattern
  matching requires the *current directory* to itself be inside one of `go.work`'s member modules.
  Run from the repo root itself (which is **not** a workspace member — the six modules are all
  subdirectories):
  ```
  $ go build ./...
  pattern ./...: directory prefix . does not contain modules listed in go.work or their selected dependencies
  ```
  `go build all` / `go vet all` do resolve at the repo root, but `all` also pulls in the Go standard
  library's own package tree — not useful for a project build. The commands that actually work, and
  that this repo's own per-module `package.json` shims and turbo already use, run **from inside a
  module directory**:
  ```
  $ cd libs/golang/err && go build ./... && go vet ./... && test -z "$(gofmt -l .)" && go test ./...
  ```
  or, equivalently, through turbo from the repo root:
  ```
  $ pnpm exec turbo run build --filter='lib.golang.err'
  lib.golang.err:build: > go build ./...
   Tasks:    1 successful, 1 total
  ```
  For every module at once, use turbo's language filter rather than a bare workspace-root command:
  `pnpm exec turbo run build lint test --filter='lib.golang.*'`.

## Fresh clone → running state (verified this session)

- **Go:** all six `libs/golang/*` modules build/vet cleanly via the per-module command above
  (`lib.golang.err` shown; the same shim runs for the other five). No install step required —
  reused this worktree's own `init-workspace` state rather than re-cloning.
- **Python:** `uv sync` resolves and installs the whole workspace cleanly (output above), and
  `libs/python/cli-tools` imports successfully from the resulting root `.venv` — proving the `uv`
  workspace mechanism genuinely works end-to-end for at least one package.
- **JavaScript:** `lib.javascript.svelte.resume-builder` builds cleanly via `vite build` (output
  above), producing real `dist/` output.
