# Package-management strategy

**Chosen: S3 — three per-language workspaces under one task runner (D1).** This is the settled
decision, not a live question — recorded in the plan of record,
[`project-plans/lint-import-audit-08-12-26/plan.md`](../project-plans/lint-import-audit-08-12-26/plan.md),
section **"Decisions settled at the gate"** (D1), which itself resolves the four candidates weighed
in that same plan's **"Package-management strategy candidates"** section. This page summarizes that
record; the plan file is the source of truth if the two ever disagree. (Once this plan ships and is
archived per this repo's plan lifecycle, that file moves to
`project-plans/completed/lint-import-audit-08-12-26.md` — update this link then.)

## The four options considered

| | S1 · Repair in place | S2 · triple-m literal | **S3 · chosen** | S4 · polyglot build system |
|---|---|---|---|---|
| JS | fix pnpm globs, one root lock | same | same | Bazel/Pants targets |
| Python | keep per-package venv + Poetry | one root `pyproject`, one venv, import-by-path | `uv` workspace: per-package `pyproject` kept, one root `.venv` + `uv.lock` | hermetic per-target deps |
| Go | bump `pythonify` only | (no story) | `go.work`, `dae-go` paths untouched | `rules_go` |
| Keeps `dae-go` sync working | yes | **no** | yes | yes |
| Keeps mirrored packages standalone | yes | **no** | yes | yes |
| New tool to install | none | none | `uv` (now installed and pinned) | Bazel or Pants |

**Why S1 (repair in place) wasn't enough on its own.** Cheapest and lowest risk — and in fact a
*prerequisite* of S3 regardless — but left nine per-package virtualenvs each re-installing Poetry,
no cross-package dependency resolution, and eight uncoordinated `poetry.lock` files (seven of them
empty). It fixes the workspace-visibility bugs but not the N-venvs problem.

**Why S2 (triple-m's literal shape) was rejected.** triple-m's Python model — one root
`pyproject.toml`, one venv, the whole backend reached by a single `sys.path.insert` — works there
because its "packages" are Django apps sharing one dependency set with no independent distributions.
daedalus-mono's Python packages are **real distributions with committed wheels**, and its Go modules
are **published** to `github.com/dae-go/*`. Collapsing Python into one import tree, as S2 does, would
remove the per-package manifests that both the wheel builds and the `cp -R` mirroring
(`build-maze-runner.yml`) depend on — it "**breaks two hard constraints**" per the plan text. S2 is
explicitly noted as "**Viable for the `apps/` half only**", not the whole repo.

**Why S4 (reviving Bazel/Pants) was rejected.** The repo has residue from two prior, incomplete
attempts (`WORKSPACE` for Bazel; `/.pants.*` in `.gitignore`). Genuinely the most correct option for
three languages and hermetic builds — and the only one that models the real Go dependency graph —
but "**wildly disproportionate for a solo portfolio repo whose CI does not currently run a single
test**". Listed in the plan specifically to give it an explicit "no, and here's why" rather than
silence, given the user's own history of two prior attempts.

**Why S3 was chosen.** Each language keeps the one workspace mechanism it actually has (pnpm
workspaces for JS, a `uv` workspace for Python, `go.work` for Go), with `turbo` as the single
cross-language entry point via the pre-existing `package.json`-shim convention. Per the plan: "only
`uv` is net-new; pnpm is already pinned and `go.work` is a config file, not a tool; the three
mechanisms share no integration surface." It is, in the plan's own words, "the honest answer to 'not
everything can be that nice': one *pattern*, three *mechanisms*."

## Related decisions that bear on package management

- **D2 — ML package Python-version unification.** Settled as **(c) + (a)**: first dedupe the
  duplicate `tensorflow/open-ai-gym` copy (phase 2.3), then unify the surviving projects on Python
  3.11 (`requires-python >= 3.11`, root `.python-version`), deleting the three
  `apps/flask/*/runtime.txt` `python-3.8.0` pins. This exists because a single `uv` workspace needs
  one resolvable interpreter, and the packages disagreed (`^3.8` to an exact `3.11`) before this
  decision.
- **D6 — every JS package is private.** `"private": true` on every `libs/javascript/**` /
  `apps/next/**` package (phase 3.1) — nothing in this repo is published to a registry. Landed on
  this branch — verified every such `package.json` carries the field.
- **D7 — the two legacy CRA/React 16 packages.** `markdown-builder` and `quote-builder`
  (`react-scripts@2.1.1`, from 2018) are **not** migrated to the repo's React 18 toolchain — they are
  deliberately excluded from the pnpm workspace via negated globs in `pnpm-workspace.yaml` (already
  landed, phase 1.1) and marked legacy at the package level (phase 3.3, not yet landed). This is a
  package-management decision, not an oversight: the workspace glob change and its rationale are
  already live even though the per-package marking isn't yet.

## Cost accepted

`uv` was the one net-new tool this strategy required, and it is now a real, landed dependency of the
dev workflow: `uv 0.12.4` is installed and on `$PATH`, pinned via the committed root `uv.lock`, and
Phase 2 subphase 2.5 has shipped. Python package management is the single root `uv` workspace
described above (see [`installation.md`](./installation.md) for the current, verified mechanism) —
not per-package Poetry, which this migration fully replaced.
