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

## Round 2 — 08-14-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 3
```

Reviewed independently (fresh, no conversation history) against the same plan
(`project-plans/lint-import-audit-08-12-26/plan.md`, now including the round-2 "Decisions settled
at the code gate" section) and the real diff `main...HEAD` on `bug/lint-import-audit`, worktree
`/home/icarus64/repos/daedalus-mono/.workflows/lint-import-audit` (HEAD `967ed09`). This round
verifies specifically: (1) round 1's blocking finding (5.3 doc-format), (2) round 1's two open
questions (C14 human decision; the 5.3 rework-vs-deviation call), and (3) the two new subphases
(2.8, 4.4) added at the round-2 gate — all re-checked with live commands, not by re-trusting exit
reports or the progress log.

### Findings

- [non-blocking] **Round-1 finding "Lane 1, 1.2's literal `BUILD` grep" still applies unchanged.**
  `git grep -l BUILD` under `libs/` still returns the same pre-existing corrupted `.gitignore`
  files (e.g. `libs/golang/crud-server/.gitignore` = `.logBUILD`, no separating newline), byte-
  identical to `main`. Correctly out of round 2's scope; carried forward for the record, not
  reflagged as new.
- [non-blocking] **Round-1 finding "3.2's test oracle unenforced" and "node/maze-runner's stale
  `main` field" both still stand, unchanged from round 1.** Neither was in scope for round 2 and
  neither regressed; re-verified present and still low-impact (no build failure, nothing in-repo
  consumes the stale field).
- [non-blocking] **The run's progress log (`​.artifacts/progress-log.md`) is stale relative to the
  actual shipped state.** Its "Gate rounds" section ends mid-round-2 (last entry: "l6 ROUND 4
  DISPATCHED … Then code-gate round 2"), with no entry recording l6 round 4's outcome, its merge,
  or this round-2 code-gate dispatch itself, even though `git log` shows the branch is fully
  merged and green (no `l6` branch remains; HEAD is `967ed09`, a pure 4-line syllabus-tick commit
  on top of the 5.3 rework). Not a code defect — verified independently below with live commands
  rather than trusting the log — but the log is a run artifact that's supposed to be the
  reconstructable source of truth for a resumed session, and it isn't currently accurate. Worth a
  closing update before this run's artifacts are archived.

### What verified clean (no blocking issues) — round-2-specific + full re-verification

- **Round-1 blocking finding (5.3 doc-format) — FIXED, verified independently of the exit
  report.** `find . -name README.md` (excluding `docs/`, `node_modules/`, `.git/`) shows every one
  of the 36 project READMEs is now a real symlink (`test -L` true for all); `docs/apps/**` and
  `docs/libs/**` mirror the source tree with 37 real README files underneath. Spot-checked
  `apps/flask/maze-runner/README.md` → `../../../docs/apps/flask/maze-runner/README.md`, a valid
  relative symlink resolving to a real 5.7 KB file. No dangling symlinks anywhere in the tree
  (`find -xtype l` returns only two pre-existing, unrelated `.next/standalone` node_modules links).
  No README content contains relative links/images that would break by living at a new physical
  path (`grep` for `](../`, `](./`, relative `<img src>` in `docs/apps`/`docs/libs` → zero hits).
- **The mirror-dereferencing half of D11 — proven by an actual simulated copy, not just read.**
  `build-maze-runner.yml` now uses `cp -RL` (was `cp -R`) on all 6 lines; `sync-go-packages.yml`
  uses `rsync -avL --delete` (was `-av`). I ran `cp -RL apps/flask/maze-runner
  /tmp/.../maze-runner-copy` myself: the copied `README.md` is a real 83-line file, not a dangling
  symlink — the exact regression the fix claims to prevent, reproduced and confirmed absent.
  `create-mono-file-tree.sh` needs no change per the plan's claim; I ran it directly and its
  `[ -f "$dir/README.md" ]` project-detection correctly followed the new symlinks (every mirrored
  project still appears with its README link in the generated tree), and the run left the tree
  clean (no incidental writes).
- **C14 / D9 (`pyto-widgets` removal) — confirmed at the git level, not just by directory
  listing.** `git ls-files libs/python/pyto-widgets` returns nothing (fully untracked/removed);
  `git status --porcelain -uall` is empty repo-wide, meaning the `node_modules`/`.venv`/`.turbo`
  directories still physically present under that path are pre-existing gitignored build cache
  from before the deletion, not tracked or resurrected content — a fresh clone would not have this
  directory at all. No reference to `pyto-widgets`/`pyto_widgets`/`pytowidgets` remains in
  `pyproject.toml`, `uv.lock`, `pnpm-workspace.yaml`, or `package.json`. Both open questions from
  round 1 about C14 are closed: the plan's new "Decisions settled at the code gate" section
  (D9) records the human was actually asked and answered "dead, not content-pending," and the
  deletion in 5ef6114 executes that answer.
- **4.4 (`pkg/abf` zip type-identity fix) — technically verified correct, not just re-run.** Read
  `Zip[T any, S ~[]T](iters ...S) []S` in `pkg/abf/utils.go:55` and the test-local
  `type zipper [][]any` in `pkg/abf/utils_test.go:8`: since `S = []any` is inferred from the
  `zipper`-typed test inputs, `Zip` genuinely returns the unnamed literal type `[][]any`, never the
  named `zipper` type, even though they share an identical underlying type —
  `reflect.DeepEqual` legitimately treats those as unequal. The fix (wrap the call site,
  `zipper(Zip(...))`, at the three call sites in `utils_test.go`) is test-only, changes no
  production code, and is the technically correct fix versus the alternative of relaxing the
  comparison or renaming `Zip`'s return type. `go test ./...` in `pythonify` now passes clean
  (`ok github.com/dae-go/pythonify/pkg/abf`), and `go vet ./...` is clean in all six Go modules.
  Re-ran the standalone-mirror convention check by moving `go.work` aside and rebuilding
  `pythonify` alone — still builds and vets clean without it, so 4.4 didn't reintroduce a
  cross-module dependency.
- **Full integration re-proof, run live in this pass (equivalent to 6.1), independent of any
  builder's claim:**
  - `pnpm install --frozen-lockfile` — succeeds, no Go toolchain triggered, lockfile already
    up to date (34 workspace projects incl. root).
  - `turbo run build` — 31/31 successful.
  - `turbo run lint` — 33/33 successful (0 errors; 4 pre-existing unrelated Next.js
    `no-unused-vars` warnings only); tree stays clean (`git status --porcelain -uall` empty)
    before and after both runs.
  - `uv sync --inexact` — resolves the 14-member workspace; site-packages count 272 before and
    272 after (the F5 venv-pruning regression from round-1's l6 report stays fixed).
  - `bash libs/bash/build-tools/import-check` — 13/13 importable workspace members OK (2 correctly
    skipped as non-package, no-main-entry directories).
  - `ruff check .` and `ruff format --check .` — both clean (214 files already formatted, 0
    findings).
  - `.venv/bin/python -c "import flask"` — succeeds (`flask 2.3.3`), the plan's original
    reproduction confirmed still fixed.
  - `go vet ./...` clean in all six `libs/golang/*` modules.
- **Syllabus and scope hygiene.** All 22 original subphases plus the two round-2 additions (2.8,
  4.4) show `[x]` in the current `plan.md`; all C1–C14 candidates remain `[x]`. The only round-2
  plan-file commit (`967ed09`) touches exactly `plan.md`, 4 lines. `pnpm-lock.yaml`'s only
  round-2-era write is 2.8's documented one-off exception (`5ef6114`); no other lane touched it in
  this round.

### Open questions

None outstanding. Both round-1 open questions are closed: C14 was put to the human and answered
(remove — D9), and the 5.3 rework-vs-deviation call was answered (rework — D11), and both are
verified actually implemented above, not just recorded as decided.
