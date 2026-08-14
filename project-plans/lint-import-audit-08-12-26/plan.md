# lint-import-audit — 08-12-26

Ranked diagnosis of the lint and package-import failures in `daedalus-mono`, plus ranked
package-management strategies for the multi-language monorepo. **This report is the plan**
(diagnose workflow).

> **Gate outcome — plan APPROVED and promoted (round 1).** The human settled every decision
> point; the answers are baked into the phase detail blocks below and recorded in full under
> "Decisions settled at the gate". In short:
> **D1 = S3** (three per-language workspaces — fixed pnpm globs + a `uv` workspace for Python +
> `go.work` — all driven by turbo). **All 14 candidates C1–C14 are picked**, so all six phases
> execute. **D3 = ruff**, canonical for this repo (`ruff format` replaces black, `ruff check`
> replaces flake8 + isort). **D4 = the library is canonical.** D2 = dedupe first, then unify on
> Python 3.11. D5 = drop the submodule. D6 = all JS packages private. D7 = the CRA packages are
> marked legacy, not migrated. D8 = untrack build artifacts, keep the model weights.
> The strategy-comparison section is retained unchanged as the record of what was weighed.

---

## Phase syllabus

- [ ] Phase 1: Single source of truth for the workspace
  - [x] 1.1: Fix the pnpm globs; delete the npm `workspaces` array             (lane 1)
  - [x] 1.2: Delete the competing and dead build-system config                 (lane 1, after: 1.1)
  - [x] 1.3: Root ruff config + shared tool / language-version config          (lane 1, after: 1.1)
  - [x] 1.4: Untrack build outputs; drop the `dots-js` submodule               (lane 1, after: 1.1)
- [ ] Phase 2: Python package management
  - [x] 2.1: One manifest per Python project, real dependencies declared       (lane 2, after: 1.1)
  - [x] 2.2: Make shared libs installable; remove the sys.path injection       (lane 2, after: 2.1)
  - [x] 2.3: Dedupe the forked trees onto the canonical library                (lane 2, after: 2.1)
  - [x] 2.4: Fix package identity — directory / distribution / import names    (lane 2, after: 2.3)
  - [x] 2.5: Adopt the uv workspace — one root `.venv`, one `uv.lock`          (lane 2, after: 2.1, 2.3)
  - [x] 2.6: Python mechanical lint sweep with `ruff`                          (lane 2, after: 2.4, 2.7)
  - [x] 2.7: Real Python defects — F821 undefined names, E999 syntax errors    (lane 2, after: 2.4)
  - [x] 2.8: Remove `libs/python/pyto-widgets` — C14 resolved: dead            (lane 2, after: 2.5)
- [ ] Phase 3: JavaScript package management
  - [x] 3.1: Admit `libs/javascript/**` to the workspace and declare its deps  (lane 3, after: 1.1)
  - [x] 3.2: Repair unresolvable specifiers and mixed module systems           (lane 3, after: 3.1)
  - [x] 3.3: Mark the CRA / React 16 packages legacy and exclude them          (lane 3, after: 3.1)
  - [x] 3.4: JavaScript lint baseline                                          (lane 3, after: 3.1, 1.3)
- [ ] Phase 4: Go modules
  - [x] 4.1: Raise `pythonify`'s `go` directive to what its code compiles at   (lane 4)
  - [x] 4.2: `go.work` for local resolution; prune orphan require + stray sum  (lane 4, after: 4.1)
  - [x] 4.3: Fix the Go task shims                                             (lane 4, after: 4.1)
  - [x] 4.4: Fix the `pkg/abf` zip type-identity test failures                 (lane 4, after: 4.1)
- [ ] Phase 5: Verification in CI, and documentation
  - [x] 5.1: Add a real lint/build/test workflow per language                  (lane 5, after: 1.1)
  - [x] 5.2: Align the Go CI toolchain and the two sync workflows              (lane 5, after: 1.1)
  - [x] 5.3: Docs mirror + symlinks per `doc-format`; deref the mirror copies  (lane 5, after: 1.1)
- [ ] Phase 6: Integration proof
  - [x] 6.1: Fresh-clone install → build → lint → import-check every package   (after: 2.5, 2.8, 3.1, 4.2, 4.4, 5.1, 5.3)

Lanes have disjoint file scopes. **All edits to the three shared root files
(`package.json`, `pnpm-workspace.yaml`, `turbo.json`) belong to lane 1 only** — including the
Go-motivated `turbo.json` outputs change that would otherwise be written from lane 4.

**One documented exception, added in round 2:** 2.8 regenerates `pnpm-lock.yaml` as an unavoidable
consequence of removing a workspace member. It is safe only because lanes 1, 3 and 4 are already
complete and no other writer is live — see 2.8's detail block. It is an exception, not a precedent.

---

## Goal & scope

**Goal.** Explain *why* imports break and lint fails across all three languages, at the
structural/package-management level rather than symptom by symptom; catalog the mechanical
lint fixes and every import problem site; and put ranked package-management strategies in
front of the human gate.

**In scope.** Committed `main` as checked out at
`/home/icarus64/repos/daedalus-mono/.workflows/lint-import-audit` (branch `bug/lint-import-audit`,
base `main`). All of `apps/`, `libs/`, `templates/`, `.github/`, and the root manifests.

**Out of scope.**
- The ~50 uncommitted modifications present in the user's main working tree but not in this
  worktree (flagged in the run's progress log; this audit describes committed `main`).
- Behavioural correctness of application logic beyond imports and the specific `F821`/`E999`
  defects listed in Catalog A.
- **Migrating anything outside this repo to ruff.** D3 makes ruff canonical *for daedalus-mono
  only*. Converting `~/.claude/hooks/smart-lint.sh`, the `~/repos/agentic` rule/skill set, and
  `money-makers/triple-m` (which uses black + isort + flake8) is a **recorded FOLLOW-UP, outside
  this repo and this run**. Consequence builders must expect: **the local smart-lint hook will
  keep reporting black/flake8 findings for the whole run.** Do not fight it, do not re-format to
  satisfy it, and do not treat its output as a gate — see the hook-hazard entry under Risks.
- Migrating `markdown-builder` / `quote-builder` off CRA (D7 = mark legacy, not migrate).
- Moving the `.keras`/`.h5` model weights to Git LFS (D8 = deferred decision).

**Supersedes.** Nothing — this is the first plan in this repo's plans dir.

---

## Stack & MAJOR versions

Every row verified from a manifest, lockfile, or the installed binary; never from memory.

| Thing | Declared | Installed / resolved | Source |
|---|---|---|---|
| Package manager | `pnpm@9.1.0` | `pnpm 9.1.0` | `package.json:24` `"packageManager"`; `pnpm --version` |
| pnpm lockfile | — | `lockfileVersion: '9.0'` | `pnpm-lock.yaml:1` |
| Task runner | `turbo` **`"latest"`** (unpinned) | `turbo 2.5.5` | `package.json:22`; `./node_modules/.bin/turbo --version` |
| Node | no `engines`, no `.nvmrc` | `v24.15.0` | absence verified repo-wide; `node --version` |
| Python | per-package `^3.8` / `^3.10` / `^3.11` / `3.11` / `<4.0`; `runtime.txt` says `python-3.8.0` ×3 | `3.11.7` | the eleven `pyproject.toml`s; `apps/flask/*/runtime.txt`; `python3 --version` |
| Poetry | not pinned anywhere; installed into each venv at run time | `1.8.2` on PATH | `libs/bash/build-tools/py-scripts/py-install:13` `pip install poetry` |
| Go | modules declare `1.21` ×2, `1.22` ×1, `1.24.2` ×3; CI pins `1.21` | `go1.26.5` | the six `go.mod`; `.github/workflows/sync-go-packages.yml` `go-version: '1.21'`; `go version` |
| Next.js | `^12.1.5` in 4 packages | `12.3.7` | `apps/next/maze-runner/package.json`; `pnpm-lock.yaml` |
| React | `^18.0.0` ×3 **and** `^16.6.1` / `^16.8.6` ×2 | `18.3.1` (only the workspace-visible one) | `libs/javascript/react/*/package.json` |
| CRA | `react-scripts` pinned `2.1.1` (2018, EOL) ×2 | not installed | `libs/javascript/react/{markdown-builder,quote-builder}/package.json` |
| Svelte | `^5.0.0` (+ Vite `^5.4.0`, TS `^5.0.0`, plugin-svelte `^4.0.0`, Storybook `^8.6.14`) | not installed | `libs/javascript/svelte/resume-builder/package.json` |
| Tailwind | **absent** — styling is `sass ^1.32.8` + CSS modules | — | no `tailwind` string in any manifest |
| Python linters | none configured; `py-lint` installs `ruff` at run time, unpinned, no config | `black 24.8.0`, `flake8 7.3.0` on PATH; **`ruff` not installed** | `libs/bash/build-tools/py-scripts/py-lint:18-23`; `ruff --version` → not found |
| JS linters | **none** — no eslint/prettier config or devDependency anywhere | — | repo-wide config inventory (six config files total, none lint-related) |
| Dead build systems | Bazel `WORKSPACE` (rules_nodejs 4.4.6, rules_python 0.4.0, rules_go 0.29.0); Pants (`/.pants.*` in `.gitignore:2`) | — | `WORKSPACE:1-44`; `.gitignore:1-2` |

**Structural constraint that shapes every strategy below:** this repo is a monorepo of
*separately published* things. `.github/workflows/sync-go-packages.yml` rsyncs every
`libs/golang/*` into its own repo under the `dae-go` GitHub org and rewrites the module path to
`github.com/dae-go/<name>` (which is why all six `go.mod`s already declare that path — it is
deliberate, **not** a mistake). `.github/workflows/build-maze-runner.yml` mirrors five of the six
`maze-runner` copies into `icarus612/maze-runner-mono`. Twelve built Python wheels/sdists are
committed under `*/dist/`. **Per-package self-containment is a requirement here**, and it is the
single biggest difference from the `triple-m` reference.

---

## Conventions to enforce

Hard constraints, taken from the repo's own established practice — not suggestions.

1. **pnpm only.** `"packageManager": "pnpm@9.1.0"`; never npm or yarn, never a second lockfile.
2. **Dotted package names mirroring the path** — `app.flask.pokedex`, `lib.python.maze-runner`,
   `lib.golang.err`. Applied consistently across all 35 `package.json` files today; keep it.
3. **kebab-case project directories; snake_case only for the Python import package nested
   inside** (`libs/python/anki-tools/anki_tools/`). `libs/python/flask_utils/` is the one
   project-level violation.
4. **`package.json` is the universal task shim.** Every project — Python, Go, bash — carries one
   whose `build`/`dev`/`lint`/`test` scripts shell out to the real toolchain. This is the
   mechanism that lets one `turbo` command span three languages; preserve it.
5. **Uniform script names only**: `dev`, `build`, `lint`, `test`, `clean`. `turbo.json` declares
   exactly these four today (`turbo.json:4-26`; note `clean` is a root script with no turbo task).
6. **Every `libs/golang/*` module must remain independently `go get`-able at
   `github.com/dae-go/<name>`** — the sync workflow depends on it. No change may make a Go
   module resolvable only from inside the monorepo.
7. **Every mirrored package must stay buildable standalone** after `cp -R` into another repo
   (`build-maze-runner.yml:32-37`).
8. **Go rules from CLAUDE.md apply** to `libs/golang/**`: no `interface{}`, no `time.Sleep`,
   concrete types from constructors, `fmt.Errorf("...: %w", err)`, table-driven tests.
9. **`console.info` is never removed** from JS (user's standing instruction).
10. No time estimates anywhere in this plan.

---

## Scope & sources

- **Issue (verbatim):** "there are large quantities of errors related to things in this project
  around both linting and import issues. create a document lists easy lint fixes as well as all
  places that there are package import issues. the review gate here will be on comming up with a
  quality solution for package manegment in this large multilangue monorepo. i like the somple
  solution of ../money-makers/triple-m, but not everything can be that nice."
- **Suspect ref:** the worktree checkout itself (committed `main`). No regression hunt — this is a
  whole-repo state audit, so there is no `git diff <base>...<ref>` to summarise; the diff against
  `main` is empty by construction.
- **Pre-gathered evidence:** `.artifacts/evidence-lint-sweep-08-12-26.md` — full smart-lint sweep
  (go vet, black, complete flake8 listing). Incorporated into Catalog A and Catalog B rather
  than repeated.
- **Reference repo (read-only, separate):** `/home/icarus64/repos/money-makers/triple-m`.
- **This investigation added:** five parallel investigations (Python packaging, JS/TS workspace,
  Go modules, the triple-m reference, repo tooling/CI) plus first-hand verification recorded below.

---

## Reproduction

**The documented install path leaves a Flask app without Flask.** Reproduced end to end in this
worktree after the run's `init-workspace` stage executed `pnpm install`:

```
$ cd apps/flask/maze-runner
$ ./.venv/bin/python -c "import flask"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'flask'

$ ./.venv/bin/python -c "import poetry; print('poetry present')"
poetry present
```

The venv holds 103 site-packages entries — every one of them a dependency of **Poetry itself**
(`requests`, `requests_toolbelt`, `anyio`, …). Not one of the app's ten declared runtime
dependencies is present.

Why, in four verified steps:

1. `apps/flask/maze-runner/package.json:5` declares `"install": "py-install"`. `install` is an npm
   lifecycle hook, so pnpm fires it for every workspace project on every `pnpm install`.
2. `libs/bash/build-tools/py-scripts/py-install:9-25` branches `if [ -f "pyproject.toml" ] … elif
   [ -f "requirements.txt" ]`. It creates `.venv`, then `pip install poetry`, then `poetry install`.
3. `apps/flask/maze-runner/pyproject.toml` wins that branch. It declares
   `package-mode = false` and, under `[tool.poetry.dependencies]`, only `python = "^3.10.0"`.
   `poetry install` therefore installs **nothing**.
4. `apps/flask/maze-runner/requirements.txt` — the file that actually lists `Flask==2.3.3`,
   `gunicorn`, `Jinja2`, `requests`, `Werkzeug`, `itsdangerous`, `flask-bootstrap4`,
   `flask_sslify`, `flask-fontawesome`, `MarkupSafe` — is never read, because of the `elif`.

The same `elif` shadowing hits `libs/python/pyto-widgets`, `libs/python/web-crawlers`,
`libs/python/neural-networks/digit-recognition`, and `libs/python/neural-networks/market-analyzer`.

**Second reproduction — the JavaScript half of the workspace does not exist.** `turbo`'s own
package graph, taken from a dry run in this worktree:

```
$ ./node_modules/.bin/turbo run lint --dry=json
"packages": [ "app.flask.maze-runner", "app.flask.pokedex", "app.flask.weather-fortcast",
  "app.microservices.market-bots", "app.next.maze-runner", "lib.bash.build-tools",
  "lib.bash.cli-tools", "lib.bash.github-actions", "lib.golang.complex-dsa",
  "lib.golang.crud-server", "lib.golang.err", "lib.golang.maze-runner",
  "lib.golang.process-monitor", "lib.golang.pythonify", "lib.prompting.claude",
  "lib.prompting.gemini", "lib.python.anki-tools", "lib.python.cli-tools",
  "lib.python.maze-runner", "lib.python.pyto-widgets", "lib.python.web-crawlers" ]
```

21 packages. **Zero `lib.javascript.*`.** `pnpm-lock.yaml`'s `importers:` block contains the same
21 plus `.` and no `libs/javascript/**` key. Independently confirmed on disk: after
`pnpm install`, every `libs/javascript/**` package still has no `node_modules`, while
`libs/javascript/react/labyrinth/package.json` declares `next`, `react`, `react-dom`, `animejs`,
`classnames`, `sass` — none of which are installed anywhere for it.

**Third reproduction — `go vet` fails in one module.** From `libs/golang/pythonify`:

```
pkg/dict.go:48:49: slices.Collect requires go1.23 or later (module is go1.22)
pkg/abf/utils_test.go:129:8: testing.Loop requires go1.24 or later (module is go1.22)
```
(9 errors total; the other five modules vet clean.)

---

## Ranked candidates

Ranked on **likelihood × ease** — likelihood first (how strongly the evidence supports this being
the actual cause), ease as tie-break. Each entry's `files` list is that fix lane's file scope.

> **All 14 candidates were PICKED at the gate**, which is why every box below is ticked and all
> six phases execute. **A ticked box here means "selected for fixing", not "already fixed"** —
> this is the gate's pick list, per the diagnose workflow. Completion is tracked separately, in
> the phase syllabus, whose boxes stay `- [ ]` until the corresponding subphase actually lands.

- [x] **C1 — The workspace has two definitions that disagree, and the authoritative one is too
  shallow to see any JavaScript package.**
  `likelihood: High` (reproduced) · `ease: High`
  - **Evidence.** `pnpm-workspace.yaml` declares four globs — `apps/*`, `apps/*/*`, `libs/*`,
    `libs/*/*` — so its effective depth under `libs/` is **2**. Every JavaScript package lives at
    depth 3 (`libs/javascript/react/quest`, `libs/javascript/svelte/resume-builder`), as do
    `libs/python/neural-networks/*` (4 packages) and `libs/python/tensorflow/open-ai-gym`.
    `package.json:4-12` declares a **second, different** list — `apps/*/*`, `libs/bash/*`,
    `libs/golang/*`, `libs/javascript/*/*`, `libs/python/*`, `libs/python/tensorflow/*`,
    `libs/prompting/*` — which *does* cover `libs/javascript/*/*` but omits
    `libs/python/neural-networks/*`. **pnpm reads only the YAML and ignores the `workspaces`
    array entirely**, so the more-correct list is inert decoration. Net effect, confirmed three
    independent ways (turbo dry-run above; `pnpm-lock.yaml` importers; absence of `node_modules`
    on disk after install): **14 of 35 packages are outside the monorepo** — all 10 under
    `libs/javascript/**`, the 4 under `libs/python/neural-networks/`, and
    `libs/python/tensorflow/open-ai-gym`. Four of those (`neural-networks/*`) are matched by
    **neither** list, yet each declares `"lib.bash.build-tools": "workspace:*"`, a dependency
    that can never resolve.
  - **Consequences that read as "import errors".** Nothing installs `libs/javascript/**`'s
    dependencies, so every import in those packages is unresolvable; `turbo lint`/`build`/`test`
    silently skip 40% of the repo and report green; and
    `libs/javascript/svelte/resume-builder/pnpm-lock.yaml` survives as a detached
    `lockfileVersion: '6.0'` island under a root that is `'9.0'`.
  - **Proposed fix.** Pick one definition. Keep `pnpm-workspace.yaml`, extend it to the real depth
    (`libs/*/*/*` or explicit globs covering `libs/javascript/*/*` and `libs/python/*/*`), delete
    the `workspaces` array from `package.json`, re-lock, and delete the nested lockfiles.
  - **Files.** `pnpm-workspace.yaml`, `package.json`, `pnpm-lock.yaml`,
    `libs/javascript/svelte/resume-builder/pnpm-lock.yaml`, `apps/next/maze-runner/pnpm-lock.yaml`.

- [x] **C2 — Python dependencies are essentially undeclared, and the install script prefers the
  empty manifest over the populated one.**
  `likelihood: High` (reproduced) · `ease: High`
  - **Evidence.** Of eleven `pyproject.toml` files, **nine declare no dependency but `python`**;
    only the two `open-ai-gym` copies declare real ones. Three `requirements.txt` files are
    **0 bytes** (`libs/python/neural-networks/digit-recognition`, `libs/python/pyto-widgets`,
    `libs/python/web-crawlers`). `libs/python/neural-networks/market-analyzer/requirements.txt`
    is a 37-line `pip freeze` of a developer machine that omits the three heaviest actual imports
    (`tensorflow`, `scikit-learn`, `matplotlib`, used at `classes/analyzer.py:4-9`) while
    declaring `pytest`, `pre-commit`, `virtualenv`, `isort`, `nodeenv`.
    Undeclared-but-imported, by package: `web-crawlers` → `requests`, `bs4`, `selenium`,
    `webdriver_manager`, `google_speech`, `retrying` (~40 modules); `anki-tools` → `anki`
    (`anki_tools/get_deck_info.py:3`), `requests`; `cli-tools` → `Pillow`
    (`cli_tools/img_resizer.py:1`); `digit-recognition` → `tensorflow`, `numpy`, `scikit-learn`.
    Layered on top, `py-install:9-21`'s `if pyproject / elif requirements` makes the empty
    manifest win wherever both exist — the reproduction above.
    Reproducibility is illusory: **seven of the eight committed `poetry.lock` files are stubs**
    containing `package = []` (`libs/python/maze-runner/poetry.lock:1`, same shape in
    `anki-tools`, `cli-tools`, `web-crawlers`, `pyto-widgets`,
    `neural-networks/abstract-base-classes`, `apps/flask/maze-runner`), and lock-version is mixed
    (`1.1` vs `2.0`).
  - **Proposed fix.** Declare real dependencies per project from an import scan; delete the empty
    `requirements.txt` files and the freeze dump; collapse to **one** manifest kind per project;
    regenerate every lock with a single resolver version.
  - **Files.** all eleven `*/pyproject.toml`, the five `*/requirements.txt`,
    `apps/flask/maze-runner/setup.py`, the eight `*/poetry.lock`,
    `libs/bash/build-tools/py-scripts/py-install`.

- [x] **C3 — Shared Python libraries have no installable form, so apps reach them by injecting
  `sys.path`, which in turn forced a duplicated directory.**
  `likelihood: High` · `ease: High`
  - **Evidence.** All three Flask apps carry the identical line at `main.py:6`:
    `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../libs/python"))`
    immediately followed at `:7` by `from flask_utils.port_finder import find_available_port`
    (`apps/flask/maze-runner`, `apps/flask/pokedex`, `apps/flask/weather-fortcast`). These are the
    **only** three `sys.path` sites in the repo. `libs/python/flask_utils/` has **no manifest of
    any kind** — it cannot be a dependency, so the path hack is the only mechanism.
    The duplication follows directly: `libs/python/flask-utils/port_finder.py` and
    `libs/python/flask_utils/port_finder.py` are **byte-identical** (`diff` → no output); the only
    difference is a 0-byte `__init__.py` in the underscore copy. The hyphenated original is
    unimportable by name, is referenced by nothing, and survives only as dead weight. Both are
    tracked; the auto-generated README renders both as unlinked plain text (`README.md:62-63`),
    because `libs/bash/github-actions/create-mono-file-tree.sh:15` links only directories that
    contain a README.
    The hack also breaks the mirroring convention: it works only while the `../../../`
    relationship holds, and `build-maze-runner.yml:32` copies `apps/flask/maze-runner` out on its own.
  - **Proposed fix.** Give `flask_utils` a manifest, depend on it as a workspace/path dependency
    from the three apps, delete the three `sys.path.insert` lines, and delete
    `libs/python/flask-utils/`.
  - **Files.** `libs/python/flask_utils/`, `libs/python/flask-utils/`,
    `apps/flask/{maze-runner,pokedex,weather-fortcast}/main.py` and their manifests.

- [x] **C4 — Package identity is inconsistent at every level: directory name ≠ distribution name
  ≠ import name, with two outright collisions.**
  `likelihood: High` · `ease: Med`
  - **Evidence.** Seven of eleven Python `pyproject.toml` names disagree with their directory:
    `cli-tools`→`clitools-lib-py`, `pyto-widgets`→`pytowidgets-lib-py`,
    `digit-recognition`→`digitrecognition-ann-py`, `market-analyzer`→`marketanalyzer-ann-py`,
    `abstract-base-classes`→`abstract_base_classes`, both `open-ai-gym`→`open_ai_gym`. Two
    naming generations (`*-lib-py`/`*-ann-py` vs bare kebab) are visibly mid-migration, and
    `libs/python/anki-tools/dist/` still holds wheels under a **fourth** name
    (`ankibuildtools_lib_py-0.1.0`).
    **Collisions:** `apps/flask/maze-runner/pyproject.toml:2` and
    `libs/python/maze-runner/pyproject.toml:2` both declare `name = "maze-runner"`; both
    `open-ai-gym` copies declare `name = "open_ai_gym"` and ship identically-named wheels.
    `apps/flask/maze-runner` alone carries five manifests and four names — `app.flask.maze-runner`
    (package.json), `maze-runner` (pyproject), `Maze Runner` (`setup.py:4`, with a space in a
    distribution name), and `mazeRunner-PY` in the setup.py URL.
    **Un-importable packages:** `__init__.py` files sit at hyphenated directory levels —
    `libs/python/maze-runner/__init__.py`, `libs/python/neural-networks/open-ai-gym/__init__.py`,
    `libs/python/tensorflow/open-ai-gym/__init__.py` — declaring packages whose names are not
    legal Python identifiers. `libs/python/maze-runner/__init__.py` is one line,
    `from src import *`, and **there is no `src/` directory** (the code was renamed to
    `maze_runner/`, which itself lacks an `__init__.py` despite
    `pyproject.toml:8` declaring `{ include = "maze_runner" }`).
    **The worst case:** `libs/python/neural-networks/abstract-base-classes/pyproject.toml:8`
    ships `packages = [{ include = "src" }]` — it installs a top-level module literally named
    `src` into site-packages — while both consumers import
    `from abstract_base_classes.ann_shell import ANN_Shell`
    (`digit-recognition/classes/MLP_tensorflow.py:7`,
    `open-ai-gym/open_ai_gym/classes/env_builder.py:5`), a module that exists under no name; the
    real class is `ANN_Shell` in `src/shells/ANN.py:17`.
  - **Proposed fix.** One name per project, derived from the directory; rename `src/` →
    `abstract_base_classes/` and add the `ann_shell` module (or re-export); delete the three
    hyphenated-level `__init__.py` files; add `maze_runner/__init__.py`; rename the colliding
    distributions.
  - **Files.** all eleven `*/pyproject.toml`, `apps/flask/maze-runner/setup.py`,
    `libs/python/maze-runner/{__init__.py,bin/solver.py,maze_runner/}`,
    `libs/python/neural-networks/abstract-base-classes/`,
    `libs/python/{neural-networks,tensorflow}/open-ai-gym/__init__.py`.

- [x] **C5 — Nothing in CI ever builds, lints, or tests the repo, which is why C1–C4 survived
  three `feature/turborepo-setup` pull requests.**
  `likelihood: High` · `ease: Med`
  - **Evidence.** `.github/workflows/` holds exactly three files and all three are mirror or
    README-generation jobs. `update-readme.yml` regenerates `README.md` from
    `libs/bash/github-actions/create-mono-file-tree.sh` and pushes. `build-maze-runner.yml` is a
    `cp -R` mirror into `maze-runner-mono` (`:32-37`). `sync-go-packages.yml` is the only workflow
    that installs a toolchain — `actions/setup-go@v4` with `go-version: '1.21'` — and it runs only
    `go mod edit`/`go mod init` plus `rsync`; **never `go build` or `go test`**. There is no
    `setup-node`, no `pnpm`, no `setup-python`, no `pip`, no `poetry` anywhere under `.github/`.
    The root scripts `turbo build|lint|test` (`package.json:14-18`) are unreachable from CI.
    Related: the pinned CI Go 1.21 is **below** three modules' own directives (`1.24.2`), so a
    build step added naively would fail immediately.
    Also dead and misleading: `apps/next/maze-runner/.github/workflows/*` (two files running
    `npm ci` in a pnpm repo with no `package-lock.json`; GitHub never executes non-root workflow
    directories), and `libs/bash/github-actions/build-maze-runner.sh`, a tracked `100755` script
    containing literal `${{ secrets.PAT }}` Actions template syntax — not valid bash — that
    references a nonexistent `libs/javascript/solid/`.
  - **Proposed fix.** Add one workflow per language that installs and actually runs
    lint/build/test, gated on paths; align `setup-go` with the highest module directive; delete
    the dead nested workflows and the broken helper script.
  - **Files.** `.github/workflows/`, `apps/next/maze-runner/.github/`,
    `libs/bash/github-actions/build-maze-runner.sh`.

- [x] **C6 — Duplicated and hard-forked trees mean the same code exists two or three times, with
  the copies already diverged.**
  `likelihood: High` · `ease: Low`
  - **Evidence.**
    *The Flask maze-runner is a hard fork, not a vendored snapshot.*
    `apps/flask/maze-runner/main.py:8-9` imports its own `modules/`, never the library.
    `diff -rq apps/flask/maze-runner/modules libs/python/maze-runner/maze_runner` reports all
    three files differing, and the divergence is **API-breaking**: the app's
    `Maze.build_new(self, width=None, height=None, …)` versus the lib's
    `build_new(self, height=10, width=10, …)` — the first two positional parameters are swapped;
    the app's `build=[(10, 10), "h"]` packs into one argument where the lib takes
    `build=(10,10), build_type="h"`; `node.py` has an app-only `add_visited()`; `runner.py`
    differs in `if` vs `elif` in the neighbour chain (a behavioural difference) and in `set` vs
    `list`. `build-maze-runner.yml` copies **both** downstream, propagating the fork.
    *The open-ai-gym tree is duplicated verbatim.* All four `.py` files under
    `libs/python/neural-networks/open-ai-gym` and `libs/python/tensorflow/open-ai-gym` are
    identical; they share the distribution name `open_ai_gym` and identical committed wheels. The
    tensorflow copy's path dependency was never re-pointed:
    `pyproject.toml:13` declares `abstract_base_classes = {path = "../abstract-base-classes"}`
    and `libs/python/tensorflow/abstract-base-classes` **does not exist** — the copied
    `poetry.lock:22-25` bakes the broken directory URL in, so that package can never install.
    *The Python build toolchain exists three times.* `libs/bash/build-tools/py-scripts/`
    (canonical, `100755`); `libs/bash/cli-tools/src/py-scripts/` (missing `py-lint`, drifted
    `py-dev`); `libs/bash/cli-tools/bin/` (same blobs, committed `100644` — not executable).
  - **Proposed fix (D4 + D2 settled).** Per pair: reconcile then delete. **The library is
    canonical** — `apps/flask/maze-runner` gains a declared dependency on
    `lib.python.maze-runner`, its call sites are rewritten to the library's
    `build_new(height, width, …)` signature, and `apps/flask/maze-runner/modules/` is deleted.
    **`libs/python/tensorflow/open-ai-gym` is the copy that goes** (it is the one carrying the
    broken `{path = "../abstract-base-classes"}` dependency), leaving
    `libs/python/neural-networks/open-ai-gym`. Delete the two stale `py-scripts` copies under
    `libs/bash/cli-tools/`.
  - **Files.** `apps/flask/maze-runner/modules/`, `libs/python/maze-runner/maze_runner/`,
    `libs/python/tensorflow/open-ai-gym/`, `libs/bash/cli-tools/{src/py-scripts,bin}/`.

- [x] **C7 — Unresolvable JavaScript specifiers: path aliases without the `jsconfig.json` that
  makes them work, and CommonJS mixed with ESM.**
  `likelihood: High` · `ease: High`
  - **Evidence.** There are **zero** genuine cross-package JS imports — no `@scope/` specifier
    exists, no local package name is ever imported, and a repo-wide grep for `'../../'` in
    JS/TS/Svelte sources returns nothing. What breaks is root-relative alias style
    (`components/…`, `styles/…`) copied from the Next apps into packages that have neither the
    `jsconfig.json` `baseUrl` nor the target directories. Only three packages have that jsconfig
    (`apps/next/maze-runner`, `libs/javascript/react/{labyrinth,quest}`), and in those the aliases
    resolve correctly. The broken sites are enumerated in Catalog B.
    Separately, `libs/javascript/node/maze-runner/src/quick-solver.js:1-4` puts
    `const fs = require("fs");` and `import { QuickSolver } from ".";` in the **same file**, then
    imports `"../lib/maze"` and `"../lib/runner"` from a `lib/` directory that does not exist (the
    files are `src/maze.js`, `src/runner.js`). None of the three `libs/javascript/node/*` packages
    declares `"type": "module"` while their sources use ESM.
  - **Proposed fix.** Rewrite the specifiers to relative paths where the target exists; add the
    missing `jsconfig.json` (or delete the package as a dead copy) where it does not; add
    `"type": "module"` to the node packages and finish the CJS→ESM conversion.
  - **Files.** `libs/javascript/react/maze-runner/src/{build,index,randomizer}.js`,
    `libs/javascript/react/quote-builder/src/{index,pages}.js`,
    `libs/javascript/react/quest/modules/list-item.js`,
    `libs/javascript/node/maze-runner/{package.json,src/}`,
    `libs/javascript/node/build-scripts/package.json`,
    `libs/javascript/node/web-crawlers/package.json`.

- [x] **C8 — `libs/golang/pythonify` declares an older language version than its code compiles
  against.**
  `likelihood: High` · `ease: High`
  - **Evidence.** `libs/golang/pythonify/go.mod:3` says `go 1.22`. `pkg/dict.go:48,50` and
    `pkg/frozenset.go:30` use `slices.Collect`/`maps.Keys`/`maps.Values` (go1.23+);
    `pkg/abf/utils_test.go:129,145,161` use `testing.Loop` (go1.24+). `go vet ./...` emits 9
    errors, quoted in Reproduction. The other five modules vet clean. The binding constraint is
    `testing.Loop`, so **1.24** is the correct target — bumping only to 1.23 leaves the three test
    errors. Its siblings `complex-dsa`, `process-monitor`, `err` already declare `1.24.2`.
  - **Proposed fix.** One line: `go 1.24` (or `1.24.2` to match the siblings exactly).
  - **Files.** `libs/golang/pythonify/go.mod`.

- [x] **C9 — No `go.work` and no `replace` directives, making the first cross-module import a
  silent remote fetch.**
  `likelihood: Med` (no breakage today; certain on the first shared-package refactor) · `ease: High`
  - **Evidence.** Six independent modules, no `go.work`/`go.work.sum` anywhere, no `replace` in any
    `go.mod`. All 14 `github.com/dae-go/*` import sites are *intra*-module, so nothing breaks yet.
    But the module paths point at **real published repos** (the `dae-go` org, populated by
    `sync-go-packages.yml`), so an import of a sibling would resolve to the *published* copy from
    the network rather than the working tree — the worst kind of silent staleness. Also here:
    `libs/golang/crud-server/go.mod:5` requires `github.com/mattn/go-sqlite3 v1.14.28` that no
    code imports (`pkg/db/db.go` is an in-memory `map` behind a `sync.RWMutex`; no `database/sql`
    anywhere), and `libs/golang/process-monitor/go.sum` is a tracked **0-byte** file.
  - **Proposed fix.** Add a `go.work` with a `use` line per module; `go mod tidy` `crud-server`;
    untrack the empty `go.sum`. The `dae-go` module paths stay exactly as they are — the sync
    workflow requires them.
  - **Files.** new `go.work`, `libs/golang/crud-server/{go.mod,go.sum}`,
    `libs/golang/process-monitor/go.sum`.

- [x] **C10 — Git tracks its own build outputs, including the exact paths turbo declares as
  artifacts.**
  `likelihood: High` · `ease: Med` (needs owner sign-off on removals)
  - **Evidence.** `.gitignore:3` says `/dist/` — root-anchored — so **12 wheels/sdists under
    `*/dist/` are tracked**, while `turbo.json:12-15` declares `"outputs": ["dist/**", ".next/**"]`.
    Eight compiled Go binaries are tracked (`libs/golang/crud-server/bin/*` ≈43 MB,
    `libs/golang/maze-runner/bin/*` ≈4.8 MB, plus a stray `libs/golang/process-monitor/main`), and
    `turbo.json` does **not** list `bin/**` as an output, so turbo caches Go builds with zero
    recorded outputs — a cache hit restores nothing. Six `.keras`/`.h5` model weights are tracked
    with no `.gitattributes`/LFS. Four `.DS_Store` files and two
    `apps/next/maze-runner/.firebase/hosting.*.cache` files are tracked. Roughly 30 of 547 tracked
    files are regenerable artifacts. Bazel-era residue compounds it: ~10 per-project `.gitignore`
    files whose entire content is the line `BUILD`, while two empty `BUILD` files
    (`libs/python/anki-tools/BUILD`, `libs/python/neural-networks/market-analyzer/BUILD`) are
    tracked anyway.
  - **Proposed fix (D8 settled).** Change `/dist/` → `dist/`, add `bin/`, `.DS_Store`,
    `.firebase/`; add `bin/**` to `turbo.json` outputs; `git rm --cached` the wheels/sdists, Go
    binaries, `.DS_Store` files and firebase caches; delete the `BUILD` residue. **The six
    `.keras`/`.h5` model weights stay tracked** — Git LFS is a deferred decision, explicitly out
    of scope for this run.
  - **Files.** `.gitignore`, `turbo.json`, `libs/golang/*/bin/`, `libs/python/*/dist/`,
    the `.DS_Store`/`BUILD`/`.firebase` files.

- [x] **C11 — The lint tooling disagrees with itself and is configured nowhere.**
  `likelihood: Med` · `ease: Med`
  - **Evidence.** `libs/bash/build-tools/py-scripts/py-lint:18-23` does `pip install -q ruff` at
    run time and `ruff check .` with default rules and **no committed config** — while the errors
    the user is seeing come from `black` + `flake8` (the local hook's toolchain, versions 24.8.0 /
    7.3.0). `ruff` is not even installed on this machine. There is **no** `.flake8`, `setup.cfg`,
    `tox.ini`, `ruff.toml`, `.pylintrc`, `.editorconfig`, `.eslintrc*`, `eslint.config.*`, or
    `.prettierrc*` anywhere in the repo. The six Go shims run `"lint": "go vet ./... && go fmt
    ./..."` — `go fmt` **writes** files, so `turbo lint` mutates the tree instead of checking it.
    Five JS packages declare `"lint": "echo 'No lint configured'"`. Net: `turbo lint` lints zero
    JavaScript, rewrites Go sources, and runs an uninstalled Python linter under default rules.
  - **Proposed fix (D3 settled: ruff).** **`ruff` is canonical for this repo** — `ruff format`
    replaces black, `ruff check` replaces flake8 + isort. Commit a root ruff config, pin ruff as
    a declared dependency (never `pip install` it at run time), and point `py-lint` at the
    committed config. Add a root flat ESLint config + Prettier; change the Go shims to
    `test -z "$(gofmt -l .)"`; add `.editorconfig`. Migrating the tooling *outside* this repo to
    ruff is an explicit out-of-scope follow-up.
  - **Files.** new root tool configs, `libs/bash/build-tools/py-scripts/py-lint`,
    all six `libs/golang/*/package.json`, the JS packages' `package.json`.

- [x] **C12 — The `install` lifecycle hook makes `pnpm install` build one virtualenv per Python
  package and require a Go toolchain.**
  `likelihood: Med` · `ease: Med`
  - **Evidence.** All fifteen Python-bearing `package.json` files use `"install": "py-install"`
    (e.g. `libs/python/maze-runner/package.json:6`) — an npm lifecycle name, so pnpm fires it for
    every project on every install. Each invocation runs `python3 -m venv .venv`, `pip install
    poetry`, `poetry install`. Measured in this worktree: nine `.venv` directories, and the venv
    contents confirm the cost is real — 103–105 site-packages entries per venv, dominated by
    Poetry itself. Root `package.json:19` adds `"postinstall": "go install
    gotest.tools/gotestsum@latest"`, so a plain `pnpm install` silently requires Go and pulls an
    unpinned tool. The six Go shims then invoke it by the hardcoded machine-specific path
    `~/go/bin/gotestsum`.
  - **Proposed fix.** Rename the script off the `install` lifecycle name (e.g. `setup`), or move
    Python environment creation into the chosen strategy's single-lock install; pin `gotestsum`
    and invoke it off `PATH`.
  - **Files.** the fifteen Python `package.json` files, root `package.json`,
    `libs/bash/build-tools/py-scripts/`, the six `libs/golang/*/package.json`.

- [x] **C13 — Broken or dead imports inside individual Python modules (independent of packaging).**
  `likelihood: High` · `ease: Med`
  - **Evidence.** `apps/microservices/market-bots/controllers/base_trade_bot_RH.py:7` does
    `from src.utilities import RobinhoodCredentials` (used at `:20`) and
    `apps/microservices/market-bots/src/` **does not exist** — leftover from a standalone-repo
    layout. `libs/python/maze-runner/bin/solver.py:4` does `from . import Maze, Runner` while
    `bin/` has no `__init__.py` and the file is exposed as the `py-maze-runner` bin
    (`package.json:15`) — an unavoidable `ImportError` when run as a script. Python-2 implicit
    relative imports survive in `abstract-base-classes/src/shells/{MLP,MLP_vanilla}.py:1`
    (`from ANN import ANN_Shell`), both `open_ai_gym/classes/lunar_lander_v2.py:5`, and
    `libs/python/cli-tools/cli_tools/mass_img_resizer.py:1`. Three
    `web_crawlers/.../japanese/common_words_*.py` files import `helpers.jpod101_crawlers`, which
    resolves only when cwd is that directory — and **22 of 24 directories under `web_crawlers/`
    lack `__init__.py`**. Two modules shadow importable names outright:
    `web_crawlers/anki_scrapers/python/sys.py` and `.../python/matplotlib.py`.
  - **Proposed fix.** Convert to explicit relative imports, add the missing `__init__.py` files,
    rename the two shadowing modules, and restore or author the missing `market-bots` utilities
    module.
  - **Files.** listed inline above; full enumeration in Catalog B.

- [x] **C14 — `libs/python/pyto-widgets` is a fully manifested package containing no Python source.**
  `likelihood: Low` (an oddity, not a cause) · `ease: High`
  - **Evidence.** The directory holds only `.gitignore`, `package.json`, `pyproject.toml`
    (`name = "pytowidgets-lib-py"`, `package-mode = false`), `poetry.lock` (a stub), `README.md`,
    and a 0-byte `requirements.txt`. Zero `.py` files. It nonetheless gets a `.venv` built on
    every `pnpm install`.
  - **Proposed fix — RESOLVED at the code gate (D9): remove it.** The ask-at-build-time condition
    is **discharged**. The question was put to the user in round 2 and answered: the package is
    **dead, not content-pending**. `libs/python/pyto-widgets/` is deleted by subphase **2.8**,
    along with its uv workspace membership and lockfile entries. The builder must not re-ask.
    (Round-1 history, for the record: this shipped as an ask-at-build-time item, the ask never
    reached the human, and the package was kept on a dispatcher instruction — which also inverted
    the stated default of removing it when unanswered. `code-review.md` round 1 flagged that as a
    non-blocking process deviation; D9 closes it.)
  - **Files.** `libs/python/pyto-widgets/`.

---

## Catalog A — easy lint fixes

Mechanical, low-risk, no design decision required. The Python rows are the flake8/black findings
from `.artifacts/evidence-lint-sweep-08-12-26.md`; the Go and JS rows are new.

> **Observed with black + flake8; FIXED with ruff.** These counts are what the smart-lint sweep
> measured using the tools installed today. Per **D3 the fixer is `ruff`** — `ruff format` for the
> formatting rows, `ruff check --fix` for the style rows. The rule codes below (`E`, `W`, `F`)
> carry over unchanged because ruff reimplements the same pycodestyle/pyflakes checks, so the
> catalog stays valid as a worklist. Exact counts will shift slightly: ruff's formatter is not
> byte-identical to black, and line-length is whatever the root config sets. **Re-measure with
> ruff at the start of 2.6 rather than treating these numbers as targets.**

### Python — auto-fixable by formatter

| Fix | Count | Where |
|---|---|---|
| Formatter reformat (measured with `black`; performed with `ruff format`) | **73 files** would be reformatted, 25 already clean | repo-wide |
| Files the formatter **cannot** parse | 2 | see "real defects" below |

### Python — mechanical style (measured with flake8; fixed with `ruff check --fix`)

| Rule | Count | Notable clusters |
|---|---|---|
| `E722` bare `except:` | ~25 | `apps/flask/pokedex/main.py` ×2, `apps/flask/weather-fortcast/main.py`, `libs/python/maze-runner/bin/solver.py` ×5, and across `web-crawlers` (`ibm_c_docs`, `golang/packages_downloader`, `jlptsensei` ×2, `update_katakana`, `basic/smart_audio_jlpt_nrkt`, `ttsmp3_get_audio`, `particles_ttsmp3`, `jpod101_crawlers` ×3, `w3schools` ×2, `get_js`, `vim_rtorr`, `get_masterrussian_1000`, `cube_tutor`, `image_from_url`) |
| `E711` `== None` | 3 | `apps/flask/maze-runner/modules/maze.py:26,30`; `apps/flask/pokedex/main.py:60` |
| `E501` line too long | ~45 | biggest cluster `apps/microservices/market-bots/controllers/base_trade_bot_RH.py` ×17 |
| `F541` empty f-string | 7 | scattered |
| `W605` invalid escape sequence | 4 | `web-crawlers/.../golang/packages_downloader.py` ×3, `particles_list_188.py` |
| `E741` ambiguous name `l` | 3 | — |
| `E731` lambda assignment | 2 | both `open-ai-gym/.../env_builder.py` copies (the same file, twice) |
| `F841` unused local | 2 | `anki-tools/get_deck_info.py:26` (`deck_id`), `particles_ttsmp3.py:59` (`e`) |

### Python — real defects, NOT style (fix with care)

| Rule | Where |
|---|---|
| `E999` syntax error | `libs/python/neural-networks/abstract-base-classes/src/shells/MLP.py:3` — `class MLP_Shell(ANN_Shell)` missing the `:` |
| `E999` syntax error | `libs/python/web-crawlers/web_crawlers/site_scrapers/steam.py:13` — IndentationError |
| `F821` undefined name | `apps/flask/maze-runner/modules/maze.py:70` (`maze` ×2) |
| `F821` undefined name | `libs/python/neural-networks/digit-recognition/classes/MLP_tensorflow.py:12` (`l` ×2) |
| `F821` undefined name | `libs/python/web-crawlers/.../japanese/common_words_2000.py:24` (`idx`) |
| `F821` undefined name | `libs/python/web-crawlers/.../russian/get_masterrussian_1000.py:42` (`r`) |
| `F821` undefined name | `libs/python/web-crawlers/.../text_to_speech/advanced_google_TTS.py:78,81` (`word`, `file`) |
| `F821` undefined name | `libs/python/web-crawlers/.../text_to_speech/basic_google_TTS.py:78,81` (`word`, `file`) |

The two `E999` files cannot be auto-formatted — they block any formatter (black today, `ruff
format` after D3) on those paths, so 2.7 must fix them before 2.6's sweep can cover them.

### Go — mechanical

| Fix | Where |
|---|---|
| One-line `go` directive bump `1.22` → `1.24` (clears all 9 `go vet` errors) | `libs/golang/pythonify/go.mod:3` |
| Drop the orphan `require github.com/mattn/go-sqlite3 v1.14.28` and its `go.sum` lines (`go mod tidy`) | `libs/golang/crud-server/{go.mod:5,go.sum}` |
| Untrack the 0-byte `go.sum` | `libs/golang/process-monitor/go.sum` |
| `"lint": "go vet ./... && go fmt ./..."` → `go vet ./... && test -z "$(gofmt -l .)"` (stop mutating the tree during lint) | all six `libs/golang/*/package.json` |
| Add `"bin/**"` to build outputs (Go builds are currently cached with no outputs) | `turbo.json:12-15` — **lane 1** |

### Repo hygiene — mechanical

| Fix | Where |
|---|---|
| `/dist/` → `dist/` so nested build output is actually ignored | `.gitignore:3` |
| Add `bin/`, `.DS_Store`, `.firebase/` | `.gitignore` |
| Delete the dead bazel `WORKSPACE` and the Pants `/.pants.*` ignore line | `WORKSPACE`, `.gitignore:1-2` |
| Delete ~10 single-line `.gitignore` files containing only `BUILD`, and the two tracked 0-byte `BUILD` files | `libs/python/**`, `libs/golang/**` |
| Delete the dead nested workflows (`npm ci` in a pnpm repo; GitHub never runs them) | `apps/next/maze-runner/.github/workflows/` |
| Delete the broken helper containing literal `${{ secrets.PAT }}` bash | `libs/bash/github-actions/build-maze-runner.sh` |
| Pin `turbo` (currently `"latest"`) | `package.json:22` |
| Fill the two 0-byte READMEs the generated tree links as projects | `libs/bash/github-actions/README.md`, `templates/next-js/README.md` |

---

## Catalog B — every package-import problem site

### B1. Python — path injection (the shared-library workaround)

| Site | Import |
|---|---|
| `apps/flask/maze-runner/main.py:6-7` | `sys.path.insert(0, …"../../../libs/python")` then `from flask_utils.port_finder import find_available_port` |
| `apps/flask/pokedex/main.py:6-7` | identical |
| `apps/flask/weather-fortcast/main.py:6-7` | identical |

These are the only three `sys.path` sites in the repo. Each is followed by the `E402`
module-level-import-not-at-top cluster flake8 reports (6, 5, and 4 occurrences respectively) —
those `E402`s are a *symptom* of the hack, not an independent style problem, and they disappear
when C3 is fixed.

### B2. Python — imports of things that do not exist

| Site | Import | Why it fails |
|---|---|---|
| `libs/python/maze-runner/__init__.py:1` | `from src import *` | no `src/` directory (code was renamed to `maze_runner/`) |
| `libs/python/maze-runner/bin/solver.py:4` | `from . import Maze, Runner` | `bin/` has no `__init__.py`; the file is the `py-maze-runner` console entry point |
| `apps/microservices/market-bots/controllers/base_trade_bot_RH.py:7` | `from src.utilities import RobinhoodCredentials` | no `src/` in the app |
| `libs/python/neural-networks/digit-recognition/classes/MLP_tensorflow.py:7` | `from abstract_base_classes.ann_shell import ANN_Shell` | the dependency ships a module named `src`, and `ann_shell` exists under no name |
| `libs/python/neural-networks/open-ai-gym/open_ai_gym/classes/env_builder.py:5` | same | same |
| `libs/python/tensorflow/open-ai-gym/open_ai_gym/classes/env_builder.py:5` | same | same, **plus** its path dependency `{path = "../abstract-base-classes"}` points at a directory that does not exist |

### B3. Python — implicit relative / cwd-dependent imports

| Site | Import |
|---|---|
| `libs/python/neural-networks/abstract-base-classes/src/shells/MLP.py:1` | `from ANN import ANN_Shell` (Python-2 implicit relative) |
| `libs/python/neural-networks/abstract-base-classes/src/shells/MLP_vanilla.py:1` | same |
| `libs/python/neural-networks/open-ai-gym/open_ai_gym/classes/lunar_lander_v2.py:5` | `from env_builder import EnvBuilder` |
| `libs/python/tensorflow/open-ai-gym/open_ai_gym/classes/lunar_lander_v2.py:5` | same |
| `libs/python/cli-tools/cli_tools/mass_img_resizer.py:1` | `from img_resizer import resize` |
| `libs/python/web-crawlers/.../japanese/common_words_1000.py:1` | `from helpers.jpod101_crawlers import …` |
| `libs/python/web-crawlers/.../japanese/common_words_2000.py:1` | same |
| `libs/python/web-crawlers/.../japanese/particles_jp101.py:1` | same |

Plus: 22 of 24 directories under `libs/python/web-crawlers/web_crawlers/` have no `__init__.py`;
`libs/python/maze-runner/maze_runner/` has none despite its manifest declaring the package; and
`libs/python/web-crawlers/web_crawlers/anki_scrapers/python/{sys.py,matplotlib.py}` shadow
importable names if that directory reaches `sys.path[0]`.

### B4. Python — undeclared third-party imports (per package)

| Package | Imported but undeclared |
|---|---|
| `libs/python/web-crawlers` | `requests`, `bs4`, `selenium`, `webdriver_manager`, `google_speech`, `retrying` (~40 modules) |
| `libs/python/anki-tools` | `anki` (`anki_tools/get_deck_info.py:3`), `requests` (`mp3_filename_update.py:1`) |
| `libs/python/cli-tools` | `Pillow` — `from PIL import Image` in `img_resizer.py:1`, `mass_re_rez.py:1`, `re_rez.py:1` |
| `libs/python/neural-networks/digit-recognition` | `tensorflow`, `numpy`, `scikit-learn`, `abstract_base_classes` |
| `libs/python/neural-networks/market-analyzer` | `tensorflow`, `scikit-learn`, `matplotlib` (`classes/analyzer.py:4-9`) |
| `apps/flask/{maze-runner,pokedex,weather-fortcast}` | the local `flask_utils` library; and for `maze-runner` specifically, **all ten** of its `requirements.txt` entries, because its `pyproject.toml` wins the install branch |

Declared-but-unimported (dead weight): `numpy` in `apps/microservices/market-bots/requirements.txt:4`;
most of `market-analyzer/requirements.txt` (a machine freeze — `pytest`, `pre-commit`,
`virtualenv`, `isort`, `nodeenv`, `py`, `robin-stocks`, `pyotp`, `vaderSentiment`, `cryptography`,
`oauthlib`).

Flake8's `F401` unused-import list — `apps/flask/maze-runner/main.py:2` (`requests`),
`apps/flask/pokedex/main.py:10` (`json`), `libs/python/anki-tools/anki_tools/mp3_filename_update.py:1`,
`libs/python/maze-runner/bin/solver.py:2` (`re`),
`digit-recognition/classes/MLP_tensorflow.py:1`, `market-analyzer/classes/analyzer.py:2-9` (×6),
`market-analyzer/classes/gpt.py:1,3`, the `web-crawlers` `F401`/`F811` cluster (11 files), and the
selenium `F401` cluster (4 files) — is catalogued in full in
`.artifacts/evidence-lint-sweep-08-12-26.md`.

### B5. JavaScript — unresolvable specifiers

| Site | Import | Why it fails |
|---|---|---|
| `libs/javascript/react/maze-runner/src/build.js:1` | `from 'react'` | `react` not declared — the package declares **no dependencies at all** |
| `libs/javascript/react/maze-runner/src/build.js:2` | `from 'classnames'` | not declared |
| `libs/javascript/react/maze-runner/src/build.js:4,5,6` | `"components/maze"`, `"components/runner"`, `"components/header"` | no `components/` dir and no `jsconfig.json` `baseUrl` |
| `libs/javascript/react/maze-runner/src/build.js:8,9` | `'styles/layout.module.scss'`, `'styles/global.module.scss'` | no `styles/` dir; no sass toolchain declared |
| `libs/javascript/react/maze-runner/src/index.js:1,2,3,4,6` | same alias pattern | same |
| `libs/javascript/react/maze-runner/src/index.js:7` | `from "next/link"` | `next` not declared |
| `libs/javascript/react/maze-runner/src/randomizer.js:1-7` | same alias pattern | same |
| `libs/javascript/react/quote-builder/src/index.js:2` | `from './components/router.js'` | no `src/components/`; the file is `src/router.js` |
| `libs/javascript/react/quote-builder/src/pages.js:1` | `from "components/input"` | should be `./input`; no `jsconfig.json` |
| `libs/javascript/react/quest/modules/list-item.js:1` | `from '../anime/lib/anime.es.js'` | no `anime/` dir; sibling modules correctly use `from 'animejs'` |
| `libs/javascript/node/maze-runner/src/quick-solver.js:1-2` | `require("fs")` and `import { QuickSolver } from "."` **in one file** | invalid under either module system |
| `libs/javascript/node/maze-runner/src/quick-solver.js:3,4` | `from "../lib/maze"`, `from "../lib/runner"` | no `lib/` dir; the files are `src/maze.js`, `src/runner.js` |
| `libs/javascript/node/maze-runner/src/runner.js:1` | `require("./node")` beside ESM siblings | no `"type": "module"` in the package |
| `libs/javascript/node/build-scripts/src/*.js:1-2` | ESM `import fs from 'fs'` | no `"type": "module"`, no build step |

Missing declared dependency: `libs/javascript/react/quote-builder` runs `react-scripts build`
without `react-dom`.

**All of the above sit in packages the workspace cannot see (C1), so none of them is installed,
linted, or built today.** Fix C1 first or these findings cannot even be reproduced.

### B6. Go — imports

Zero true cross-module imports exist. All 14 `github.com/dae-go/*` import sites are intra-module
and resolve from the local module root. The import-adjacent problems are: the `pythonify`
language-version mismatch (C8), the absent `go.work` that makes any *future* cross-module import
fetch from the network (C9), and the orphan `go-sqlite3` require that no code imports (C9).

---

## Package-management strategy candidates

**This was what the review gate judged, and it chose S3.** This whole section is retained
**unchanged, as the record of what was weighed** — it is not a live question. The reference the
user likes is `/home/icarus64/repos/money-makers/triple-m`; the caveat is "not everything can be
that nice." Below: what actually makes triple-m nice, what daedalus-mono has that triple-m never
had to solve, and the four options that were compared.

### What triple-m actually does (verified from its manifests)

- **One workspace definition per language, flat and shallow.** `pnpm-workspace.yaml` is 8 lines
  (`apps/*`, `services/*`, `admins/*`, `packages/{scripts,node,python,django}/*`) — **depth capped
  at 2**, which is exactly the property daedalus-mono's globs violate.
- **One `packageManager` pin (`pnpm@9.15.4`) and one root `pnpm-lock.yaml`**; CI uses
  `pnpm install --frozen-lockfile`.
- **`package.json` as a universal task shim for non-JS services.**
  `services/django-api/package.json` declares `"build": "django-build ."`, `"test": "python
  manage.py test"`, `"install:dev": "pip install -r requirements.txt"`, and a `postinstall` that
  bootstraps the venv. **daedalus-mono already has this exact mechanism** in
  `libs/bash/build-tools` — it is the one part of the design that is already right.
- **The shim scripts are themselves a workspace package** (`packages/scripts`, 9 `bin` entries)
  consumed as `"pkg.scripts": "workspace:*"` — one place to fix a dev-server incantation. Again,
  daedalus-mono's `lib.bash.build-tools` is the same idea; it is the only real `workspace:*` edge
  in the whole repo.
- **Uniform script names are the entire contract**: every member defines a subset of
  `dev/build/lint/type-check/test/clean/health-check`, and `turbo.json` declares exactly those.
- **`workspace:*` for every internal dependency**, so turbo's `dependsOn: ["^build"]` derives
  build order from `package.json` alone.
- **One Python import root, one tool-config file.** Root `pyproject.toml` carries **only**
  `[tool.black]`, `[tool.isort]`, `[tool.pytest.ini_options]` — **no `[project]`, no
  `[build-system]`**. The backend is one importable tree (`packages/__init__.py` +
  `packages/django/__init__.py`) reached by a single `sys.path.insert(0, str(repo_root))` in
  `manage.py:9`, and `flake8` gets its own root `.flake8` because it cannot read `pyproject.toml`.
- **A two-tier root script vocabulary** — `lint` → `lint:node` + `lint:python`, plus `:apps`,
  `:admins`, `:pkg` scopes — so CI calls the same names a human would.

### What triple-m never had to solve

Verified absences in the reference: **no Go** (zero `.go` files, no `go.mod`); **no git
submodules**; **no published packages** (all 20 node packages are `private: true`, versions
`0.0.0`, no changesets, no release workflow); **essentially no independent Python distributions**
— exactly one dir has a `[project]`/`[build-system]` table, and that one
(`services/fast-api/ai-connector`) has already drifted its `[tool.black]` line-length to 88 against
the root's 100 and fell out of CI entirely. It also has **no Python lockfile at all** (no
`uv.lock`, no `poetry.lock`, unpinned `>=` floors), and its root `requirements.txt` is stale —
CI installs `services/django-api/requirements.txt` instead. Its `turbo.json` declares no `inputs`
and no `env`, which is safe only because there is exactly one build environment.

So: **triple-m's single-import-tree Python model is not transferable here**, because its
"packages" are Django apps inside one distribution sharing one dependency set — whereas
daedalus-mono's Python packages are real distributions with committed wheels, and its Go modules
are published to `dae-go/*`. What *is* transferable is every organising principle: one workspace
definition, shallow globs, uniform script names, the `package.json` shim, one lockfile per
language, shared root tool config.

### The four options

| | S1 · Repair in place | S2 · triple-m literal | **S3 · Three workspaces, one task runner** | S4 · Revive a polyglot build system |
|---|---|---|---|---|
| **JS** | fix pnpm globs, delete the npm array, one root lock | same | same | Bazel/Pants targets |
| **Python** | keep per-package venv + Poetry; declare deps properly | one root `pyproject`+`requirements`, one venv, import-by-path | **`uv` workspace: per-package `pyproject` kept, one root `.venv`, one `uv.lock`, internal deps via `[tool.uv.sources] workspace = true`** | hermetic per-target deps |
| **Go** | bump `pythonify` only | (no story) | `go.work` for local resolution; `dae-go` module paths untouched | `rules_go` |
| **Effort** | Low | Medium | Medium–High | Very high |
| **Risk** | Low | High | Medium | High |
| **Keeps `dae-go` sync working** | yes | **no** | yes | yes |
| **Keeps mirrored packages standalone** | yes | **no** | yes | yes |
| **Fixes N-venvs / no shared resolution** | no | yes | yes | yes |
| **New tool to install** | none | none | `uv` (**not currently installed**) | Bazel or Pants |

**S1 — Repair in place.** Fix C1's globs, declare the dependencies C2 names, give `flask_utils` a
manifest (C3), leave the per-package-venv + Poetry model alone. Cheapest, lowest risk, preserves
every publishing constraint, and it is a strict prerequisite of S3 and S4 anyway. What it does not
fix: nine virtualenvs each re-installing Poetry, no cross-package resolution, eight uncoordinated
`poetry.lock` files (seven of them empty), and the `install`-lifecycle cost (C12).

**S2 — triple-m literal.** One root `pyproject.toml` for tool config, one root `requirements.txt`,
one venv, Python reached by path from the repo root; single pnpm workspace; turbo over both.
Best day-to-day DX and it is the shape the user already likes. But it **breaks two hard
constraints**: the Python packages here are distributions that get built into `dist/` and mirrored
out, and collapsing them into one import tree removes the per-package manifests the mirroring
depends on. It also assumes one coherent dependency set, which is false here — `tensorflow` +
`gymnasium` ML packages, Flask apps, and pure-stdlib libraries in one environment, with declared
`requires-python` ranging from `^3.8` to an exact `3.11`. **Viable for the `apps/` half only.**

**S3 — Three per-language workspaces under one task runner. ← CHOSEN (D1).** Each language gets
the one workspace mechanism it actually has, and turbo stays the single entry point:
- *JS*: fix the pnpm globs; one root `pnpm-lock.yaml`; delete the npm `workspaces` array and the
  two nested lockfiles.
- *Python*: a root `[tool.uv.workspace] members = [...]` plus a root `[tool.ruff]`/`.flake8`;
  **each package keeps its own `pyproject.toml`** (so `cp -R` mirroring still works), internal
  dependencies declared via `[tool.uv.sources] <pkg> = { workspace = true }`; **one `.venv` at the
  root, one `uv.lock`**. Replaces nine venvs, eight stub locks, and the `pip install poetry`
  bootstrap with a single resolve.
- *Go*: add `go.work` with a `use` line per module for local resolution; the `dae-go` module paths
  and per-module `go.mod`s stay exactly as they are, so `sync-go-packages.yml` is unaffected.
- *Everything*: keep the `package.json`-shim pattern that already exists, adopt triple-m's uniform
  script names and two-tier root vocabulary (`lint` → `lint:node` + `lint:python` + `lint:go`).
This is the honest answer to "not everything can be that nice": one *pattern*, three *mechanisms*.
Cost: `uv` is a new dependency and is not installed on this machine (installing and pinning it is
part of 2.5); the ML packages' conflicting `requires-python` pins are reconciled by **D2 —
dedupe the tensorflow copy first, then unify the survivors on Python 3.11**.

**S4 — Revive a true polyglot build system.** The repo has residue from two prior attempts —
`WORKSPACE` (Bazel: rules_nodejs 4.4.6, rules_python 0.4.0, rules_go 0.29.0) and `/.pants.*` in
`.gitignore:1-2` — neither completed, neither documented. Genuinely correct for three languages
plus hermetic builds and remote caching, and the only option that models the real Go dependency
graph. Wildly disproportionate for a solo portfolio repo whose CI does not currently run a single
test. Listed because the user's own history shows two attempts, so it deserves an explicit
"no, and here's why" rather than silence.

**Outcome.** **S3 was chosen (D1).** Phase 1 of the syllabus (one workspace definition, dead
config deleted, root tool config added) would have been required under S1 and S4 too; Phases 2–5
below are written as concrete S3 work and carry no remaining branching.

---

## Phased subphases

Each block names its **file scope**, the pattern to follow, acceptance criteria, and its
**test oracle**. Per the diagnosis workflow, the default oracle for a fix lane is *the
reproduction*: fixed when the repro no longer triggers and nothing previously green went red.

### Phase 1: Single source of truth for the workspace (lane 1)

**1.1 — Fix the pnpm globs; delete the npm `workspaces` array**
- *File scope:* `pnpm-workspace.yaml`, `package.json`, `pnpm-lock.yaml`.
- *Pattern:* triple-m's `pnpm-workspace.yaml` — one flat glob list, no second definition anywhere.
- *Concrete work (S3, JS leg).* `pnpm-workspace.yaml` becomes the single workspace definition and
  gains the depth-3 coverage it lacks — at minimum `libs/javascript/*/*` and `libs/python/*/*`
  alongside the existing globs, so that all 10 `libs/javascript/**` packages, the four
  `libs/python/neural-networks/*`, and `libs/python/tensorflow/open-ai-gym` are matched. The
  `workspaces` array is **deleted** from `package.json` (pnpm never read it; leaving it is what
  created the illusion of correct config). Re-lock so `pnpm-lock.yaml` records every importer.
  **Also carries D7's workspace-level exclusion**: the two legacy CRA packages
  (`libs/javascript/react/{markdown-builder,quote-builder}`) are excluded here via a negation
  glob (`!libs/javascript/react/markdown-builder`, `!libs/javascript/react/quote-builder`) with a
  comment naming D7 as the reason. **Lane ownership:** `pnpm-workspace.yaml` is a lane-1 file, so
  the exclusion is written here even though it is motivated by lane 3's 3.3 — 3.3 owns only the
  package-level marking and the docs. This keeps every root-file edit in lane 1.
- *Acceptance:* `turbo run lint --dry=json` lists **33 packages — all 35 minus the two D7
  legacy exclusions** — including every remaining `lib.javascript.*`, the four
  `lib.python.neural-networks.*`, and `lib.python.tensorflow.open-ai-gym`; `pnpm-lock.yaml`'s
  `importers:` block matches that set exactly; the `workspaces` array is gone from
  `package.json`; `turbo` is pinned to an exact version. Baseline to beat: **21 packages, zero
  `lib.javascript.*`**. (The count drops again later — 2.3 deletes
  `lib.python.tensorflow.open-ai-gym` and C14 may remove `lib.python.pyto-widgets` — so assert
  against the *membership* rule, not a frozen number.)
- *Test oracle:* **existing suite** — the reproduction is the turbo dry-run package list quoted
  above; the fix is verified when that list is complete.

**1.2 — Delete the competing and dead build-system config** *(after: 1.1)*
- *File scope:* `WORKSPACE`, `.gitignore` (lines 1-2), the ~10 single-line `BUILD`-only
  `.gitignore` files, `libs/python/anki-tools/BUILD`,
  `libs/python/neural-networks/market-analyzer/BUILD`, the two nested `pnpm-lock.yaml` files,
  `apps/next/maze-runner/.github/`, `libs/bash/github-actions/build-maze-runner.sh`.
- *Pattern:* one build system, named in one place.
- *Acceptance:* exactly one workspace definition, one lockfile per language, and no file
  referencing Bazel or Pants remains. `git grep -l BUILD` returns nothing under `libs/`.
- *Test oracle:* **existing suite** — `pnpm install --frozen-lockfile` still resolves.

**1.3 — Root ruff config + shared tool / language-version config** *(after: 1.1)*
- *File scope:* new root `ruff.toml`, `.editorconfig`, `.python-version`, `.nvmrc`, root
  `eslint.config.js` + `.prettierrc`; `package.json` (`engines`).
- *Pattern:* triple-m's split — one root config per tool, ESLint as one shared flat config
  re-exported by children in two lines. **Diverging from triple-m deliberately on the Python
  side:** it uses black + isort + flake8 and therefore needs both a `pyproject.toml` block *and*
  a separate `.flake8` (flake8 cannot read TOML). **D3 picks `ruff` for this repo**, which
  collapses that into a single `ruff.toml` — strictly simpler than the reference.
- *Concrete work (D3 settled).* `ruff` is canonical: **`ruff format` replaces black**, and
  **`ruff check` replaces flake8 + isort**. Commit one root `ruff.toml` selecting at minimum the
  rule families this audit found live (`E`, `W`, `F`, plus `I` for import sorting) and setting an
  explicit `line-length` and `target-version` (`py311`, per D2). Ruff must be a **pinned, declared
  dependency** resolved through 2.5's uv workspace — never `pip install`ed at run time, which is
  what `py-lint` does today. `.python-version` = `3.11` (D2); `.nvmrc` = the Node major in use.
- *Acceptance:* one config per tool, at the root, with no per-package override except where a
  package genuinely differs; no linter runs on default rules any more; `ruff --version` resolves
  from the project environment rather than a machine PATH.
- *Out of scope, recorded follow-up:* this makes ruff canonical **for daedalus-mono only**.
  `~/.claude/hooks/smart-lint.sh`, `~/repos/agentic`, and `money-makers/triple-m` still run
  black + flake8 and are **not** migrated by this run. Practical consequence for every builder:
  **the local smart-lint hook will keep reporting black/flake8 findings on this repo for the whole
  run.** That is expected noise, not a gate — do not re-format to satisfy it, and do not treat its
  exit code as blocking for this plan's work.
- *Test oracle:* **new contract tests** — this subphase adds behaviour (a lint baseline). A
  contract test asserts each configured linter runs and reports against the committed config.

**1.4 — Untrack build outputs; drop the `dots-js` submodule** *(after: 1.1)*
- *File scope:* `.gitignore`, `turbo.json`, `libs/golang/*/bin/`,
  `libs/golang/process-monitor/main`, `libs/python/*/dist/`, the four `.DS_Store` files,
  `apps/next/maze-runner/.firebase/`, `.gitmodules`, `libs/javascript/node/dots-js`.
- *Pattern:* turbo's declared `outputs` and git's ignore list must agree — nothing turbo produces
  may be tracked.
- *Concrete work (D5 + D8 settled).*
  - **D5: remove `libs/javascript/node/dots-js` from `.gitmodules`** and drop the gitlink. It is
    an uninitialised, empty directory that nothing imports; it is not to be initialised. The
    generated README links it, so `create-mono-file-tree.sh`'s output changes on the next
    `update-readme.yml` run — expected, not a regression.
  - **D8: untrack the regenerable artifacts, keep the model weights.** `git rm --cached` the 12
    Python wheels/sdists under `*/dist/`, the 8 Go binaries under `libs/golang/*/bin/`, the stray
    `libs/golang/process-monitor/main`, the 4 `.DS_Store` files, and the 2
    `apps/next/maze-runner/.firebase/hosting.*.cache` files. **The six `.keras`/`.h5` model
    weights stay tracked** — moving them to Git LFS is deferred and explicitly out of scope.
- *Acceptance:* `/dist/`→`dist/`; `bin/`, `.DS_Store`, `.firebase/` added to `.gitignore`;
  `bin/**` added to `turbo.json` outputs; the artifacts above untracked; `.gitmodules` no longer
  mentions `dots-js`; the `.keras`/`.h5` files still tracked and unmodified.
- *Test oracle:* **existing suite** — after `turbo build`, `git status` is clean; `git ls-files`
  still lists every model weight.

### Phase 2: Python package management (lane 2)

*File scope for the whole lane:* `apps/flask/**`, `apps/microservices/**`, `libs/python/**`,
`libs/bash/build-tools/**`, `libs/bash/cli-tools/**`. Disjoint from lanes 1, 3, 4, 5.

**2.1 — One manifest per Python project, real dependencies declared** *(after: 1.1)*
- *File scope:* the eleven `*/pyproject.toml`, the five `*/requirements.txt`,
  `apps/flask/maze-runner/setup.py`.
- *Pattern:* triple-m's `services/fast-api/ai-connector/pyproject.toml` — a real `[project]` table
  with an explicit `dependencies` list.
- *Acceptance:* every project declares every third-party module it imports (Catalog B4 empty);
  no project carries two competing dependency manifests; the three 0-byte `requirements.txt` files
  and the `market-analyzer` freeze dump are gone; `apps/flask/maze-runner/setup.py` deleted.
  **Boundary:** this subphase settles *which* dependencies each project declares. It does **not**
  touch `requires-python` — unifying the interpreter on 3.11 is 2.5's job under D2, and must
  happen after 2.3's dedupe removes the package that pins `3.11` exactly.
- *Test oracle:* **the reproduction** — `python -c "import flask"` succeeds in the
  `apps/flask/maze-runner` environment after a clean install, and an import-check script passes
  for every package.

**2.2 — Make shared libs installable; remove the sys.path injection** *(after: 2.1)*
- *File scope:* `libs/python/flask_utils/`, `libs/python/flask-utils/`,
  `apps/flask/{maze-runner,pokedex,weather-fortcast}/{main.py,pyproject.toml}`.
- *Pattern:* a declared workspace/path dependency, exactly as
  `libs/python/neural-networks/open-ai-gym/pyproject.toml:13` already attempts.
- *Acceptance:* `flask_utils` has a manifest and is a declared dependency of all three apps; the
  three `sys.path.insert` lines are deleted; `libs/python/flask-utils/` is deleted; the `E402`
  clusters in the three `main.py` files clear as a side effect.
- *Test oracle:* **the reproduction** — each app imports `flask_utils.port_finder` with no path
  manipulation, and still does so after being copied out of the repo (mirroring constraint).

**2.3 — Dedupe the forked trees onto the canonical library** *(after: 2.1)*
- *File scope:* `libs/python/tensorflow/open-ai-gym/`,
  `libs/python/neural-networks/open-ai-gym/`, `apps/flask/maze-runner/{main.py,modules/}` and its
  manifest, `libs/python/maze-runner/maze_runner/`, `libs/bash/cli-tools/{src/py-scripts,bin}/`.
- *Pattern:* one implementation, one location, depended upon rather than copied.
- *Concrete work (D4 + D2 settled).*
  - **D4 — the library is canonical.** `apps/flask/maze-runner` declares a dependency on
    `lib.python.maze-runner` (as a uv workspace source, per 2.5) and imports `Maze`/`Runner`
    from it. **Its call sites are rewritten to the library's signature** — `build_new(height,
    width, …)`, i.e. the first two positional arguments swap versus the app's current
    `build_new(width, height, …)`; and the app's packed `build=[(10, 10), "h"]` becomes the
    library's `build=(10, 10), build_type="h"`. Then **delete `apps/flask/maze-runner/modules/`
    entirely.** Two app-only behaviours must be carried into the library rather than lost:
    `node.py`'s `add_visited()`, and `runner.py`'s `if`-vs-`elif` neighbour chain (a real
    behavioural difference, not a style one) — decide per-behaviour whether it is a fix or a
    regression, and record which, because `build-maze-runner.yml` mirrors the result downstream.
  - **D2 (first half) — `libs/python/tensorflow/open-ai-gym/` is deleted**, leaving
    `libs/python/neural-networks/open-ai-gym/`. The tensorflow copy is the one carrying the
    unresolvable `{path = "../abstract-base-classes"}` dependency and the `poetry.lock` that bakes
    the broken directory URL in, so deleting it removes a defect rather than merely a duplicate.
    Doing this **before** 2.5 is what makes the interpreter unification possible: the deleted copy
    is the package pinning `python = "3.11"` exactly.
  - Delete the two stale `py-scripts` copies under `libs/bash/cli-tools/{src/py-scripts,bin}/`,
    leaving `libs/bash/build-tools/py-scripts/` canonical.
- *Acceptance:* one `open-ai-gym` survives with a resolvable dependency; `apps/flask/maze-runner`
  has no `modules/` directory and imports the library; the two stale `py-scripts` copies are gone;
  no behaviour from the deleted app fork is silently lost.
- *Test oracle:* **new contract tests** — reconciling the forked `Maze`/`Runner` API is a
  behavioural change; contract tests written from the **library's** signature must pass for both
  the library and the Flask app, and must cover the two carried-over behaviours above.

**2.4 — Fix package identity — directory / distribution / import names** *(after: 2.3)*
- *File scope:* the surviving `*/pyproject.toml`, `libs/python/maze-runner/{__init__.py,bin/solver.py,maze_runner/}`,
  `libs/python/neural-networks/abstract-base-classes/`, the two hyphenated-level `__init__.py` files.
- *Pattern:* convention #3 — kebab-case project dir, snake_case import package nested inside,
  distribution name derived from the directory.
- *Acceptance:* no two distributions share a name; every `pyproject` name matches its directory;
  no `__init__.py` sits at a hyphenated level; `abstract-base-classes` ships
  `abstract_base_classes`, not `src`, and `ann_shell` resolves for all three consumers.
- *Test oracle:* **the reproduction** — every consumer import in Catalog B2 resolves after install.

**2.5 — Adopt the uv workspace: one root `.venv`, one `uv.lock`** *(after: 2.1, 2.3)*
- *File scope:* a new root `pyproject.toml` (workspace declaration + shared config only), new root
  `uv.lock`, `libs/bash/build-tools/py-scripts/`, the fifteen Python `package.json` files, the
  eight `poetry.lock` files, every surviving `*/pyproject.toml` (`requires-python` only), and
  `apps/flask/*/runtime.txt`.
- *Pattern:* triple-m's `packages/scripts` shim package — the scripts are a workspace package, not
  copy-pasted bash. The resolver is **uv**, per D1/S3.
- *Concrete work (S3 Python leg + D2 second half).*
  - Root `pyproject.toml` declares `[tool.uv.workspace] members = [...]` listing every surviving
    Python project. **Each package keeps its own `pyproject.toml`** — that is what preserves the
    `cp -R` mirroring constraint (convention #7) and is the reason S2 was rejected.
  - Internal dependencies are declared via `[tool.uv.sources] <pkg> = { workspace = true }` —
    this is the mechanism that replaces C3's `sys.path` hack and 2.2's path dependency.
  - **One `.venv` at the repo root and one `uv.lock`**, replacing nine per-package venvs and the
    eight `poetry.lock` files (seven of which are `package = []` stubs). Delete every
    `poetry.lock`; Poetry leaves the repo entirely.
  - **D2 (second half) — unify the interpreter on Python 3.11.** With the exact-`3.11` pin removed
    by 2.3, set `requires-python` consistently to `>=3.11` across the surviving projects, set
    `.python-version` to `3.11` (1.3), and **delete the three `apps/flask/*/runtime.txt` files**
    that declare `python-3.8.0` — they are stale Heroku pins contradicting every manifest.
  - **C12 — get off the `install` lifecycle name.** Rename the per-package `"install":
    "py-install"` script to something outside npm's lifecycle (e.g. `"setup"`) so `pnpm install`
    stops building venvs per package, and pin `gotestsum` rather than `go install …@latest` in
    root `postinstall`, so a plain install no longer silently requires a Go toolchain.
  - `ruff` is pinned here as a workspace dev dependency, satisfying 1.3.
- *Acceptance:* exactly one Python lockfile, and it actually locks (no `package = []` stubs, no
  mixed lock-version); exactly one `.venv`, at the root; no `poetry.lock` and no `runtime.txt`
  remains; `pnpm install` no longer creates virtualenvs or requires Go.
- *Test oracle:* **the reproduction** — fresh clone → install → `import` succeeds for every
  package (including `import flask` in `apps/flask/maze-runner`, the original repro), and the
  install does not require a Go toolchain.

**2.6 — Python mechanical lint sweep with `ruff`** *(after: 2.4, 2.7)*
- *File scope:* every `.py` file under the lane's scope.
- *Pattern:* the committed linter config from 1.3; no rule may be silenced to make a file pass.
- *Acceptance:* Catalog A's Python style table is empty; `ruff format --check` reports 0 files
  needing reformatting and `ruff check` exits 0 against the committed root config (D3) — black
  and flake8 are no longer the oracle for this repo.
- *Test oracle:* **existing suite** — `ruff check` and `ruff format --check` exit 0 repo-wide.

**2.7 — Real Python defects: F821 undefined names, E999 syntax errors** *(after: 2.4)*
- *File scope:* the ten files named in Catalog A's "real defects" table, plus
  `apps/microservices/market-bots/controllers/base_trade_bot_RH.py` and the modules in Catalog B3.
- *Pattern:* fix the logic, never silence the rule.
- *Acceptance:* both `E999` files parse; every `F821` resolves to a real binding; the
  `RobinhoodCredentials` provider exists; `web_crawlers` subpackages have `__init__.py`; the two
  stdlib-shadowing modules are renamed.
- *Test oracle:* **new contract tests** — each `F821` site is a real bug whose corrected behaviour
  needs a test written from the intended contract, not from the current code.

**2.8 — Remove `libs/python/pyto-widgets` (C14 resolved: dead, not pending)** *(after: 2.5)*
- *File scope:* `libs/python/pyto-widgets/` (deleted), the root `pyproject.toml`
  (`[tool.uv.workspace] members`), `uv.lock`, `pnpm-lock.yaml`.
- *Why this exists.* C14 shipped as an **ask-at-build-time** item and the ask never reached the
  human — the lane-2 builder kept the package on a dispatcher instruction, which also inverted
  the plan's stated default (remove if unanswered). `code-review.md` round 1 raised this as a
  non-blocking process deviation; the question has now been put to the user and **answered:
  the package is dead, not pending. Remove it.** The ask-at-build-time condition is discharged —
  the builder must NOT re-ask.
- *Pattern:* 2.3's deletions — remove the directory, then remove every reference to it from the
  workspace declarations and regenerate the locks rather than hand-editing them.
- *Concrete work.* Delete `libs/python/pyto-widgets/` (it contains zero `.py` files — only
  `.gitignore`, `package.json`, `pyproject.toml`, a stub `poetry.lock`, `README.md`, and a 0-byte
  `requirements.txt`). Drop it from `[tool.uv.workspace] members` in the root `pyproject.toml`,
  then regenerate `uv.lock`; drop its `pnpm-lock.yaml` importer entry by re-running the pnpm
  install rather than editing the lockfile by hand.
- **Lane-boundary exception, deliberate and recorded.** `pnpm-lock.yaml` is otherwise a lane-1
  file (1.1). Removing a workspace member necessarily regenerates its importer entry, so 2.8
  touches it. This is safe *only* because lanes 1, 3 and 4 have already completed and there is no
  concurrent writer — it is a documented exception to the disjoint-scope rule, not a precedent.
  The change to `pnpm-lock.yaml` must be a pure regeneration artifact: no hand edits, and no other
  root file touched.
- *Acceptance:* `libs/python/pyto-widgets/` no longer exists; `uv sync` resolves **13** Python
  workspace members (down from 14) with no unresolved references; `pnpm install
  --frozen-lockfile` succeeds; `libs/bash/build-tools/import-check` passes for all 13 remaining
  members; `turbo run lint` and `turbo run build` stay green with the package absent from the
  graph; `git status --porcelain` is clean afterwards.
- *Test oracle:* **existing suite** — the import-check script and the turbo build/lint runs from
  6.1, re-run with 13 members.

### Phase 3: JavaScript package management (lane 3)

*File scope for the whole lane:* `libs/javascript/**`, `apps/next/**`. Disjoint from all other lanes.
**No lane-3 subphase may edit `package.json`, `pnpm-workspace.yaml`, or `turbo.json` at the root** —
those belong to 1.1.

**3.1 — Admit `libs/javascript/**` to the workspace and declare its deps** *(after: 1.1)*
- *File scope:* the ten `libs/javascript/*/*/package.json`.
- *Pattern:* `libs/javascript/react/labyrinth/package.json` — the one library package that declares
  its full dependency set correctly.
- *Acceptance:* the eight non-legacy packages appear in `pnpm-lock.yaml` importers with
  `node_modules` populated (the two CRA packages are deliberately excluded per D7 — see 3.3);
  `libs/javascript/react/maze-runner` declares `react`/`next`/`classnames`/`sass`;
  **every JS package carries `"private": true`** (D6 settled: nothing is published — drop
  `quote-builder`'s explicit `"private": false` and `resume-builder`'s `prepublishOnly`).
- *Test oracle:* **existing suite** — `pnpm install --frozen-lockfile` links every package and
  `turbo build` reaches them.

**3.2 — Repair unresolvable specifiers and mixed module systems** *(after: 3.1)*
- *File scope:* every file listed in Catalog B5.
- *Pattern:* `libs/javascript/react/quest/modules/catapult.js:1` (`import anime from 'animejs'`) —
  the correct form its sibling `list-item.js` got wrong.
- *Acceptance:* every specifier in Catalog B5 resolves; the three `libs/javascript/node/*`
  packages declare `"type": "module"` with no `require()` left; `quick-solver.js` points at
  `./maze.js`/`./runner.js`.
- *Test oracle:* **existing suite** — a resolution check (ESLint `import/no-unresolved`, or `node
  --check` plus a build) passes for every JS package.

**3.3 — Mark the CRA / React 16 packages legacy and exclude them** *(after: 3.1)*
- *File scope:* `libs/javascript/react/{markdown-builder,quote-builder}/package.json` and sources.
- *Pattern:* the repo's own React 18 + Next 12 packages.
- *Acceptance:* D7 settled — **marked legacy, not migrated**: `markdown-builder` and
  `quote-builder` are excluded from the workspace **deliberately** (explicit exclusion or
  documented omission from the globs, not glob accident), each gains a README note naming them
  legacy CRA/React-16 packages kept as-is, and neither is touched by 3.2/3.4.
- *Test oracle:* **existing suite** — whichever path is chosen builds.

**3.4 — JavaScript lint baseline** *(after: 3.1, 1.3)*
- *File scope:* the ten `libs/javascript/*/*/package.json` plus `apps/next/maze-runner/package.json`.
- *Pattern:* triple-m's `apps/bard-ai/eslint.config.js` — a two-line re-export of one shared base.
- *Acceptance:* no `"lint": "echo 'No lint configured'"` remains; `turbo lint` actually parses
  JavaScript; `console.info` calls survive the lint rules (convention #9).
- *Test oracle:* **new contract tests** — a lint baseline is new behaviour; assert the rule set is
  applied and that a deliberately bad file fails.

### Phase 4: Go modules (lane 4)

*File scope for the whole lane:* `libs/golang/**` and a new root `go.work`. The `turbo.json`
outputs change motivated here lives in 1.4.

**4.1 — Raise `pythonify`'s `go` directive**
- *File scope:* `libs/golang/pythonify/go.mod`.
- *Pattern:* its siblings `complex-dsa`/`process-monitor`/`err`, already at `1.24.2`.
- *Acceptance:* `go vet ./...` exits 0 from `libs/golang/pythonify`.
- *Test oracle:* **the reproduction** — the nine quoted vet errors are gone.
- **Correction (round 2).** This block originally read "…and `go test ./...` still passes". That
  was an unverified planning assumption: `pkg/abf`'s zip tests fail on **unmodified `main`**, so
  `go test ./...` was never green in `pythonify` and 4.1 could not have kept it so. The vet fix is
  still correct and complete as written; the pre-existing test failure is now owned by **4.4**,
  which is what makes the full-suite claim true rather than aspirational.

**4.2 — `go.work` for local resolution; prune the orphan require and stray sum** *(after: 4.1)*
- *File scope:* new `go.work`, `libs/golang/crud-server/{go.mod,go.sum}`,
  `libs/golang/process-monitor/go.sum`.
- *Pattern:* the `dae-go` publishing contract (convention #6) — module paths are **not** to change.
- *Acceptance:* `go.work` `use`s all six modules; `crud-server` no longer requires
  `go-sqlite3`; the 0-byte `go.sum` is untracked; `go build ./...` succeeds in every module both
  with and without the workspace file (the standalone-mirror constraint).
- *Test oracle:* **existing suite** — `go vet ./...` and `go test ./...` pass in all six modules.

**4.3 — Fix the Go task shims** *(after: 4.1)*
- *File scope:* the six `libs/golang/*/package.json`.
- *Pattern:* a lint script that reports rather than writes.
- *Acceptance:* `lint` is `go vet ./... && test -z "$(gofmt -l .)"`; `gotestsum` is invoked off
  `PATH` at a pinned version rather than via the hardcoded `~/go/bin/` path; `turbo lint` leaves
  the working tree unmodified.
- *Test oracle:* **existing suite** — `turbo lint` followed by `git status --porcelain` is empty.

**4.4 — Fix the `pkg/abf` zip type-identity test failures** *(after: 4.1)*
- *File scope:* `libs/golang/pythonify/pkg/abf/` — the zip implementation and/or
  `pkg/abf/utils_test.go`. Nothing outside `libs/golang/pythonify/pkg/abf/`.
- *Why this exists.* `TestZip`, `TestZipNoArgs` and `TestZipLargeSlices` fail on **unmodified
  `main`** — they predate this run and are not a regression from lanes 1–5. They were carried as a
  known-issue allowance while the run's Go work was scoped to vet/module hygiene; **this subphase
  removes that allowance**, so `pythonify` is held to a fully green suite like every other module.
- *The defect.* The failures are a **type-identity** mismatch, not a value mismatch:
  `reflect.DeepEqual` compares the zipper's **named return type** against plain `[]S` literals in
  the test expectations. `reflect.DeepEqual` treats a named type and its underlying type as
  unequal even when the elements are identical, so the assertions fail while the data is right.
- *Concrete work.* The builder must first **determine the intended contract** by reading the
  package — this plan deliberately does not pick for it, because the evidence supports two
  defensible readings and only the code can settle which the API meant:
  - (a) the exported surface is meant to be the **named type**, in which case the *tests* are
    wrong and must construct expectations of that named type (or compare element-wise); or
  - (b) the named type is incidental and `zip` should return a plain `[]S`, in which case the
    *implementation* is wrong.
  **Fix the code XOR the tests — never both, and never by loosening the assertion to hide the
  mismatch** (no `assert`-style deep-equal shims, no comparing formatted strings). Whichever way
  it goes, record the reasoning in the exit report, since this changes a published API surface:
  `pythonify` is mirrored to `github.com/dae-go/pythonify` by `sync-go-packages.yml`, so option
  (b) is a breaking change for any external consumer and must be called out as such.
- *Conventions:* CLAUDE.md's Go rules bind here — concrete types, no `interface{}`, table-driven
  tests, and **delete the old code when replacing it** rather than keeping both paths.
- *Acceptance:* `go test ./...` is **fully green** in `libs/golang/pythonify`, with no test
  skipped, no `t.Skip`, and no assertion weakened to pass; `go vet ./...` and `go build ./...`
  stay clean; the module still builds standalone with `go.work` moved aside (the mirror
  constraint verified in 4.2).
- *Test oracle:* **the reproduction** — the three named tests fail before and pass after. If the
  builder takes option (a), the corrected expectations are the oracle; if option (b), the existing
  tests become the oracle unchanged.

### Phase 5: Verification in CI, and documentation (lane 5)

*File scope for the whole lane:* `.github/**`, `README.md`, `/docs/**`.

**5.1 — Add a real lint/build/test workflow per language** *(after: 1.1)*
- *File scope:* new files under `.github/workflows/`.
- *Pattern:* triple-m's split — `lint-frontend.yml` (setup-node + `pnpm/action-setup` +
  `pnpm install --frozen-lockfile` + `pnpm lint:node`) and `lint-backend.yml` (setup-python +
  the linters only, since linters do not import the code).
- *Acceptance:* a PR that reintroduces C1 (shallow globs) or C8 (stale `go` directive) fails CI.
- *Test oracle:* **new contract tests** — CI verification is new behaviour; prove it by pushing a
  branch that reintroduces one known defect and confirming red.

**5.2 — Align the Go CI toolchain and the two sync workflows** *(after: 1.1)*
- *File scope:* `.github/workflows/{sync-go-packages.yml,build-maze-runner.yml}`.
- *Acceptance:* `setup-go` is at least the highest module directive (currently `1.21` vs modules
  at `1.24.2`); `build-maze-runner.yml` either copies `libs/golang/maze-runner` too or documents
  why not; the mirrors still produce standalone-buildable repos after Phases 2–4.
- *Test oracle:* **existing suite** — `workflow_dispatch` run succeeds and the mirrored repos build.

**5.3 — Docs mirror + symlinks per `doc-format`; dereference the mirror copies** *(after: 1.1)*
**REWORKED (round 2) — unticked and redispatched.** Round 1 shipped four good flat files under
`/docs` but built **no mirror structure and converted zero READMEs to symlinks**, which
`code-review.md` round 1 raised as its single **blocking** finding (`impl-wrong`). The content
that shipped is correct and is kept — this rework adds the structure that was skipped, plus the
workflow change that makes the structure safe.

- *File scope (grown):* `docs/**` (including the new `docs/apps/<project>/` and
  `docs/libs/<pkg>/` mirror); every project-level `README.md` being converted to a symlink;
  `.github/workflows/build-maze-runner.yml`; `.github/workflows/sync-go-packages.yml`; and
  `.github/workflows/update-readme.yml` **if** the generated tree needs to handle symlinks.
- *Pattern:* the `doc-format` rule, followed **fully** rather than partially — mirror the source
  layout under the docs root, edit only the file under `/docs`, and make every nested doc path a
  symlink to its root counterpart. Never a copy; if the same content would exist twice, one of
  them must become a symlink.
- *Concrete work.*
  1. **Build the mirror.** Move each project's `README.md` content to its `/docs` counterpart —
     `apps/flask/pokedex/README.md` → `docs/apps/flask/pokedex/README.md`,
     `libs/golang/err/README.md` → `docs/libs/golang/err/README.md`, and so on. Create **only the
     structure the code justifies** — no empty scaffolding for directories that have no docs. The
     four existing top-level files (`README.md`, `installation.md`, `development.md`,
     `package-management-strategy.md`) stay where they are as the root-level/global docs.
  2. **Convert every project `README.md` to a symlink** pointing at its `/docs` counterpart.
     Verifiable with `test -L`, which currently finds none.
  3. **Dereference the mirror copies — the enabling change.** This is what makes step 2 safe.
     `build-maze-runner.yml` uses `cp -R` and `sync-go-packages.yml` uses `rsync -av --delete`;
     both would copy the **symlinks themselves** into the mirrored repos, where the `/docs`
     targets do not exist — every mirrored package would ship a dangling README. Switch both to
     dereferencing copies (`cp -RL`, `rsync --copy-links`, or equivalent) so the mirrors receive
     **real files**. Without this change, doc-format and the mirroring convention (#7) are in
     direct conflict and one of them has to break.
  4. **Check the README generator.** `update-readme.yml` runs
     `libs/bash/github-actions/create-mono-file-tree.sh`, which links only directories containing
     a README. Confirm it still resolves projects correctly when those READMEs are symlinks, and
     fix it if not.
- *Acceptance:*
  - `docs/apps/**` and `docs/libs/**` mirror the real project layout, with no empty scaffolding.
  - **Every project-level `README.md` is a symlink** — `find apps libs -name README.md | xargs -r
    test -L` succeeds for all of them, and `git diff main...HEAD --summary` shows the mode/type
    changes (round 1 showed none).
  - No content exists in two places: each doc is a real file under `/docs` and a symlink elsewhere.
  - **Verified by inspecting a simulated mirror copy** — run the mirror command the workflow now
    uses (`cp -RL` / `rsync --copy-links`) into a scratch directory and confirm the copied
    package contains a **real, readable README file, not a dangling symlink**. This check is the
    point of the whole subphase; do not mark it done on the workflow diff alone.
  - The round-1 content bar still holds: a reader can install and run any package from the docs,
    with real per-language commands.
- *Test oracle:* **existing suite** — the `test -L` sweep, the simulated-mirror dereference check,
  and a fresh clone followed literally by the documented steps reaching a working state.

### Phase 6: Integration proof

**6.1 — Fresh-clone install → build → lint → import-check every package**
*(after: 2.5, 2.8, 3.1, 4.2, 4.4, 5.1, 5.3)*
- **UNTICKED (round 2) — must be re-run.** 6.1 passed in round 1 and its evidence is recorded in
  `code-review.md` ("Phase 6" verified clean). That proof no longer covers the tree: 2.8 removes a
  workspace member, 4.4 changes a Go package, and 5.3 converts every project `README.md` to a
  symlink. **An integration proof over a tree that has since changed is not a proof**, so the
  `after:` list above is extended and the box is cleared. Nothing about the round-1 run was wrong
  — it simply needs re-running once the three new subphases land.
- *File scope:* none (verification only); may add one script under `libs/bash/build-tools/`.
- *Acceptance:* from a clean clone: install succeeds without a Go toolchain being incidentally
  required; `turbo build` builds every package in the graph; `turbo lint` exits 0 and leaves the
  tree unmodified; an import-check imports every Python module and resolves every JS specifier;
  `git status` is clean. **Round-2 additions:** the import-check covers **13** Python workspace
  members (2.8); **`go test ./...` is green in all six Go modules**, `pythonify` included, with no
  known-issue allowance (4.4); and every project `README.md` is a symlink whose target resolves,
  with a simulated mirror copy yielding real files (5.3).
- *Test oracle:* **the reproduction** — all three reproductions in this report are gone.

---

## Risks, open questions, decision points

### Decisions settled at the gate (08-12-26, round 1)

All eight decision points were answered by the user at the pick gate; the answers below are
baked into the phase detail blocks and are the spec of record.

- **D1 = S3.** Three per-language workspaces — fixed pnpm globs (JS), a `uv` workspace with one
  root `.venv` + one `uv.lock` (Python), `go.work` (Go) — all under turbo via the existing
  `package.json` shim convention. Rationale accepted: only `uv` is net-new; pnpm is already
  pinned and `go.work` is a config file, not a tool; the three mechanisms share no integration
  surface. S4 (Bazel/Pants) declined as disproportionate; S2 declined because it breaks the
  `dae-go` sync and package-mirroring constraints.
- **Scope = everything.** All candidates C1–C14 picked; all six phases execute.
- **D2 = (c)+(a).** Dedupe the `tensorflow/open-ai-gym` copy first (2.3), then unify surviving
  projects on Python 3.11 (`requires-python >= 3.11`, root `.python-version`), deleting the three
  `apps/flask/*/runtime.txt` `python-3.8.0` pins (2.5).
- **D3 = ruff**, canonical for THIS repo: `ruff format` replaces black, `ruff check` replaces
  flake8+isort; root config committed; `py-lint` pins ruff. **Recorded follow-up OUTSIDE this
  run:** migrate `~/.claude/hooks/smart-lint.sh`, `~/repos/agentic`, and
  `~/repos/money-makers/triple-m` to ruff (verified: triple-m's pytest/vitest tests are
  unaffected — only lint config/commands change). Until then the local smart-lint hook keeps
  reporting black/flake8; builders must not fight it (see Risks).
- **D4 = the library is canonical.** `apps/flask/maze-runner` depends on
  `lib.python.maze-runner`; app call sites rewritten to the lib signature (`height, width`);
  `apps/flask/maze-runner/modules/` deleted (2.3).
- **D5 = remove `dots-js`** from `.gitmodules` (1.4).
- **D6 = `"private": true` on every JS package** — nothing is published (3.1).
- **D7 = legacy, not migrated** — `markdown-builder` + `quote-builder` deliberately excluded and
  documented (3.3).
- **D8 = untrack build artifacts** (wheels, Go binaries, `.DS_Store`, firebase caches) but
  **keep the `.keras`/`.h5` model weights tracked**; LFS is a deferred decision (1.4).
- **C14 note:** remove `libs/python/pyto-widgets` unless the user says content is pending — ask
  at build time before deleting. **→ Superseded by D9 below: the ask has been answered, remove it.**

### Decisions settled at the code gate (08-14-26, round 2)

`code-review.md` round 1 returned `rejected` / `impl-wrong` (1 blocking, 6 non-blocking) after the
build completed all 22 subphases. The user settled three further decisions; they are baked into
2.8, 4.4 and 5.3, and they are the reason Phase 6 must re-run.

- **D9 = remove `libs/python/pyto-widgets` (C14 closed).** The round-1 ask-at-build-time step
  never actually reached the human — the lane-2 builder kept the package on a dispatcher
  instruction, which also inverted the plan's stated default of removing it when unanswered. The
  question has now been put and answered: **the package is dead, not content-pending.** New
  subphase **2.8** deletes it and drops it from the uv workspace and the lockfiles. The
  ask-at-build-time condition is discharged; the builder must not re-ask.
- **D10 = fix the `pkg/abf` zip failures now, removing the known-issue allowance.**
  `TestZip`/`TestZipNoArgs`/`TestZipLargeSlices` fail on **unmodified `main`** — a pre-existing
  `reflect.DeepEqual` type-identity mismatch between the zipper's named return type and the
  tests' plain `[]S` literals, not a regression from this run. Rather than ship with `pythonify`
  excused from a green suite, new subphase **4.4** fixes it, with the builder determining from the
  code whether the named type or the plain slice is the intended contract and fixing code XOR
  tests accordingly. This also corrects 4.1, whose oracle asserted `go test ./...` "still passes"
  — it never did.
- **D11 = follow `doc-format` fully, and dereference the mirror copies to make that safe.**
  Round 1's flat four-file `/docs` is **not** accepted as a deviation; **5.3 is reworked and
  unticked**. The open question in `code-review.md` ("rework, or accept the deviation?") is
  answered as *rework*.
  **Rationale — the mirroring conflict, and why the workflow change is the enabling half.**
  `doc-format` requires every nested doc path to be a **symlink** into `/docs`. But this repo
  mirrors packages out to other repositories: `build-maze-runner.yml` uses `cp -R` and
  `sync-go-packages.yml` uses `rsync -av --delete`, **neither of which follows symlinks**. Applied
  naively, the symlink conversion would ship dangling READMEs into every mirrored repo, breaking
  convention #7 (mirrored packages must stay standalone) in order to satisfy `doc-format`. The two
  rules are only compatible if the mirrors **dereference** — hence 5.3 now also switches both
  workflows to `cp -RL` / `rsync --copy-links` (or equivalent), and requires proof by inspecting a
  simulated mirror copy rather than by reading the workflow diff. This is why the docs work and
  the CI work are one subphase and not two: neither half is correct without the other.

### Decision points as posed at the gate (record — all settled above)

- **D1 — Which strategy?** S1 (repair in place), S2 (triple-m literal), **S3** (three workspaces,
  one task runner), or S4 (polyglot build system). Phase 1 is required under all of S1/S3/S4;
  Phases 2–5 change shape with the answer. *No default has been chosen — this is the gate's
  primary question.*
- **D2 — If S3: how are the ML packages handled?** A single `uv` workspace needs one resolvable
  interpreter, but `libs/python/tensorflow/open-ai-gym/pyproject.toml:14` pins `python = "3.11"`
  exactly, `abstract-base-classes` says `<4.0`, and `libs/python/maze-runner` says `^3.8`. Options:
  (a) unify everything on 3.11 and delete the Heroku `runtime.txt` files that say `python-3.8.0`;
  (b) exclude the tensorflow/gymnasium packages from the shared lock and give them their own;
  (c) drop the duplicate tensorflow copy first (see D4) and unify the rest.
- **D3 — Which Python linter is canonical?** The shipped script runs `ruff` (uninstalled,
  unconfigured); the errors the user is seeing come from `black` + `flake8` (24.8.0 / 7.3.0).
  Picking `ruff` makes `py-lint` honest and is faster; picking `black`+`flake8` matches what
  currently reports and what triple-m uses. Cannot be both.
- **D4 — Which `maze-runner` is canonical?** `apps/flask/maze-runner/modules/` and
  `libs/python/maze-runner/maze_runner/` have **incompatible** `Maze.build_new` signatures (the
  first two positional parameters are swapped). Reconciling means picking one and rewriting the
  other's callers. Note `build-maze-runner.yml` mirrors both downstream, so the choice propagates.
  Related: does the six-copy `maze-runner` family across python/go/node/react/next/flask represent
  six deliberate ports, or drift to be consolidated?
- **D5 — `libs/javascript/node/dots-js`.** An uninitialised gitlink (`git submodule status` →
  `-9b2b2b87…`), an empty directory, imported by nothing, but linked by the generated README.
  Initialise it or remove it from `.gitmodules`.
- **D6 — Are any JS packages meant to be published?** Six omit `"private": true` and
  `quote-builder` sets `"private": false` explicitly, while `resume-builder` has a
  `prepublishOnly` script but no `main`/`module`/`exports`/`files`. Every non-JS package in the
  repo sets `private: true`.
- **D7 — The two CRA / React 16 packages** (`markdown-builder`, `quote-builder`, both on
  `react-scripts@2.1.1` from 2018): migrate to the repo's React 18 toolchain, or mark legacy and
  exclude deliberately?
- **D8 — Committed artifacts.** Removing ~30 tracked regenerable files (12 Python wheels/sdists,
  8 Go binaries, 6 model weights, 4 `.DS_Store`, 2 firebase caches) is a repo-history-visible
  change. The `.keras`/`.h5` model weights in particular may be intentional (there is no LFS
  config); confirm before deleting.

### Risks

- **Order dependency.** C7's JavaScript import failures cannot be *reproduced* until C1 is fixed,
  because the packages are not installed. Fixing C1 first will make CI go from silently green to
  loudly red — that is the point, but it should be expected, not treated as a regression.
- **Mirroring is load-bearing.** Any change that makes a `libs/golang/*` module resolvable only
  from inside the monorepo breaks `sync-go-packages.yml`; any change that removes a mirrored
  package's own manifest breaks `build-maze-runner.yml`. Both workflows push to *other* repos on
  merge to `main`.
- **`turbo` is unpinned** (`"turbo": "latest"`, resolving to 2.5.5 today), so the task graph can
  shift under the repo without any commit.
- **The `.venv` footprint is real** — `apps/microservices/market-bots/.venv` alone measures 302 MB
  on disk, one per Python package by design.
- **The hook mutates product files.** The local smart-lint hook runs `black --write` repo-wide on
  every file write, so any builder working this plan will see unrelated files change under it.
  Those pre-existing failures are this run's *subject*, not regressions.

### Unverified / could not confirm

- Whether `libs/python/pyto-widgets` is empty deliberately (C14).
- Whether the `dae-go` org repos are actively consumed by anything outside this monorepo — the
  sync workflow creates them, but no consumer was found.
- Whether the `.keras`/`.h5` weights are reproducible from the committed training code, or are the
  only copy.
- Nothing was installed or executed inside `/home/icarus64/repos/money-makers/triple-m`; all
  reference claims are read from its manifests.
- The `pnpm install` that produced the venv evidence was run by this run's `init-workspace` stage,
  not by this investigation; the import failure was independently reproduced against its result.

---

## Skill mapping

| Work | Skill / agent |
|---|---|
| This report, and every amendment to it | `planner` (diagnose module) — stays warm through the revision loop |
| Picking causes + strategy (D1–D8) | `review-plan` gate — the human decision, not the planner's |
| Phase 1 (root topology, lane 1) | `builder` → `coder`; serialized, must land before lanes 2/3/5 |
| Phase 2 (Python, lane 2) | `builder` → `coder` + `contract-tester` for 2.3 and 2.7 |
| Phase 3 (JavaScript, lane 3) | `builder` → `coder` + `contract-tester` for 3.4 |
| Phase 4 (Go, lane 4) | `builder` → `coder`; smallest lane, fully independent |
| Phase 5 (CI + docs, lane 5) | `builder` for the workflows; `document-local` for 5.3 (docs root is a local path) |
| Round-2 rework: 2.8 (lane 2), 4.4 (lane 4), 5.3 (lane 5) | `builder` redispatch per lane from the existing contracts; 4.4 pairs `coder` with `contract-tester` since it may change a published API |
| Phase 6 (integration proof) | `builder`'s own e2e verification, then `review-code` |
| Environment setup in each lane's worktree | `init-workspace` |
| Ship | `review-pr` → `push-pr` → `cleanup-merged` |
