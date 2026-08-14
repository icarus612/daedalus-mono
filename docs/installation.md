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
  `pnpm-lock.yaml`. **Verified caveat:** on this branch today, the same `pnpm install` also fires
  every Python project's `install` lifecycle script (see the Python section) — so a top-level
  `pnpm install --frozen-lockfile` run today can exit non-zero from a *Python* package's Poetry
  resolution even when every JS package installs cleanly. That is Phase 2 pending work (out of this
  lane's scope), not a JS-side problem.
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

- **Manager, today:** **per-package Poetry**, bootstrapped by
  `libs/bash/build-tools/py-scripts/py-install` — every `libs/python/**` (and `apps/flask/**`,
  `apps/microservices/**`) project's `package.json` declares `"install": "py-install"`, which creates
  a `.venv` *inside that package's own directory*, `pip install poetry`, then `poetry install` from
  that package's own `pyproject.toml`/`poetry.lock`. There is **no shared root virtualenv and no
  root lockfile** — each package resolves independently. `.python-version` pins `3.11` at the root
  (D2).
- **Pending migration — say this explicitly, not silently:** Phase 2 subphase 2.5 (not yet landed on
  this branch) replaces this with a single root **`uv` workspace** — one `.venv`, one `uv.lock`,
  internal deps via `[tool.uv.sources]`, each package keeping its own `pyproject.toml` so `cp -R`
  mirroring still works (see `package-management-strategy.md`). `uv` is **not installed** on this
  machine today (`uv` on `$PATH` → not found) — installing and pinning it is part of 2.5. **This
  section will need a follow-up edit once 2.5 lands** — it currently documents the real, current
  mechanism, not the future one.
- **Install one package (verified):**
  ```
  $ cd libs/python/cli-tools
  $ pnpm exec py-install
  ...
  Installing dependencies from lock file
  Installing the current project: clitools-lib-py (0.1.0)
  ✅ Python package installed successfully
  ```
  exit code `0`. The same package via turbo, from the repo root:
  ```
  $ pnpm exec turbo run build --filter='lib.python.cli-tools'
  lib.python.cli-tools:build: Installing the current project: clitools-lib-py (0.1.0)
  lib.python.cli-tools:build: ✅ Python package built successfully

   Tasks:    2 successful, 2 total
  ```
- **Lint:** `ruff` is the canonical linter for this repo (D3) — `ruff --version` → `0.16.2` in this
  worktree, `ruff check .` / `ruff format --check .` replace flake8+isort / black. Today `py-lint`
  still `pip install`s ruff at run time rather than resolving it as a pinned dependency (2.5/2.6 make
  that durable); see [`development.md`](./development.md).

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
- **Python:** `lib.python.cli-tools` installs and builds cleanly end-to-end (output above), proving
  the current per-package Poetry mechanism genuinely works for at least one package even though a
  repo-wide `pnpm install --frozen-lockfile` today can fail on an unrelated Python package pending
  Phase 2 (see the JS section's caveat).
- **JavaScript:** `lib.javascript.svelte.resume-builder` builds cleanly via `vite build` (output
  above), producing real `dist/` output.
