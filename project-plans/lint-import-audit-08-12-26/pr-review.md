# pr-review

## Round 1 — 08-14-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 4
```

Reviewed the full branch diff `main...bug/lint-import-audit` (387 files, +17963/-10883,
88 commits) against the spec of record, `project-plans/lint-import-audit-08-12-26/plan.md`
(re-read at review time, including the round-2 "Decisions settled at the code gate" section),
in the parent worktree `/home/icarus64/repos/daedalus-mono/.workflows/lint-import-audit`. This
is a diagnose→build run; the plan IS the diagnosis report and the implementation spec together.
`code-review.md` (2 rounds, latest verdict `ready`/0 blocking/3 non-blocking) was read but not
trusted blind — every one of its headline claims was independently re-run below, plus checks of
my own (run-scope, secrets, stray artifacts, `.gitignore`).

### Verification performed independently (live commands, not re-trusting reports)

- **`verify-run-scope.sh . main .artifacts`** — raised 213 raw `UNCLAIMED:` lines, all inside
  `l2-exit.md`'s and `l3-exit.md`'s "Files touched" sections. Root cause identified: those two
  exit reports write **multi-path bullets** (e.g. `` `pyproject.toml` (rewritten), `__init__.py`
  (deleted), ... `` on one line) and one blanket reference ("ruff-format-only changes across the
  remaining ~50 `.py` files ... full list in commit `626766c`'s diffstat"); the script's own
  `claims_from_report()` only takes the first backticked path per bullet by design (documented in
  the script's header as the accepted trade-off, not a bug to fix by tightening
  `validate-report.sh`). Cross-checked every one of the 213 flagged paths: 167 are literally
  substring-present elsewhere in the same bullet's text; the remaining 46 (mostly
  `libs/python/web-crawlers/web_crawlers/**` files covered only by the "remaining ~50" blanket
  reference, plus 5 `libs/javascript/react/maze-runner/{components,styles}/*` files covered only
  by `{header,maze,node,runner}.js`-style brace shorthand) were checked individually against
  `git log main..HEAD -- <file>`: every one lands in a commit the corresponding exit report
  already names by hash (`626766c` "2.6: ruff mechanical sweep across the lane", `0644050`
  "feat(3.1,3.2,3.4): revive react/maze-runner", `4c2a710` "2.7: fix web-crawlers TTS F821s..."). No
  file in the diff is actually unclaimed — this is a report-formatting gap in the mechanical
  parser, not a scope violation. See non-blocking finding below.
- **`ruff check .` / turbo lint** — ran fresh: `ruff check .` → "All checks passed!"; `turbo run
  lint` (no dry-run, real execution) → 33/33 successful, full-turbo cache-consistent, tree clean.
- **Flask repro** — `.venv/bin/python -c "import flask"` → succeeds, `flask 2.3.3`, confirming
  the plan's original reproduction (`ModuleNotFoundError: No module named 'flask'`) is fixed.
- **Docs mirror/symlink (5.3 / D11)** — every non-root, non-cache project `README.md` found by
  `find` is a real symlink into `docs/**` (spot-checked several, including
  `libs/prompting/gemini/README.md -> ../../../docs/libs/prompting/gemini/README.md`); root
  `README.md` and `.pytest_cache/README.md` are correctly not symlinks (root has nothing to mirror
  into; `.pytest_cache/` is gitignored, pytest-generated, not part of the diff).
- **`.gitignore` / run-dir hygiene** — `.artifacts/` is committed-ignored on this branch (inherited
  from `main`'s `b55b085`); the branch's own `.gitignore` diff (removed the dead `/.pants.*`,
  un-anchored `/dist/` → `dist/`, added `.DS_Store`, `.firebase/`, one stray Go binary path) matches
  Phase 1's dead-build-system cleanup, nothing unexplained.
- **Stray-file / secrets scan** — `git diff main...HEAD` grepped for credential-shaped patterns:
  the only hits are a `RH_PASSWORD` env-var read, an obviously-fake test fixture password
  (`"s3cr3t-pw"`), and two **removed** `secrets.GITHUB_TOKEN` lines inside a deleted dead nested
  `apps/next/maze-runner/.github/workflows/firebase-hosting-*.yml` pair (GH Actions expression
  syntax, never a literal secret, and being deleted, not added). No TODO/FIXME/XXX added in the
  diff. Four `.DS_Store` files are **deletions**, not additions.
- **Convention spot-checks** — dotted `package.json` names, `pnpm@9.1.0` only (no npm/yarn
  lockfile added), no `libs/golang/*` module path changed away from `github.com/dae-go/<name>`,
  `console.info` presence unaffected (JS diff is formatting/dep/private-flag only where sampled).

### Findings

- [non-blocking] **`l2-exit.md` and `l3-exit.md` use multi-path bullets and blanket references in
  "Files touched" instead of one claim per bullet**, which defeats `verify-run-scope.sh`'s
  mechanical claim parser (213 false-positive `UNCLAIMED:` lines this round, all manually resolved
  — see above). No actual scope violation, but the mechanical check is supposed to make the
  harness-scoped-writes invariant auditable *without* a human re-deriving it via `git log`
  per-file, and this round it couldn't. Worth a note for future builders: one backticked path per
  bullet in "Files touched," even when a directory's changes are homogeneous (ruff-format sweeps,
  brace-expandable filenames).
- [non-blocking] **`libs/javascript/node/maze-runner/package.json:6`** still declares `"main":
  "src/lib/index.js"`, but the file lives at `src/index.js` (pre-existing bug inside 3.2's file
  scope, not fixed). Confirmed independently: `ls src/` shows `index.js` at the top level, no
  `lib/` subdirectory. Low impact — nothing in-repo consumes this package via its `main` field —
  but it's a real stale reference a future consumer would trip on.
- [non-blocking] **`git grep -l BUILD` under `libs/` still returns 7 pre-existing corrupted
  `.gitignore` files** (content glued to a literal `BUILD` with no separating newline, e.g.
  `libs/golang/crud-server/.gitignore` = `.logBUILD`), which 1.2's literal acceptance criterion
  ("`git grep -l BUILD` returns nothing under `libs/`") technically fails. Confirmed
  byte-identical to `main` on all 7 (`git diff main...HEAD` empty for each) — pre-existing, not
  introduced or silently "fixed" beyond 1.2's stated scope; the plan's own evidence section
  mischaracterized these files, a planning-side miss carried since round 1 of the code gate.
- [non-blocking] **3.2's resolution oracle for `libs/javascript/react/maze-runner` is asserted by
  convention, not mechanically enforced.** Its bare specifiers resolve only via `jsconfig.json`'s
  `baseUrl`; the package's `build` script is a no-op and no `import/no-unresolved`-style lint rule
  exists anywhere in the repo, so nothing in CI would catch a broken specifier here the way it
  would for every other Catalog B5 package. Not wrong, just unverified by tooling.

### Open questions

None. Both open questions code-review round 1 raised (5.3 rework-vs-deviation; whether the C14
keep/remove decision was actually put to the human) were closed at the code gate (D9, D11 in
plan.md's round-2 "Decisions settled" section) and independently re-verified above (docs mirror
is real; `libs/python/pyto-widgets` is fully removed — `git ls-files` returns nothing for it).
