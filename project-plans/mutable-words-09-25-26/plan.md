# Russian Mutable Words — deck package builder, four note types, ElevenLabs audio

## Phase syllabus

- [ ] Phase 1: Fixture relocation and old-plan closeout
  - [x] 1.1: Relocate `source-word-list.md` out of the plan dir into `tests/data/`
  - [x] 1.2: Reconcile the old plan's syllabus with what shipped, then archive it   (after: 1.1)
- [ ] Phase 2: Shared foundation
  - [x] 2.1: Hoist deterministic Anki identity helpers into `anki_identity.py`      (after: 1.1)
  - [x] 2.2: Hoist the audio-picker block into a parameterized `card_audio.py`      (after: 2.1)
  - [x] 2.3: Add the `openpyxl` dependency and relock
- [ ] Phase 3: Source of truth
  - [ ] 3.1: `vocabulary_source.py` — workbook reader + TSV writer                  (lane 1, after: 2.3)
  - [ ] 3.2: Commit the four TSVs and their provenance README                       (lane 1, after: 3.1)
  - [ ] 3.3: `mutable_words_plan.py` — pure core                                    (lane 1, after: 2.2, 3.2)
- [ ] Phase 4: Deck package builder
  - [ ] 4.1: Four note types in a scratch collection                                (lane 2, after: 3.3)
  - [ ] 4.2: Deck tree, notes, media attach, `.apkg` export + CLI                   (lane 2, after: 4.1)
- [ ] Phase 5: Audio generation tooling
  - [ ] 5.1: Work-set computation and exact budget sizing                           (lane 3, after: 3.3)
  - [ ] 5.2: `mutable_words_audio.py` resumable driver + CLI                        (lane 3, after: 5.1)
- [ ] Phase 6: Deck renumbering tooling
  - [x] 6.1: `renumber_russian_decks.py` — reverse-order rename, backup, revert     (lane 4, after: 1.2)
- [ ] Phase 7: Integration and dry-run verification
  - [ ] 7.1: Entry points — `package.json` bin + module guards                      (after: 4.2, 5.2, 6.1)
  - [ ] 7.2: End-to-end dry run over the real source, zero network, zero mutation   (after: 7.1)
- [ ] Phase 8: Execution against the real world
  - [ ] 8.1: Generate the 2352 recordings                                           (after: 7.2)
  - [ ] 8.2: Build and verify the real `.apkg` with media attached                   (after: 8.1)
  - [ ] 8.3: Back up and renumber the live collection                                (after: 8.2)
  - [ ] 8.4: Import into the live collection and verify                              (after: 8.3)
- [ ] Phase 9: Records
  - [ ] 9.1: Runbook — what was executed, and how to reverse each step              (after: 8.4)
  - [ ] 9.2: Docs                                                                   (after: 9.1)

---

## Goal & scope

**Ask of record**: `/home/icarus64/repos/daedalus-mono/.workflows/mutable-words/.artifacts/the-ask.md`
(durable file; read in full before this plan was written, and updated at the plan gate with a
"Decisions taken at the plan gate" section recording D1–D6 and Q1–Q4). Its five original gate
decisions **and** the eleven settled at the plan gate are FIXED constraints, not open questions.

Supersedes nothing. Subphase 1.2 **archives** `project-plans/russian-immutable-words-08-31-26/` as
finished work — archival, not supersession: its scope shipped and none of it carries over here.

### In scope

Build a new `Languages::Russian::3. Mutable Words` deck tree — four subdecks, one per sheet of
`~/Downloads/russian_vocabulary.xlsx`, with one purpose-built note type per subdeck — generate
ElevenLabs TTS audio for each card's base word(s) in exactly two voices (`f1` Alisa, `m2` Nester
Surovy), and **execute** the result into the user's live collection. Concretely:

1. Relocate the still-live `source-word-list.md` test fixture out of an unarchived plan directory,
   then close that plan out properly (Phase 1). This is first because the plans-dir layout check
   currently fails, and because leaving the fixture where it is arms a break of 154 passing tests
   the moment anyone correctly archives that plan.
2. A reproducible, committed, diffable source of truth in the repo, converted once from the
   workbook (the workbook itself lives outside the repo and cannot be a build input).
3. Four new note types with deterministic ids, four new subdecks, **1004 notes / 2366 cards**,
   exported as a standalone `.apkg` built **without ever mutating the real collection** — the safety
   property `anki_tools/immutable_words.py` already establishes.
4. A resumable, exactly-budgeted TTS driver producing 2366 `.mp3` files (**2352 new network
   requests**) into both the review directory and the Anki media directory, via the existing
   `anki_tools/elevenlabs_tts.py` choke point.
5. A backed-up, dry-runnable, revertible CLI that renumbers the three existing sibling decks
   (`3.`→`4.`, `4.`→`5.`, `5.`→`6.`).
6. **Executing** all of it (Phase 8): the real spend, the real renumber, the real import — authorized
   by the user at the plan gate (decision D6), with no pre-spend checkpoint (explicitly declined).
7. Records: a runbook of what was executed and how to reverse each step, plus docs (Phase 9).

### Explicitly out of scope

- Touching the five existing `2. Immutable Words` subdecks' **notes, note types, or audio**.
  Phase 1.1 moves a test fixture; Phases 2.1/2.2 refactor code those modules import, under
  byte-identical-output requirements. Neither changes the note type, the templates, or any note.
- Changing `elevenlabs_tts.VOICES` / `DEFAULT_VOICES` / the CLI's `--all-voices` semantics for other
  callers. The two voices are selected **at the call site**, per the ask.
- Re-recording or re-slotting any existing audio. The seven words whose slugs already exist in the
  Anki media directory (`кафе`, `кино`, `кофе`, `метро`, `пальто`, `просто`, `согласно`) reuse the
  existing recordings; nothing overwrites them.
- Filling the workbook's empty "yellow" columns. Per decision **D5** they become note fields and
  ship blank, so the user can fill them in Anki later.
- Re-litigating D1–D6 or Q1–Q4. All are settled; see "Settled decisions" below.

### Settled decisions (were decision points; now constraints)

| Id | Resolution |
|---|---|
| **D1** | **Hoist** (option a). Phases 2.1/2.2 proceed, under byte-identical-output acceptance criteria. |
| **D2** | **FOUR cards per verb note** (option b — not the planner's default). Imperfective and perfective each get a full recall pair, so verbs contribute **716** cards, not 358. |
| **D3** | **Split** `направо / справа` and `налево / слева` into separate notes (option a), mirroring `immutable_words_plan.ROW_SPLITS`. Adverbs 130 → **132** notes; base words **1183**; pairs **2366**; requests **2352**. |
| **D4** | **Drop** the `Status` column. |
| **D5** | **Keep** the empty "yellow" columns as blank fields. |
| **D6** | **This run executes** the three real-world steps — the spend, the renumber, the import (Phase 8). **A pre-spend checkpoint was explicitly declined**: no smoke test, no sample card for sign-off before the full 2352 requests. Every safety mechanism already designed stays in force. |
| **Q1** | Note-type names carry "Mutable": `Russian - Mutable Nouns (Ellis Version)`, `… Verbs …`, `… Adjectives …`, `… Adverbs …`. |
| **Q2** | Subdeck lettering `a. Nouns` / `b. Verbs` / `c. Adjectives` / `d. Adverbs`, in workbook sheet order — as assumed. |
| **Q3** | The answer-side details block follows the existing `addTitle` pattern — as assumed. |
| **Q4** | Audio on `Card 1`'s front and on the reverse card's back — as assumed, extended to all four verb templates. |

---

## Stack & MAJOR versions

Every version below was read from a manifest or lockfile in this worktree — none from memory.

| Thing | Version | Verified from |
|---|---|---|
| Python | `>=3.11`, repo pins `3.11` | `libs/python/anki-tools/pyproject.toml` `requires-python`; `.python-version` |
| Package manager (Python) | `uv`, workspace lock | root `pyproject.toml` `[tool.uv.workspace]`; `uv.lock`; `libs/bash/build-tools/py-scripts/py-test` (`uv run --group dev pytest`) |
| Package manager (JS) | `pnpm@9.1.0` | root `package.json` `packageManager` |
| Monorepo runner | `turbo` 2.5.5 | root `package.json` |
| `anki` | **26.8.1** (reports itself as `26.08.1`) | `uv.lock` lines 239-241; `.venv/.../anki/buildinfo.py` |
| `requests` | `>=2.28.0` | `libs/python/anki-tools/pyproject.toml` |
| `pytest` | dev group | `libs/python/anki-tools/pyproject.toml` `[dependency-groups] dev` |
| `ruff` | `>=0.8`, `line-length = 88`, `target-version = "py311"`, `select = ["E","W","F","I"]`, `known-first-party = ["anki_tools"]` | root `pyproject.toml`; `ruff.toml` |
| `openpyxl` | **NOT PRESENT** — `grep -c openpyxl uv.lock` → `0` (positive control: `grep -c requests uv.lock` → `21`). Phase 2.3 adds it and records the version `uv lock` actually resolves. | `uv.lock` |
| `pandas` | 3.0.5 present in `uv.lock`, but declared by `market-bots` / neural-network members, **not** by `anki-tools`; it would itself need `openpyxl` to read `.xlsx`, so it is strictly worse here. | `uv.lock` line 2343; root `pyproject.toml` members |

### Anki API facts this plan depends on (verified against the installed 26.8.1, not memory)

- `col.decks.rename(deck: DeckId | DeckDict, new_name: str) -> OpChanges` — `anki/decks.py:273-279`,
  backend stub `anki/_backend_generated.py:583-590`. Not deprecated. Docstring: *"Rename deck prefix
  to NAME if not exists. Updates children."*
- **Rename preserves cards and scheduling.** The request carries only `deck_id` + `new_name`
  (`anki/decks_pb2.pyi:760-775`); the deck id is an input and is never reassigned. Cards reference
  decks by id (`Card.did`, `anki/cards.py:45`; `DeckManager.cids` does
  `select id from cards where did=?`, `anki/decks.py:398-404`). Nothing on the rename path touches
  the `cards` table. Scheduling columns live on the card row and are untouched.
- **Children auto-rename**, because deck names are `::` paths — backend symbol
  `anki::decks::name::…::rename_child_decks` present in `_rsbridge.so`. Renaming
  `4. 100 Words & Phrases` carries `::a. Listening` and `::b. Recall` with it.
- **Deck names are DB-unique** — `CREATE UNIQUE INDEX idx_decks_name ON decks (name);` (string
  embedded in `_rsbridge.so`, confirmed by `strings`), and the rename docstring says *"if not
  exists"*. This is why the renumber runs in **reverse order** (5→6, then 4→5, then 3→4) and
  pre-checks with `col.decks.id_for_name()` (`anki/decks.py:149-153`).
- `col.create_backup(*, backup_folder: str, force: bool, wait_for_completion: bool) -> bool` —
  `anki/collection.py:332-354`. Already used by `anki_tools/rebalance_due.py:532`.
- Opening a collection is **exclusive**; there is no read-only mode. A locked file raises
  `anki.errors.DBError` (`anki/_backend.py:227-228`) with the message *"Anki already open, or media
  currently syncing."* The workaround is to copy the `.anki2` and open the copy.
- **Field-name validity**: the leading-character rule is confirmed verbatim in the Python source —
  *"The field name should not start with #, ^ or /"* (`anki/_fluent.py:5711-5714`). The
  contains-rule is a templated Fluent string whose literal Python-side text reads *"The field name
  should not contain :, ", or ."* (`anki/_fluent.py:5717-5720`) — the specific character list is
  interpolated at runtime from Fluent template args, so **the exact forbidden set could not be
  independently confirmed from this source**. Treat `:`, `"`, `{`, `}` as forbidden (the
  conventional set) and rely on subphase 4.1's live check — `build_col.new_note(nt)` must accept
  every generated note type — as the actual proof that the chosen names are legal.

### Source workbook facts (read directly from `~/Downloads/russian_vocabulary.xlsx`)

| Sheet | Data rows | Base-word column(s) | Audio items/row | Notes after D3 split |
|---|---|---|---|---|
| Nouns | 541 | `Russian` | 1 | 541 |
| Verbs | 179 | `Imperfective` **and** `Perfective` (both non-empty on all 179 rows) | 2 | 179 |
| Adjectives | 152 | `Russian (m)` | 1 | 152 |
| Adverbs | 152 rows, **130 real** | `Adverb` | 1 | **132** (two rows split) |

- The workbook's own `Key` sheet states the totals independently: Nouns 541 / Verbs 179 /
  Adjectives 152 / Adverbs 130 / **Total 1002** — matching the row counts above.
- **22 Adverbs rows are placeholders.** Four independent signals agree exactly (all 22, same rows,
  no partial-signal row exists): `Adverb == "—"`, `Formation == "none"`, `English == ""`,
  `Status == ""`. The `Key` sheet says so in prose too: *"Formation 'none' rows have no true adverb
  … they're left out of the progress counts."*
- **Base words carry no stress marks** — 0 of 1183 contain a combining acute (U+0301); the `Stress`
  column carries the marked form.
- **No cell in the four data sheets contains a tab, CR, or LF**; the longest cell **across the four
  data sheets** is 75 characters (Verbs row 76, `Case / Preposition`). TSV is therefore a lossless,
  safe container. (The `Key` sheet has a 160-character prose cell, but `vocabulary_source.py` never
  reads `Key`, so that figure applies to nothing this plan builds. Positive control: the tab
  detector does fire on a string that has one.)
- **`Status` is `"New"` on 1002 of 1002 real rows — 100%, with no other value anywhere.** The only
  22 empty `Status` cells are the Adverbs placeholder rows, which are excluded before any note is
  built. The workbook's `Key` sheet agrees (`New=1002`). A fully uniform column carries no
  information, which is why **D4** drops it.
- **Dash-only cells are MEANINGFUL and must never be blanket-normalized.** Exactly four columns
  contain dash-only cells, and the `Key` sheet assigns two of them meaning:
  `Nouns.Plural` **107** cells (*"Plural '—' = no plural in everyday use"* — a real linguistic
  fact), `Adverbs.Comparative` **36** cells (no comparative form), plus `Adverbs.Adverb` 22 and
  `Adverbs.Stress` 22, which are the placeholder rows that get dropped. Every other column has
  **zero** dash-only cells. `immutable_words_plan._EMPTY_INFO` collapses `—`/`–`/`-`/`--` to `""`;
  copying that rule here would silently destroy 143 real facts. The rule for this plan is therefore
  **preserve every cell verbatim and normalize nothing** — see the assertion in 3.2.
- Many "yellow" columns are empty except the row-1 example: Nouns `Genitive Sg`/`Genitive Pl` (540
  of 541 empty), Verbs `Conjugation`/`я (1sg)`/`ты (2sg)`/`они (3pl)`/`Past (m / f)`/`Case /
  Preposition` (178 of 179 empty), Adjectives `Short Form`/`Comparative` (151 of 152 empty). Per
  **D5** they ship as blank fields.
- **The two D3 split rows, verbatim** (so the builder needs no judgement):

  | `#` | `Adverb` | `English` | `Stress` | `From Adjective` | `Formation` | `Comparative` |
  |---|---|---|---|---|---|---|
  | 104 | `направо / справа` | `to the right / on the right` | `напра́во / спра́ва` | `правый` | `irregular` | `—` |
  | 105 | `налево / слева` | `to the left / on the left` | `нале́во / сле́ва` | `левый` | `irregular` | `—` |

  All three slash-joined cells (`Adverb`, `English`, `Stress`) split in parallel on `" / "`;
  `From Adjective`, `Formation`, `Comparative`, `Additional Info` are shared by both halves.

### Collision check over the full new word set — run, and clean

Required by `audio_naming.sanitize_word_slug`'s docstring, whose collision-free guarantee was only
ever verified against the old 151-row list. Computed with the real `sanitize_word_slug` over all
**1183** base-word instances (post-D3-split):

- **1183 instances → 1183 distinct slugs. Zero collisions.** No two genuinely different strings
  sanitize to the same slug, and no string appears twice within the new set.
- **7 slugs overlap the 205 slugs already in the Anki media directory**: `кафе`, `кино`, `кофе`,
  `метро`, `пальто`, `просто`, `согласно`. All seven are byte-identical Russian strings to existing
  immutable-words rows — the "legitimate shared file" case the docstring names, not a collision.
  Nothing is overwritten. (Re-verified after the D3 split: still exactly these seven.)

Subphase 3.3 makes this an assertion in the pure core, so a future edit to the TSVs that introduces
a real collision fails the suite instead of silently producing two cards pointing at one recording.

### Existing collection facts (read from a COPY; the original was never opened)

- Source note type `1698803891108` is actually named **`Russian - Common Words (Ellis Version) `**
  (trailing space) — not "Immutable Words". `immutable_words.py` looks it up by id precisely to
  dodge that. 6 fields; only `Pronunciation` has a non-`None` field id (`205146537490678414`).
  2 templates (`Card 1` Russian→Translation, `Card 2` Translation→Russian).
- `Russian - Immutable Words (Ellis Version)` exists, id `3897610691970966744`, 7 fields
  (`AudioRefs` last), 207 notes / 414 cards, CSS byte-identical to the source note type's.
- Deck tree today: `1. Alphabet` (33 cards), `2. Immutable Words` + 5 subdecks (207 notes / 414
  cards), `3. Sentences (lingo llama)` (253 cards), `4. 100 Words & Phrases` (+ `a. Listening` 100,
  `b. Recall` 100), `5. Master Russian 300+` (+ `a. Listening` 321, `b. Recall` 321). **Nothing
  named `Languages::Russian::6.` exists**, so the reverse-order renumber has a free first step.
- The shared CSS/JS builds the card header with `deckName.split("::")` then `.split(". ")[1]`, so
  **every leaf deck name must contain a `". "`** — the `a. `/`b. `/`c. `/`d. ` prefixes are
  load-bearing, not decorative (already documented at `immutable_words_plan.subdeck_name`).

### Deck and card counts — recomputed under D2 and D3

| Subdeck | Notes | Templates/note | Cards |
|---|---|---|---|
| `…::3. Mutable Words::a. Nouns` | 541 | 2 | 1082 |
| `…::b. Verbs` | 179 | **4** (D2) | **716** |
| `…::c. Adjectives` | 152 | 2 | 304 |
| `…::d. Adverbs` | **132** (D3) | 2 | 264 |
| **Total** | **1004** | — | **2366** |

Arithmetic: 541 + 179 + 152 + 132 = 1004 notes; (541 × 2) + (179 × 4) + (152 × 2) + (132 × 2) =
1082 + 716 + 304 + 264 = 2366 cards.

> **Coincidence warning, stated so nobody conflates the two.** The card total (**2366 cards**) and
> the audio-pair total (**2366 `(word, slot)` pairs**) are numerically identical and completely
> unrelated — one is 4 templates × 179 verbs plus 2 × 825 other notes, the other is 1183 base words
> × 2 voices. A reviewer who sees "2366" in two places is not seeing a copy-paste error.

### Cost control — the exact expected request count, derived from real row counts

| Quantity | Value | Derivation |
|---|---|---|
| Source words after the D3 split | 1004 | 541 + 179 + 152 + 132 |
| Base-word audio items | **1183** | 1004 + 179 (verbs' second aspect) |
| Voices | 2 | `f1` Alisa (`t6lBrEl93uCiLR1Lgm8v`), `m2` Nester Surovy — `elevenlabs_tts.VOICES` slots |
| `(word, slot)` pairs | **2366** | 1183 × 2 |
| Pairs already on disk in the Anki media dir | 14 | the 7 overlapping words × 2 slots |
| **Network requests required** | **2352** | 2366 − 14 |

**A verified defect this plan must route around.** `elevenlabs_tts.build_and_save` skips a pair for
free only when the file exists in **both** the primary output dir and the Anki media dir. All 14
overlapping pairs exist in `~/.local/share/Anki2/User 1/collection.media` but **not** in
`~/Desktop/russian-audio` (checked pair by pair: present-in-media 14, present-in-both 0), so a naive
`build_and_save_batch` call would re-issue 14 paid requests and then refuse to overwrite the media
file anyway. Subphase 5.1 therefore computes the work set against the **Anki media directory** — the
authoritative location — and narrows the `voices=` list per word before calling `build_and_save`.

---

## Conventions to enforce

Hard constraints. A violation is a defect, not a preference.

1. **`uv` for Python, `pnpm` for JS.** Never `npm`, `yarn`, `pip`, or `python -m venv`. Tests run
   via `pnpm test` → `py-test` → `uv run --group dev pytest`. Lint via `pnpm lint` → `py-lint` →
   `uv run ruff format --check .` then `uv run ruff check .`, from the repo root.
2. **Minimal code comments** (`~/.claude/rules/minimal-code-comments.md`). Explanatory prose goes in
   `/docs`, never inline. **Tests are not exempt** — a test file that is a quarter comment lines is
   a violation. The existing `anki_tools` modules carry very heavy docstrings; **that is
   pre-existing debt and is NOT the pattern to copy** (see R7). New modules get short module
   docstrings and short contract-stating function docstrings, nothing more.
   `check-diff-hygiene.sh` runs at builder teardown and `pr-ready-hygiene-guard.sh` at the
   draft→ready flip — a builder that mirrors the neighbours' comment density will fail that hook.
3. **The real collection is mutated in exactly two places**, both in Phase 8, both after a backup:
   `renumber_russian_decks.py` (8.3) and the Anki import (8.4). Every other module either opens no
   collection or opens one and asserts its mtime is unchanged afterwards
   (`immutable_words.assert_unmodified`). **No test ever touches the user's collection**; tests use
   a scratch `Collection` under `tempfile.mkdtemp`.
4. **Never bypass `RequestBudget`.** Every real request goes through
   `elevenlabs_tts.fetch_tts_audio_metered`, which takes a required `RequestBudget`. New code
   constructs a budget sized to the exact computed work set and passes it down; it never patches,
   subclasses, or works around the choke point.
5. **Never print, log, or CLI-flag the API key.** `elevenlabs_tts.get_api_key()` reads
   `ELEVENLABS_API_KEY` from the environment only. Keep it that way, including in Phase 8, where an
   agent holds the key in its environment.
6. **Deterministic identity, always.** Note GUIDs and note-type ids are derived by hash from stable
   inputs, never minted by Anki and never from Python's salted `hash()`.
7. **Filename identity vs spoken text stay separate.** `audio_naming.build_filename` always derives
   from raw source text; `audio_naming.spoken_text_for` is applied only when building the API
   payload. Collapsing them is the single easiest mistake in this lane.
8. **`AudioRefs` is never referenced by any template.** Rendering it would autoplay every clip back
   to back — the exact bug the plain-text `Audio` field plus random-picker JS exists to avoid.
9. **Every leaf deck name contains `". "`** (see the template `split(". ")[1]` above).
10. **Never blanket-normalize dash-only cells** (see the workbook facts above): 143 of them carry
    real meaning. Preserve every cell verbatim.
11. **No test fixture ever lives inside a plan directory.** A plan dir is deleted at archive time
    (`plan-format`), so a fixture there is an armed break. This is what Phase 1 exists to undo; do
    not reintroduce it — including for 2.1's golden GUID oracle.
12. **No `Any`/`object` escape hatches, meaningful names, early returns, delete replaced code.** No
    compatibility shims, no `_v2` names, no TODOs in final code.
13. **Ruff clean and pytest green before any exit report.** Hook failures are blocking.
14. **No attribution trailers** on any commit or PR — no `Co-Authored-By`, no `Claude-Session`, no
    session URL in a commit message or PR body.

---

## Phase 1: Fixture relocation and old-plan closeout

Serialized, first, no lane. `plan-lifecycle.sh check` fails today and blocks the gate structurally;
the fixture relocation must precede the archive that would otherwise delete the fixture.

### 1.1 — Relocate `source-word-list.md` out of the plan dir into `tests/data/`

**File scope**
- MOVE `project-plans/russian-immutable-words-08-31-26/source-word-list.md`
  → `libs/python/anki-tools/tests/data/source-word-list.md` (new directory)
- EDIT `libs/python/anki-tools/tests/test_audio_naming.py` (path constant + its docstring reference)
- EDIT `libs/python/anki-tools/tests/test_immutable_words_plan.py` (same)
- EDIT `libs/python/anki-tools/tests/test_immutable_words.py` (same)
- EDIT `libs/python/anki-tools/tests/test_elevenlabs_tts.py` (same)
- EDIT `libs/python/anki-tools/anki_tools/elevenlabs_tts.py` (prose only, line 57)
- EDIT `libs/python/anki-tools/anki_tools/audio_naming.py` (prose only, line 80)
- EDIT `libs/python/anki-tools/anki_tools/immutable_words_plan.py` (prose only, line 198)

**Why, verified.** This file is **not stray debris — it is a live, actively-maintained test
fixture**. Four test files build a hard path to it with **no skip guard**, all four via
`Path(__file__).resolve().parents[4] / "project-plans" / "russian-immutable-words-08-31-26" /
"source-word-list.md"`:

| File | Line of the filename term | Constant name |
|---|---|---|
| `tests/test_audio_naming.py` | 46 | `REAL_SOURCE_PATH` |
| `tests/test_immutable_words_plan.py` | 65 | `REAL_SOURCE_PATH` |
| `tests/test_immutable_words.py` | 1221 | `SOURCE_DOC_PATH` |
| `tests/test_elevenlabs_tts.py` | 282 | `SOURCE_WORD_LIST_PATH` |

Measured baseline: `uv run --group dev pytest tests/test_audio_naming.py
tests/test_elevenlabs_tts.py -q` → **`154 passed in 0.32s`**. Commit `4794da4` ("make the word list
match the real collection") maintains the file; subphase 5.3 of the old plan deliberately put it
there. `plan-lifecycle.sh archive` moves only `plan.md` and removes the rest — so archiving that
plan **would delete this fixture and break those 154 tests**. That is the armed form of exactly the
time bomb subphase 3.2's own placement rationale warns about.

**Pattern to follow**: the three path constants become
`Path(__file__).resolve().parent / "data" / "source-word-list.md"` — the test file's own directory,
the same self-relative shape `conftest.py` already relies on (`conftest.py` exists at the package
root precisely so pytest resolves this package regardless of invocation directory). Use
`git mv` so the move is a rename in the diff, not a delete-plus-add.

The three module-prose edits are one-line path/wording corrections in docstrings that name the old
location. They are **not** an invitation to expand those docstrings — convention 2 still applies,
and the surrounding prose is pre-existing debt being corrected in place, not extended.

**Acceptance criteria**
- `libs/python/anki-tools/tests/data/source-word-list.md` exists and is byte-identical to the file
  that was at the old path (`git mv` plus a `git diff --stat` showing a pure rename, or a
  `sha256sum` recorded before and after).
- `project-plans/russian-immutable-words-08-31-26/` contains only `plan.md` and `plan-review.md`.
- `grep -rn "russian-immutable-words-08-31-26" libs/` returns **nothing**, with a positive control
  demonstrating the search works (e.g. `grep -rc "source-word-list" libs/python/anki-tools/tests/`
  returns non-zero hits at the new path).
- **Equivalence, with cited real output**: `uv run --group dev pytest tests/test_audio_naming.py
  tests/test_elevenlabs_tts.py -q` still reports **154 passed**, and the full package suite
  (`pnpm test` in `libs/python/anki-tools`) reports the same pass count as its pre-move baseline,
  which the builder records before touching anything.
- `ruff format --check` and `ruff check` clean from the repo root.
- No test gains a skip guard as a side effect — the fixture must remain unconditionally present.

**Test approach**: `existing suite` + `equivalence check`. The 154+ existing tests ARE the oracle;
no new test is written here. The builder records the pre-move pass count, performs the move, and
cites the post-move count.

### 1.2 — Reconcile the old plan's syllabus with what shipped, then archive it

**File scope**
- EDIT `project-plans/russian-immutable-words-08-31-26/plan.md` (syllabus checkboxes + in-place annotations)
- RUN `plan-lifecycle.sh archive` on that plan (moves `plan.md` → `project-plans/completed/russian-immutable-words-08-31-26.md`, removes the dir)

**Why the reconciliation is required first.** `plan-lifecycle.sh archive` reads the syllabus to
decide whether the plan shipped: it errors with *"plan has unchecked subphases; use 'supersede' to
remove it if it was abandoned, or finish the syllabus"* unless every subphase is `[x]`, `[done]`, or
`[dropped]`, and errors again if **all** are `[dropped]`. That plan's syllabus is currently
**0 checked**: 5 phase-header checkboxes plus **11 subphase checkboxes**, none ticked — even though
the work demonstrably shipped (the `2. Immutable Words` deck is live with 207 notes / 414 cards
across five subdecks). `plan-format`'s living-document rule requires the syllabus to reflect reality
before archive runs.

**The reconciliation, with the evidence for each verdict** (verify each before ticking; do not tick
from this table on trust):

| Subphase | Verdict | Evidence |
|---|---|---|
| 1.1 Source-document parser and row model | `[x]` | `immutable_words_plan.parse_word_list`, `WordRow` |
| 1.2 Deck naming and POS template stripping | `[x]` | `subdeck_name`, `strip_part_of_speech` |
| 2.1 Clone the source note type | `[x]` | `immutable_words.clone_note_type`; note type `3897610691970966744` live |
| 2.2 Build the deck tree and notes | `[x]` | `build_deck_tree`; 207 notes live across five subdecks |
| 2.3 Export the `.apkg`, CLI, `--dry-run` | `[x]` | `export_package`, `build_parser` with `--dry-run` |
| 3.1 Round-trip verification | `[x]` | `tests/test_immutable_words.py` e2e round-trip test |
| 4.1 ElevenLabs TTS client | `[x]` | `anki_tools/elevenlabs_tts.py`; 205 words × 4 slots on disk |
| 5.1 `bin` entry points | `[x]` | `package.json`: `anki-immutable-words`, `anki-elevenlabs-tts` |
| 5.2 Audio attachment / repackage | `[x]` | `attach_media`, `--audio-dir`; `AudioRefs` field live |
| 5.3 Relocate the source word list into the plan directory | `[x]` + annotation | The file was there. Annotate in place: **superseded by `mutable-words-09-25-26` subphase 1.1**, which relocates it to `tests/data/` because a plan dir is deleted at archive. |
| 5.4 Document both commands in the docs root | **`[dropped]`** | **Never shipped.** `grep -c immutable docs/libs/python/anki-tools/README.md` → `0`; `grep -c "elevenlabs\|ElevenLabs"` → `0`; positive control `grep -c rebalance` → `14`. The docs dir holds only `README.md`. |

Because 5.4 never shipped, **this run absorbs that debt**: subphase 9.2 already edits that exact
README and documents `anki-immutable-words` and `anki-elevenlabs-tts` alongside the four new
commands. The `[dropped]` annotation must say so, so the dropped work is traceable to where it
actually lands rather than silently lost.

**Acceptance criteria**
- Every one of the 11 subphase checkboxes is `[x]` or `[dropped]`, matching the table above, with
  each verdict independently re-verified (not copied from this plan).
- 5.3 and 5.4 carry in-place annotations in their phase sections naming what superseded / absorbed
  them.
- `plan-lifecycle.sh archive` on that plan exits 0; afterwards
  `project-plans/completed/russian-immutable-words-08-31-26.md` exists and
  `project-plans/russian-immutable-words-08-31-26/` does not.
- **`plan-lifecycle.sh check` (full scan) exits 0** with no `FAIL:` line — the structural blocker
  from gate round 1 is cleared. Baseline for comparison, captured before this subphase as the sole
  output of a bare invocation (not inside a compound command, which would contaminate the status):
  `FAIL: unexpected file in plan dir …/russian-immutable-words-08-31-26: source-word-list.md`,
  **exit 1**. That one `FAIL:` line is the entire finding — every other plan dir passes — so this
  subphase's success condition is precisely "that line is gone".
- The package suite is still green after the archive (proving 1.1 actually decoupled the fixture —
  this is the regression that would have fired had the order been reversed).

**Test approach**: `existing suite` — the archive is verified by `plan-lifecycle.sh check` exiting 0
and by the suite still passing with the plan dir gone.

---

## Phase 2: Shared foundation

Serialized, no lane: every later lane depends on at least one of these, and 2.1/2.2 edit existing
files no lane may touch concurrently.

### 2.1 — Hoist deterministic Anki identity helpers into `anki_identity.py`

**File scope**
- NEW `libs/python/anki-tools/anki_tools/anki_identity.py`
- EDIT `libs/python/anki-tools/anki_tools/immutable_words.py` (remove `_notetype_id_for_name`, import it)
- EDIT `libs/python/anki-tools/anki_tools/immutable_words_plan.py` (remove `_GUID_ALPHABET`, `_base91`, `guid_for_row`, import them)
- EDIT `libs/python/anki-tools/tests/test_immutable_words.py`, `tests/test_immutable_words_plan.py` (import sites only)
- NEW `libs/python/anki-tools/tests/test_anki_identity.py`
- NEW `libs/python/anki-tools/tests/data/immutable_guids.json` (the golden oracle)

**Pattern to follow**: the functions being moved, verbatim —
`immutable_words._notetype_id_for_name` (`immutable_words.py:46-76`) and
`immutable_words_plan._base91` / `guid_for_row` / `_GUID_ALPHABET`
(`immutable_words_plan.py:130-197`). The new module is pure: `hashlib` only, no `anki`, no
`requests` — the same discipline `audio_naming.py` states in its own docstring.

Public surface:
```
GUID_ALPHABET: str
base91(num: int) -> str
guid_for_row(discriminator: str, text: str) -> str      # sha256 over f"{discriminator}\x1f{text}"
notetype_id_for_name(name: str) -> int                  # sha256(name)[:8] big-endian & (1<<62)-1
```
Parameters are renamed from `(russian, pos)` to `(discriminator, text)` because the mutable side
hashes a sheet name plus a Russian string — **the canonical byte string and the argument order are
unchanged**, so every existing GUID is preserved.

**This is a move, not a rewrite.** The old definitions are DELETED from their current homes; no
re-export shim, no alias. `immutable_words_plan.guid_for_row` becomes an import, so existing callers
and tests that do `from anki_tools.immutable_words_plan import guid_for_row` keep working without a
compatibility layer.

**The golden oracle is a committed fixture, never a plan-dir path** (convention 11, and the gate's
round-1 finding). Before the move, generate `(pos, russian) -> guid` for every row of the relocated
word list and commit the result as `tests/data/immutable_guids.json`, beside the relocated
`source-word-list.md` from 1.1 and the `immutable_audio_block.html` golden from 2.2. The test reads
the committed JSON; it must not re-derive expectations from the implementation under test, and it
must not reference `project-plans/` at all.

**Acceptance criteria**
- `anki_identity.notetype_id_for_name("Russian - Immutable Words (Ellis Version)")` returns exactly
  `3897610691970966744` — the id that note type actually carries in the live collection.
- Every `(pos, russian)` pair in `tests/data/immutable_guids.json` maps to the same GUID after the
  move as the committed value. The JSON was generated from the pre-move code; the test asserts
  against the file, not against a recomputation.
- `grep -rn "project-plans" libs/python/anki-tools/tests/test_anki_identity.py` returns nothing.
- `anki_identity` imports nothing but `hashlib` — asserted by importing it in a subprocess with a
  clean `sys.modules` and inspecting what appeared.
- `base91(0)` keeps its documented sharp edge (encodes as the first alphabet character, not `""`).
- `grep -n "_notetype_id_for_name\|_base91" anki_tools/immutable_words*.py` returns nothing.
- Full existing suite green with no test-body changes beyond import lines.

**Test approach**: `existing suite` + `equivalence check`. The existing `test_immutable_words*.py`
suites are the regression net; `test_anki_identity.py` adds the golden-value and purity assertions.

### 2.2 — Hoist the audio-picker block into a parameterized `card_audio.py`

**File scope**
- NEW `libs/python/anki-tools/anki_tools/card_audio.py`
- EDIT `libs/python/anki-tools/anki_tools/immutable_words_plan.py` (`rewrite_audio_playback` body only; `_AUDIO_DIV` stays)
- NEW `libs/python/anki-tools/tests/test_card_audio.py`
- NEW `libs/python/anki-tools/tests/data/immutable_audio_block.html` (golden)
- EDIT `libs/python/anki-tools/tests/test_immutable_words_plan.py` (add the golden assertion; do not weaken existing ones)

**Why — restated for the D2 four-card verb shape.** Under D2 each verb template side carries at most
one audio block, so the original "two pickers collide on one card" argument no longer applies and is
not the justification. The real reasons are:
1. **The field reference differs per note type and per verb template** — `{{Audio}}` for nouns,
   adjectives and adverbs; `{{Audio Imperfective}}` on the verb note type's Cards 1–2 and
   `{{Audio Perfective}}` on Cards 3–4. A hardcoded `{{Audio}}` cannot serve five note types.
2. **Distinct DOM ids and state keys keep each aspect's pick independent** rather than leaning on
   the existing JS's `files.indexOf(previous) !== -1` membership check as the only thing preventing
   a perfective card from replaying an imperfective pick. Belt and braces, cheaply.
3. The alternative is a second copy of a ~45-line JS blob that must never drift from the first —
   which the project's own standards forbid (convention 12).

**Pattern to follow**: the literal HTML+JS currently inside
`immutable_words_plan.rewrite_audio_playback` (`immutable_words_plan.py:405-544`). The long
explanatory comment inside the generated JS is part of the **generated artifact**, not source-code
commentary — it ships into the note type and must be preserved verbatim, with only the state-key
name substituted. Convention 2 does not apply to it.

Public surface:
```
audio_block(field: str, dom_id: str, state_key: str) -> str
```
returning the `<div id="{dom_id}">…</div><script>…</script>` string, where `{{field}}` is the Anki
field reference, `dom_id` names both the container (`{dom_id}`) and its data span
(`{dom_id}-data`), and `state_key` is the `window.__…` property carrying the pick across the
question→answer re-render.

`rewrite_audio_playback` becomes: match `_AUDIO_DIV`, substitute
`audio_block("Audio", "audio", "__immutableWordsAudioChoice")`.

**Acceptance criteria**
- **Byte-identical output.** `tests/data/immutable_audio_block.html`, captured from the CURRENT
  `rewrite_audio_playback` output before the change, must equal the post-change output exactly —
  every space, tab, and newline. This is the whole safety argument for touching a module the ask
  puts out of scope.
- `audio_block("Audio Perfective", "audio-perfective", "__mutableVerbPerfectiveChoice")` produces a
  block whose container id, data-span id, field reference, and state key are all the perfective
  ones, sharing no identifier with the imperfective block.
- Two blocks concatenated contain no duplicated `id="…"` attribute (assert by regex over the
  concatenation) — kept as a criterion even though D2 means the two never co-occur on one card,
  because it is the cheap structural guard against a future template change reintroducing that.
- `card_audio` imports nothing but the standard library.
- Existing `test_immutable_words_plan.py` assertions on `rewrite_audio_playback` pass unchanged.

**Test approach**: `equivalence check` (golden file) plus `new contract tests` for the
parameterization.

### 2.3 — Add the `openpyxl` dependency and relock

**File scope**
- EDIT `libs/python/anki-tools/pyproject.toml` (`[project] dependencies`)
- EDIT `uv.lock` (repo root — regenerated, never hand-edited)

**Decision, with its justification.** `openpyxl` is **not present** in `uv.lock`
(`grep -c openpyxl uv.lock` → 0; positive control `requests` → 21), and nothing else in the tree can
read `.xlsx`. `pandas` 3.0.5 *is* in the lock, but it is declared by other workspace members, is not
an `anki-tools` dependency, and its `read_excel` needs `openpyxl` underneath anyway — so adding
`pandas` would mean adding `openpyxl` plus ~40 MB of transitive weight for a four-sheet read.
`openpyxl` goes into `[project] dependencies`, not the dev group, because `vocabulary_source.py` is
a shipped CLI module that imports it at module level; hiding a runtime import inside a function to
keep the dep "dev-only" is the kind of cleverness this repo rejects.

**Acceptance criteria**
- `libs/python/anki-tools/pyproject.toml` declares `openpyxl>=3.1`.
- `uv lock` run from the repo root; `uv.lock` regenerated and committed; the diff touches only the
  `openpyxl` (and its transitive `et-xmlfile`) entries and `anki-tools`' requirement list.
- The **resolved** `openpyxl` version is read back out of `uv.lock` and recorded in this plan's
  Stack table and in `docs/libs/python/anki-tools/README.md` — never asserted from memory.
- `uv run --group dev python -c "import openpyxl"` succeeds; `pnpm lint` and `pnpm test` still green
  from the repo root.

**Test approach**: `existing suite` (the whole suite must pass under the new lock) plus a manifest
assertion that `openpyxl` appears in `[project] dependencies`.

---

## Phase 3: Source of truth — lane 1

### 3.1 — `vocabulary_source.py`: workbook reader + TSV writer

**File scope**
- NEW `libs/python/anki-tools/anki_tools/vocabulary_source.py`
- NEW `libs/python/anki-tools/tests/test_vocabulary_source.py`

**The reproducibility problem this solves**: the workbook lives at
`~/Downloads/russian_vocabulary.xlsx`, outside the repo and outside version control. A build that
reads it directly is not reproducible, not diffable, and not reviewable in a PR — the exact reason
`immutable_words.py` reads a committed document rather than an original. This module is the
**one-way import boundary**: it runs by hand when the workbook changes, and its output is what
everything downstream reads. Nothing else in the package ever imports `openpyxl`.

**Pattern to follow**: `anki_tools/immutable_words.py`'s CLI shape — `build_parser()` kept separate
from `main()` so both are testable, `--dry-run` that writes nothing, explicit `SystemExit` codes.

Public surface:
```
SHEETS: tuple[str, ...]                       # ("Nouns", "Verbs", "Adjectives", "Adverbs")
EXPECTED_HEADERS: dict[str, tuple[str, ...]]  # per sheet, verbatim from the workbook
class WorkbookError(Exception)
read_sheet(workbook_path: str, sheet: str) -> list[dict[str, str]]
write_tsv(rows: list[dict[str, str]], headers: tuple[str, ...], out_path: str) -> None
build_parser() / main()
```

Behaviour contract:
- Opens the workbook with `openpyxl.load_workbook(path, read_only=True, data_only=True)`.
- **Header validation is strict**: if a sheet's header row is not exactly `EXPECTED_HEADERS[sheet]`
  (order included), raise `WorkbookError` naming the sheet and the difference. A silently renamed or
  reordered column is the failure mode that would otherwise put English glosses in the Gender field.
- Every cell is normalized to `str`: `None` → `""`, numbers → their integer/decimal text,
  surrounding whitespace stripped, Unicode NFC-normalized. **Dash-only cells are NOT touched**
  (convention 10) — no `_EMPTY_INFO`-style collapsing anywhere in this module.
- A row where every cell is empty is dropped (trailing spreadsheet rows).
- **Rejects** any cell containing a tab, CR, or LF, naming sheet/row/column — that is what makes TSV
  lossless, and it is asserted rather than assumed (verified today: zero such cells across the four
  data sheets).
- The `Key` sheet is never read.
- `write_tsv` writes UTF-8, `\n` line endings, header row first, no quoting, no BOM.
- **Neither the Adverbs placeholder filter nor the D3 split lives here.** This module is a faithful
  transcription of the workbook; dropping and splitting rows are *meaning* decisions and belong in
  the pure core (3.3). All 152 Adverbs rows are written, slash-joined cells intact.

**Acceptance criteria**
- Against the real workbook: `read_sheet` returns 541 / 179 / 152 / 152 rows respectively.
- `EXPECTED_HEADERS` matches the four header tuples recorded in the Stack section, verbatim.
- A synthetic workbook (built in-test with `openpyxl.Workbook()`) with a renamed column raises
  `WorkbookError` mentioning both the expected and the found header.
- A synthetic workbook with a tab inside a cell raises `WorkbookError` naming the sheet, the row
  number, and the column.
- A synthetic sheet containing a dash-only cell round-trips with the dash **intact**.
- A round trip `read_sheet` → `write_tsv` → re-read with `csv.DictReader(delimiter="\t")` returns
  dicts equal to the originals.
- `main()` with `--dry-run` prints per-sheet row counts and writes no file.

**Test approach**: `new contract tests`. Synthetic workbooks built with `openpyxl` in `tmp_path` for
the error paths; the real-workbook test `pytest.skip`s when
`~/Downloads/russian_vocabulary.xlsx` is absent, so CI and a fresh clone stay green.

### 3.2 — Commit the four TSVs and their provenance README

**File scope**
- NEW `libs/python/anki-tools/anki_tools/data/russian-vocabulary/nouns.tsv`
- NEW `libs/python/anki-tools/anki_tools/data/russian-vocabulary/verbs.tsv`
- NEW `libs/python/anki-tools/anki_tools/data/russian-vocabulary/adjectives.tsv`
- NEW `libs/python/anki-tools/anki_tools/data/russian-vocabulary/adverbs.tsv`
- NEW `libs/python/anki-tools/anki_tools/data/russian-vocabulary/README.md`
- NEW `libs/python/anki-tools/tests/test_vocabulary_data.py`

**Where, and why there.** Inside the package directory — **never** a plan directory (convention 11,
and the whole reason Phase 1 exists). `anki_tools/data/` ships with the wheel (hatchling includes
non-`.py` files under `packages = ["anki_tools"]`) and is reachable from tests and from the installed
package alike. Note the deliberate split from Phase 1's destination: build **inputs** live under
`anki_tools/data/`, test **fixtures** under `tests/data/`.

The README states: the source workbook's filename and export date, the `vocabulary_source.py`
command that regenerates each TSV, the sheet→file mapping, and the fact that these files — not the
workbook — are the build input.

**Acceptance criteria**
- Each TSV's header row equals `EXPECTED_HEADERS[sheet]` exactly.
- Row counts: `nouns.tsv` 541 + 1 header, `verbs.tsv` 179 + 1, `adjectives.tsv` 152 + 1,
  `adverbs.tsv` 152 + 1 (placeholders included and slash rows unsplit — both handled downstream).
- Files are UTF-8 without BOM, `\n` endings, and contain no tab inside any field.
- **Dash-only cell census, asserted**: exactly 107 in `nouns.tsv`'s `Plural`, 36 in `adverbs.tsv`'s
  `Comparative`, 22 each in `adverbs.tsv`'s `Adverb` and `Stress`, and **zero everywhere else**. A
  future workbook edit that starts using a dash to mean "empty" fails this test instead of silently
  destroying a linguistic fact.
- Regenerating from the real workbook produces byte-identical files (the converter is deterministic).
- `uv build` (or an equivalent wheel inspection) shows the four TSVs inside the wheel.

**Test approach**: `new contract tests` — a test module reading the four committed TSVs by
package-relative path and asserting counts, headers, encoding, and the dash census. These committed
files are also the fixture corpus for 3.3, 4.x and 5.x, so every later phase exercises them.

### 3.3 — `mutable_words_plan.py`: the pure core

**File scope**
- NEW `libs/python/anki-tools/anki_tools/mutable_words_plan.py`
- NEW `libs/python/anki-tools/tests/test_mutable_words_plan.py`

**Pattern to follow**: `anki_tools/immutable_words_plan.py` — Anki-free, `requests`-free, a frozen
row dataclass with `deck` / `guid` / `fields()`, a `DECK_ROOT` constant, an ordered `SUBDECK_LEAVES`
mapping driving the `a.`/`b.`/… prefixes, a `ROW_SPLITS` table, and audio filenames PREDICTED through
the shared `audio_naming.build_filename` so the deck side and the TTS side can never drift. Imports:
`anki_identity`, `audio_naming`, `card_audio`, stdlib. Nothing else.

**Constants**
```
DECK_ROOT = "Languages::Russian::3. Mutable Words"
SUBDECK_LEAVES = {"Nouns": "Nouns", "Verbs": "Verbs",
                  "Adjectives": "Adjectives", "Adverbs": "Adverbs"}   # -> a. / b. / c. / d.
VOICE_SLOTS = ("f1", "m2")     # THE two slots for this deck; never audio_naming.SLOTS
```
`VOICE_SLOTS` is defined here, not taken from `audio_naming.SLOTS` (the immutable deck's four-slot
roster, which must not change). It is the single place the two-voice decision is written down; 5.x
reads it rather than restating it.

**Note types** — four, per ask decision 5 and **Q1**:

| Sheet | Note type name | id |
|---|---|---|
| Nouns | `Russian - Mutable Nouns (Ellis Version)` | `anki_identity.notetype_id_for_name(name)` |
| Verbs | `Russian - Mutable Verbs (Ellis Version)` | same |
| Adjectives | `Russian - Mutable Adjectives (Ellis Version)` | same |
| Adverbs | `Russian - Mutable Adverbs (Ellis Version)` | same |

**Field sets.** Source headers are kept **verbatim** as field names, with exactly three deliberate
departures, each documented in 9.2:
- `#` → `Rank` (a field name may not start with `#` — confirmed verbatim in `_fluent.py:5711-5714`).
- `English` → `Translation` (the whole `… (Ellis Version)` family calls it that, and the reverse
  card's question side is built around it).
- `Status` is **dropped** per **D4** — it is `"New"` on **1002 of 1002** real rows (100%, no other
  value anywhere; the only 22 empties are the excluded placeholder rows), so it carries no
  information, and Anki's own scheduler supersedes it.

```
Nouns   (13): Russian, Translation, Stress, Gender, Plural, Genitive Sg, Genitive Pl,
              Animate, Category, Additional Info, Rank, Audio, AudioRefs
Verbs   (15): Imperfective, Perfective, Translation, Stress, Conjugation, я (1sg), ты (2sg),
              они (3pl), Past (m / f), Case / Preposition, Additional Info, Rank,
              Audio Imperfective, Audio Perfective, AudioRefs
Adjectives (14): Russian (m), Translation, Stress, Feminine, Neuter, Plural, Short Form,
              Comparative, Opposite, Stem Type, Additional Info, Rank, Audio, AudioRefs
Adverbs (11): Adverb, Translation, Stress, From Adjective, Formation, Comparative,
              Additional Info, Rank, Audio, AudioRefs
```
`AudioRefs` is last in every set and is **never referenced by a template** (convention 8). It holds
every filename for the note as concatenated `[sound:…]` tags so Anki's media-usage scan — which
reads field text directly — bundles the bytes on export.

**Rows and identity**
- One frozen dataclass per sheet (`NounRow`, `VerbRow`, `AdjectiveRow`, `AdverbRow`), each with
  `sheet`, `rank`, the sheet's columns, and `guid` / `deck` / `fields()`.
- `guid = anki_identity.guid_for_row(sheet, base_word)` where `base_word` is the sheet's base-word
  column (`Imperfective` for verbs). Derived from sheet + Russian text ONLY — never from the English
  gloss, the stress form, or anything audio-related, all of which legitimately change on a rebuild
  and must UPDATE the existing note rather than mint a new one.
- **The Adverbs placeholder filter lives here**, in `parse_adverbs`, and nowhere else: a row is
  dropped when `Formation == "none"`. That column, not the `Adverb == "—"` dash, is the semantic
  signal — the `Key` sheet says *"Formation 'none' rows have no true adverb"* — and the parser
  additionally **asserts all four signals agree** (`Adverb` is a dash, `English` empty, `Status`
  empty), raising if they ever disagree.
- **The D3 split lives here too**, as a `ROW_SPLITS` table keyed on the exact `Adverb` cell text,
  mirroring `immutable_words_plan.ROW_SPLITS`:
  ```
  ROW_SPLITS = {
      "направо / справа": (("направо", "to the right"), ("справа", "on the right")),
      "налево / слева":   (("налево", "to the left"),   ("слева", "on the left")),
  }
  ```
  `Stress` splits in parallel on `" / "` (`напра́во`/`спра́ва`, `нале́во`/`сле́ва`);
  `From Adjective`, `Formation`, `Comparative` and `Additional Info` are shared by both halves. Two
  rows in → four rows out, so Adverbs yields **132** notes.

**Audio prediction**
- `audio_names(row)` = `[build_filename(w, slot) for w in row.base_words for slot in VOICE_SLOTS]`.
- Nouns / Adjectives / Adverbs: `Audio` holds the two names comma-joined, no spaces.
- Verbs: `Audio Imperfective` holds the imperfective's two; `Audio Perfective` the perfective's two.
- `AudioRefs` = every name for the note as `[sound:…]` tags, derived from the same list, never
  computed independently.

**Templates** — `qfmt`/`afmt` are BUILT here (not cloned and patched), composing:
- the shared header (`#path`, `#deck`, the deck-name script) taken verbatim from note type
  `1698803891108`;
- `card_audio.audio_block(...)` per audio field, with per-notetype DOM ids and state keys
  (`audio` / `__mutableAudioChoice` for the single-audio types; `audio-imperfective` /
  `__mutableVerbImperfectiveChoice` and `audio-perfective` / `__mutableVerbPerfectiveChoice` for
  verbs);
- a generated details block listing the sheet's remaining fields as `addTitle`-labelled rows on the
  answer side (**Q3**), reusing the existing `addTitle` script verbatim;
- CSS taken verbatim from note type `1698803891108` (identical across the whole family today).

Card shapes (**Q4**, and **D2** for verbs):

| Note type | Templates | Shape |
|---|---|---|
| Nouns / Adjectives / Adverbs | 2 | `Card 1` Russian → Translation (audio on front); `Card 2` Translation → Russian (audio on back) |
| Verbs | **4** | `Card 1` Imperfective → Translation (impf audio, front); `Card 2` Translation → Imperfective (impf audio, back); `Card 3` Perfective → Translation (perf audio, front); `Card 4` Translation → Perfective (perf audio, back) |

Each verb template side carries **exactly one** audio block, for the aspect that template is about.

**Spoken text**: `spoken_text_for` from `audio_naming` is reused as-is. After the D3 split no base
word contains a slash, so no new override entry is needed — assert that, rather than assuming it.

**Acceptance criteria**
- Parsing the four committed TSVs yields 541 / 179 / 152 / **132** rows; total **1004**.
- Exactly 22 Adverbs rows are dropped, and the parser raises if the four placeholder signals
  disagree on any row (assert with a doctored fixture).
- Exactly 2 Adverbs rows are split into 4; the four resulting rows carry the Russian, English and
  Stress values from the table in the workbook-facts section, and share their parent's
  `From Adjective` / `Formation` / `Comparative` / `Additional Info`.
- **No base word contains `"/"`** after the split (this is the assertion that keeps a slash out of
  an ElevenLabs payload).
- Card-count derivation: `sum(len(note_type.templates) for each note) == 2366`, broken down 1082 /
  716 / 304 / 264 — asserted per subdeck, not just in total.
- `all_subdeck_names()` → `["…::3. Mutable Words::a. Nouns", "…::b. Verbs", "…::c. Adjectives",
  "…::d. Adverbs"]`; every name contains `". "`.
- Every field name passes the leading-character rule and contains none of `:`, `"`, `{`, `}`;
  `AudioRefs` is last in every set.
- **No template string contains `{{AudioRefs}}`** — assert across all **20 template sides**
  (2+4+2+2 = 10 templates, each with a `qfmt` and an `afmt`).
- No template side contains a duplicated `id="…"` attribute.
- **Collision assertion**: over all 1183 base words, the slug set has size 1183; the test fails
  loudly, naming the colliding strings, if a future TSV edit breaks it. The seven media-dir overlaps
  are asserted to be byte-identical strings — the legitimate shared-file case, not a collision.
- `guid_for_row` output is stable across two invocations in two separate subprocesses (rules out
  salted `hash()`).
- Predicted `Audio` values equal `audio_naming.build_filename` output for the same `(word, slot)` —
  computed through the shared function, never re-derived.
- Dash-only cells survive into field values unchanged (e.g. a noun whose `Plural` is `—` renders
  `—`, not `""`).
- The module imports no `anki`, no `requests`, no `openpyxl` (subprocess import check).

**Test approach**: `new contract tests`, reading the committed TSVs from 3.2 as fixtures.

---

## Phase 4: Deck package builder — lane 2

### 4.1 — Four note types in a scratch collection

**File scope**
- NEW `libs/python/anki-tools/anki_tools/mutable_words.py` (note-type half)
- NEW `libs/python/anki-tools/tests/test_mutable_words.py` (note-type half)

**Pattern to follow**: `immutable_words.clone_note_type` (`immutable_words.py:80-158`), including
every hard-won detail its body already encodes:
- `source_col` is **read-only** — `.models.get(id)` and `.models.copy(nt, add=False)`, nothing else.
- Look the source note type up by **id** `1698803891108`, never by name (its real name,
  `"Russian - Common Words (Ellis Version) "`, has a trailing space).
- Fields created with `build_col.models.new_field(...)` must have their `id` pinned to `None`, or
  `new_field()`'s random id makes the field fail to match itself across builds (`NoteField::is_match`
  compares by id when both ids are non-None, else by name).
- `cloned["id"]` is set to the deterministic `notetype_id_for_name(name)`; `cloned["mod"]` is bumped
  to `int(time.time())` so Anki's `IF_NEWER` reimport condition actually refreshes templates and CSS
  in place.
- Registration goes through `build_col._backend.add_or_update_notetype(json=to_json_bytes(cloned),
  preserve_usn_and_mtime=True, skip_checks=False)` — `models.add_dict` panics on a non-zero id.
- `assert_unmodified(collection_path, mtime_before)` is called in a `finally` after the source
  collection is closed.

The function is `build_note_types(source_col, build_col) -> dict[str, NotetypeDict]`, keyed by sheet
name, producing all four from `mutable_words_plan`'s field sets, templates, and ids. Only the CSS and
the `sortf`/`type` scalars are taken from the source note type; the fields and template sides are
built, not patched, because the sheets' columns bear no resemblance to the source note type's six
fields.

**Acceptance criteria**
- Four note types registered in a fresh scratch collection; each `nt["id"]` equals
  `notetype_id_for_name(nt["name"])` and is stable across two independent builds.
- Field names and order per note type match `mutable_words_plan`'s field sets exactly; every field
  has `id is None` (all four sets are newly invented).
- Template counts: 2 / **4** / 2 / 2, named `Card 1`…`Card 4` as applicable.
- CSS is byte-identical to note type `1698803891108`'s CSS.
- **`build_col.new_note(nt)` succeeds for every generated note type** — the practical proof that
  every chosen field name is legal, given the Fluent-string caveat recorded in the Stack section.
- The source collection's mtime is unchanged (`assert_unmodified`). The test synthesizes its own
  source note type in a scratch collection; it never opens the user's collection.

**Test approach**: `new contract tests`, against scratch `Collection` instances under
`tempfile.mkdtemp`.

### 4.2 — Deck tree, notes, media attach, `.apkg` export + CLI

**File scope**
- `libs/python/anki-tools/anki_tools/mutable_words.py` (remainder)
- `libs/python/anki-tools/tests/test_mutable_words.py` (remainder)

**Pattern to follow**: `immutable_words.build_deck_tree` / `attach_media` / `export_package` /
`print_deck_table` / `build_parser` / `main` (`immutable_words.py:174-438`), and `rebalance_due.main`'s
`try/finally: col.close()` discipline.

- `build_deck_tree(build_col, rows_by_sheet, note_types) -> dict[str, int]` — creates the four
  subdecks in `all_subdeck_names()` order, adds one note per row with `note.guid = row.guid` and
  fields from `row.fields()`, returns per-deck counts with all four keys always present.
- `attach_media(build_col, audio_dir)` — over the UNION of filenames referenced by every audio field
  on every note (verbs contribute two fields), returning `(found, missing)` sorted, never raising on
  a missing file. **Deck-before-audio**: a build with no recordings yet must still export and import
  cleanly.
- `export_package(build_col, DECK_ROOT, out_path, force)` — `ExportAnkiPackageOptions(
  with_scheduling=False, with_deck_configs=False, with_media=True, legacy=False)` with a
  `DeckIdLimit` on the root.
- CLI flags: `--source-dir` (default: the packaged `anki_tools/data/russian-vocabulary`), `--out`,
  `--audio-dir`, `--collection`, `--dry-run`, `--force`. `--out` required unless `--dry-run`.

**Acceptance criteria**
- Per-deck note counts: `a. Nouns` 541, `b. Verbs` 179, `c. Adjectives` 152, `d. Adverbs` 132;
  total **1004 notes**.
- Per-deck card counts: 1082 / 716 / 304 / 264; total **2366 cards**. `print_deck_table` must not
  assume 2 cards per note — the immutable precedent hardcodes `cards = notes * 2`
  (`immutable_words.py:286`) and that is wrong for verbs; derive it from the note type's template
  count.
- The source collection is opened read-only-in-effect and `assert_unmodified` passes; no code path
  in this module writes to it.
- Building twice into two scratch collections produces the same 1004 GUIDs and the same four
  note-type ids.
- Re-importing the exported `.apkg` into a scratch collection that already holds a previous build's
  notes **updates in place**: 1004 notes, 4 note types, no `+`-suffixed duplicate.
- With `--audio-dir` holding a subset of the predicted files, `attach_media` reports the exact
  missing list and the export still succeeds.
- `--dry-run` opens no collection at all and writes nothing.
- Exporting to an existing path without `--force` raises `FileExistsError`.

**Test approach**: `new contract tests`. The export/reimport round trip runs entirely between two
scratch collections in `tmp_path`.

---

## Phase 5: Audio generation tooling — lane 3

### 5.1 — Work-set computation and exact budget sizing

**File scope**
- NEW `libs/python/anki-tools/anki_tools/mutable_words_audio.py` (pure half)
- NEW `libs/python/anki-tools/tests/test_mutable_words_audio.py` (pure half)

**Pattern to follow**: `elevenlabs_tts.main`'s budget discipline (`elevenlabs_tts.py:871-963`) —
count the work first, print it, confirm it, then construct `RequestBudget(limit=<that exact count>)`
so the choke point can stop a runaway word/voice list before a second unauthorized request reaches
the network.

Pure functions, no network, no Anki:
```
select_voices(slots: Sequence[str]) -> list[Voice]        # from elevenlabs_tts.VOICES, by slot
pending_pairs(words: Sequence[str], slots, media_dir: str) -> list[tuple[str, str]]
plan_requests(words, slots, media_dir) -> AudioWorkPlan   # .total_pairs, .pending, .skipped
```

- `select_voices(("f1", "m2"))` filters the module-level `VOICES` tuple by slot. **This is the
  "select at the call site" the ask requires** — `elevenlabs_tts.VOICES`, `DEFAULT_VOICES`, and
  `--all-voices` are untouched, so every other caller is unaffected. It raises if a requested slot
  is absent rather than silently producing a short list.
- `pending_pairs` tests existence against the **Anki media directory** only — the authoritative
  location, and the one `build_and_save` refuses to overwrite. This is the fix for the verified
  14-request waste documented in Cost control.

**Acceptance criteria**
- Over the real word set (1183 words × `("f1", "m2")`): `total_pairs == 2366`.
- With a fixture media dir containing N of the predicted filenames, `len(pending) == 2366 - N` and
  `pending` contains no pair whose file is present.
- `select_voices(("f1", "m2"))` returns exactly Alisa (`t6lBrEl93uCiLR1Lgm8v`) and Nester Surovy, in
  that order; `select_voices(("f3",))` raises naming the unknown slot.
- `elevenlabs_tts.DEFAULT_VOICES` is still length 1 and still `VOICES[:1]` after this module is
  imported (proves nothing was mutated globally).
- The pure half makes no network call — assert by injecting a session double that raises on any use.

**Test approach**: `new contract tests`, with fixture media directories in `tmp_path`.

### 5.2 — `mutable_words_audio.py`: resumable driver + CLI

**File scope**
- `libs/python/anki-tools/anki_tools/mutable_words_audio.py` (remainder)
- `libs/python/anki-tools/tests/test_mutable_words_audio.py` (remainder)

**Pattern to follow**: `elevenlabs_tts.build_and_save_batch` is called **per word with a narrowed
`voices=` list**, not in one blanket batch, because the skip decision is per `(word, slot)` and
`build_and_save` only takes a word-level voice list. One shared `RequestBudget` and one shared
`requests.Session()` across the whole run, exactly as `main()` does today.

```
generate(words, *, slots, media_dir, output_dir, budget, session=None,
         api_key=None, replace=False) -> list[SynthesisResult]
build_parser() / main()
```

CLI flags: `--source-dir` (default: the packaged TSVs), `--sheet` (repeatable, default all four),
`--output-dir` (default `elevenlabs_tts.DEFAULT_OUTPUT_DIR`), `--anki-media-dir`, `--limit N`
(process the first N pending words), `--dry-run` (print the cost table, issue nothing), `--yes`.

- **Resumability is the default, not a flag.** Every run recomputes `pending_pairs` against the media
  directory, so an interrupted run resumed later re-requests only what is still missing. No state
  file, no checkpoint format — the media directory *is* the state.
- **The budget is sized to `len(pending)`, never to the total.**
- `--dry-run` prints total pairs, already-present, pending, and the two voice names, then exits 0
  having issued nothing.
- Without `--yes`, a run of more than 1 request prompts, mirroring
  `elevenlabs_tts.CONFIRM_ABOVE_REQUESTS`. Phase 8.1 passes `--yes` because D6 authorized the spend
  and declined a checkpoint; the prompt stays for every other caller.
- The API key is read only via `elevenlabs_tts.get_api_key()`; never a flag, never printed, never
  interpolated into a message.

**Acceptance criteria**
- `--dry-run` against the real TSVs and the real media dir prints `total 2366 / present 14 /
  pending 2352` and makes zero HTTP calls (assert with a session double).
- With a doubled word list, the budget still caps total spend at `len(pending)` and
  `BudgetExceededError` is raised rather than a second request issued.
- A run over a fixture set writes each file to **both** `output_dir` and `media_dir`; a second run
  over the same set issues **zero** requests.
- **A pair already in `media_dir` but absent from `output_dir` issues zero requests** — the 14-pair
  case; this is the specific regression test for the documented waste.
- `--limit 2` issues at most `2 × len(slots)` requests.
- Every request in the fake transport carries `spoken_text_for(word)` as its text and a `voice_id`
  from the two selected slots only — never `f2`/`m1`.
- Filenames written match `audio_naming.build_filename(word, slot)` exactly.
- No test makes a real network call; `ELEVENLABS_API_KEY` is injected via `monkeypatch.setenv` with a
  dummy value and never appears in captured stdout.

**Test approach**: `new contract tests`, with a fake `requests.Session` double recording every call,
mirroring how `tests/test_elevenlabs_tts.py` already exercises the module.

---

## Phase 6: Deck renumbering tooling — lane 4

One new module, one new test file, no shared file. `(after: 1.2)` only because Phase 1 must clear the
structural blocker before any lane dispatches; there is no code dependency.

### 6.1 — `renumber_russian_decks.py`

**File scope**
- NEW `libs/python/anki-tools/anki_tools/renumber_russian_decks.py`
- NEW `libs/python/anki-tools/tests/test_renumber_russian_decks.py`

**Pattern to follow**: `anki_tools/rebalance_due.py`'s `main()` safety flow, in this exact order —
feasibility precheck → backup → plan print → `y/N` confirm → apply → `finally: col.close()`
(`rebalance_due.py:435-681`), with `col.create_backup(backup_folder=…, force=True,
wait_for_completion=True)` at `rebalance_due.py:532` and the
`--backup-dir` / `--no-backup` / `--dry-run` / `--yes` flag set at `rebalance_due.py:354-398`.

**How the renumber is done**
```
RENAMES = (("3. Sentences (lingo llama)", "4. Sentences (lingo llama)"),
           ("4. 100 Words & Phrases",     "5. 100 Words & Phrases"),
           ("5. Master Russian 300+",     "6. Master Russian 300+"))
```
applied in **reverse order** — `5.`→`6.` first, then `4.`→`5.`, then `3.`→`4.` — because deck names
carry a `UNIQUE` index (`idx_decks_name`) and `DeckManager.rename`'s contract is *"Rename deck prefix
to NAME **if not exists**"*. Reverse order removes the collision hazard categorically rather than by
case analysis. Each rename targets the **parent** deck only; the backend's `rename_child_decks`
carries `::a. Listening` / `::b. Recall` along.

**How it is verified**
- **Precheck, before the backup**: every `old` name resolves via `col.decks.id_for_name(old)`; every
  `new` name resolves to `None`. On failure, print what and exit non-zero having written nothing.
- Capture, before: `{deck_id: (name, card_count)}` for the whole `Languages::Russian` subtree.
- Apply, then re-capture and assert: **the set of deck ids is identical**, **every deck id's card
  count is identical**, and only the three parent names (plus their four children, by prefix) have
  changed. A vanished deck id or a moved card count is a failure, reported loudly.
- Also assert `col.decks.id_for_name("Languages::Russian::3. Sentences (lingo llama)") is None`
  afterwards and `…::4. Sentences (lingo llama)` is not `None`.

**How it is reversible** — three layers, in order of preference:
1. `--revert` applies the inverse map (`6.`→`5.`, `5.`→`4.`, `4.`→`3.`) in **forward** order, with the
   same precheck/verify machinery. Deck ids never changed, so this restores the prior state exactly.
2. The pre-write backup: `col.create_backup(backup_folder=<collection dir>/backups, force=True,
   wait_for_completion=True)`. `--no-backup` exists but is never used in Phase 8.
3. Anki's own undo — `rename_deck` returns `OpChanges` and registers a `"Rename Deck"` undo entry —
   available only in a live Anki session, so a convenience, not the safety net.

**Acceptance criteria**
- Against a scratch collection seeded with the seven real deck names and cards in each: after
  `main()`, the three parents and four children carry their new names; deck ids unchanged; per
  deck-id card counts unchanged; `1. Alphabet` and the whole `2. Immutable Words` subtree untouched.
- `--revert` immediately after restores the exact original name set.
- Renames are issued in reverse order — assert on the recorded call sequence.
- A precheck failure (e.g. a deck already named `6. Master Russian 300+`) exits non-zero **before**
  `create_backup` is called and before any rename.
- `--dry-run` prints the three planned renames, applies none, and leaves the collection mtime
  unchanged.
- Without `--yes`, a "n" answer applies nothing and exits non-zero.
- A backup exists before the first rename — assert both that `create_backup` was called and on its
  ordering relative to the first `rename`.
- `DBError` on open (Anki running) is caught and reported as *"Make sure Anki is not running"*,
  matching `immutable_words.main`'s existing message.
- No test opens or copies the user's real collection.

**Test approach**: `new contract tests`, against scratch `Collection` instances in `tmp_path` seeded
with the real deck names and a few cards per deck, plus a recording double over `col.decks.rename`
for the ordering assertions.

---

## Phase 7: Integration and dry-run verification

Serialized; these subphases touch shared files no lane may edit concurrently, and 7.2 is the gate
that must pass before any real spend.

### 7.1 — Entry points

**File scope**
- EDIT `libs/python/anki-tools/package.json` (`bin`)
- EDIT the four new modules (shebang + `if __name__ == "__main__":` guard) if not already present

Add, alongside the seven existing `bin` entries: `anki-vocabulary-source`, `anki-mutable-words`,
`anki-mutable-words-audio`, `anki-renumber-russian-decks`.

**Acceptance criteria**: each new module has an executable shebang and a `__main__` guard matching the
existing ones; `pnpm build` in the package succeeds; each `--help` renders without opening a
collection or issuing a request.

**Test approach**: `new contract tests` — a parametrized test invoking each CLI with `--help` in a
subprocess, asserting exit 0 and no network/collection access.

### 7.2 — End-to-end dry run over the real source, zero network, zero mutation

**File scope**
- NEW `libs/python/anki-tools/tests/test_mutable_words_e2e.py`

**Pattern to follow**: `tests/test_min_separation_e2e.py` and `tests/test_separation_repair_e2e.py` —
end-to-end over real data, in a scratch collection, asserting the whole pipeline's shape.

The chain: committed TSVs → `mutable_words_plan` rows → note types + deck tree in a scratch
collection → `.apkg` export → reimport into a second scratch collection → the audio driver's
`--dry-run` cost table.

**This is the last gate before Phase 8 spends money.** Because D6 declined a pre-spend human
checkpoint, this test is the only thing standing between a mistake in the plan module and 2352 paid
requests. Its assertions are therefore stated as exact numbers, not ranges.

**Acceptance criteria**
- **1004 notes / 2366 cards** across the four subdecks, per-deck counts 541/179/152/132 notes and
  1082/716/304/264 cards.
- Round-trip reimport is idempotent: still 1004 notes, still 4 note types, no `+` duplicate.
- The audio plan reports `total 2366`; `pending` equals 2366 minus whatever the fixture media dir
  holds.
- **Every predicted audio filename is well-formed and slash-free**, and the union of predicted
  filenames across all notes has exactly 2366 members.
- Zero HTTP calls (session double raises on use) and zero writes outside `tmp_path`, asserted.
- The user's real collection is never opened by this test.

**Test approach**: `new contract tests`.

---

## Phase 8: Execution against the real world

**Authorized by decision D6.** The user explicitly authorized an agent to perform these steps and
**explicitly declined a pre-spend checkpoint** — no smoke test, no sample card for sign-off. Every
safety mechanism designed in Phases 5 and 6 stays in force; what is gone is the human pause, not the
machinery.

Sequenced so the collection work happens only after the audio exists and the package verifies:
**audio → package → renumber → import.**

Preconditions for the whole phase, checked at 8.1 and re-checked at 8.3:
- 7.2 green — this is the substitute for the declined checkpoint.
- **Anki desktop is not running.** The backend opens collections exclusively; a running Anki yields
  `DBError: "Anki already open, or media currently syncing."`
- `ELEVENLABS_API_KEY` present in the executing environment, sourced from
  `/home/icarus64/repos/daedalus-mono/.env` — gitignored, and therefore **absent from this workflow
  worktree** (verified: no `.env` at the worktree root). The executing agent must load it from that
  absolute path and must never echo, log, or pass it as a flag.

### 8.1 — Generate the 2352 recordings

**File scope**: no repo files. Writes to `~/Desktop/russian-audio` and
`~/.local/share/Anki2/User 1/collection.media`.

Run `anki-mutable-words-audio --dry-run` first and confirm the printed table reads
`total 2366 / present 14 / pending 2352`; a different pending count means something upstream changed
and the run **stops** rather than spending. Then run for real with `--yes`.

**Acceptance criteria**
- The dry-run table reads exactly `total 2366 / present 14 / pending 2352` before the real run.
- After the run, `budget.spent == 2352` and `budget.limit == 2352` as reported by the driver's final
  line.
- `~/.local/share/Anki2/User 1/collection.media` contains all 2366 predicted filenames
  (`<slug>_f1.mp3` and `<slug>_m2.mp3` for every one of the 1183 base words) — counted, not assumed.
- The 14 pre-existing files have unchanged mtimes and sizes (recorded before the run): nothing was
  overwritten.
- No `_f2` or `_m1` file is newly created (the two-voice constraint, verified on disk).
- A spot-check of file sizes shows no zero-byte or truncated `.mp3`.
- Re-running the driver afterwards reports `pending 0` and issues zero requests (proves resumability
  and that the run is complete).
- The API key appears nowhere in any captured output, log, or exit report.
- On interruption: the run is resumed by re-invoking the same command; nothing already generated is
  re-requested, and the exit report records how many requests each attempt actually spent.

**Test approach**: `existing implementation` — the behaviour is pinned by 5.2's suite; this subphase
verifies the real-world result against the counts above.

### 8.2 — Build and verify the real `.apkg` with media attached

**File scope**: no repo files. Writes `~/Desktop/mutable-words.apkg`.

`anki-mutable-words --out ~/Desktop/mutable-words.apkg --audio-dir ~/Desktop/russian-audio`.

**Acceptance criteria**
- The printed deck table reads 541/179/152/132 notes and 1082/716/304/264 cards, total 1004 / 2366.
- `attach_media` reports **0 missing** files — every predicted filename was found. A non-zero missing
  count blocks 8.3 and 8.4.
- The `.apkg` is inspected before import: it contains 1004 notes, 4 note types with the four
  deterministic ids, and 2366 media entries.
- The user's collection mtime is unchanged by this step (`assert_unmodified` passes) — the build is
  still non-mutating even now.

**Test approach**: `existing implementation`, verified against 4.2's asserted contract.

### 8.3 — Back up and renumber the live collection

**File scope**: no repo files. Mutates `~/.local/share/Anki2/User 1/collection.anki2`.

`anki-renumber-russian-decks --dry-run`, then for real with `--yes`.

**Acceptance criteria**
- Anki is confirmed not running before the command is issued.
- A backup file appears in `~/.local/share/Anki2/User 1/backups` with a timestamp from this run,
  **before** the first rename.
- The deck tree afterwards reads `1. Alphabet`, `2. Immutable Words` (+5), `4. Sentences (lingo
  llama)`, `5. 100 Words & Phrases` (+2), `6. Master Russian 300+` (+2).
- **Deck ids are unchanged** and **per-deck-id card counts are unchanged** — 33 / 86 / 70 / 62 / 84 /
  112 / 253 / 100 / 100 / 321 / 321 — captured before and compared after.
- No deck named `Languages::Russian::3. …` exists at this point (the slot is free for the import).
- The rollback path is exercised on paper, not in practice: the exit report records the exact
  `--revert` command and the backup filename.

**Test approach**: `existing implementation`, verified against 6.1's asserted contract.

### 8.4 — Import into the live collection and verify

**File scope**: no repo files. Mutates `~/.local/share/Anki2/User 1/collection.anki2`.

Import `~/Desktop/mutable-words.apkg`. The import is performed programmatically against the closed
collection (Anki desktop stays shut), using the `anki` library's package-import path with
`update_notes` / `merge_notetypes` at their defaults — the same conditions 4.2's reimport-idempotence
test covers.

**Acceptance criteria**
- A second backup is taken before the import.
- Afterwards: `Languages::Russian::3. Mutable Words` exists with subdecks `a. Nouns` (541 notes /
  1082 cards), `b. Verbs` (179 / 716), `c. Adjectives` (152 / 304), `d. Adverbs` (132 / 264).
- The four note types exist with exactly the ids `notetype_id_for_name` predicts, and **no
  `+`-suffixed duplicate note type** was created.
- The pre-existing tree is untouched: `1. Alphabet` 33 cards; `2. Immutable Words` 207 notes / 414
  cards across five subdecks with note type `3897610691970966744` unchanged (same id, same 7 fields,
  same templates); `4.`/`5.`/`6.` card counts as asserted in 8.3.
- `Tools → Check Media` equivalent reports **no missing media** for the new notes — the `AudioRefs`
  field did its job.
- A rendered sample of one card per note type shows: the deck header resolving (not
  `Russian - undefined`), exactly one audio element, and no visible `[sound:…]` text.
- The exit report records both backup filenames and the full reversal procedure (delete the four new
  decks and note types, then `--revert` the renumber, or restore the backup).

**Test approach**: `existing implementation`. Note that reversing an import is materially harder than
reversing a rename, which is why the backup at the top of this subphase is mandatory and why it runs
last in the sequence.

---

## Phase 9: Records

### 9.1 — Runbook: what was executed, and how to reverse each step

**File scope**
- NEW `docs/libs/python/anki-tools/mutable-words-runbook.md`

Written **after** Phase 8, as a record of what was actually done, not instructions for someone else
to do it. Contents: the four commands as executed, the real numbers each one reported, both backup
filenames, and the reversal procedure for each step in reverse order (remove the imported decks and
note types; `anki-renumber-russian-decks --revert`; restore a backup as the blunt fallback; the
generated `.mp3` files are additive and need no reversal).

**Acceptance criteria**: every number in the runbook is a figure actually observed in Phase 8, not
copied from this plan's projections; the two backup filenames are real paths that exist; the key
appears nowhere.

**Test approach**: `existing implementation`.

### 9.2 — Docs

**File scope**
- EDIT `docs/libs/python/anki-tools/README.md`
- NEW `docs/libs/python/anki-tools/mutable-words.md`
- symlinks per `doc-format` if any are missing for this package

Per `doc-format`: docs live under the docs root and mirror the source layout; nested paths are
symlinks to their root counterparts; edit under `/docs`, never the symlinked location.

Content:
- The deck/note-type/field design, the four-cards-per-verb shape (**D2**) and the D3 adverb split,
  with the exact counts (1004 notes / 2366 cards).
- The three deliberate header departures (`#`→`Rank`, `English`→`Translation`, `Status` dropped —
  the last because it is `"New"` on **1002 of 1002** rows) with their reasons.
- **Why dash-only cells are preserved** and what the 143 of them mean.
- The source-of-truth boundary and why the workbook is not a build input.
- The two-voice selection and where it is written down (`mutable_words_plan.VOICE_SLOTS`).
- The exact cost derivation, the collision-check guarantee, and the seven legitimate shared files.
- The renumber's reverse-order requirement and its three reversibility layers.
- The resolved `openpyxl` version read back from `uv.lock` in 2.3.
- **The debt absorbed from the archived plan's dropped subphase 5.4**: `anki-immutable-words` and
  `anki-elevenlabs-tts` get their README entries here, since that plan never documented them
  (verified: 0 mentions today, positive control 14 for `rebalance`).

**Acceptance criteria**: no rationale added to code comments that belongs here; the README's
"Structure / entry points" list includes the four new modules, the four new `bin` entries, **and**
the two previously-undocumented immutable-words commands; every number in the doc matches a number
asserted by a test or observed in Phase 8.

**Test approach**: `existing implementation`.

---

## Risks, open questions, decision points

**No open decision points remain.** D1–D6 and Q1–Q4 were all settled at the plan gate and are
recorded as constraints in "Settled decisions" above and appended to `the-ask.md`.

### Risks

- **R1 — The 2352-request spend is irreversible, and D6 removed the human checkpoint.** This raises
  the stakes on 7.2, which is now the only gate before the spend. Mitigations: an exact,
  dry-runnable cost table derived from real row counts, asserted as exact numbers in 7.2; a hard
  stop in 8.1 if the dry-run pending count is anything other than 2352; a `RequestBudget` sized to
  the computed pending set and never to a round number; resumability keyed on the media directory so
  an interruption costs nothing.
- **R2 — Renaming decks in the live collection (8.3).** Mitigations: precheck before backup, backup
  before first write, reverse-order renames against a `UNIQUE` name index, id-and-card-count
  verification after, `--revert`, `--dry-run`, and a hard stop when Anki is running. Verified from
  the `anki` source that rename touches no card row and preserves scheduling.
- **R3 — Importing into the live collection (8.4) is the hardest step to reverse.** A rename is
  exactly invertible; an import is not. Mitigations: it runs **last**, after the audio exists and
  the package has been inspected; a second backup immediately precedes it; the reimport-idempotence
  property is pinned by tests in 4.2 and 7.2 before it is relied on; the reversal procedure is
  written down in 9.1.
- **R4 — A wrong note-type id or GUID scheme silently duplicates the deck on every re-import.** A
  defect the immutable lane already hit once. Mitigations: deterministic ids from `anki_identity`, a
  golden assertion against the id the live immutable note type actually carries, a two-subprocess
  stability check ruling out salted `hash()`, and explicit reimport-idempotence tests in 4.2 and
  7.2.
- **R5 — Slug collisions as the word set grows ~8×.** Checked: 1183 words → 1183 distinct slugs,
  zero collisions; the 7 media-dir overlaps are byte-identical strings. Made permanent as an
  assertion in 3.3. Per `audio_naming`'s docstring, a real collision must be **reported and resolved
  explicitly** — never patched by re-adding a hash suffix.
- **R6 — Blanket dash-normalization would silently destroy 143 linguistic facts** (107 in
  `Nouns.Plural`, 36 in `Adverbs.Comparative`). The immutable precedent's `_EMPTY_INFO` rule is the
  attractive nuisance here. Mitigated by convention 10, by 3.1's "normalize nothing" contract, and
  by 3.2's dash census assertion.
- **R7 — The existing modules' very heavy docstrings are pre-existing debt, not a pattern.** New
  code must satisfy `minimal-code-comments`, which `check-diff-hygiene.sh` enforces at builder
  teardown and `pr-ready-hygiene-guard.sh` at the draft→ready flip. A builder that mirrors the
  neighbours' comment density will fail those hooks. The one exception is the audio-picker JS
  comment in 2.2, which is part of a generated artifact rather than source commentary.
- **R8 — The workbook drifts.** A renamed or reordered column would silently mis-map fields.
  Mitigated by strict header validation in 3.1 and by the committed TSVs being the only build input.
- **R9 — `.env` is not in the workflow worktree.** `ELEVENLABS_API_KEY` lives in
  `/home/icarus64/repos/daedalus-mono/.env` (gitignored, hence absent from
  `.workflows/mutable-words/`). Phase 8's preconditions name the absolute path; no code change is
  needed since `get_api_key()` reads the environment only.
- **R10 — `~/Downloads/russian_vocabulary.xlsx` may be absent on another machine.** Tests that read
  it `pytest.skip`; the committed TSVs carry every fact the suite actually asserts on.
- **R11 — Phase 1's ordering is load-bearing.** Archiving before relocating deletes a fixture 154
  tests depend on. The `(after: 1.1)` edge on 1.2 is not cosmetic, and 1.2's acceptance criteria
  re-run the suite after the archive precisely to catch a reversed order.
- **R12 — `print_deck_table` hardcodes 2 cards per note** in the immutable precedent
  (`immutable_words.py:286`). Copying it would misreport verb counts by 358. Called out explicitly in
  4.2's acceptance criteria.

### Open questions

None. Every assumption previously flagged as Q1–Q4 was confirmed or overridden at the plan gate.

---

## Skill mapping

| Work | Agent / skill |
|---|---|
| This plan; amendments from the gate | `planner` (`plan-feature`) |
| Plan approval gate | `review-plan` |
| Draft PR opened right after plan approval | `push-pr --stage open-draft` |
| Phase 1 (fixture relocation + old-plan closeout) | `builder` — single lane, dispatched first, before anything else |
| Phase 2 (shared foundation) | `builder` — single lane, after Phase 1 |
| Phase 3 (lane 1), Phase 4 (lane 2), Phase 5 (lane 3), Phase 6 (lane 4) | `builder` per lane, each expanding its subphases into packets for `coder` + `contract-tester` |
| Test authoring in every subphase | `contract-tester` (blind — writes from the contract text only) |
| Implementation in every subphase | `coder` (never reads or writes tests) |
| Lane merge-backs and record commits | `push-pr --stage update` |
| Phase 7 (integration + the pre-spend gate) | `builder` — single lane after all four merge back |
| Phase 8 (execution against the real world) | `builder` — single lane, serialized; holds the API key in its environment and never emits it |
| Code review gate | `review-code` |
| Phase 9 (runbook + docs) and the changelog commit | `document-local` |
| PR gate over the whole branch diff | `review-pr`, then `comment-pr` |
| Draft → ready | `push-pr --stage finalize` |
| Post-merge closeout | `cleanup-merged` |

**Lane shape, stated plainly.** Four lanes, with Phases 1–2 serialized ahead of them and Phases 7–9
serialized behind them. Lanes 1–3 form a dependency chain rooted at 3.3 (lane 1's pure core); lanes
2 and 3 are disjoint from each other; lane 4 has no code dependency at all and shares no file with
anything. The shared touchpoints — `pyproject.toml` and `uv.lock` (2.3), `package.json` (7.1), the
docs tree (9.2), the two existing immutable modules (2.1, 2.2), the four existing test files and the
old plan dir (1.1, 1.2) — are each owned by exactly one serialized subphase and are never touched
from a lane.

**Phase 8 is deliberately not a lane.** It mutates state outside the repo — the user's collection,
their media directory, and their ElevenLabs balance — where worktree isolation provides no
protection and concurrency provides no benefit. It runs once, serially, after everything else is
green.
