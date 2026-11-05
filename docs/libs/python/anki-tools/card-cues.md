# Card cues, case pills, and the mechanical checks

How the Russian word cards (both families: `Russian - Immutable Words (Ellis Version)` and the
Mutable note types) show a word's meaning, its disambiguating cue, and the case it governs, and what
keeps that from regressing. Built by the 11-03-26 `anki-card-cues-rework` run. See
[`mutable-words.md`](mutable-words.md) for the deck design and [`README.md`](README.md) for the sync
and drift tools.

## Rules that shape the data

- **One fact, one place.** A fact is shown once per card side. A cue equal to or contained in the
  gloss is removed; the deck header already says the part of speech, so a bare "adj." / "adverb"
  cue is removed too. Removed text is not moved into another field unless it says something the
  other field does not.
- **Meaning text is frozen.** Only parentheticals and separators may be removed from `Translation`.
  `tests/data/meaning-freeze-baseline.tsv` holds every Translation (1,474 rows) as the baseline;
  `tests/test_qualifier_classification.py` compares the built values against it with tint markup and
  parentheticals stripped. A seeded edit ("thanks to" to "thanks too") fails it.
- **No case names in free text.** `Additional Info`, the distinctions and `Case / Preposition` never
  name a case, in full or abbreviated ("acc.", "D/I/P"), nor describe one roundabout ("takes object").
  The case lives in the `Case` field and renders as a pill. Three words keep a government note
  phrased without a case name: `похожий` ("похож на + what/whom"), `рад`, `аллергия`. Ten advisory
  declension notes (мать, дочь, я, тот, этот, мой, два, восемь, 999, значить) are kept as written and
  allowed by the ban.
- **GUIDs never move.** Notes keep their deterministic GUIDs (`anki_identity.guid_for_row`). A
  renamed row that must keep its note is pinned in `GUID_PINS` (`immutable_words_plan.py`), keyed by
  `(note type label, Russian text)`. It holds one entry, `("Base Adverbs", "так (adverb)")`, which
  keeps the user's reviewed note (27 reviews) instead of minting a new one for the renamed row.
  `WordRow.guid` consults the pins before hashing.

## Case pills

The `Case` field holds the governed case names, comma-separated for several ("Accusative,
Prepositional"). There are no Anki tags and no script: the template renders six pills hidden inside a
wrapper that exists only when `Case` is non-empty, with `data-case="{{text:Case}}"`, and CSS attribute
selectors show the pills the field names. A multi-case word shows one pill per case.
`anki_tools/case_pill.py` builds the block, CSS and palette.

Textbook palette (each pill has light and dark mode colours; every pair is at least 4.5:1 contrast,
asserted by test): Nominative grey, Genitive red, Dative green, Accusative blue, Instrumental orange
(`#c43e00` on light, darkened from the planned `#e65100` which measured 3.79:1), Prepositional purple.

On a word whose meaning lines map to different cases (в, на, с, за, обращаться), each meaning line's
text is tinted in its case's colour, text only, no backgrounds. The mapping lives in the
`meaning->case` column of `case-government.tsv`; a word with one gloss line carrying several cases
(под) stays untinted.

**Who gets a pill.** Every word that governs a case: prepositions, verbs, quantity words (нет, мало,
много, немного, сколько, чуть-чуть, вроде), and the adverb that does. Nouns, adjectives, pronouns and
numerals are excluded: they are declined, not governors, and carry no `Case` field.
`anki_tools/data/case-government.tsv` is the audited source (581 rows: 223 governors and an explicit
`none` row for every other immutable word, verb and adverb), each row with a reference
(en.wiktionary `{{+obj}}`, OpenCorpora transitivity, elon.io government pages). `Case` in
`verbs.tsv`/`adverbs.tsv` equals the table, asserted per row; the immutable `Case` is read from the
table by GUID. `case-text-routing.tsv` (114 rows) records where each removed case-bearing text went.

## Card spec per note type

**Immutable** (`Card 1` Russian to English, `Card 2` English to Russian):

| Side | Card 1 (Russian prompt) | Card 2 (English prompt) |
|---|---|---|
| Front | header, audio, Russian, Russian Distinction cue (same-spelling pairs only) | header, Translation (multi-case lines tinted), English Distinction cue (only where a cue is needed to separate a pair), case pills |
| Back | FrontSide, Translation, English Distinction cue, case pills, Additional Info, Examples | FrontSide (pills appear here once), audio, Russian, Russian Distinction cue, Additional Info, Examples |

Case pills are on both sides for English-prompt cards and on the back only for Russian-prompt cards;
the English cue stays on the Russian-prompt back. The old `#prompt-case` cue and the labelled `Case`
row are gone, and `CASE_CSS`/`CASE_ID` no longer exist.

**Mutable** (Nouns, Verbs, Adjectives, Adverbs, Pronouns, Numerals; headword-front is Card 1, and
Card 3 on Verbs; gloss-front is Card 2, and Card 4 on Verbs):

| Side | Headword-front | Gloss-front |
|---|---|---|
| Front | header, audio, headword, Russian Distinction cue | header, Translation (+ aspect on Verbs), English Distinction cue, case pills (Verbs and Adverbs with `Case` only) |
| Back | FrontSide, Translation, English Distinction cue, case pills (Verbs/Adverbs), counterpart aspect (Verbs), details block, Additional Info, Examples | FrontSide, audio, headword, Russian Distinction cue, counterpart aspect (Verbs), details block, Additional Info, Examples |

The distinctions are no longer detail rows (each used to print twice); `Case` is never a detail row.

**Details block.** The labelled grammar rows (Gender, Plural, Genitive Sg/Pl, Animate, Category,
and each type's inflection fields) render as one centred group: CSS grid with
`grid-template-columns: max-content max-content`, `width: max-content; margin: 0 auto`, row wrappers
`display: contents`, labels right-aligned and values left-aligned on a shared gutter. Each row is
wrapped in `{{#Field}}...{{/Field}}`, so an empty field renders no row and no gap.

**Pronoun Type row.** Anki templates cannot compare two fields, so the pronoun rule is applied in
data: `PronounRow.fields()` empties `Pronoun Type` when its content words equal the cue's (for ты and
вы: when they are contained in the cue), and the existing conditional drops the row. Eleven notes
lose it: ты, вы, кто, себя, тот, какой, который, весь, твой, ваш, свой.

**Deliberate repeats (allowed, listed in `ALLOWED` in `tests/test_card_dedup.py`, each with a
reason):** the six nouns whose Category equals the gloss word (время, люди, семья, тело, здоровье,
раз) since Category is a classification label; and ten short-label cues elaborated by a longer info
line (просто, здравствуйте, это, правда, жаркий, горячий, синий, занятой, грязно, скучно). Dropped as
repeats: only the `только` info line, the `жаловать` info line, and the English cue of `притом` and
`пускай` (their Russian cue stays).

## The three mechanical checks

All run in the normal suite (`pnpm --filter lib.python.anki-tools test`, about 2,700 tests).

1. **Card dedup** (`anki_tools/card_dedup.py`, `tests/test_card_dedup.py`). Renders every template
   side of every note type through the real Anki backend (6,736 sides) and flags, per side: a cue
   equal to or contained in another segment, a cue whose content words are all covered by the union
   of the side's other segments, and more than one case-pill wrapper. Inflection cells are dropped
   before any rule. Exemptions are explicit dicts (`STRUCTURAL`, `ALLOWED`, `OPEN`), each entry with a
   reason, and the tests assert they still reproduce and are disjoint. `OPEN` is empty. The four
   screenshot cases (ещё, до, для того чтобы, всё) pass as shipped and fail on the pre-rework data.
2. **Case ban and coverage** (`anki_tools/case_ban.py`, `tests/test_case_ban.py`,
   `tests/test_case_coverage.py`). The ban pattern over every free-text field of the seven note
   types has zero hits; coverage asserts every governor in the table builds a non-empty `Case`, the
   excluded types carry none, and an emptied preposition fails (positive control).
3. **WebKit layout** (`tests/test_card_layout.py`, needs `playwright==1.61.0` and a WebKit install).
   Renders every mutable sheet x card x (full row set, sparse row set) x (390 px, 768 px) and asserts
   the details block's centre equals the headword's within 1 px, label right edges and value left
   edges align, and no empty field leaves a non-zero-height element. Measurement is text extent, not
   element rects, so a full-width flush-left block cannot pass. The pre-rework template fails all 28
   card/width combinations. If WebKit cannot launch the test skips with the launch error (`-rs`).

Run `anki-source-drift` as a fourth, live check: against the rebuilt-and-imported collection it
reports zero drift, zero orphans, zero missing.

## Form fill

The empty inflection cells in Nouns (Genitive Sg/Pl), Verbs (Conjugation, я, ты, они, Past) and
Adjectives (Short Form, Comparative) were filled from a reviewed artifact, never guessed.

- `anki_tools/form_census.py` counts empty cells per field and reconciles the TSVs against the live
  collection (positive control: counting only `""` undercounts Adjectives Short Form 151 vs 158).
- `anki_tools/form_fill.py` generates `anki_tools/data/russian-vocabulary/form-fill.tsv` (2,355
  rows: 2,267 `missing-filled` plus 88 `unresolved`), the review artifact; its `#` header records
  the source, licence, candidate rule, exclusions, coverage and oracle counts.
- **Source.** The kaikki.org Wiktionary extract of the English Wiktionary Russian entries
  (wiktextract; extracted 2026-10-30 from the 2026-10-01 dump), cross-checked against OpenRussian
  (CC BY-SA 4.0). **Licence note:** Wiktionary entry text is dual-licensed CC BY-SA 4.0 and GFDL;
  kaikki.org states no licence text and asks citation of Ylonen, Wiktextract (LREC 2022). Each row
  carries its source URL. Stress is written as U+0301, absent on monosyllables and on ё; Wiktionary
  footnote marks (`*`, `^*`) are stripped.
- Candidates are only cells empty in both the TSV and the collection; explicit dashes and
  hand-edited cells are never touched. Verbs Conjugation is emitted only when the 2sg/3pl endings
  agree, so irregular verbs stay unresolved. Excluded: Adverbs Formation, Numerals Gender Forms /
  Genitive, Pronouns Oblique Forms.
- Applied: 2,267 cells (nouns 1,209, verbs 815, adjectives 243), each checked as previously empty and
  equal to the approved value, GUIDs and row order unchanged.
- **88 cells stay blank** (72 covered by neither source, 16 covered only by OpenRussian, which the
  source rule leaves unresolved). They are listed in [form-fill-blank-cells.md](form-fill-blank-cells.md) for hand-citing:
  fill the cell in the TSV with a cited value, then rebuild.

## Source drift as a gate

Before touching any source after a pull, `anki-source-drift` must be read: user edits made on a
device show up as drift and are adopted into the sources first (on this run that was one row, это,
whose Translation `this (is) / that (is) / it (is)` was the user's). The 44 `Case` drift rows seen
then were expected: the collection held cases the source did not yet derive.

## Operational notes

- Packages are built to `~/Desktop/anki-rebuild/{mutable,immutable}-words.apkg` and imported by
  `--stage rebuild`; duplicates the source no longer builds (the unreviewed `так` twin and five
  Mutable Nouns twins of indeclinable nouns) are deleted at that step after a backup.
- Audio for `жаловать / пожаловать` and any flagged-audio regeneration need `ELEVENLABS_API_KEY`;
  run `python -m anki_tools.word_audio пожаловать --mode single` in a shell where it is exported,
  and `python -m anki_tools.flagged_audio_cli --fix` for flagged cards. Until then the built mutable
  package references four missing audio files.
