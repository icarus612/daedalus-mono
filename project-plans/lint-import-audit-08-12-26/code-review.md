# code-review

## Round 1 — 08-14-26

```
verdict: rejected
next: impl-wrong
blocking: 1
non-blocking: 6
```

Reviewed independently (fresh, no conversation history) against
`project-plans/lint-import-audit-08-12-26/plan.md` and the real diff `main...HEAD` on
`bug/lint-import-audit`, worktree `/home/icarus64/repos/daedalus-mono/.workflows/lint-import-audit`.
Verification was delegated per-lane to five independent sub-reviews (one per plan lane: 1 root
workspace config, 2 Python, 3 JavaScript, 4 Go, 5+6 CI/docs/integration), each of which re-ran the
plan's own load-bearing commands rather than trusting commit messages. This report synthesizes
their findings.

### Findings

- [blocking] **5.3's doc-format requirement was not implemented.** The plan's own file scope for
  5.3 states docs go under `/docs`, "per the docs rule — the docs root is the single source of
  truth, with symlinks back into the tree" (plan.md:1171-1173), which is the project's global
  `doc-format` convention (mirror the source layout under `/docs`; every nested doc path — e.g.
  `apps/[project]/README.md` — is a **symlink** to its `/docs` counterpart, never a copy). What
  actually shipped: `/docs` contains 4 flat files (`README.md`, `installation.md`,
  `development.md`, `package-management-strategy.md`) with **no mirrored `docs/apps/**`/
  `docs/libs/**` structure**, and **zero README.md files in the repo were converted to symlinks**
  — verified with `find … -name README.md | xargs test -L` (no hits) and
  `git diff main...HEAD --summary` (no README mode/type changes on this branch). Content quality
  of the four files is otherwise good (real, verified per-language install commands), and the root
  `README.md` links prominently to `docs/README.md`, so the softer "reader can install from the
  README" acceptance bar is arguably met transitively — but the literal, explicitly-stated
  file-scope requirement (mirror + symlink) was skipped entirely, not partially done. Routed
  `impl-wrong` because the plan and the underlying doc-format rule are both correct and unambiguous
  here; lane 5's 5.3 simply didn't build the mirror/symlink structure.

- [non-blocking] **Lane 1, 1.2's literal acceptance criterion fails, but harmlessly.** The plan
  states "`git grep -l BUILD` returns nothing under `libs/`"; it currently returns 7 files
  (`libs/golang/crud-server/.gitignore`, `labyrinth`, `markdown-builder`, `quote-builder`,
  `python/anki-tools/.gitignore`, `neural-networks/market-analyzer/.gitignore`, plus one more).
  Verified byte-identical to `main` (`git diff main...HEAD` empty on each) — these are pre-existing
  corrupted `.gitignore` files where other content is glued to a literal `BUILD` string with no
  separating newline (e.g. `libs/golang/crud-server/.gitignore` = `.logBUILD`). The plan's own
  evidence section (plan.md:485-487) mischaracterized these as clean single-line `BUILD` files —
  a planning-side misread, not something lane 1 introduced or should have silently "fixed" beyond
  its stated scope. Worth a follow-up, not a rework.

- [non-blocking] **C14 (`libs/python/pyto-widgets`) was kept without the plan's required
  ask-at-build-time step actually reaching the user.** The plan is explicit: the lane-2 builder
  "must put the question to the user before deleting, and if the answer is unanswered, remove [it]
  by default." `.artifacts/reports/l2-exit.md:48` and the run's progress log show the keep decision
  was made by "explicit dispatcher instruction," not by a question actually put to and answered by
  the human — and the default-on-no-answer was inverted (kept instead of removed). Low impact (an
  empty manifest, no code to lose), but it's a real process deviation from an explicit gate
  instruction and should be surfaced to the human now if it wasn't already.

- [non-blocking] **Lane 2:** `libs/python/flask_utils/` itself stays snake_case at the project-dir
  level, which the plan's own conventions section calls out as "the one project-level violation" of
  convention #3 (kebab-case project dirs). This was descriptive context in the plan, not a 2.2
  acceptance item, so no action was required and none was taken — flagged for awareness only.

- [non-blocking] **Lane 3, 3.2's stated test oracle isn't actually enforced for
  `libs/javascript/react/maze-runner`.** Its bare specifiers (`components/header`,
  `styles/layout.module.scss`, etc.) resolve only via `jsconfig.json`'s `baseUrl` convention, but
  the package's own `build` script is a no-op (`"echo 'No build configured'"`) and no
  `import/no-unresolved`-style lint rule is configured anywhere in the repo, so resolution is
  asserted by convention but never mechanically checked — unlike every other package in Catalog B5,
  which do get a real resolution proof via `turbo build`/`turbo lint`. Not necessarily wrong, but
  unverified by tooling; worth a follow-up resolution check.

- [non-blocking] **Lane 3:** `libs/javascript/node/maze-runner/package.json:5` still declares
  `"main": "src/lib/index.js"`, but the file lives at `src/index.js` — a pre-existing bug inside
  3.2's explicit file scope that wasn't fixed. Low impact since nothing in-repo consumes this
  package via its `main` field.

- [non-blocking] **Lane 5, 5.1** shipped as three workflow files
  (`lint-go.yml`/`lint-javascript.yml`/`lint-python.yml`) rather than the plan's stated two-file
  triple-m split (`lint-frontend.yml`/`lint-backend.yml`). Coverage and correctness are equivalent
  or better (each genuinely installs and runs real lint/build, gated on paths, plus a real
  `verify-workspace-membership.sh` guard against C1 regressing) — naming only.

### What verified clean (no blocking issues)

- **Phase 1 (root workspace, lane 1):** `turbo run lint --dry=json` lists 34 packages matching the
  plan's membership rule exactly (35 `importers:` entries = 34 + root); `workspaces` array deleted
  from `package.json`; `turbo` pinned to `2.5.5`; root `ruff.toml`/`.editorconfig`/`.python-version`
  /`.nvmrc`/`eslint.config.js`/`.prettierrc` all present and correctly scoped; ruff is a pinned
  `uv`-resolved dev dependency, no more runtime `pip install`; `bin/**` added to `turbo.json`
  outputs; `.gitmodules`/`dots-js` removed correctly; all 4 remaining `.keras`/`.h5` files unchanged
  (2 removed only as a correct side effect of lane 2's D2 dedup, confirmed via `git log
  --diff-filter=D`).
- **Phase 2 (Python, lane 2):** `uv sync` resolves all 14 workspace members with real packages;
  `flask` imports successfully in `apps/flask/maze-runner`'s venv (original repro fixed); `ruff
  check .` and `ruff format --check .` both exit clean; the `Maze.build_new(height, width, …)`
  argument-order rewrite in `apps/flask/maze-runner/main.py` was independently verified correct
  against the library's actual signature; `add_visited()`/if-vs-elif behavior carry-over was
  verified via the exit report and confirmed as a deliberate, recorded decision, not a silent drop;
  zero distribution-name collisions remain; 80/80 new contract tests pass across 7 packages.
- **Phase 3 (JavaScript, lane 3):** all 11 JS `package.json` files carry `"private": true`;
  `pnpm-lock.yaml` importers match the plan's membership exactly; `pnpm install --frozen-lockfile`
  and `turbo run build` both succeed (8/8 JS build tasks); the two legacy CRA packages are correctly
  excluded and untouched; a real ESLint contract test (`eslint-baseline.test.mjs`) proves
  `console.info` is never flagged and `no-undef` violations do fail; no lane-3 commit touched a
  root-owned file (`package.json`/`pnpm-workspace.yaml`/`turbo.json`).
- **Phase 4 (Go, lane 4):** `go vet ./...` and `go build ./...` pass clean in all six modules, both
  with and without `go.work` present (standalone-mirror constraint actually tested by moving
  `go.work` aside and back); no `module github.com/dae-go/<name>` path was changed; `crud-server`'s
  unused `go-sqlite3` require removed; lint scripts no longer mutate (`gofmt -l .` read-only check,
  not `go fmt`); `turbo lint` leaves the tree clean.
- **Phase 5.2 (Go CI, lane 5):** `go-version-file: go.work` in both `lint-go.yml` and
  `sync-go-packages.yml` resolves to `1.24.2`, matching the highest actual module directive;
  `build-maze-runner.yml` now copies `libs/golang/maze-runner` with a documented rationale.
- **Phase 6 (integration proof):** run live from a clean `git status`: `pnpm install
  --frozen-lockfile` succeeds without any incidental Go toolchain install; `turbo run build` — 32/32
  successful; `turbo run lint` — 34/34 successful, 0 errors; `git status --porcelain` unchanged
  after both (tree stays clean); all three of the plan's original reproductions independently
  re-run and confirmed fixed (`import flask` succeeds, the turbo graph now lists 34 packages
  including 8 `lib.javascript.*`, `go vet` is clean in `pythonify`); a genuine
  `libs/bash/build-tools/import-check` script exists and passes for all 14 Python workspace
  members.

### Open questions

- Should 5.3 be reworked to build the actual `/docs` mirror + symlink structure the plan's file
  scope and the project's `doc-format` rule both require, or is the flat 4-file `/docs` with a
  root-README link an intentional, accepted deviation for this run? (Drives whether this is a
  redispatch of lane 5's 5.3 or a plan amendment relaxing the doc-format requirement for this run
  specifically.)
- Was the C14 (`pyto-widgets`) keep decision ever actually put to the human, outside of what the
  exit report and progress log capture? If yes, this finding can be closed as satisfied; if no, the
  human should be asked now before this ships.
