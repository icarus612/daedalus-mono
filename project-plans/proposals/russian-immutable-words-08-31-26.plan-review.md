# russian-immutable-words-08-31-26.plan-review

## Round 1 — 08-31-26

```
verdict: rejected
next: plan-wrong
blocking: 2
non-blocking: 2
```

### Findings

- [blocking] **Subphase 1.3's stated ambiguity-resolution algorithm does not
  produce the numbers its own acceptance criteria (and Decision D1's "Option
  A") claim it produces — verified by independently implementing the
  algorithm exactly as written and running it against the real
  `.artifacts/col-snapshot.anki2` and `.artifacts/source-word-list.md`.**

  The prose (lines 358–367) defines the policy as: "among the candidate
  notes for a row, prefer one … under Master Russian 300+; break a
  remaining tie by lowest note_id; a note already claimed by an earlier row
  is not available, and a row left with **no available candidate** falls
  through to CREATE." Read literally, this filters a row's hit-set down to
  unclaimed candidates, prefers a Master-Russian one among what's left, and
  only CREATEs when that filtered set is **empty**.

  I ran exactly that: parsed the real source doc (152 rows, 43/35/32/42 —
  confirmed), built the normalized index from all 707 real
  `Languages::Russian` notes in the snapshot, and processed rows in the
  stated document order (Prepositions → Conjunctions → Particles →
  Indeclinable, ascending rank). Result for the three ambiguous rows:
  - `что` (Conj #2): candidates `{754, 856}`, both Master Russian → picks
    `754` (lower id). Matches the plan's stated Option A/B behavior for this
    row (both options agree here).
  - `да` (Conj #20, processed first): candidates `{1699033385794` (Master
    Russian), `1711350738175` (100 Words)`} → picks the Master Russian one,
    `794`. Matches the plan.
  - `да` (Particles #20, processed second): candidates are the **same two
    notes**; `794` is now claimed, but `175` is **not** claimed by anything
    else and is still in the row's hit-set. By the stated rule ("no
    available candidate" is the only CREATE trigger), the available set is
    `{175}` — non-empty — so the row **moves** via `175`. This is Option
    B's outcome (43 moves / 109 creates), **not** Option A's claimed outcome
    (42 moves / 110 creates, Particles 15/17) that subphase 1.3's own
    acceptance-criteria table stars as the default.

  So the algorithm as specified computes Option B by default, while the
  plan documents it as computing Option A by default and asks the user to
  choose between A/B/C at the gate as if the written algorithm already were
  A. Either the algorithm prose is missing an unstated rule (something like
  "ambiguity resolution never falls back to a non-Master-Russian candidate,
  even if it is the sole survivor — only a single, unambiguous hit at step
  3 can select one"), or subphase 1.3's acceptance criteria / Decision D1's
  "Option A" description need to change to match what the written algorithm
  actually does. As written, a coder implementing 1.3 from the prose alone
  and a contract-tester writing tests from the same prose could reasonably
  land on either number, and the acceptance criteria table would fail
  against a correct implementation of the stated rule. This is exactly the
  ambiguity the plan itself calls "the one that changes the shipped
  numbers," so it must be pinned down textually (not just resolved by
  gate-time verbal agreement) before build.

  Recommendation: revise 1.3's prose to state explicitly that ambiguity
  resolution only ever assigns a **Master-Russian-tier** candidate or
  CREATEs — never a lower-tier candidate as a fallback — if Option A is
  still the intended default; or, if Option B's literal-algorithm behavior
  is actually preferred, update Decision D1's "Option A" row and 1.3's
  starred acceptance-criteria table (42/110, Particles 15/17) to read 43/109
  and Particles 16/16 instead.

- [blocking] **Subphase 1.4's second acceptance criterion asserts things that
  are not in Card 2's `afmt`, and would fail as written against a correct
  implementation.** The criterion reads: "Applied to Card 2's `afmt`,
  **likewise**, and `{{Translation}}`, `{{Additional Info}}` and the
  `addTitle` script survive." The preceding bullet, which "likewise" refers
  back to, requires the result to "still contain `{{Russian}}`, `{{Audio}}`,
  `{{hint:Pronunciation}}`, `<div id="deck">{{Deck}}</div>` and the full
  `dName[dName.length-1].split(". ")[1]` script."

  Dumped note type `1698803891108` from a throwaway copy of
  `.artifacts/col-snapshot.anki2`. Card 2's `afmt` (723 bytes) is
  `{{FrontSide}}` + `{{Audio}}` + `{{Russian}}` + `{{hint:Pronunciation}}` +
  `{{Part of Speech}}` + `{{Additional Info}}` + the `addTitle` script. It
  contains **no** `{{Translation}}`, **no** `<div id="deck">{{Deck}}</div>`
  and **no** `split(". ")[1]` script — those live in Card 2's **`qfmt`**
  (365 bytes: deck div + `{{Translation}}` + the header script). A
  contract-tester writing tests from this bullet, as subphase 1.4's test
  approach instructs ("each of the four bullets above is asserted against
  them"), produces a test that fails against a correct `strip_part_of_speech`.

  Everything else in 1.4 is correct and was re-verified: the two
  `{{Part of Speech}}` occurrences are byte-identical
  (`\t<div id="part-of-speech">{{Part of Speech}}</div>\n`, 51 bytes), they
  sit on Card 1 `qfmt` and Card 2 `afmt` only, and Card 1 `afmt` / Card 2
  `qfmt` are untouched by the transform (byte-identity confirmed: 486→435,
  598→598, 365→365, 723→672).

  Recommendation: restate the bullet as what Card 2's `afmt` actually holds —
  no `{{Part of Speech}}` / `id="part-of-speech"` afterwards, with
  `{{FrontSide}}`, `{{Audio}}`, `{{Russian}}`, `{{hint:Pronunciation}}`,
  `{{Additional Info}}` and `addTitle` surviving — and move the `{{Deck}}` /
  header-script assertion onto Card 2's `qfmt`, where the identity case
  already covers it.

- [non-blocking] **Subphase 3.2's acceptance criterion cites the wrong
  pre-existing test count.** It says "the pre-existing 192 tests still pass
  unmodified". `pytest --collect-only -q` in
  `libs/python/anki-tools` reports **195 tests collected** (across
  `test_due_plan.py`, `test_due_stats.py`, `test_followup_fixes.py`,
  `test_rebalance_due.py`). The number is factually wrong, not merely stale
  in spirit; it is non-gating only because it changes no design decision and
  the correction is a single digit. Replace 192 with 195, or phrase it as
  "the pre-existing suite still passes unmodified" so it cannot drift again.

- [non-blocking] **Subphase 1.2's list of punctuated rows names 12 of the 17
  that actually exist**, which under-specifies the parametrized table it
  mandates. Re-parsing `.artifacts/source-word-list.md` gives 17 rows whose
  Russian cell trips the predicate (Prepositions #1, #3, #5, #10;
  Conjunctions #8, #16, #18, #23, #24, #26, #27, #28, #29, #30; Particles
  #16, #24, #25); the five the plan does not name are `то... то...`
  (Conj #24), `для того, чтобы` (#27), `с тех пор, как` (#28),
  `до того, как` (#29) and `перед тем, как` (#30). Those last four
  comma-bearing subordinator rows are the interesting
  omission: they are the only cases that exercise the `,` arm of the
  predicate other than `несмотря на то, что`, and they are exactly the rows
  a naive "`/` or `...` or leading `-`" implementation would silently
  misclassify as moves. The plan's false-cases list (`ну и`, `всё-таки`,
  `из-за`, `из-под`, `потому что`, `так как`, `то есть`) is complete and
  correct as written — all seven verified against the doc.

### Verified independently (second pass)

A second, independent verification pass was run over the plan's highest-risk
claims, recomputing rather than re-reading. All of the following reproduced
exactly:

- **The D1 partition arithmetic.** Re-parsed the doc (152 rows: 43/35/32/42)
  and re-derived the partition from the snapshot: **43 rows classify as move,
  matching 45 distinct notes**, via the three ambiguous rows the plan names,
  with the exact note ids it lists (`1699033385754`/`…856`;
  `1699033385794`/`1711350738175`; `1699033385804`/`1711350738176`). Naive
  per-POS split is Prepositions 15/28, Conjunctions 12/23, Particles 16/16,
  Indeclinable Nouns 0/42 — identical to the ask's table. The named move
  lists in 1.3's acceptance criteria are byte-correct for both Prepositions
  (15 words) and Conjunctions (12 words).
- **Both D1 options' costed numbers.** Implementing option A (Master-Russian
  tier as a hard filter) yields 42/110, Particles 15/17, MR 321→280, 100
  Words 100→99 — exactly as the plan states. Implementing option B yields
  43/109, Particles 16/16, MR 321→280, 100 Words 100→98 — exactly as stated.
  Option C's MR 321→279 also checks out (the 45 candidates split 42 Master
  Russian / 3 100 Words). The plan's claim that the ask's headline table and
  its provenance sentence "cannot both be true" is correct: option C is the
  only reading giving 42 out of Master Russian, and it takes **3** notes out
  of 100 Words, not the 1 the ask's sentence asserts. Also confirmed:
  `1711350738196` (`Пока`) is the **only** row whose sole candidate lies
  outside Master Russian, and all **45** candidate notes are on note type
  `1698803891108`.
- **R5 / risk R-B — the retype preserves scheduling.** On a private copy:
  `change_notetype_info` derives `new_fields == [0,1,2,3,4,5]` and
  `new_templates == [0,1]`. Retyping five real notes drawn from both source
  decks (`1699033385754`, `…794`, `…804`, `1711350738175`, `1711350738196`)
  left the card-id set identical and every
  `(nid, ord, type, queue, due, ivl, factor, reps, lapses, did, odid, revlog count)`
  tuple **byte-identical**, with all six field values unchanged. Only `mid`
  changed. The plan's claim is accurate.
- **Risk R-A — the full sync is real and unavoidable on this route.**
  `col.schema_changed()` was `0` on open, still `0` after `add_dict`, and
  became `1` immediately after `change_notetype_of_notes`. The mitigation
  text (sync before, close Anki, choose *Upload to AnkiWeb* at the next
  sync, then re-sync other devices) is correct Anki advice for a
  schema-modifying change.
- **R2 — the `<letter>. ` leaf-prefix contract.** Both templates' *question*
  sides (Card 1 `qfmt`, Card 2 `qfmt`) run
  `deck.innerHTML = "Russian - " + dName[dName.length-1].split(". ")[1];`.
  Subphase 2.3's assertion (every leaf name contains `". "` after its last
  `::`, asserted over the module-level constant) genuinely protects it for
  the four proposed leaves.
- **Card generation.** A fresh note on the clone with `Russian` and
  `Translation` filled generates exactly 2 cards, both in the target leaf,
  both new (`type=0, queue=0`) — so 152 notes → 304 cards holds.
- **Repo claims.** `anki` **26.8.1** at `uv.lock` lines 238–241; `due_plan.py`
  has zero Anki imports and exposes `validate_bounds` / `build_target_line`;
  `rebalance_due.py` has `build_parser()`, `get_anki_collection_path()`,
  `resolve_deck_ids`, `collect_cards`, `apply_moves`, `render_histogram`,
  `create_backup(...)`, `raise SystemExit(n)`, the
  `input("Apply these changes? [y/N] ")` prompt, the "Make sure Anki is not
  running" message, and the five flags the plan reuses. The plan's
  *deliberate* divergence from `rebalance_due`'s order is real and correctly
  described: `rebalance_due` backs up at line ~417 **before** its
  `if args.dry_run:` at line 526, so it does take a `.colpkg` on a dry run;
  the new tool exiting before the backup is a stated, reasoned departure,
  not a silent one. `build_deck.py:33`'s `parse_known_args()` tuple bug
  exists and is correctly scoped out.
- **Lint baseline.** `ruff format --check .` → "12 files already formatted"
  (exit 0); `ruff check .` → "All checks passed!" (exit 0). The README's
  line 151 claim of "11 pre-existing findings" plus a `black`/`flake8` hook
  is confirmed stale, as the plan says.
- **Ask-vs-plan faithfulness.** All eight capture-time decisions are honored:
  POS leaf with both cards together (2.4 issues one `set_deck` per leaf over
  all of a note's cards); `2. Immutable Words` (2.3); plural leaf names
  (2.3); punctuation as *literal* doc-row punctuation and explicitly not the
  stress mark (1.2); all 152 rows covered (1.1, 1.3); multi-form rows kept
  verbatim as one note (1.1); duplicates moved not copied (1.3/2.4); new
  note type dropping the Part-of-Speech render (1.4/2.2). All four of the
  ask's "open decisions the planner must surface" are surfaced as D1–D4. No
  inversion found, and nothing is delivered that the ask did not ask for.
- **Snapshot integrity.** `.artifacts/col-snapshot.anki2` is unchanged —
  same size (35782656) and mtime as at hand-off, with no `-wal`/`-shm`
  siblings. All collection work was done on private copies.

### Open questions

- Decisions D1–D4 are correctly surfaced in the plan as user choices, not
  planning defects, and D1's three options are otherwise faithfully
  computed (the `что`/`да`(Conj)/`нет` resolutions all check out against
  the real snapshot). Once the blocking finding above is resolved,
  confirming D1 (with correct numbers for whichever variant is written
  down), D2, D3, and D4 with the user remains a gate-time step, not a
  re-verification item.
