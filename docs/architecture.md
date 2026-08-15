# Architecture

## Orchestration

pnpm workspaces + Turborepo drive the repo. Root `package.json` scripts fan out via `turbo`:

```
pnpm build   → turbo build   (outputs: dist/**, .next/**; task depends on ^build)
pnpm dev     → turbo dev     (uncached, long-running)
pnpm lint    → turbo lint
pnpm test    → turbo test    (depends on ^build)
pnpm clean   → turbo clean
postinstall  → go install gotest.tools/gotestsum@latest
```

This only reaches the packages pnpm actually recognizes as workspace members — see [known-issues.md](known-issues.md#workspace-glob-excludes-a-third-of-the-repo) for why roughly a third of the repo is excluded.

Root `package.json` also still carries a legacy npm/yarn-style `workspaces` array (deeper globs like `libs/javascript/*/*`, `libs/python/tensorflow/*`) that pnpm itself ignores — pnpm reads only `pnpm-workspace.yaml`. The mismatch between the two suggests the deeper nesting was *intended* to be covered but never fixed in `pnpm-workspace.yaml`.

### Bazel (legacy, unused)

A root `WORKSPACE` file references `rules_nodejs 4.4.6`, `rules_python 0.4.0`, `rules_go v0.29.0`. No `BUILD` file in the repo has any content (the two that exist, `libs/python/anki-tools/BUILD` and `libs/python/neural-networks/market-analyzer/BUILD`, are both 0 bytes) and no tooling in `package.json`/CI invokes `bazel`. Treat this as vestigial from an earlier iteration of the repo.

## The cross-language wrapper pattern

Go and Python packages don't consume npm dependencies — `package.json` in those packages is a thin wrapper whose `scripts.{build,dev,lint,test}` shell out to native tooling, so `turbo build/dev/lint/test` can drive a polyglot repo uniformly from one root command.

`libs/bash/build-tools` exposes bin scripts (`py-build`, `py-dev`, `py-lint`, `py-test`, implemented in `py-scripts/`). Every Python app/lib declares `lib.bash.build-tools` as a `workspace:*` devDependency and calls those scripts from its own `package.json` scripts. They shell to a single root `uv` workspace — `py-build` runs `uv sync --inexact` (never a bare `uv sync`, which would prune the shared root `.venv` down to one member's dependency closure), the rest use `uv run`. There is no per-package virtualenv and no `install` lifecycle script: `pnpm install` handles JavaScript only, and `uv sync` installs every Python member at once. See [installation.md](installation.md) and [package-management-strategy.md](package-management-strategy.md).

Because `turbo.json`'s `build` task has `dependsOn: ["^build"]`, `lib.bash.build-tools#build` (which just `chmod +x py-scripts/*`) runs before any consumer's build.

### Known inconsistency: two port-selection mechanisms

`py-dev` special-cases Flask apps and assigns a fixed port per directory name (`maze-runner`→5001, `pokedex`→5002, `weather-fortcast`→5003, `market-bots`→5004). Independently, the Flask apps' own `main.py` (e.g. `apps/flask/maze-runner/main.py`) self-selects a free port in the 3000–3100 range via `find_available_port` (from `libs/python/flask_utils/port_finder.py`). These two mechanisms were not reconciled during exploration — unverified which one actually wins when both are in play; treat any assumption about "the app's port" with that caveat.

## Dependency graph

- **Workspace-internal (declared)**: all Python apps/libs → `lib.bash.build-tools` (workspace devDependency).
- **Cross-package via filesystem, not via workspace deps (fragile)**: `apps/flask/maze-runner/main.py` does `sys.path.insert(0, "../../../libs/python")` then imports `flask_utils.port_finder` and a local `modules.maze` — a raw relative-path import bypassing the package manager entirely. This dependency is invisible to pnpm/turbo's graph; renaming or moving `libs/python/flask_utils` would silently break the Flask apps without any workspace tooling noticing.
- **Standalone leaves**: no package under `libs/javascript/*` or `libs/python/neural-networks/*` / `libs/python/tensorflow/*` depends on, or is depended on by, anything else in-repo.
- **Go modules** are fully independent (`github.com/dae-go/<name>`); no intra-repo Go module dependencies exist between them.

## CI/CD: this repo is a source of truth that fans out

Three GitHub Actions workflows (`.github/workflows/`), all on push/PR-close to `main` plus `workflow_dispatch`, all pushing to **external** repos using a `PAT` secret:

1. **`update-readme.yml`** — regenerates the root `README.md`'s directory tree via `libs/bash/github-actions/create-mono-file-tree.sh` and commits it back into this repo. This is why the root `README.md` must not be hand-edited (see [docs/README.md](README.md)).
2. **`sync-go-packages.yml`** — for every directory in `libs/golang/*`, rsyncs it into a standalone repo under the `dae-go` GitHub org (creating the repo via API if missing), rewrites `go.mod`'s module path to `github.com/dae-go/<name>`, and pushes. This is why every Go library's module path is `github.com/dae-go/...` rather than pointing at `daedalus-mono`.
3. **`build-maze-runner.yml`** — clones a separate `maze-runner-mono` repo, copies the five "maze-runner" implementations (Flask, Next.js, Python, Node, React) into it, regenerates that repo's README via the same file-tree script, and pushes.

A number of in-package `README.md` files across the repo turned out, on inspection, to be output from the same tree-generating script (or a generic personal-profile boilerplate), rather than package-specific documentation — see each package's page under [apps](apps/README.md) / [libs](libs/README.md) for which ones were superseded here.
