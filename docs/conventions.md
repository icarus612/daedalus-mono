# Conventions

## Naming

- Every workspace package's `package.json#name` follows `app.<category>.<name>` or `lib.<category>.<subpath...>.<name>` (e.g. `app.flask.pokedex`, `lib.golang.crud-server`, `lib.python.neural-networks.digit-recognition`). This is purely a workspace-graph label — Go and Python packages don't actually consume npm dependencies (see [architecture.md](architecture.md#the-cross-language-wrapper-pattern)).
- Directory names are kebab-case throughout.
- Documentation topic files (this tree) are lowercase kebab-case; each directory's entry point is `README.md`.

## Go

- Standard `cmd/`, `internal/`, `pkg/` layout.
- Concrete types — no `interface{}`.
- No `time.Sleep` / busy-waits.
- Table-driven tests, `_test.go` alongside source in `pkg/` (verified real tests exist, e.g. `libs/golang/err/pkg/*_test.go`).
- Each module has its own `go.mod` with an independent Go version; there is no repo-wide `go.work`.

## Python

- Poetry (`pyproject.toml` + `poetry.lock`) is the "proper" library pattern: `anki-tools`, `cli-tools`, `maze-runner`, `web-crawlers`, `pyto-widgets`.
- Flask apps instead mix `requirements.txt` + `Procfile` + `runtime.txt` (Heroku-style deploy), even though `templates/next-js` exists as a GCP Cloud Build deploy template for a *different* app type — deployment strategy is inconsistent across apps, not a repo-wide standard.
- `ruff` is the linter driven by `py-lint` (see [architecture.md](architecture.md#the-cross-language-wrapper-pattern)).

## Bash

- Pure CLI shims installed as `bin` entries in `package.json` — no formal shell version pin, written POSIX-ish.

## AI-assistant (Claude Code / Gemini CLI) prompting conventions

`libs/prompting/claude` and `libs/prompting/gemini` are portable configuration bundles (not application code) that codify house rules for coding-assistant sessions working in *other* repos: pnpm-only, Svelte v5 required, Tailwind v4 where used, "Research → Plan → Implement", zero-tolerance linting via hooks (`smart-lint.sh`, `smart-test.sh`), and forbidding `interface{}`, `time.Sleep`, versioned function names (`processV2`), and migration/compatibility layers.

Note: the Tailwind v4 rule is aspirational as far as *this* repo goes — no Tailwind dependency was found in any manifest here; the bundle is written to be dropped into other projects, not to describe daedalus-mono's own stack.

## Doc-format used by this `/docs` tree

- One `README.md` per directory as the entry point; other files are lowercase kebab-case topic pages.
- The docs tree mirrors the source tree: `apps/<x>` → `docs/apps/<x>`, `libs/<x>` → `docs/libs/<x>`.
- Every in-project `README.md` that has a `/docs` counterpart is a **symlink** into it (`ln -sfr docs/... path/README.md`), except `libs/javascript/node/dots-js` — a git submodule whose own README is not owned by this repo and is deliberately left untouched.
- Directories with zero files (`apps/solid`, `apps/svelte`, `libs/golang/auth-go`) are documented as placeholders in `/docs` but have no file added to the empty directory itself, so they remain genuinely empty in the source tree.
