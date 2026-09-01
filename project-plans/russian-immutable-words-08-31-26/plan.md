# Russian Immutable Words — deck package builder + audio generation

**Revision 2, 2026-08-31.** This replaces revision 1's migration design in place (same slug,
per `plan-format`: revisions update the plan, they do not spawn versioned copies). Revision 1
planned a collection migration that moved and retyped 43 existing notes. The user withdrew that
scope — *"dont worry about the other decks for now and moving anything over, for now just make a
new deck… dont worry about other deck overlap at all"* — and then asked for the result as a
script pair rather than a one-off artifact: *"make both a script so we can add the audio part
after. and build incrimentally"*. Everything about matching, moving, retyping and deduplication
is gone, and with it revision 1's decisions D1–D3 and its headline risk R-A.

## Phase syllabus

- [ ] Phase 1: Pure core
  - [ ] 1.1: Source-document parser and row model                            (lane 1)
  - [ ] 1.2: Deck naming and part-of-speech template stripping               (lane 1)
- [ ] Phase 2: Package builder
  - [ ] 2.1: Clone the source note type, minus the rendered part of speech   (lane 1, after: 1.2)
  - [ ] 2.2: Build the deck tree and notes into a scratch collection         (lane 1, after: 1.1, 2.1)
  - [ ] 2.3: Export the `.apkg`, CLI surface, `--dry-run`                    (lane 1, after: 2.2)
- [ ] Phase 3: Verification
  - [ ] 3.1: Round-trip verification — import the package and assert the tree (lane 1, after: 2.3)
- [ ] Phase 4: ElevenLabs audio
  - [ ] 4.1: ElevenLabs text-to-speech client                                (lane 2)
- [ ] Phase 5: Integration
  - [ ] 5.1: `bin` entry points for both commands                            (after: 2.3, 4.1)
  - [ ] 5.2: Audio attachment — fill the `Audio` field and repackage         (after: 3.1, 4.1)
  - [ ] 5.3: Relocate the source word list into the plan directory
  - [ ] 5.4: Document both commands in the docs root                         (after: 5.1, 5.2)

**Lanes: two, by the user's instruction that each script gets its own builder.**

| Lane | Scope | Files (disjoint) |
|---|---|---|
| **1** — deck package | 1.1–3.1 | `anki_tools/immutable_words_plan.py`, `anki_tools/immutable_words.py`, `tests/test_immutable_words_plan.py`, `tests/test_immutable_words.py` |
| **2** — ElevenLabs TTS | 4.1 | `anki_tools/elevenlabs_tts.py`, `tests/test_elevenlabs_tts.py` |

The two lanes share no file and no import: lane 2's client synthesizes a string to an `.mp3`
and knows nothing about decks or packages. Everything that genuinely couples them —
`package.json`'s `bin` block (a shared manifest, touched from both lanes if it were not
serialized), the audio-attachment step that needs both halves, and the docs — is pulled into
**Phase 5, which runs serially after both lanes return**, per `plan-format`'s rule that shared
touchpoints get their own integration subphase rather than being edited from two lanes.

Phase 5.2 remains sequenced after 3.1 by the user's *"build incrimentally"*: the deck package is
verified working before audio is layered onto it.

**No branch, no PR.** The user has said this run does not need one. The publish arc
(`push-pr`, the PR gate, `cleanup-merged`) is therefore not part of this plan; work lands in the
working tree for the user to review and commit as they see fit.

---

## Goal & scope

**Ask of record:** `/home/icarus64/repos/daedalus-mono/.workflows/russian-immutable-words/.artifacts/the-ask.md`

That file carries the verbatim original ask, Amendment 1 (the scope reduction), the surviving
capture-time decisions, requirements R1–R9, the sole open decision D4, and the explicit
out-of-scope list. It was rewritten rather than patched when the amendment landed, so it reads
coherently; its "Amendment 1" section is authoritative wherever it and older text disagree.

### In scope

Two commands in `libs/python/anki-tools`:

1. **`anki-immutable-words`** — reads the source word list, clones the note type
   `Russian - Common Words (Ellis Version) ` (id `1698803891108`) into a new one that does not
   render `{{Part of Speech}}`, and writes a **`.apkg`** carrying the note type, the four
   subdecks and all 152 notes. Importing it once creates everything.
2. **`anki-immutable-words-audio`** — generates Russian audio for those words via ElevenLabs
   text-to-speech and produces a package whose notes have the `Audio` field filled.

Target tree:

```
Languages::Russian::2. Immutable Words
├── a. Prepositions          43 notes   86 cards
├── b. Conjunctions          35 notes   70 cards
├── c. Particles             32 notes   64 cards
└── d. Indeclinable Nouns    42 notes   84 cards
                            152 notes  304 cards
```

### Out of scope

- Reading, moving, editing, deduplicating or renumbering **any** existing deck or note. The
  builder never opens the user's collection for write. It opens it **read-only, once**, solely
  to clone the source note type's CSS and templates (2.1), and must work from an explicit
  `--collection` path or Anki's default location without modifying either.
- Overlap with `2. 100 Words & Phrases` and `4. Master Russian 300+`. ~49 of the 152 words also
  live there; under Amendment 1 this is explicitly fine and is neither measured nor acted on.
- Stress marks. The document's unaccented forms are written verbatim.
- Renumbering the sibling `2.`–`4.` decks — the user does that.

## Stack & MAJOR versions

| Thing | Version | Verified from |
|---|---|---|
| Python | `>=3.11` (3.11.7 in the worktree venv) | `libs/python/anki-tools/pyproject.toml`, `.python-version` |
| `anki` | 26.8.1 | root `uv.lock`, resolved into `.workflows/russian-immutable-words/.venv` |
| `requests` | `>=2.28.0` | `libs/python/anki-tools/pyproject.toml` |
| pytest | dev group | `libs/python/anki-tools/pyproject.toml` `[dependency-groups] dev` |
| Build backend | hatchling, PEP 621 | `libs/python/anki-tools/pyproject.toml` |

`genanki` is **not** installed and must not be added — `anki` 26.8.1 can build and export a
package on its own. Any new runtime dependency (an ElevenLabs SDK) must be justified in 4.1;
prefer `requests`, which is already declared.

## Conventions to enforce

- **Mirror the `due_plan.py` / `rebalance_due.py` split**, the package's established pattern: a
  pure module with no Anki imports and table-driven tests, plus a CLI owning all Anki plumbing.
- Module docstring on every new module explaining its role and naming its only caller, matching
  `due_plan.py`'s opening.
- Frozen dataclasses for value types; type hints throughout; comments on non-obvious fields.
- CLI shape follows `rebalance_due.py`: `argparse`, `--dry-run`, `--collection PATH`, and its
  exact "Make sure Anki is not running when you execute this script." message on `DBError`.
- Tests via `pnpm test` (`py-test` → pytest) in the package; lint via `pnpm lint`. Both must be
  green; the lint baseline is currently clean.
- Secrets never in source. The ElevenLabs key is read from `ELEVENLABS_API_KEY`, already staged
  in the repo-root gitignored `.env`.
- **`.apkg` output is a build artifact** — write it to a path the user names, defaulting inside
  the gitignored run dir. Never commit one.

## Phase 1: Pure core

### 1.1: Source-document parser and row model

- *Files:* `libs/python/anki-tools/anki_tools/immutable_words_plan.py` (new),
  `libs/python/anki-tools/tests/test_immutable_words_plan.py` (new).
- *Pattern:* `anki_tools/due_plan.py` — module docstring naming its only caller, frozen
  dataclasses, no Anki imports. A working draft exists at
  `.artifacts/draft-immutable_words_plan.py`; treat it as a starting point to review, not as
  finished work, and do not assume it is correct.
- *Acceptance:* parses the four `### ` sections of `.artifacts/source-word-list.md` into
  **exactly 152 rows** — 43 / 35 / 32 / 42 in document order. Part 2 of the document (the TTS
  add-on guide, which has no tables) is ignored. A missing section raises, rather than silently
  yielding fewer rows. Each row exposes its six field values with `Russian` and `Translation`
  from the document, `Part of Speech` a singular label, and `Pronunciation` / `Audio` /
  `Additional Info` empty.
- *Tests:* table-driven over a small inline fixture plus the real document; assert per-section
  counts, verbatim preservation of the 17 multi-form rows (`словно / будто`, `ни... ни...`,
  `-то`, `несмотря на то, что`), and that a truncated document raises.

### 1.2: Deck naming and part-of-speech template stripping

- *Files:* same two as 1.1.
- *Pattern:* pure string helpers beside the parser.
- *Acceptance:* `subdeck_name` returns `…::a. Prepositions` … `…::d. Indeclinable Nouns`, plural
  names, in document order. **Every leaf contains `". "`** — assert it, because both templates
  build their header with `deckName.split(". ")[1]` and a leaf without it renders
  `Russian - undefined` (R2). `strip_part_of_speech` removes the `id="part-of-speech"` element
  and returns the input unchanged when there is none.
- *Tests:* assert the `". "` invariant over every generated leaf; assert stripping is a no-op on
  the two template sides that have no such element, and idempotent when applied twice.

## Phase 2: Package builder

### 2.1: Clone the source note type, minus the rendered part of speech

- *Files:* `libs/python/anki-tools/anki_tools/immutable_words.py` (new),
  `libs/python/anki-tools/tests/test_immutable_words.py` (new).
- *Pattern:* `rebalance_due.py`'s collection handling and its `get_anki_collection_path()`
  equivalent in `get_deck_info.py`.
- *Acceptance:* opens the user's collection **read-only**, reads note type `1698803891108` by
  name (the name has a **trailing space** — match it exactly or look up by id), and produces a
  new note type named per D4 with: the same six fields in order; the same CSS **verbatim**; both
  templates with the part-of-speech element stripped and everything else byte-identical,
  the deck-header script included. Assert the source collection's mtime is unchanged after the
  read.
- *Tests:* against a copy of `.artifacts/col-snapshot.anki2` — never the live collection. Assert
  the cloned CSS equals the source CSS exactly, that `{{Part of Speech}}` appears in **neither**
  rendered template, and that `{{Russian}}`, `{{Translation}}`, `{{Audio}}` and the header
  script all survive.

### 2.2: Build the deck tree and notes into a scratch collection

- *Files:* `immutable_words.py`, `test_immutable_words.py`.
- *Acceptance:* creates a temporary collection, adds the cloned note type, creates the four
  subdecks (parents auto-created), and adds all 152 notes to their decks. Result: **152 notes,
  304 cards**, distributed 86 / 70 / 64 / 84. Nothing writes to the user's collection at any
  point.
- *Tests:* assert the per-deck card counts and that every note has exactly 2 cards. Assert the
  two `да` notes (Conjunctions #20 and Particles #20 — the only exact intra-doc duplicate, and
  intended) both exist, in their respective decks.

### 2.3: Export the `.apkg`, CLI surface, `--dry-run`

- *Files:* `immutable_words.py`, `test_immutable_words.py`.
- *Acceptance:* exports a `.apkg` at `--out`. `--dry-run` prints the per-deck table and writes
  nothing. `--collection` overrides auto-detection. A locked collection produces
  `rebalance_due.py`'s exact "Make sure Anki is not running" message. **Refuses to overwrite an
  existing `--out` without `--force`** (R9's spirit: no silent clobber).
- *Tests:* assert the file is produced and non-empty; assert `--dry-run` leaves no file behind;
  assert the overwrite refusal.

## Phase 3: Verification

### 3.1: Round-trip verification — import the package and assert the tree

- *Files:* `test_immutable_words.py`.
- *Acceptance:* the strongest evidence this run can produce — build the `.apkg`, import it into
  a **fresh empty collection**, then assert the imported result: the four deck paths exist with
  their `<letter>. ` leaves intact, 152 notes / 304 cards distributed 86 / 70 / 64 / 84, the
  note type present with `{{Part of Speech}}` rendered nowhere, and a spot-checked note's
  `Russian` and `Translation` matching the document verbatim.
- *Tests:* this subphase **is** the test. It must exercise a real import, not a re-read of the
  builder's own in-memory state.

## Phase 4: ElevenLabs audio

### 4.1: ElevenLabs text-to-speech client

- *Files:* `libs/python/anki-tools/anki_tools/elevenlabs_tts.py` (new),
  `libs/python/anki-tools/tests/test_elevenlabs_tts.py` (new).
- *Pattern:* `anki_scrapers/text_to_speech/basic_google_TTS.py`'s `build_and_save(word, ...)`
  shape and its retry decorator; `rebalance_due.py` for the CLI.
- *Acceptance:* reads `ELEVENLABS_API_KEY` from the environment (never a literal, never a CLI
  flag that would land in shell history); synthesizes one Russian string to an `.mp3` at a
  deterministic filename; retries with backoff; **skips a file that already exists** unless
  asked to replace, so a resumed run is cheap and idempotent. Voice id and model are flags with
  documented defaults. A missing key fails with a clear message naming the variable, never a
  traceback.
- *Tests:* the HTTP call is **mocked** — no test may hit the network or spend the user's
  credits. Assert the request carries the key from the environment, that an existing file is
  skipped, that backoff fires on a 429, and that a missing key raises the friendly error.
- *Open question for 4.1:* which voice. Needs the user's pick before this ships; see Risks.

## Phase 5: Integration

### 5.1: `bin` entry point

- *Files:* `libs/python/anki-tools/package.json`.
- *Acceptance:* `"anki-immutable-words": "anki_tools/immutable_words.py"` added alongside the
  existing five, matching their exact style. No other manifest key changes.
- *Tests:* none beyond `pnpm lint` staying green; this is a manifest edit.

### 5.2: Audio attachment — fill the `Audio` field and repackage

- *Files:* `immutable_words.py` (or a thin sibling), `test_immutable_words.py`.
- *Acceptance:* given a directory of generated `.mp3`s, adds each as a media file and sets the
  note's `Audio` field to `[sound:<filename>]`, matching the existing `ic_mr_*.mp3` convention
  in `4. Master Russian 300+`. Exports a package whose media travels with it. Words with no
  audio file keep an empty `Audio` field and are reported, not silently skipped.
- *Tests:* build with a fixture directory of tiny fake mp3s; assert `[sound:…]` values are set,
  that media is present in the exported package, and that a missing file is reported.

### 5.3: Relocate the source word list into the plan directory

- *Files:* `project-plans/russian-anki-cards-08-31-26/` (removed),
  `project-plans/russian-immutable-words-08-31-26/` (the promoted plan dir).
- *Acceptance:* the word list moves into this plan's own directory and the stray, wrongly-named
  directory is gone. It is currently untracked in the main checkout and sits at a path
  `plan-format` does not permit.

### 5.4: Document both commands in the docs root

- *Files:* `docs/libs/python/anki-tools/README.md` (exists — extend, do not replace).
- *Acceptance:* both commands documented in the style of the existing `anki-rebalance-due`
  section: flag table, what it does, what it refuses to do. Must state plainly that the builder
  **never writes to the user's collection**, and that the `.apkg` is imported by the user.
- *Tests:* none; prose. `doc-format` governs placement.

## Risks, open questions, decision points

### Open decisions

- **D4 — the new note type's name.** Proposed `Russian - Immutable Words (Ellis Version)`,
  dropping the source's trailing-space typo. User-visible in Anki's note-type list and awkward
  to rename later. *Carried from revision 1; still unanswered.*
- **D5 — the ElevenLabs voice.** 4.1 cannot ship a sensible default without a pick. Needs a
  voice id, and a decision on model (quality vs cost per character). Blocks 4.1 only; phases
  1–3 proceed without it.

### Risks

- **R-1 — the builder must never write to the live collection.** It opens it read-only for one
  note-type read. Mitigated by 2.1's mtime assertion, by every test running against a copy of
  the snapshot, and by the `.apkg` design itself: the user's collection changes only when they
  choose to import. *This replaces revision 1's R-A and R-B, both of which are gone with the
  retype.*
- **R-2 — re-importing the package twice.** Anki's importer dedupes on the first field within a
  note type, so a second import of an unchanged package updates rather than duplicating. This
  should be **verified in 3.2**, not assumed — and the docs should say what actually happens.
- **R-3 — ElevenLabs costs real money per character.** 152 short words is small, but a retry
  loop or an accidental re-run is not free. Mitigated by 4.1's skip-if-exists behaviour and by
  tests never hitting the network.
- **R-4 — the snapshot is from 2026-08-31.** Only 2.1 depends on the live collection, and only
  for the note type's CSS and templates. If the user edits that note type's styling before the
  real run, the clone picks up the newer styling — which is correct behaviour, not a defect.
- **R-5 — the repo-wide `smart-lint` hook fires on every edit.** Recorded in this project's
  memory: it lints repo-wide, so one edit can surface unrelated findings. Route bulk edits via
  Bash, restore collateral, and leave pre-existing debt elsewhere alone.
- **R-6 — two sibling decks both prefixed `2. `.** `2. Immutable Words` and
  `2. 100 Words & Phrases` coexist until the user renumbers. Anki permits it and the header
  script reads the *leaf*, so nothing breaks; the docs should say so.

### Assumptions I could not verify

- **That `anki` 26.8.1's importer dedupes on first field as described in R-2.** 3.2 must
  actually test it.
- **That the user's Anki desktop client can import a package written by `anki` 26.8.1.** A much
  older client may not. The `.apkg` route is far safer here than the retype revision 1 planned,
  but it is still worth confirming the client version.

## Skill mapping

| Stage | Skill / agent | Notes |
|---|---|---|
| Build (single lane, `l1`) | `builder` → `coder` + `contract-tester` | Phases 1–5, dispatched incrementally: 1–3 first, then 4, per the user's "build incrimentally" |
| Code gate | `review-code` | Focus on R-1 (no writes to the live collection) and 3.2's round-trip evidence |
| Records + docs | `document-local` | Phase 5 |
| Publish | `push-pr` (`open-draft` → `update` → `finalize`) | |
| PR gate | `review-pr` → `comment-pr` | |
| Closeout | `cleanup-merged` | |
