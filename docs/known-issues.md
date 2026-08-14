# Known issues & open questions

Verified facts and explicitly-flagged unverified items surfaced while mapping this repo. Where something couldn't be confirmed, it's marked **unverified** rather than asserted.

## Workspace glob excludes a third of the repo

**Verified.** `pnpm-workspace.yaml` declares:

```yaml
packages:
  - 'apps/*'
  - 'apps/*/*'
  - 'libs/*'
  - 'libs/*/*'
```

This is only 2 levels deep under `libs/`. Root `package.json` still carries a legacy npm/yarn-style `workspaces` array with deeper globs (`libs/javascript/*/*`, `libs/python/tensorflow/*`, etc.) that pnpm never reads — suggesting the deeper nesting was meant to be covered but the pnpm config was never updated to match.

Confirmed via `pnpm list -r --depth -1` and `turbo run build --dry` (both read-only) that the following packages are **silently excluded** from the pnpm workspace and from every `turbo build/dev/lint/test` run, despite having valid `package.json` files with `workspace:*` devDependencies that would fail to resolve if actually installed:

- All of `libs/javascript/node/*` (build-scripts, dots-js, maze-runner, web-crawlers)
- All of `libs/javascript/react/*` (e-card, labyrinth, markdown-builder, maze-runner, quest, quote-builder)
- All of `libs/javascript/svelte/*` (resume-builder)
- All of `libs/python/neural-networks/*` (abstract-base-classes, digit-recognition, market-analyzer, open-ai-gym)
- `libs/python/tensorflow/open-ai-gym`

Only these 21 packages are actually recognized by pnpm/turbo: `app.flask.maze-runner`, `app.flask.pokedex`, `app.flask.weather-fortcast`, `app.microservices.market-bots`, `app.next.maze-runner`, `lib.bash.build-tools`, `lib.bash.cli-tools`, `lib.bash.github-actions`, `lib.golang.complex-dsa`, `lib.golang.crud-server`, `lib.golang.err`, `lib.golang.maze-runner`, `lib.golang.process-monitor`, `lib.golang.pythonify`, `lib.prompting.claude`, `lib.prompting.gemini`, `lib.python.anki-tools`, `lib.python.cli-tools`, `lib.python.maze-runner`, `lib.python.pyto-widgets`, `lib.python.web-crawlers`.

**Impact**: anyone running `pnpm install` or `turbo build/dev/lint/test` at the root silently skips the excluded packages listed above. They must be built manually inside their own directories.

**Open question**: intentional exclusion, or an oversight? Unverified.

## pnpm version drift

**Unverified which is authoritative.** Root `package.json#packageManager` declares `pnpm@9.1.0`, but the pnpm binary actually resolving in the explored environment was `8.15.1`.

## Two Flask dev-port mechanisms

**Verified both exist, unverified which wins.** `py-dev` (in `libs/bash/build-tools`) assigns a fixed port per app directory name (maze-runner→5001, pokedex→5002, weather-fortcast→5003, market-bots→5004). Independently, each Flask app's own `main.py` self-selects a free port in the 3000–3100 range via `find_available_port` (`libs/python/flask_utils/port_finder.py`). Which mechanism is actually in effect when running `pnpm dev` was not verified.

## `flask-utils` vs `flask_utils` duplication

**Verified.** `libs/python/flask-utils/port_finder.py` (hyphenated directory, no `__init__.py`, no `package.json`) and `libs/python/flask_utils/{__init__.py,port_finder.py}` (underscored directory) contain the same file content. Only the underscored one is importable as a Python module and is what `apps/flask/*/main.py` actually imports via its `sys.path` hack. The hyphenated copy appears to be dead/orphaned — Python cannot import a hyphenated module name directly.

## `.env` present in `apps/microservices/market-bots`, not gitignored

**Verified.** `apps/microservices/market-bots/.env` exists in the working tree. The root `.gitignore` does not list `.env` (or `*.env`) explicitly, and `git check-ignore` confirms it is **not** currently ignored by any rule. This file was not opened as part of this exploration (secrets-shaped file, flagged only). Confirm untracked/gitignore status before any commit work touches that app, and consider adding `.env` to `.gitignore` if it isn't meant to be tracked.

## Bazel `WORKSPACE` is vestigial

**Verified.** No `BUILD` file in the repo has content — the two that exist (`libs/python/anki-tools/BUILD`, `libs/python/neural-networks/market-analyzer/BUILD`) are both 0 bytes. No script in `package.json` or CI invokes `bazel`. Treated as dead tooling from an earlier iteration; not documented as a live build system anywhere else in `/docs`.

## `libs/python/pytorch` is empty

**Verified.** The directory contains zero files. Unverified whether it's reserved for a future library or leftover cruft.

## Symlink direction exception for CI-synced packages

**Deliberate deviation, made during this documentation bootstrap.** The house doc convention is: the real file lives under `/docs` and the in-tree `README.md` is a symlink to it. But three CI workflows copy directories out of this repo verbatim (`.github/workflows/sync-go-packages.yml` uses `rsync -av`, which preserves symlinks as symlinks; `.github/workflows/build-maze-runner.yml` uses `cp -R`, same effect) — a symlinked README in those directories would arrive **dangling** in the published satellite repos (`dae-go/*`, `maze-runner-mono`). So for exactly these packages the direction is reversed: the in-tree `README.md` stays a real file and the `/docs` counterpart is the symlink:

- `libs/golang/{complex-dsa,crud-server,err,maze-runner,process-monitor,pythonify}` (synced to `github.com/dae-go/<name>`)
- `apps/flask/maze-runner`, `apps/next/maze-runner`, `libs/python/maze-runner`, `libs/javascript/node/maze-runner`, `libs/javascript/react/maze-runner` (copied into `maze-runner-mono`)
- `libs/javascript/node/dots-js` (git submodule of an external repo — its contents are never modified from here at all)

Either way the content exists exactly once. If the CI fan-out is ever retired, these can be flipped to the standard direction.

## Many in-repo `README.md` files were boilerplate, not documentation

**Verified.** A significant number of package `README.md` files (several Flask apps, some Go/JS/Python leaves, `libs/bash/cli-tools`, `libs/python/cli-tools/static_files`) contained either a generic personal-profile blurb or the same CI-generated directory-tree listing used by `update-readme.yml`/`build-maze-runner.yml`, rather than package-specific docs. These were superseded by the corresponding page under `/docs` during this documentation bootstrap; see [architecture.md](architecture.md#cicd-this-repo-is-a-source-of-truth-that-fans-out).
