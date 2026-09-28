# mutable-words-09-25-26.plan-review

## Round 1 — 09-25-26

```
verdict: rejected
next: needs-input
blocking: 3
non-blocking: 2
```

### Findings

- [blocking] `plan-lifecycle.sh check` (full scan) fails with `FAIL: unexpected file in plan dir
  /home/icarus64/repos/daedalus-mono/.workflows/mutable-words/project-plans/russian-immutable-words-08-31-26:
  source-word-list.md`. This is a pre-existing violation in an older, still-active
  (never-archived, syllabus 100% unchecked) plan directory — not a defect in
  `mutable-words-09-25-26.md` itself. Per this gate's own rule, a `FAIL:` from `plan-lifecycle.sh
  check` blocks structurally regardless of whether it originates in the plan under review or
  elsewhere in the plans dir, and a pre-existing/legacy layout is explicitly not an excuse.
  `validate-plan.sh` on the plan under review returned clean (`OK: plan is structurally valid (15
  subphases)`).

- [blocking] The same stray file is a **load-bearing input to this plan**, not just adjacent
  clutter: subphase 1.1's acceptance criteria require regenerating GUIDs "for every row in
  `project-plans/russian-immutable-words-08-31-26/source-word-list.md`" and comparing them
  against a golden fixture at that path. That path sits inside a plan directory that (a) already
  fails the layout check today, and (b) even once properly archived would have everything but
  `plan.md` deleted per `plan-format` — deleting this exact file. Subphase 1.1 as written will
  either build against a file the check already flags, or lose its oracle the moment someone
  correctly runs `plan-lifecycle.sh archive` on the older plan. This mirrors, almost exactly, the
  failure mode subphase 2.2's own "Where, and why there" note already warns against for the *new*
  TSVs — it just wasn't applied to 1.1's fixture-source citation.
  **Recommended fix**: commit a copy of the needed `(pos, russian) -> guid` golden pairs (or the
  word list itself) under `libs/python/anki-tools/tests/data/` (same treatment as the
  `immutable_audio_block.html` golden file already planned for 1.2), and cite that path instead.

- [blocking] Verified against the real workbook (`~/Downloads/russian_vocabulary.xlsx`,
  openpyxl 3.1.2): the plan's `Status` column claim — *"uniformly `"New"` on 872 of 1002 rows and
  empty on the rest"* (Field sets section, and repeated as the justification for dropping `Status`
  from every note type) — is **wrong**. The real distribution is `Status == "New"` on **1002 of
  1002** real rows (100%), 0 empty, 0 other values (the Key sheet's own New/Learning/Known summary
  agrees: New=1002). This doesn't weaken the case for dropping the field — a fully-uniform column
  is, if anything, a stronger case — but a "verified against reality" fact that is simply
  incorrect is exactly what this gate exists to catch, and the 872/1002 figure should not ship in
  the plan or downstream docs. Fix: replace with "uniformly `New` on all 1002 rows."

### Non-blocking notes

- [non-blocking] The claim "the longest cell is 75 characters" (Source workbook facts) is true
  only for the four *data* sheets (verified: max 75 chars, in Verbs row 76 / Case-Preposition).
  The `Key` sheet (never a build input) has a 160-character prose cell. Not a defect since
  `vocabulary_source.py` never reads `Key`, but the sentence should say "across the four data
  sheets" so a future reader doesn't misapply it to the whole workbook.
- [non-blocking] The quoted field-name-validity string ("should not contain `:`, `"`, `{` or `}`",
  `anki/_fluent.py:5711-5721`) has the right line range (confirmed exact: 5711/5714 and 5717/5720)
  and the right *substance* (`#`/`^`/`/` at the start is confirmed verbatim), but the
  "contains"-rule docstring is a templated Fluent string whose literal Python-side text reads
  `"The field name should not contain :, ",  or ."` — the `{`/`}` characters aren't literally
  present in that source (they're likely filled in from Fluent template args at runtime, which
  this citation doesn't reach). Doesn't affect any acceptance criterion or design decision; just
  soften the citation to "verified against the compiled Fluent string; the interpolated character
  list itself could not be independently confirmed from this source."

### Verified and not disputed (high-confidence foundation)

Two independent full read-throughs (installed `anki` 26.8.1 source + compiled `_rsbridge.so`
strings, and a byte-level copy-only inspection of the real collection's `notetypes`/`fields`/
`templates`/`decks` tables) confirmed, with no discrepancies beyond the two noted above:
`col.decks.rename` behavior and its "if not exists" / unique-index hazard (the `idx_decks_name`
string is present in `_rsbridge.so`, confirmed by `strings`); `Card.did` / `cids` query shape;
`create_backup` signature and its use in `rebalance_due.py:532`; every cited function in
`immutable_words.py` (`_notetype_id_for_name`, `clone_note_type`, `assert_unmodified`,
`build_deck_tree`, `attach_media`, `export_package`, `build_parser`, `main`) at its cited location
and behavior; every cited function/constant in `immutable_words_plan.py` (`_AUDIO_DIV`,
`_GUID_ALPHABET`, `_base91`, `guid_for_row`, `ROW_SPLITS`, `rewrite_audio_playback`); every cited
function/constant in `elevenlabs_tts.py` (`VOICES`, `DEFAULT_VOICES`, `RequestBudget`,
`fetch_tts_audio_metered`, `get_api_key`, `build_and_save[_batch]`, `CONFIRM_ABOVE_REQUESTS`) and
the exact voice roster (f1 Alisa `t6lBrEl93uCiLR1Lgm8v`, m2 Nester Surovy, m1 Mishka Yaponcik); all
Stack-table versions (`anki` 26.8.1, `requires-python`, `.python-version`, `ruff.toml` settings,
`pnpm@9.1.0`, `turbo` 2.5.5, `openpyxl` absent from `uv.lock` today, `pandas` present but owned by
`market-bots`, not `anki-tools`); the real note type `1698803891108`'s actual name (trailing
space), 6 fields, 2 templates; `Russian - Immutable Words (Ellis Version)` id
`3897610691970966744`, 7 fields with `AudioRefs` last, CSS byte-identical to the source note type;
207 notes / 414 cards; the entire `Languages::Russian` deck tree and card counts per the plan's
table, including that no `Languages::Russian::6.*` deck exists today (confirming Phase 5's "free
first step" claim); every leaf deck name containing `". "`.

Workbook facts (openpyxl against the real file, not the committed TSVs which don't exist yet):
sheet names, row counts (541/179/152/152), and headers verbatim for all four sheets; the Key
sheet's own totals (541/179/152/130/1002) and its "Formation 'none'" prose; exactly 22 Adverbs
placeholder rows with all four signals agreeing on every one (no partial-signal row exists); zero
of 1181 base-word instances contain U+0301; zero cells contain a tab/CR/LF; the two slash-joined
adverbs (`направо / справа`, `налево / слева`) are exactly and only those two, with exactly the
spacing the plan assumes; 1181 distinct slugs / zero collisions, and all seven claimed
media-directory overlaps (кафе, кино, кофе, метро, пальто, просто, согласно) do appear as real
base words; the three yellow-column empty-count claims (Nouns Genitive Sg/Pl 540/541,
Verbs six columns 178/179, Adjectives Short Form/Comparative 151/152) all match exactly.

Cost/count math (recomputed independently): 541+179+152+130=1002; 1002+179=1181; 1181×2=2362;
2362−14=2348; 1002×2=2004; every restatement of these figures elsewhere in the plan (per-deck
counts, D2's 358/716 verb-card alternative, D3's 1183/2366/2352 split-adverb alternative) is
internally consistent. Lane file-scope audit: Phase 1 (serialized) and Phase 6 (serialized) own
every shared file (`anki_identity.py`, `card_audio.py`, `immutable_words.py`,
`immutable_words_plan.py`, `pyproject.toml`, `uv.lock`, `package.json`, docs) outright; lanes 1-4
(`mutable_words_plan.py`+data / `mutable_words.py` / `mutable_words_audio.py` /
`renumber_russian_decks.py`) touch fully disjoint new files with no cross-lane collision found;
lane 4 genuinely has zero dependency edges as claimed. Ask-vs-plan diff: all five gate decisions in
`the-ask.md` (voices f1/m2, all four sheets as subdecks, deck placement + renumber map, both-verb-
aspects audio, one note type per subdeck) are delivered as specified, with no inversions found.
Subphases 1.1/1.2 editing the two "out of scope" immutable modules is a **recorded, reasoned
departure** (decision D1), not a silent inversion — the plan states it explicitly, gives its
reasoning, and backs it with a byte-identical-output acceptance criterion, so per this gate's own
rule it is not treated as blocking.

### Open questions

- **Old-plan-dir disposition (blocks the structural FAIL above).** Is
  `project-plans/russian-immutable-words-08-31-26/` finished work that was never archived, or
  abandoned/superseded work? If finished: run `plan-lifecycle.sh archive` on it (which will also
  resolve the stray-file FAIL, but see the blocking note above about 1.1's fixture path first). If
  abandoned: `plan-lifecycle.sh supersede`, with `mutable-words-09-25-26.md`'s "Supersedes nothing"
  line updated accordingly if any of its scope actually carries over. This is a human/caller
  decision, not something a planner revision can settle unilaterally.
- **D2 (verb card shape), D3 (slash-joined adverbs), D4 (Status column), D5 (empty yellow
  columns), D6 (who executes the three real-world steps)** — the plan already surfaces these as
  explicit decision points with recommended defaults and alternatives; they were not independently
  re-litigated by this review (D1 was, and is resolved above). They should still be put to the
  user at the gate, per the plan's own framing.
- **Q1-Q4** (note-type naming, subdeck lettering, answer-side details-block layout, audio-on-
  front/back card shape) — likewise the plan's own flagged assumptions for the user to confirm or
  override, not verification failures.

## Round 2 — 09-26-26

```
verdict: rejected
next: needs-input
blocking: 1
non-blocking: 1
```

### Findings

- [blocking] **The procedural knot is real, independently confirmed, and I am ruling it still
  blocks — this gate's own instructions forbid the alternative reading.** Re-ran
  `plan-lifecycle.sh check` (bare invocation, no compound command) myself: it still prints exactly
  `FAIL: unexpected file in plan dir …/russian-immutable-words-08-31-26: source-word-list.md` and
  **exits 1** — I confirm the planner's correction: round 1's "exit 2" was contamination from a
  compound command, not the tool's real behavior; a bare `cmd1 && cmd2` invocation and a bare
  invocation both give exit 1. The amended plan is correct that this specific FAIL cannot be
  cleared by any textual planner revision — clearing it requires the executable work in 1.1/1.2
  (git mv, four test-file edits, three docstring corrections, syllabus reconciliation, then
  `archive`) — and it schedules that work as its own Phase 1, first in the dependency graph
  (Phase 2 depends on 1.1; Phase 6 depends on 1.2; nothing else can dispatch before Phase 1
  completes).

  I still rule this **blocking**, not excused, because this skill's own governing text is explicit
  and leaves no room for the reading "it's about to be fixed by Phase 1, so it's fine": *"any
  `FAIL:` line from EITHER script fails the gate structurally… this holds even for a pre-existing
  flat/legacy plans dir… do not write this gate to excuse a legacy layout, the correct outcome is
  a structural failure that forces a one-time migration."* That sentence was written to pre-empt
  exactly the argument the amended plan is now making (the fix is scheduled, therefore don't
  block), and it says not to accept it. Step 2 also states any `FAIL:` blocks *"regardless of
  content quality"* — and the quality of Phase 1's design (which is good: byte-identical move,
  154-test equivalence check, evidence-per-subphase reconciliation table) is exactly the kind of
  content-quality argument that sentence excludes from consideration.

  This is not a dead end, though — I want to be explicit about the actionable path, since a bare
  "rejected" with no route forward would be unhelpful: subphases 1.1 and 1.2 are specified in
  enough concrete detail (exact `git mv` source/destination, the four file+line edits, the
  before/after pytest counts, the reconciliation table, the exact `archive` postcondition) to be
  executed **directly, right now, by the caller or a single ad hoc dispatch — outside of this
  plan's builder-dispatched execution** — rather than waiting for plan approval. Once
  `plan-lifecycle.sh check` (bare invocation) exits 0, resubmit this plan for the gate with Phase 1
  marked `[done]` (the work will already exist) rather than left as pending builder work; the rest
  of the plan (Phases 2-9) does not need to change. This is the same routing round 1 already used
  for this exact finding — a human/caller decision, not a planner-revision — and I am carrying it
  forward rather than accepting the plan's attempt to close it by absorbing it into Phase 1.
  Whoever owns this run should weigh my reading of "do not excuse" against the practical case the
  planner is making, since a strict reading of my own instructions is not infallible — but on the
  instructions as written, I cannot sign off "ready" or "tentative" with this FAIL still live.

### Verified and not disputed (round 2's specific asks)

- [non-blocking] **Dash-only cell census, verified independently against the real workbook** (openpyxl 3.1.2,
  ephemeral `uv run --with openpyxl`, not the project's lock): exactly four columns across all four
  data sheets contain dash-only cells — `Nouns.Plural` **107**/541, `Adverbs.Comparative`
  **36**/152, `Adverbs.Adverb` **22**/152, `Adverbs.Stress` **22**/152 — and a full column-by-column
  scan of all four sheets confirms **zero** dash-only cells in every other column. This matches the
  plan's claim exactly. The `Key` sheet's own prose was re-read in full: it does explicitly gloss
  `Nouns.Plural`'s dash (*"Plural '—' = no plural in everyday use (mass/abstract/collective
  nouns)"*) verbatim as quoted. It does **not** carry an equivalent explicit sentence for
  `Adverbs.Comparative` — the plan's parenthetical "(no comparative form)" for that column is a
  reasonable self-evident inference from the column's own name, not a second Key-sheet quotation,
  and the plan's framing ("the Key sheet assigns two of them meaning") slightly overstates that one
  of the two meanings is inferred rather than quoted. This does not weaken the underlying point —
  143 real dash-bearing facts across the two columns would still be destroyed by
  `immutable_words_plan._EMPTY_INFO`-style normalization — so it is **non-blocking**; just soften
  "the Key sheet assigns two of them meaning" to something like "the Key sheet glosses one
  explicitly and the other is self-evident from the column name."
- **`print_deck_table` hardcoding, verified at the cited line.** `immutable_words.py:286` is exactly
  `cards = notes * 2`. Applying that formula to the new Verbs subdeck (179 notes, 4 templates under
  D2) would report 358 cards where the real count is 716 — a 358-card misreport, exactly as
  claimed. Not a defect in the plan: subphase 4.2's own acceptance criteria already name this
  precedent and its cited line and require deriving the count from the note type's template count
  instead, and Risk R12 restates it. This finding is accurate and already fully absorbed by the
  plan; no action needed beyond what 4.2 already specifies.
- **Ask-vs-plan diff, re-run against the updated `the-ask.md`.** Read the full updated ask file
  (with its "Decisions taken at the plan gate (user, 2026-09-26)" section, D1-D6 and Q1-Q4) against
  the amended plan's "Settled decisions" table, Phase 3.3's card-shape table, Phase 8's subphase
  sequencing, and the Risks section. All four items the round-2 dispatch asked me to check are
  faithfully delivered with no inversions:
  - **Four cards per verb (D2)**: plan's field-set/template design gives Verbs 4 templates (Cards
    1-4, impf/perf x front/back), 716 cards — matches "FOUR cards per verb note… not two."
  - **Split slash-adverbs (D3)**: `ROW_SPLITS` table in 3.3 splits `направо / справа` and
    `налево / слева` into 4 rows from 2, mirroring `immutable_words_plan.ROW_SPLITS` exactly as the
    ask specifies — matches "split… into separate notes."
  - **All three real-world mutating steps as executed subphases, sequenced audio -> package ->
    renumber -> import (D6)**: Phase 8 is 8.1 (generate audio — the spend), 8.2 (build the
    `.apkg` — not itself a collection mutation, consistent with the ask's own four-word sequence
    "audio -> package -> renumber -> import"), 8.3 (renumber the live collection), 8.4 (import into
    the live collection) — matches exactly, including that the ask's "three real-world mutating
    steps" (spend/renumber/import) map onto 8.1/8.3/8.4, with 8.2 as the intervening non-mutating
    build-and-verify step the ask's own sequencing already implies.
  - **Declined pre-spend checkpoint (D6)**: Phase 8's preamble and subphase 7.2 both state the
    checkpoint was explicitly declined and that 7.2's exact-number assertions are the substitute —
    matches "A pre-spend checkpoint was explicitly declined… what is removed is the human pause,
    not the machinery," verbatim in spirit.
  - **Arithmetic, recomputed independently from the workbook row counts, not copied from the
    plan**: notes 541+179+152+132 = **1004**; cards (541x2)+(179x4)+(152x2)+(132x2) =
    1082+716+304+264 = **2366**; base-word audio items 541+(179x2)+152+132 = 1183, equivalently
    1004+179 = **1183**; pairs 1183x2 = 2366; requests 2366-14 = **2352**. Every one of these
    matches the ask's D2/D3-updated figures and the plan's own restatements exactly — no arithmetic
    drift found anywhere the two documents restate these numbers.
- **Independently reproduced supporting facts for Phase 1**: the four fixture-path citations
  (`tests/test_audio_naming.py:46`, `tests/test_immutable_words_plan.py:65`,
  `tests/test_immutable_words.py:1221`, `tests/test_elevenlabs_tts.py:282`, constant names
  `REAL_SOURCE_PATH`/`REAL_SOURCE_PATH`/`SOURCE_DOC_PATH`/`SOURCE_WORD_LIST_PATH`) are exact; the
  "154 passed" baseline reproduces exactly (`154 passed in 0.33s`); the old plan's syllabus is
  exactly 5 phase-header checkboxes plus 11 subphase checkboxes, all unchecked, as claimed; the
  docs-grep counts in 1.2's dropped-subphase evidence (`immutable` 0, `elevenlabs`/`ElevenLabs` 0,
  `rebalance` positive control 14, against the real `docs/libs/python/anki-tools/README.md`) are
  exact; `package.json`'s `bin` block has exactly the seven existing entries the plan says 7.1 adds
  alongside, including `anki-immutable-words` and `anki-elevenlabs-tts`.

### Open questions

- **Same open question round 1 raised, not yet closed by this revision**: does the caller want
  subphases 1.1/1.2 executed directly, right now, ahead of and outside this plan's approval/build
  cycle (the routing this review recommends, so the structural check clears before resubmission),
  or does the caller want to formally contest this gate's "do not excuse a legacy layout" reading
  as applied to a fix that is scheduled inside the very plan being blocked, and have that
  interpretation revisited? Either answer unblocks the same one finding; neither is something a
  planner revision can resolve on its own, and no other part of this plan is in question.

## Round 3 — 09-26-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 4
```

### Findings

- [non-blocking] **The structural blocker is cleared — independently re-verified, not taken on the
  builder's word.** Ran `plan-lifecycle.sh check` myself as a bare invocation (no compound command,
  no `--root` flag needed — resolved cwd correctly): `OK: plans dir layout is conformant`, exit 0.
  Also ran `validate-plan.sh` on the plan under review: `OK: plan is structurally valid (21
  subphases)`, exit 0. `project-plans/russian-immutable-words-08-31-26/` no longer exists;
  `project-plans/completed/russian-immutable-words-08-31-26.md` exists. Rounds 1-2's blocking
  finding is resolved by real, committed work, not a plan-text promise.
- [non-blocking] **Both of the builder's two flagged items are correct, independently confirmed.**
  (1) File-scope over-claim: `grep -n "russian-immutable-words-08-31-26\|project-plans"` against
  `anki_tools/elevenlabs_tts.py`, `anki_tools/audio_naming.py`, `anki_tools/immutable_words_plan.py`
  returns nothing (exit 1) — the three cited lines (57/80/198) name "the real 151-row source word
  list," not a path, and that figure is still accurate (`151` still appears in
  `test_elevenlabs_tts.py:20` and `test_immutable_words.py:1214`). The plan's 1.1 file-scope table
  genuinely over-claimed three edits that were never needed; this is a real, now-moot plan defect
  worth recording, not a builder scope violation — ruling as requested. (2) `git mv`-loses-edits
  defect in `plan-lifecycle.sh archive`: `git show a6ee98d:project-plans/completed/russian-immutable-words-08-31-26.md`
  shows every syllabus checkbox still `[ ]` (the pre-edit blob); `git show
  6191a5a:project-plans/completed/russian-immutable-words-08-31-26.md` shows the full reconciled
  syllabus (`[x]` ×10, `[dropped]` on 5.4, the 5.3 supersession annotation) — confirmed in the
  **committed blob**, not the working tree. The defect is real, correctly diagnosed, and correctly
  fixed by a follow-up commit rather than a force-push or amend. This is a bug in the shared
  `plan-lifecycle.sh` tool (affects any future archive that follows an unstaged edit), not a defect
  in this plan or this builder's work — worth a separate report to whoever owns that script, but out
  of scope for this plan's own gate.
- [non-blocking] Independently reran the full package suite (`pnpm test` in `libs/python/anki-tools`):
  `605 passed, 3 skipped in 30.24s` — matches the exit report exactly. Ruff, run correctly scoped to
  the package (cwd matters — a run from the worktree root instead picks up an unrelated pre-existing
  markdown code-fence in `project-plans/anki-due-rebalance-08-12-26/plan.md` and reports a false
  1-file diff; noting this so nobody chases it as a regression): `ruff format --check .` →
  `25 files already formatted`; `ruff check .` → `All checks passed!`. `check-diff-hygiene.sh --base
  main --scope all` → `OK - no attribution, no comment-budget violations`, same 66%-comment note on
  `test_elevenlabs_tts.py` as the exit report, exit 0. All four Phase 1 commits
  (`46fb310`, `a6ee98d`, `6191a5a`, and the merge `5f229ca`) carry no `Co-Authored-By`, no
  `Claude-Session`, no session URL.
- [non-blocking] Fixture and path-constant checks, independently reproduced: `tests/data/source-word-list.md`
  exists (19577 bytes); all four path constants
  (`test_audio_naming.py:41`, `test_immutable_words_plan.py:59`, `test_immutable_words.py:1217`,
  `test_elevenlabs_tts.py:277`) now read `Path(__file__).resolve().parent / "data" /
  "source-word-list.md"` — genuinely self-relative, matching the pattern the plan specified and
  matching `conftest.py`'s own resolution style.
- Spot-verified a broad sample of Phase 2-8 technical claims this review had not yet reached in
  rounds 1-2, against the real installed `anki` 26.8.1 source and `elevenlabs_tts.py`, all confirmed
  accurate: `ExportAnkiPackageOptions` protobuf fields (`with_scheduling`, `with_deck_configs`,
  `with_media`, `legacy`, all `bool`, `import_export_pb2.pyi`); `col.create_backup(*, backup_folder,
  force, wait_for_completion) -> bool` (`collection.py:332-353`); `DeckManager.rename(deck, new_name)
  -> OpChanges` with docstring *"Rename deck prefix to NAME if not exists. Updates children."*
  (`decks.py`); the exact `add_or_update_notetype(json=..., preserve_usn_and_mtime=True,
  skip_checks=False)` call shape, confirmed byte-for-byte in the *existing*
  `immutable_words.clone_note_type` this plan's 4.1 is patterned on; `immutable_words.py`'s
  `print_deck_table` hardcode (`cards = notes * 2` at line 286, confirmed exact) — the R12/4.2 defect
  round 2 already flagged, re-confirmed at the cited line; `tests/test_min_separation_e2e.py` and
  `tests/test_separation_repair_e2e.py` exist as the cited e2e pattern for 7.2;
  `pyproject.toml`'s `[tool.hatch.build.targets.wheel] packages = ["anki_tools"]`, consistent with
  3.2's packaging claim; `elevenlabs_tts.py`'s `RequestBudget` (line 280), `get_api_key` (319),
  `fetch_tts_audio_metered` (495), `build_and_save`/`build_and_save_batch` (538/659),
  `CONFIRM_ABOVE_REQUESTS = 1` (113) all present and at the cited proximity. Lane file-scope
  disjointness for Phases 3-6 re-checked against the current file-scope tables: still fully disjoint,
  unchanged from round 1's audit.
- **Phase 8 soundness, assessed as requested** (the real-world mutating executions, authorized by D6
  with the pre-spend checkpoint explicitly declined): the sequencing (audio -> package -> renumber ->
  import), the exact-count hard stop in 8.1 (dry-run must read `pending 2352` or the run stops), the
  backup-before-first-write discipline in both 8.3 and 8.4, the reverse-order renumber against the
  `UNIQUE` name index, and the deck-id/card-count verification after 8.3 are all consistent with the
  underlying API facts (confirmed above) and with D6's explicit terms — "every safety mechanism stays
  in force; what is removed is the human pause, not the machinery." No gap found beyond what R1-R3
  already name and mitigate. Confirmed as still-unexecuted, not a race with this review: no
  `mutable_words*.py` / `vocabulary_source.py` / `renumber_russian_decks.py` / `anki_identity.py` /
  `card_audio.py` module exists yet in the worktree, no `~/Desktop/mutable-words.apkg` exists, and
  `~/Desktop/russian-audio` holds only the 208 pre-existing immutable-words files (52 words x 4
  slots), not the 2366 mutable-words pairs — matching the dispatch's statement that Phases 2-9 have
  not been built. R9's claim (`.env` absent from the workflow worktree, present at the repo root)
  reproduced exactly; the source workbook and the live collection file both exist at their cited
  paths.
- No open decision points or ask-vs-plan divergences found beyond what rounds 1-2 already settled;
  the ask file (`the-ask.md`) is unchanged since round 2's diff, and Phase 1's execution is the only
  change to the plan's own text since round 2 (its syllabus entries flipped from pending to `[x]`,
  which now reflects reality).

### Open questions

None. Both open questions rounds 1-2 raised (old-plan-dir disposition; the gate's own "do not excuse
a legacy layout" reading) are moot — the caller resolved them by doing the executable work directly,
which is exactly the routing round 2 recommended, and this round confirms the result rather than
re-litigating the interpretation question.
