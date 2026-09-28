# Mutable Words deck — Phase 8 execution runbook

A record of what was actually run against the live Anki collection to ship the
`Languages::Russian::3. Mutable Words` deck, and how to reverse each step. Written after execution,
from observed output — not from the plan's projections. See
[`mutable-words.md`](mutable-words.md) for the deck/tooling design.

## Preconditions confirmed before any step

- `libs/python/anki-tools` test suite green (800 passed, 0 skipped) and `anki-mutable-words-audio
  --dry-run` reporting exactly `total 2366 / present 14 / pending 2352`.
- Anki desktop confirmed not running (`pgrep -x anki`, `lsof` on `collection.anki2`, `ps -eo
  pid,comm` all clean).
- `ELEVENLABS_API_KEY` loaded from the repo's gitignored `.env` into the process environment only —
  never echoed, logged, or passed as a flag, before or after.

## 1. Audio generation

```
anki-mutable-words-audio --yes
```

- Pre-spend dry run: `total 2366 / present 14 / pending 2352`.
- Final line: `Done: 2352 file(s) generated, 0 skipped (already existed). Budget spent: 2352/2352.`
- All 2366 predicted `<slug>_f1.mp3` / `<slug>_m2.mp3` files present afterwards in both
  `~/Desktop/russian-audio` and the Anki media directory, verified by identity (not by a directory
  file count, which the immutable-words deck's own `f1`/`m2` recordings would inflate).
- The 14 pre-existing shared-word files (`кафе`, `кино`, `кофе`, `метро`, `пальто`, `просто`,
  `согласно`, 2 slots each) were left untouched — mtimes and sizes unchanged, resumability working
  as designed.
- No `_f2`/`_m1` file was newly created — the two-voice constraint held.
- A re-run afterwards reported `pending 0` and issued zero requests.
- No API key appeared in any captured output or log.

## 2. Package build

```
anki-mutable-words --out ~/Desktop/mutable-words.apkg --audio-dir ~/Desktop/russian-audio
```

- Deck table: `a. Nouns` 541/1082, `b. Verbs` 179/716, `c. Adjectives` 152/304, `d. Adverbs`
  132/264 — total **1004 notes / 2366 cards**.
- `attach_media`: **0 missing** — the 14 shared-word files resolved from the Anki media directory via
  the automatic fallback added for this run (see [`mutable-words.md`](mutable-words.md#discrepancies-found-during-the-run)).
- `.apkg` inspected before import: 1004 notes, the four deterministic note-type ids, 2366 media
  entries.
- The live collection's mtime was unchanged by this step.

## 3–4. Backup, renumber, and import — true provenance

**The actual sequence of events is not what the plan projected, and no single exit report captures
all of it — this section states it plainly, since the code-review gate correctly flagged its absence
as a gap.**

1. Lane `l7` ran 8.1 (audio, above) successfully, then hit 8.2's hard stop: `attach_media` reported
   14 missing files (the 7 shared pre-existing words, present only in the Anki media directory). It
   stopped there without improvising.
2. Lane `l11` fixed the underlying tool (`attach_media`'s multi-directory resolution with the Anki
   media directory as an automatic fallback; see [`mutable-words.md`](mutable-words.md#discrepancies-found-during-the-run)),
   after which 8.2's package build reported **0 missing**.
3. `l7` was then re-dispatched for 8.3. Its `anki-renumber-russian-decks --dry-run` ran cleanly and
   produced a real backup (`backup-2026-09-27-21.13.51.colpkg`, taken automatically by the dry-run
   step). The follow-up mutating invocation, `anki-renumber-russian-decks --yes`, was **refused by
   this harness's own Auto Mode safety classifier** — a permission-layer stop separate from, and
   outside, this plan's own D6 authorization (which had already been given by the user at the plan
   gate). `l7` correctly stopped without improvising, leaving the collection unmutated. **`l7-exit.md`
   records the collection as untouched at that point — that report was accurate as of when it was
   written, but it is now stale**, per the sequence below.
4. The user then explicitly granted the permission the harness had withheld. **The orchestrator
   executed 8.3 and 8.4 directly, rather than re-dispatching a builder lane** — a deliberate choice,
   justified by Phase 8 touching no repo files, so there was no ownership ledger a direct execution
   could falsify:
   - Captured the pre-mutation snapshot of every `Languages::Russian::*` deck id and card count
     (33 / 86 / 70 / 62 / 84 / 112 / 253 / 100 / 100 / 321 / 321).
   - Ran `anki-renumber-russian-decks --yes`. A second backup was taken first:
     `backup-2026-09-27-21.28.58.colpkg`. Renamed, in reverse order (`5.`→`6.` first):
     `Languages::Russian::3. Sentences (lingo llama)` → `4. Sentences (lingo llama)`, `4. 100 Words &
     Phrases` → `5. 100 Words & Phrases`, `5. Master Russian 300+` → `6. Master Russian 300+`.
     Verified the deck-id set identical and every card count unchanged before and after.
   - Took a third backup, `backup-2026-09-27-21.29.21.colpkg`, immediately before the import.
   - Imported `~/Desktop/mutable-words.apkg` via `import_anki_package` (`anki` library's
     package-import path, `update_notes`/`merge_notetypes` at their defaults — the same conditions
     the reimport-idempotence tests in Phase 4/7 already cover): **1004 new, 0 updated, 0 duplicate,
     0 conflicting.**
   - Verified afterward: `Languages::Russian::3. Mutable Words` live with `a. Nouns` (541/1082),
     `b. Verbs` (179/716), `c. Adjectives` (152/304), `d. Adverbs` (132/264); the four note types at
     exactly the ids `notetype_id_for_name` predicts (`640194934991873912`, `2868982455410308617`,
     `4593112518148862433`, `835605590205032110`) with no `+`-suffixed duplicate; the pre-existing
     tree untouched (`1. Alphabet` 33 cards; `2. Immutable Words` note type `3897610691970966744`
     unchanged, 7 fields; `4.`/`5.`/`6.` card counts as captured above).
5. Independently re-verified read-only at Record (documenter agent) against the live
   `collection.anki2`, matching every figure above.

## Post-execution fix: the deck header, and a pending re-import

The code-review gate (round 1) found that the note types imported above rendered an unstyled,
incorrect deck header (`#deck-header` with no matching CSS rule, missing the `"Russian - "` prefix
and the `#path` breadcrumb) because `mutable_words_plan.py`'s header constants had been built from
spec rather than copied verbatim from the source note type, per lane l1's own self-reported
discrepancy. Lane `l12` fixed the constants to match the real note type byte-for-byte (verified
against the live collection's own template text) — see
[`mutable-words.md`](mutable-words.md#discrepancies-found-during-the-run).

**The 1004 notes above were imported once with the defective header.** The fix has not yet been
pushed onto the live collection: doing so needs one more `anki-mutable-words` build (with the
corrected constants) followed by one more import, which is safe in place — reimport idempotence is
proven and tested (4.2, 7.2) and will update the existing notes under their stable GUIDs rather than
duplicate them. That re-import is not yet reflected in this runbook because it had not been performed
as of this writing.

## Reversal, in reverse order

1. **Undo the import** — delete the four `Languages::Russian::3. Mutable Words` subdecks and their
   four note types (`Russian - Mutable {Nouns,Verbs,Adjectives,Adverbs} (Ellis Version)`), or restore
   `backup-2026-09-27-21.29.21.colpkg` (taken immediately before the import).
2. **Undo the renumber** — `anki-renumber-russian-decks --revert` (applies the inverse renaming in
   forward order: `6.`→`5.`, `5.`→`4.`, `4.`→`3.`), or restore `backup-2026-09-27-21.28.58.colpkg`
   (taken immediately before the renumber).
3. **`backup-2026-09-27-21.13.51.colpkg`** — taken automatically by lane `l7`'s earlier
   `--dry-run` invocation, before the harness's permission refusal; predates both mutations and is
   the furthest-back restore point from this run.
4. **The generated `.mp3` files are additive and need no reversal** — they only ever fill previously
   missing slots in `~/Desktop/russian-audio` and the Anki media directory.
