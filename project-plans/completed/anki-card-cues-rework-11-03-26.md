# Anki card cues rework: case pills, de-duplicated cues, planned card layouts, filled form fields

### Ask of record

**11-03-26** — we need to review recent anki conversations and note a few things are clearly wrong:
1. You added a new field recently and did so very lazily, you didn’t remove the text from the English and Russian fields so now a bunch of them have duplicate text. On top of that some of that text should stay in the English and Russian field and some of it should move over if a word has several meanings in the info only applies to a part of that meaning it should stay in the English field.
2. You modified the values of some of the English fields, when I specifically told you not to edit the meanings of any of the fields. You were only permitted to remove things in parentheses, but you are not permitted to modify any of the actual text meetings. Do not modify them back, but report to me which words you did this for.
3. The words case should be added not as additional info, and not in the English field, but as a tag. Each one should be color-coded: Nominative, Genitive, Dative, Accusative, Instrumental, Prepositional.  Given that the English version of virtually every immutable word can be differentiated by case that should be the thing we use to differentiate word types, not the notes you just added.

We want to really plan the new card set ups out, and make sure it actually makes sense for learning and differentiation. He also want to make sure any fields with duplicate info gets removed. Like on the card where the word generative is shown twice.

Screenshots attached to the ask (AnkiMobile, as the user sees cards today):
1. /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/097e593f-image.png — Base Adverbs, ещё answer: English "still / yet (ongoing) / more (asking for more)", grey cue "(ongoing, or asking for more)", info line "Marks an ongoing status or asks for more" — same info three times.
2. /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/bcbca38a-image.png — Prepositions, до answer: "up to (where/what) / until / before (when)", grey "(Genitive)", labelled row "Case Genitive" — Genitive twice.
3. /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/ad1317d0-image.png — Conjunctions prompt: "so that / in order to", grey "(so that + past or infinitive)" — cue repeats the gloss.
4. /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/65640f92-image.png — Particles prompt: "still / all / constantly (keeps on)", grey "(keeps on)" — parenthetical duplicated by the cue.

**11-03-26 — appended, mid-plan, case tag placement** — This updated photo is a (poorly done) version of what i mean. And case should be shown on both sides for english, and at least on back for russian (but maybe just both sides for both?)

Screenshot: /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/98efbd1c-image.jpg — the до card marked up by the user: the grey inline "(Genitive)" under the gloss is struck out in red; the "Case" label is struck out in red; the bare word "Genitive" is highlighted yellow and circled — i.e. a single colored case tag, no label, no inline duplicate.

**11-03-26 — appended, mid-plan, case not in English Distinction** — Case should not be in english destinction

Screenshot: /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/4c81d6cf-image.png — AnkiMobile note editor for the до note: fields Audio (4 recordings), Additional Info (empty), Examples (empty), Case = "Genitive", Russian Distinction (empty), English Distinction = "Genitive", Tags (empty). The case name is stored in BOTH the Case field and the English Distinction field; the Tags box is empty.

**11-03-26 — appended, mid-plan, case coverage** — And make sure all cards correctly have case filled out (except words that are modified by case like nouns adjectives pronouns and numerals)

**11-03-26 — appended, mid-plan, mutable form fields** — Also add to the plan filling out the remaining form fields in ALL mutable words, and  horizontally aligning (centering) those fields better

Screenshot: /home/icarus64/.claude/uploads/5175e9a8-4915-4172-9ce3-ab7ad3c07e8e/aa2b722c-image.png — Mutable Words > Nouns, жизнь answer side: word, "life", then left-aligned labelled rows "Gender f", "Plural жи́зни", a blank gap (empty form fields rendering nothing), then "Animate No", "Category Life & Mind". Labelled rows are flush-left under a centred headword.

**11-03-26 — appended, mid-plan, alignment clarification** — Or vertical, which ever makes the top and bottom center aligned


## Phase syllabus
- [ ] Phase 1: Sync down and adopt the user's edits
  - [x] 1.1: Split the sync script into pull / rebuild / push stages          (lane 1)
  - [x] 1.2: Source-drift tool: collection fields vs what the sources build   (lane 1)
  - [x] 1.3: Pull from AnkiWeb, run the drift tool, adopt the user's edits as source  (after: 1.1, 1.2)
- [ ] Phase 2: Reports, audits, and the review gate
  - [x] 2.1: Report of English meaning text changed by agent commits          (lane 2, after: 1.3)
  - [x] 2.2: Collision analysis: what the case pill, deck header, and cues each separate  (after: 1.3)
  - [x] 2.3: Per-word qualifier classification artifact                        (after: 2.2)
  - [x] 2.4: Case-government audit with the meaning-to-case table, cited      (after: 1.3)
  - [x] 2.5: Case-text routing list for every free-text field                 (after: 2.4)
  - [x] 2.6: Draft the пожаловать row                                          (after: 1.3)
  - [x] 2.7: User review gate on every artifact before any write              (after: 2.1, 2.3, 2.5, 2.6, 6.3)
- [ ] Phase 3: Case pills on the immutable deck
  - [x] 3.1: Case field values from the audited case table                    (lane 3)
  - [x] 3.2: Pill block, textbook palette, meaning-line tint                  (lane 3, after: 3.1)
  - [x] 3.3: Immutable templates per the card spec; remove the case cue and the labelled Case row  (lane 3, after: 3.2)
- [ ] Phase 4: Mutable layouts, data apply, checks, deletions
  - [x] 4.1: Mutable templates per the card spec: centred label/value block, no empty rows, distinction rows removed, Case pill on Verbs and Adverbs  (lane 4, after: 1.3, 3.2)
  - [x] 4.2: Layout render harness dev dependency                             (after: 4.1)
  - [x] 4.3: Apply the approved artifacts to the sources                      (after: 2.7, 3.3, 4.1)
  - [done] 4.4: Generate audio for пожаловать                                     (after: 4.3)
  - [x] 4.5: Rendered-card duplicate check across every note type and template  (after: 4.3)
  - [x] 4.6: Case checks: name and roundabout ban, coverage, exclusion        (after: 4.3)
  - [x] 4.7: Centre-line render assertion on every mutable answer side        (after: 4.2, 4.3)
  - [x] 4.8: Retire the workbook importer                                     (after: 4.2, 4.3)
  - [x] 4.9: Delete the shared replaced paths, with a dangling-reference sweep  (after: 4.5, 4.6, 4.7, 4.8)
- [ ] Phase 5: Integration, serialized
  - [x] 5.1: Re-pull, rebuild both packages, verify GUIDs, import locally     (after: 4.9, 6.4)
  - [done] 5.2: Regenerate audio for flagged cards                               (after: 5.1)
  - [x] 5.3: Verify the live collection                                       (after: 5.2)
  - [x] 5.4: Push to AnkiWeb, gated on the user's explicit confirmation       (after: 5.3)
- [ ] Phase 6: Fill the empty mutable form fields
  - [x] 6.1: Field census per mutable note type, with a positive control     (lane 5)
  - [x] 6.2: Reference spike: stressed-form source, license, coverage         (lane 5, after: 6.1)
  - [x] 6.3: Form generator and the reviewable fill artifact                  (lane 5, after: 6.2, 1.3)
  - [x] 6.4: Write the approved fills into the TSVs                           (after: 2.7, 4.3)

## Goal & scope

**Goal.** Fix three problems the anchors (`ce413d3`, `5b84a2b`) introduced into the Russian Anki
decks, and finish the cards properly:
1. Text is duplicated between the distinction fields, the gloss parentheticals, the case cue, and the
   info row (screenshots: ещё, до, чтобы, всё).
2. Agents changed some English meanings. The user gets a report of every one; nothing is reverted.
3. Grammatical case moves out of every free-text field into a colour-coded case **pill**, rendered from
   the `Case` field. This was settled at the gate: "tag" in the ask means a coloured pill, not an Anki
   tag.

The plan also:
- gives each of the seven note types a settled card spec, including a centred label/value block on
  mutable answers;
- fills the empty inflection fields on every mutable word from a cited reference;
- carries over the unfinished work of the superseded plan;
- ends with an AnkiWeb push gated on the user's confirmation.

**Supersession.** This plan supersedes `project-plans/proposals/anki-outstanding-fixes-10-29-26.md`
(user decision D9 at the 11-03-26 gate). Why: that plan's cue-placement work shipped in `5b84a2b`,
but its "case cue yields to the English cue" ruling and its answer-side labelled Case row are exactly
what this plan replaces.

Status of the old plan's subphases, read from HEAD `138fd75`:
- **Shipped in `5b84a2b`:** 2.1–2.3, 3.1, 3.2, 4.1, 5.1, 8.1–8.3.
- **Built by `aa9d0f2`/`138fd75`:** the pull/rebuild/push tool.
- **Carried over here:**
  - its unfinished 6.1 (add `пожаловать`, the one word still missing from the phrase decks) — here 2.6 and 4.3;
  - its 6.2 (that word's audio) — here 4.4;
  - the `anki-flagged-audio --fix` half of its 7.2 — here 5.2;
  - its integration 7.1–7.3 — here 5.1–5.4.

The old file is deleted through `plan-lifecycle.sh supersede` at promotion. This plan does not delete
it.

**In scope**
- `libs/python/anki-tools/`:
  - the immutable and mutable builders and their template helpers (`prompt_hint.py`, `case_field.py`,
    `distinction.py`, `mutable_words_plan.py`);
  - the immutable source `tests/data/source-word-list.md` (it really lives under `tests/data/`;
    `immutable_words.py --source` points at it);
  - the six vocabulary TSVs;
  - `anki_sync_and_restore.py`;
  - `vocabulary_source.py`, which is retired.
- New committed data artifacts.
- The gloss-edit report.
- Rebuilding, re-importing and pushing the live collection.

**Out of scope**
- Changing any English or Russian meaning text. The one permitted edit to a `Translation`/`English`
  value is moving or removing a parenthesized qualifier, per ask item 1.
- Reverting the agents' earlier meaning edits ("Do not modify them back").
- Scheduling and review data. The only due-date changes are the phrase set-due and aspect steps that
  `anki_sync_and_restore.rebuild` already runs and guards (`138fd75`).
- The 5 notes left in the Mutable Nouns note type after `45f3612` removed their rows from `nouns.tsv`:
  пальто, кино, кафе, метро, кофе. The collection holds 636 Nouns notes against 631 TSV rows. They
  are reported by the drift tool, not fixed here.
- Moving the immutable source out of `tests/data/`.

**Run size.** Phase 6 is large: about 2,600 empty inflection cells (census at planning time, see 6.1).
The user decided at the round-2 gate that it stays in this run.
- It shares no files with Phases 3–4 except the TSVs, which only the serialized 1.3, 4.3 and 6.4
  write.
- It runs as its own lane, is reviewed at the same gate (2.7), and 5.1 waits on it (`after: 6.4`).
- The consequences are listed under Risks (R7).

## Stack & MAJOR versions

| Component | Version | Verified from |
|---|---|---|
| Python | `>=3.11` (worktree `.venv` 3.11.7) | `libs/python/anki-tools/pyproject.toml`; init-workspace report |
| `anki` (Python package over the rslib backend) | 26.8.1 | root `uv.lock` lines 239-240 |
| `openpyxl` | 3.1.5, removed by 4.8 | root `uv.lock` lines 2168-2169 |
| `pytest` | 9.1.1 | root `uv.lock` lines 2743-2744 |
| `playwright` (Python, dev group; new) | pinned at 4.2 to the version whose bundled WebKit matches the cached `~/.cache/ms-playwright/webkit-2311` | 4.2 verifies before pinning |
| Package and env manager | uv workspace (root `pyproject.toml` `[tool.uv.workspace]`), driven through pnpm (`py-test` → `uv run --group dev pytest`, `py-lint` → ruff) | root `pyproject.toml`; `libs/python/anki-tools/package.json`; `libs/bash/build-tools/py-scripts/py-test` |
| Card renderer | Anki templates: `{{Field}}`, `{{text:Field}}`, `{{#F}}`/`{{^F}}` | docs.ankiweb.net/templates/fields.html ("If you prefix a field name with text:, Anki will not include any formatting."); templates/generation.html |
| Client | AnkiMobile (iOS, WebKit) | ask screenshots |

**Template facts the design relies on**
- **A field can be used inside an HTML attribute.** The manual's own example is
  `<a href="http://example.com/search?q={{Expression}}">` (fields.html, "Dictionary Links").
- **JavaScript.** Template JS "is provided without any support or warranty", and `{{FrontSide}}` re-runs
  the front's scripts (docs.ankiweb.net/ankimobile/more; anki `ts/reviewer/index.ts`). The pill design
  below therefore uses no script.
- **Night mode.** It is the `.nightMode` class on both desktop and AnkiMobile
  (templates/styling.html#night-mode, ankimobile/night-mode).
- **Import behaviour.** An `.apkg` import updates notes matched by GUID and never overwrites existing
  cards' scheduling. Source: rslib `import_export/package/apkg/import/notes.rs` and `cards.rs`, checked
  at commit `1003906` on 11-03-26.

**Stress convention.** Existing forms carry stress as a combining acute U+0301 after the vowel, as in
`жи́зни`. `ё` is never marked. The planning probe counted 595 such lines in `nouns.tsv`, 214 in
`verbs.tsv` and 159 in `adjectives.tsv`.

## Conventions to enforce

These are hard constraints.

1. **GUIDs never change.**
   - Immutable: `guid_for_row(self.russian, self.pos)` over the QUALIFIED headword
     (`immutable_words_plan.WordRow.guid`). The field gets `strip_qualifier(...)`. Pinned in
     `tests/data/immutable_guids.json`.
   - Mutable: pinned in `test_mutable_words_plan.py`.
   - No subphase edits a `russian` key, a TSV headword, or a `pos`. No note is split.
2. **Note types and fields.**
   - Note-type ids stay pinned (`NEW_NOTE_TYPE_ID`, `mutable_words_plan.build_note_type_id`).
   - Template ids stay pinned (`build_template_id`).
   - A newly appended field has `id` set to `None`, so a re-import matches it by name
     (`immutable_words.clone_note_type`).
   - No field is renamed or removed. `Case` stays.
   - `mod` is bumped on every build.
3. **Meaning text is frozen.**
   - A `Translation` value may lose or gain only a parenthesized segment, plus the build-time tint
     markup of 3.2.
   - After stripping tags and parentheticals and normalizing whitespace, it must be byte-identical to
     the value captured at 1.3. Test-enforced by 4.3.
4. **No case name or case paraphrase in a free-text field.**
   - The free-text fields are `Translation`, `English Distinction`, `Russian Distinction` and
     `Additional Info` on all seven note types, plus the residue of Verbs `Case / Preposition`.
   - None of them may contain a case name or a roundabout description of one. The pattern is defined
     in 4.6.
   - The case lives in `Case`, rendered as a pill.
   - Inflected word types keep their forms in their own per-case fields (`Genitive Sg/Pl`, `Oblique
     Forms`, `Genitive`, `Case Governed`), never in a note.
5. **The TSVs in git are the only mutable source.**
   - The workbook `~/Downloads/russian_vocabulary.xlsx` is retired (user decision D8).
   - No subphase mirrors anything to it.
   - 4.8 removes the importer that could regenerate TSVs from it.
6. **Pure cores stay pure.**
   - `*_plan.py`, `case_field.py`, `prompt_hint.py`, `distinction.py` and the new pure modules carry no
     Anki imports.
   - Anki plumbing stays in `immutable_words.py` and `mutable_words.py`.
7. **The live collection is written only through `anki_sync_and_restore.py`.**
   - Every write is preceded by a backup.
   - Anki must not be running.
   - Builders open the source collection read-only and check its mtime afterwards
     (`immutable_words.assert_unmodified`).
8. **Credentials stay in memory.** Never on disk, never echoed, never in argv. The existing grep test
   (`aa9d0f2`) stays green.
9. **Repo landing practice.** The repo's `CLAUDE.md` says work lands by a local merge into `main` and a
   push of `main`, never a PR. This is flagged for the orchestrator.
10. **Commit messages.** No attribution trailers of any kind: no `Co-Authored-By`, no `Claude-Session`,
    no session URL.
11. **Code style.**
    - Minimal comments.
    - Table-driven tests (`pytest.mark.parametrize`).
    - Every negative check carries a positive control, as in
      `test_empty_cue_renders_nothing_and_the_check_fails_without_the_wrapper`.
    - Untrusted downloaded data (6.2 reference dumps) goes in its own directory, and is read with
      `python -I`.
12. **Tooling.** pnpm and uv only: `pnpm test` / `pnpm lint` in `libs/python/anki-tools`, or
    `uv run --group dev pytest`.

## Settled design (user decisions at the 11-03-26 plan gate)

**Case pill, no Anki tags (D7, D2, D11)**
- `Case` stays the single source of case. It holds canonical names, comma-separated in the order the
  source names them, e.g. `Accusative, Prepositional`.
- **Mechanism, chosen: fixed pills toggled by attribute selectors. No script, and the field stays
  plain text.**
  - The template carries one wrapper, `<div class="case-pills" data-case="{{text:Case}}">`, holding six
    fixed `<span class="case-pill case-<name>"><Name></span>` elements, hidden by default.
  - CSS shows each one with `.case-pills[data-case*="Genitive" i] .case-genitive { display:
    inline-block }`.
  - `*=` (substring) is safe: no case name is a substring of another.
  - `text:` strips any formatting a phone edit introduces.
  - The `{{#Case}}…{{/Case}}` conditional makes an empty `Case` render nothing.
- **Trade-off.**
  - Pills appear in the fixed canonical order (Nominative → Prepositional), not in field order.
  - In return, the field stays human-editable on the phone: type `Genitive`, get a red pill.
- **Rejected alternatives.**
  - Build-time HTML pills in the field. The field becomes markup in the phone editor, and an edit
    breaks the class.
  - `class="case-pill {{Case}}"`. A comma list yields broken class tokens.
  - A splitting script. The user asked for no card script.
  - 3.2's render test proves that `data-case="{{text:Case}}"` renders as specified.
- **Palette (D2, textbook).** Each case gets a text colour and a pill background, plus a `.nightMode`
  variant. Final shades are fixed in 3.2, which keeps text at 4.5:1 contrast or better.

  | Case | Light | Dark |
  |---|---|---|
  | Nominative | grey `#616161` | `#bdbdbd` |
  | Genitive | red `#c62828` | `#ef9a9a` |
  | Dative | green `#2e7d32` | `#a5d6a7` |
  | Accusative | blue `#1565c0` | `#90caf9` |
  | Instrumental | orange `#e65100` | `#ffb74d` |
  | Prepositional | purple `#6a1b9a` | `#ce93d8` |

  Every pill shows its case name as text, so colour is never the only signal.
- **Multi-case words (D11).**
  - One pill per case.
  - Each English meaning line's TEXT colour (never background) is tinted to the case that meaning
    takes. The mapping comes from the hand-verified meaning→case table in `case-government.tsv` (2.4).
  - Mechanism: at build time, `WordRow.fields()` wraps each `<br>`/`<div>`-separated line of a mapped
    note's `Translation` in `<span class="case-text case-<name>">…</span>`. The source text is
    untouched. The meaning freeze compares after stripping tags.
  - A line with no single case (for example a verb whose two cases are two arguments of one meaning)
    stays untinted.
- **Coverage (D1, D5).**
  - Every word that governs a case gets a pill, indiscriminately: prepositions, the quantity words and
    other immutable governors that 2.4 finds, every case-governing Verb, and every case-governing
    Derived Adverb.
  - Only Nouns, Adjectives, Pronouns and Numerals are excluded: they are inflected by case and get no
    `Case` field and no pill.
  - Verbs and Adverbs gain an appended `Case` field (`id` None). That is a schema change, which forces a
    full sync; the staged script handles it.

**Placement (D3).**
- English-prompt cards show the pill on both sides. It is placed on the front; the back shows it
  through `{{FrontSide}}`, once.
- Russian-prompt cards show it on the back only.

**Cues (D1, D4).**
- Distinction text survives only where it says something other than the case. Any cue that is a case
  name or a roundabout description of one is removed.
- The English cue stays on the Russian-prompt back (D4). Ask item 1 can move whole-word qualifiers into
  it.
- A cue that only repeats the deck header (`adj.`, `adv.`, `noun`, …) is removed. The header
  `Russian - <leaf>` already shows it. The planning probe found 72 such cues; review found 65 with a
  narrower label list; 2.2 settles the count.

**Free-text case ban scope (D6).** Every free-text field on every note type, `Additional Info`
included. 2.5 routes each hit to the right field, or deletes it.

**Sources (D8).** The TSVs only. The workbook is retired.

**Report (D10).** The report is `<plan-dir>/gloss-edit-report.md`, beside `plan.md`.

## The card spec (settled; the user reviews the rendered result at 5.3)

**Immutable** (`Russian - Immutable Words (Ellis Version)`, 234 notes. `Card 1` is Russian→English,
`Card 2` is English→Russian. Structure read from the local collection and
`immutable_words.clone_note_type`.)

| Side | Card 1 (Russian prompt) | Card 2 (English prompt) |
|---|---|---|
| Front | deck header · audio · Russian · Russian Distinction cue (same-spelling pairs only) | deck header · Translation (multi-case lines tinted) · English Distinction cue (only where 2.2 needs one) · case pills |
| Back | FrontSide · Translation (tinted) · English Distinction cue · case pills · Additional Info · Examples | FrontSide (pills appear here once) · audio · Russian · Russian Distinction cue · Additional Info · Examples |
| Removed | `#prompt-case`; the labelled `Case` row; every cue equal to or contained in the gloss; every case name in free text | same |

**Mutable** (Nouns, Verbs, Adjectives, Adverbs, Pronouns, Numerals, all from
`mutable_words_plan.build_template`. The headword-front cards are Card 1, and Card 3 on Verbs. The
gloss-front cards are Card 2, and Card 4 on Verbs.)

| Side | Headword-front card | Gloss-front card |
|---|---|---|
| Front | deck header · audio · headword · Russian Distinction cue | deck header · Translation (+ aspect on Verbs) · English Distinction cue · case pills (Verbs and Adverbs with `Case` only) |
| Back | FrontSide · Translation · English Distinction cue · case pills (Verbs/Adverbs) · counterpart aspect (Verbs) · **details block** · Additional Info · Examples | FrontSide · audio · headword · Russian Distinction cue · counterpart aspect (Verbs) · **details block** · Additional Info · Examples |
| Removed | the `detail-russian-distinction` and `English Distinction` detail rows (today each distinction prints twice: as the FrontSide cue and as a detail row, because `_detail_fields` excludes neither); `Case` is never a detail row | same |

**Details block (ask entries "mutable form fields" and "alignment clarification").**
- The labelled grammar rows are Gender, Plural, Genitive Sg/Pl, Animate, Category on Nouns, and each
  note type's inflection fields.
- They render as one group, centred on the same centre line as the headword and gloss. Rows are not
  each centred on their own.
- Inside the block, labels and values align to a shared gutter: labels right-aligned, values
  left-aligned. This is a two-column layout (CSS grid `grid-template-columns: max-content max-content`)
  whose container is centred (`width: max-content; margin: 0 auto`).
- Each row is wrapped in `{{#Field}}…{{/Field}}`, so an empty field renders no row and no gap. Today
  жизнь shows a blank gap where its empty `Genitive Sg/Pl` divs render.
- `Additional Info` and `Examples` keep their own full-width styling below the block.
- 4.7 asserts that the block's horizontal centre equals the headword's.

## Phase 1: Sync down and adopt the user's edits

### 1.1: Split the sync script into pull / rebuild / push stages
- **File scope:**
  - `libs/python/anki-tools/anki_sync_and_restore.py`
  - `libs/python/anki-tools/tests/test_anki_sync_and_restore.py`
- **Why.** `main()` runs pull → rebuild → push in one pass (`aa9d0f2`). That leaves no point to adopt
  the user's phone edits, and no point to gate the push on the user's confirmation.
- **Pattern.**
  - `pull`, `rebuild`, `push`, `push_media` and every guard stay as they are.
  - A new argparse `--stage {pull,rebuild,push,all}` dispatches to them; `all` keeps today's behaviour.
  - Each stage keeps its own backup, Anki-running check, and credential prompt.
  - `rebuild` records a `review_state` snapshot beside the backups. `push` refuses unless the
    collection still matches that snapshot.
- **Acceptance.**
  - `--stage pull` downloads only, under the existing refuse-if-upload guard.
  - `--stage push` refuses when Anki is running, when packages are missing, or when the snapshot is
    absent or stale.
  - The existing direction-guard positive controls pass unchanged.
- **Test oracle:** `existing suite` + `new contract tests` (stage dispatch, snapshot guard; each with a
  positive control).

### 1.2: Source-drift tool
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/source_drift.py` (pure)
  - new `anki_tools/source_drift_cli.py` (read-only collection)
  - new `tests/test_source_drift.py`, `tests/test_source_drift_cli.py`
  - a `bin` entry in `libs/python/anki-tools/package.json`
- **Why.** `52478b6` found 13 hand edits by diffing `Translation` by hand. An import with
  `update_notes=always` overwrites every field the user edited on the phone.
- **Pattern.**
  - Build the expected values per GUID with the builders' own parsers:
    `immutable_words_plan.parse_word_list` + `WordRow.fields()`, and `mutable_words_plan.parse_*` +
    `.fields()`.
  - Join against the collection's notes by GUID.
  - Report each row as `guid, note type, headword, field, collection value, source value`.
  - Also report notes with no source row, such as the 5 orphaned Nouns.
  - CLI shape follows `phrase_words_cli.py`, guarded by `assert_unmodified`.
- **Acceptance.**
  - A scratch collection built from the source reports nothing.
  - Flipping one `Translation`, one `English Distinction` and one `Case` reports exactly those three.
    This is the positive control.
  - The tool never writes.
- **Test oracle:** `new contract tests`.

### 1.3: Pull, run the drift tool, adopt the user's edits as source
- **File scope:**
  - `libs/python/anki-tools/tests/data/source-word-list.md`
  - `anki_tools/data/russian-vocabulary/*.tsv`
  - `anki_tools/distinction.py` (`ENGLISH_DISTINCTIONS` values only)
- **Needs the user present** for AnkiWeb credentials. The user must not review on any device until 5.4
  finishes (Risk R1).
- **Steps.**
  1. Run `anki_sync_and_restore.py --stage pull`.
  2. Run the 1.2 tool.
  3. Write each user-made drift value into the source, following the `52478b6` pattern.
     - A row counts as user-made when the collection value differs from every value the source has
       ever produced for that GUID (`git log -p` on the source file).
     - Rows that are not user-made are listed, not adopted.
     - Ambiguous rows go to 2.7.
  4. Snapshot every `Translation` value as the meaning-freeze baseline. It is stored in the run dir
     for 4.3.
- **Acceptance.**
  - Re-running the tool shows only the listed non-user rows.
  - The commit message names every adopted row.
- **Test oracle:** `equivalence check` (post-adoption drift equals the listed non-user rows exactly).

## Phase 2: Reports, audits, and the review gate

### 2.1: Report of English meaning text changed by agent commits
- **File scope:**
  - new `<plan-dir>/gloss-edit-report.md` (D10). Before promotion, it sits as the sibling
    `proposals/anki-card-cues-rework-11-03-26.gloss-edit-report.md` and moves in with the plan.
  - a throwaway enumeration script in the run dir
- **Method.**
  1. For every commit touching `tests/data/source-word-list.md`, the six TSVs, or the gloss-override
     dicts (`ROW_SPLITS`/`TRANSLATION_OVERRIDES` in `immutable_words_plan.py`, `ROW_SPLITS` in
     `mutable_words_plan.py`), diff the English column per headword. Pair renamed headwords by hand:
     keying on the exact headword hid как's lost "how" in `8fd2ab8`.
  2. Classify each change as one of:
     - parenthesis-only;
     - parenthetical text rewritten (listed separately: `(m)`→`(male)`, бронь, many rows of
       `d87b9db`);
     - meaning edit;
     - row added;
     - row split or removed;
     - user hand-edit adopted.
  3. Cross-check against the collection through the 1.3 drift output.
- **Planning-time enumeration** (11-03-26; the builder re-derives it):
  - **61 agent meaning edits:** 58 in the data files, plus 3 in `TRANSLATION_OVERRIDES`. Two
    reorder-only rows are borderline: вид in `a885261`, так (adverb) in `1693389`.
  - **By commit:**
    - `ce413d3`: the 19 adverbs (сложно, грязно, дорого, дёшево, уродливо, холодно, тепло, горячо,
      прохладно, странно, глупо, богато, здорово, больно, весело, грустно, интересно, скучно, смешно),
      plus который `'which / that (relative)' -> 'which / who / that'`.
    - `d87b9db`: 24 verbs `'X (verb)' -> 'to X'`, plus плач, такой, ладно.
    - `4e0bcce`: с / со, по, у, вне.
    - `706590b`: -то, -ка, будто.
    - `e0e53ba`: идти, прощать.
    - `7ceeac1`: правда (noun).
    - `8fd2ab8`: как.
    - `1693389`: всё.
    - `a8ee0cb`: ни. This overwrote the user's own `85e4a42` edit; `52478b6` restored "neither".
    - `7e584f7`: привет.
  - **User adoptions, reported separately:** `4794da4`, `85e4a42`, `52478b6`.
  - **Authorship.** All commits share one author identity, so attribution rests on the commit messages.
    The report says so.
  - **The workbook** is untracked, so it has no history.
- **Acceptance.**
  - Every row reproduces from `git show <commit>:<path>`.
  - Positive control: здорово `'healthily' -> 'great / awesome (colloquial)'` is classed as a meaning
    edit, and a known parenthesis-only change is classed correctly.
  - No data changes.
- **Test oracle:** `equivalence check` (against git history).

### 2.2: Collision analysis
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/collisions.py` (pure)
  - new `tests/test_collisions.py`
- **What it computes.**
  - The gloss-collision index across both families. Senses are split with
    `gloss_separators.normalize_gloss` and the shipped separators.
  - For each collision group, what separates it:
    - (a) the deck header;
    - (b) the case pill: every member governs, and the case sets differ pairwise;
    - (c) a non-case cue, when neither (a) nor (b) does.
  - Every one of the 369 `distinction.ENGLISH_DISTINCTIONS` cues is mapped to the group it serves, or
    marked as serving none.
- **Planning-time probe** (naive split, immutable only):
  - 55 colliding senses across 97 words.
  - Case alone separates about 7 of them.
  - "from" (из/от/с), "near" (около/возле), "through" (через/сквозь) and "according to" (по/согласно)
    each share a single case, so a pill cannot separate them.
- **Acceptance.**
  - A table of groups, members, decks, cases and the separating mechanism.
  - The real-data counts are asserted.
- **Test oracle:** `new contract tests`.

### 2.3: Per-word qualifier classification artifact
- **File scope:** new `libs/python/anki-tools/anki_tools/data/russian-vocabulary/qualifier-classification.tsv`.
- **Rows.** One row per (note, qualifier). A qualifier is any of:
  - a `Translation` parenthetical;
  - an `English Distinction` value;
  - a `Russian Distinction` value;
  - an `Additional Info` value that restates any of those.
- **Columns:** `family, note type, headword (keyed), guid, source field, qualifier text, applies to
  (whole word | sense N of M), action, resulting Translation, resulting English Distinction, resulting
  Additional Info, reason`.
- **Actions.**
  - `move-to-distinction`: a whole-word qualifier.
  - `keep-inline`: a per-sense qualifier. Its duplicate cue is dropped.
  - `drop-duplicate`.
  - `drop-header-duplicate`.
  - `drop-case`: the cue is a case name or a paraphrase of one.
  - `rewrite-cue-non-case`: only where 2.2 says nothing else separates the group. The new cue
    states the sense and never the case.
  - `keep`.
- **The 28 case-bearing cues** (probe 11-03-26) are each rowed. Each loses its case part:
  - 27 in Prepositions or similar: вдоль, возле, вокруг, для, до, за, из, кроме, мало, между, мимо,
    над, насчёт, нравиться, о / об, около, от, перед, по, поверх, позади, ради, с / со, сквозь,
    согласно (preposition), среди, через.
  - бежать `в/на + acc. (destination)`.
  - A cue that is only a case name (до `Genitive`) empties.
  - A mixed cue keeps only its sense part (возле `Genitive; right beside` → `right beside`), and only
    if 2.2 says the group still needs a cue.
- **Screenshot cases.**
  - **ещё.** The per-sense gloss qualifiers stay inline. The cue and the info line drop as duplicates.
  - **до.** The cue drops (`drop-case`), and the pill carries Genitive.
  - **чтобы / чтоб.** The cue repeats the gloss. It is either rewritten to its non-gloss part, or
    dropped, per 2.2.
  - **всё.** "(keeps on)" is per-sense, so it stays inline. The cue drops.
- **Acceptance.**
  - Every cue has a row.
  - Every parenthetical in a collision-group gloss has a row.
  - A script check confirms no "resulting Translation" differs outside parentheses. Its positive
    control row is rejected.
- **Test oracle:** `new contract tests`.

### 2.4: Case-government audit with the meaning-to-case table
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/data/case-government.tsv`
  - new `tests/test_case_government.py`
- **Rows.** One row per note that GOVERNS a case. Columns:
  - `family, note type, headword (keyed), guid, pos`;
  - `cases` (canonical names, comma-separated);
  - `meaning→case` (per gloss line; blank for single-case);
  - `current Case value`;
  - `status` (`ok` | `empty` | `wrong` | `added`);
  - `reference`.
- **Coverage.**
  - **All 234 immutable notes are enumerated.**
    - The 44 prepositions.
    - The non-preposition governors the sources already name: нет "there is no + genitive", мало and
      много "Takes genitive".
    - Candidates to check: немного, сколько, несколько, and the other quantity words.
    - поздравляю's "+ с + instrumental" is governed by с, not by поздравляю (`case_field.py`
      docstring). It gets no row.
  - **All 214 Verbs.** 45 have a `Case / Preposition` value today, and 169 are empty. Transitive verbs
    govern the accusative, so most of the 169 need auditing, not only the 45.
  - **All Derived Adverbs**, e.g. согласно (adverb) "+ dative".
  - The four inflected note types get no rows.
- **Reference, never memory.** Every row cites a source that states the governed case or cases: the
  word's en.wiktionary.org entry, or a printed grammar with its section (e.g. Wade, *A Comprehensive
  Russian Grammar*).
- **Multi-case words.** в/во and на (Accusative, Prepositional), с/со (Genitive, Instrumental; plus
  Accusative "approximately"), за and под (Accusative, Instrumental), and the others the audit finds.
  Each gets a hand-verified `meaning→case` mapping against its gloss lines, and each mapping cites its
  reference.
- **Written before any write.** It is reviewed at 2.7 before any source or collection write.
- **Acceptance.**
  - Coverage: the governing rows plus an explicit "governs no case" list equal the full immutable GUID
    set (`tests/data/immutable_guids.json`) and the full Verbs and Adverbs sets.
  - Every row has a reference.
  - Only canonical case names appear.
  - Every `meaning→case` key matches an actual gloss line.
  - Positive control: deleting one preposition row fails the coverage test.
- **Test oracle:** `new contract tests` (coverage and schema). The cases themselves are checked by the
  human at 2.7 against the cited references.

### 2.5: Case-text routing list
- **File scope:** new `libs/python/anki-tools/anki_tools/data/case-text-routing.tsv`.
- **Rows.** One row per free-text hit of the 4.6 pattern, across all seven note types. Columns: `note
  type, headword, field, current text, destination field (or delete), resulting text, reason`.
- **Hits found at planning time** (the probe pattern is in 4.6; the builder re-runs it):

  **Immutable `Additional Info` (10)**

  | Words | Text | Route |
  |---|---|---|
  | в/во, на, с/со, за, под | "Accusative for motion…; Prepositional for location" etc. | delete; carried by pills + line tint |
  | вопреки | "one of the few Genitive-looking ones that takes Dative" | delete |
  | нет | "Answers "no"; also "there is no" + genitive" | keep the non-case remainder; Case=Genitive |
  | поздравляю | "often + с + instrumental" | remove the case word; keep "often + с (с днём рождения!)" |
  | мало, много | "Takes genitive" | delete; Case=Genitive |

  **Adjectives (2)**

  | Word | Text | Route |
  |---|---|---|
  | похожий | "похож на + accusative" | rephrase without a case name: "похож на + what/whom". Adjectives get no pill (R6). |
  | рад | "+ infinitive or + dative" | rephrase: "рад + infinitive, or + to whom/what" |

  **Adverbs (9)**

  | Words | Text | Route |
  |---|---|---|
  | утром, вечером, ночью, днём, зимой, весной, летом, осенью | "instrumental of …" | moved into the `Formation` grammar field |
  | согласно (adverb) | "+ dative" | delete; Case=Dative |

  **Nouns (13)**

  | Words | Text | Route |
  |---|---|---|
  | год, лес, берег, пол, сад | "(prep. -у́)" | delete the parenthetical; the example form stays |
  | почта, станция, вокзал, работа | "(на + prep.)" | same as the row above |
  | рубль, сторона, раз | "gen. sg." / "gen. pl." | the labels are deleted; the forms already have `Genitive Sg/Pl` fields, which Phase 6 fills |
  | аллергия | "на + accusative" | rephrase: "аллерги́я на + what" (R6) |

  **Numerals (4)**

  | Words | Text | Route |
  |---|---|---|
  | пять | "governs the genitive plural" | delete; `Case Governed` already says it |
  | сорок, девяносто, сто | "nom./acc." vs oblique | the forms move to `Genitive`/`Gender Forms`; the labels are deleted |

  **Pronouns (5)**

  | Words | Text | Route |
  |---|---|---|
  | оно, себя | "nominative" / "oblique" remarks | delete; `Oblique Forms` holds the forms |
  | его, её, их | "Same spelling as the genitive of он…" | the case clause is deleted; "as a possessive it never changes form: …" stays |

  **Verbs `Case / Preposition` (45 non-empty)**
  - The case names move to the new `Case` field.
  - The residue keeps the preposition and construction note, with no case word. For example,
    `+ dative of the person, о + prepositional of the topic` becomes `Case=Dative, Prepositional` with
    residue `… of the person; о … of the topic`.
  - Every residue is listed for review.

  **English Distinction (28)**
  - Routed by 2.3 (`drop-case`), cross-referenced here.
- **Acceptance.**
  - Every 4.6 hit on the pre-change sources has exactly one row.
  - No row's resulting text matches the 4.6 pattern.
  - Positive control: the pattern run over the pre-change sources reproduces the hit count.
- **Test oracle:** `new contract tests`.

### 2.6: Draft the пожаловать row
- **File scope:**
  - a draft row in the run dir. Nothing is committed until 4.3.
- **Pattern.** The superseded plan's 6.1: immutable-class words go to the md source, the rest go to
  the TSVs.
  - пожаловать is the perfective of the verb pair жаловать / пожаловать, used in "добро пожаловать".
  - It is drafted as a `verbs.tsv` row: stress, conjugation, past forms, and gloss. Every form is cited
    against its en.wiktionary.org entry.
  - It is distinct from the existing жаловаться / пожаловаться ("complain", `verbs.tsv` row 145).
- **Acceptance.**
  - The draft row parses with `mutable_words_plan.parse_verbs`.
  - Every form carries the U+0301 stress mark.
- **Test oracle:** `new contract tests` (parse plus format).

### 2.7: User review gate on every artifact before any write
- **File scope:** none; this is a human gate.
- **The orchestrator hands the user:**
  - `qualifier-classification.tsv`;
  - `case-government.tsv`, with its meaning→case table;
  - `case-text-routing.tsv`;
  - `gloss-edit-report.md`;
  - the пожаловать draft;
  - the 6.3 form-fill artifact.
- **Approvals to collect.**
  - Each artifact is approved separately; amendments go into the files.
  - The user's approval also covers the ElevenLabs credits spent at 4.4.
  - Record each approval in the progress log.
- **Test oracle:** `equivalence check` (what 4.3 and 6.4 commit equals what was approved).

## Phase 3: Case pills on the immutable deck

### 3.1: Case field values from the audited case table
- **File scope:**
  - `libs/python/anki-tools/anki_tools/case_field.py`: a reader for `case-government.tsv`, which
    replaces `case_name_for_row`'s Prepositions-only parse of the `Info` cell
  - `anki_tools/immutable_words_plan.py`: `WordRow.fields()` fills `Case` from the reader
  - `tests/test_case_field.py`, `tests/test_immutable_words_plan.py`
- **Pattern.**
  - Lane 3 builds against a fixture TSV with the 2.4 schema. The approved real file is wired in by 4.3.
  - `GOVERNING_SECTION` gating is removed: any listed note gets a `Case`, whatever its section.
- **Acceptance.**
  - Every fixture-listed note gets its comma-joined cases; every other note gets `""`.
  - GUIDs are identical to `immutable_guids.json`.
- **Test oracle:** `new contract tests`.

### 3.2: Pill block, textbook palette, meaning-line tint
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/case_pill.py` (pure): the pill markup, the palette CSS
    (light and `.nightMode`), the tint CSS, and `tint_lines(translation, mapping)`
  - new `tests/test_case_pill.py`
- **Pattern.** As in the settled design. The markup is `{{#Case}}<div class="case-pills"
  data-case="{{text:Case}}">` plus six fixed spans, then `</div>{{/Case}}`. There is no script.
- **Acceptance.** Rendered through the Anki backend (`card.render_output()`, as in
  `test_mutable_words_plan.py:825`):
  - `Case=Accusative, Prepositional` yields a `data-case` attribute with exactly that text.
  - An empty `Case` renders no wrapper.
  - A `Case` value holding HTML renders as plain text in the attribute, which proves `text:`.
  - Pure-CSS check: for every case, the selector `.case-pills[data-case*="<Name>" i] .case-<name>`
    exists and is unique.
  - `tint_lines` wraps each line of в/во's two-line gloss in its case span, and leaves the text
    identical once tags are stripped.
- **Test oracle:** `new contract tests`.

### 3.3: Immutable templates per the card spec
- **File scope:**
  - `libs/python/anki-tools/anki_tools/immutable_words.py` (`clone_note_type`)
  - `anki_tools/prompt_hint.py`
  - `anki_tools/case_field.py`: removing `add_case_row` only; lane 3 already owns this file
  - `tests/test_immutable_words.py`, `tests/test_prompt_hint.py`
  - `tests/test_case_field.py`, for the `add_case_row` tests that 3.3 removes
- **Changes. 3.3 is the sole owner of these deletions:**
  - `PROMPT_CASE_ID`, its `HINT_IDS` entry, and its call;
  - the `unless_field` parameter of `add_prompt_hint` and `hint_div`;
  - `case_field.add_case_row` and its call.
- **Insertions.**
  - The 3.2 pill block, on the Card 2 front and the Card 1 back.
  - `case_pill` CSS is appended to the note type's CSS.
  - `WordRow.fields()` applies `tint_lines` to mapped notes' `Translation`.
- **Pinned `prompt_hint` API.**
  - `add_prompt_hint(template_html, field_name, element_id=PROMPT_HINT_ID,
    anchor_id=TRANSLATION_ANCHOR)` keeps exactly those four parameters, in that order, with those
    defaults.
  - The constants `PROMPT_HINT_ID`, `RUSSIAN_HINT_ID`, `TRANSLATION_ANCHOR` and `RUSSIAN_ANCHOR` stay.
  - Lane 4 (4.1) relies on them.
- **Acceptance.**
  - An `inspect.signature` test pins the API.
  - The table-driven render tests (`test_every_distinction_notetype_cues_the_side_that_needs_it` and
    the related tests) are rewritten to the spec.
  - No side renders `(Genitive)` or a "Case" label.
  - The pills appear exactly once per side where the spec puts them, including through FrontSide.
- **Test oracle:** `new contract tests` (intentional change, settled at the gate).

## Phase 4: Mutable layouts, data apply, checks, deletions

### 4.1: Mutable templates per the card spec
- **File scope:**
  - `libs/python/anki-tools/anki_tools/mutable_words_plan.py`: `FIELD_NAMES` (append `Case` to Verbs
    and Adverbs), the `parse_verbs`/`parse_adverbs` `Case` column, `_detail_fields`,
    `_DETAIL_ID_OVERRIDES`, `_detail_block`, `_build_extra_css`, `build_template`
  - `anki_tools/mutable_words.py`: appends `case_pill` CSS; the appended `Case` field gets id None
  - `anki_tools/data/russian-vocabulary/verbs.tsv` and `adverbs.tsv`: a new empty `Case` column only.
    This is why 4.1 runs after 1.3.
  - `tests/test_mutable_words_plan.py`, `tests/test_mutable_words.py`
- **Changes.**
  1. Exclude both distinction fields and `Case` from the detail rows.
  2. The cues render once: the Russian cue under the headword, the English cue under the gloss on both
     card kinds. They are added with `prompt_hint.add_prompt_hint(..., element_id=...,
     anchor_id=...)` only, the API pinned in 3.3.
  3. Insert `case_pill`'s block on Verbs and Adverbs, per the placement rule (D3). The `after: 3.2`
     edge is real.
  4. Rebuild the details block as the settled centred two-column group:
     - each row wrapped in `{{#Field}}…{{/Field}}`, so empty rows vanish;
     - `addTitle` replaced by static label cells, because the conditional already handles emptiness.
       `_ADD_TITLE_FUNCTION` stays only as long as something still calls it.
  5. Keep `_all_detail_slugs`/`EXTRA_CSS` coverage consistent.
- **Acceptance.**
  - `test_no_duplicate_ids_once_frontside_expands` passes.
  - `test_the_answer_keeps_a_labelled_russian_distinction_row` is replaced by its opposite.
  - The rendered жизнь answer has no element for its empty `Genitive Sg`/`Genitive Pl`.
  - Note-type ids and template ids are unchanged.
- **Test oracle:** `new contract tests`.

### 4.2: Layout render harness dev dependency
- **File scope:**
  - `libs/python/anki-tools/pyproject.toml` (`[dependency-groups] dev`)
  - root `uv.lock`
- **Why this is its own serialized subphase.** It touches the shared manifest and lockfile.
- **Change.** Add `playwright` to the dev group, so 4.7 can measure layout in WebKit, the engine
  AnkiMobile uses. The cached `~/.cache/ms-playwright/webkit-2311` suggests an existing install. 4.2
  pins the version whose bundled WebKit build matches it, or installs WebKit through the package's own
  installer.
- **Acceptance.**
  - `uv run --group dev python -c "from playwright.sync_api import sync_playwright"` succeeds.
  - A WebKit page launches headless.
- **Test oracle:** `existing suite` (full suite green after the lock change).

### 4.3: Apply the approved artifacts to the sources
- **File scope:**
  - `libs/python/anki-tools/tests/data/source-word-list.md`
  - `anki_tools/data/russian-vocabulary/*.tsv`: cue moves, the routing rows, the Verbs and Adverbs
    `Case` values, the `Case / Preposition` residues, and the пожаловать row
  - `anki_tools/distinction.py` (`ENGLISH_DISTINCTIONS` values)
  - `anki_tools/case_field.py`: `residual_info` reduced to what routing leaves
  - the approved `case-government.tsv`, wired in as the reader's real input
  - the approved `qualifier-classification.tsv` and `case-text-routing.tsv`, committed as the audit
    record
  - new `tests/test_qualifier_classification.py`
- **Pattern.**
  - Apply each artifact's "resulting" values.
  - A test asserts the built rows equal those columns. The build reads the sources, and the artifacts
    are only compared against, so there is no second source.
- **Acceptance.**
  - The meaning freeze (Convention 3) passes against the 1.3 baseline for every `Translation` in both
    families. Positive control: a seeded meaning edit fails.
  - Every GUID is unchanged.
  - The `distinction` "no two colliding words share a cue" test is re-derived over the groups 2.2
    marked (c), and holds.
- **Test oracle:** `equivalence check` (built == approved) + `existing suite`.

### 4.4: Generate audio for пожаловать
- **File scope:** the media files that `anki_tools.word_audio` writes, outside the repo.
- **Pattern.** `python3 -m anki_tools.word_audio пожаловать --mode single`, as the superseded plan's
  6.2 specified for a mutable word (slots f1/m2). This spends ElevenLabs credits; the 2.7 approval
  covers it.
- **Acceptance.** Every audio filename the пожаловать row predicts exists and is non-empty.
- **Test oracle:** `existing implementation` (the word_audio tool's own output is the check).
- **Outcome (11-05-26): done differently.** No `ELEVENLABS_API_KEY` in the session, so no audio was generated (lane l14, needs-input). The user runs `.venv/bin/python -m anki_tools.word_audio пожаловать --mode single` themselves in a shell with the key exported. The 4 жаловать/пожаловать audio refs in the built mutable package are unattached until then.

### 4.5: Rendered-card duplicate check
- **File scope:**
  - new `libs/python/anki-tools/tests/test_card_dedup.py`
  - new `anki_tools/card_dedup.py` (pure helper)
- **Definition.**
  1. Render every note of all seven note types, every template, and both sides into a scratch
     collection built from the real sources.
  2. Strip markup.
  3. Split each side into segments: each gloss sense, each parenthetical, each cue, each pill, each
     detail value, the info row.
  4. A side fails if any of these holds:
     - (a) two segments are equal after normalization;
     - (b) every content word of a cue or info segment appears in one other single segment;
     - (c) a case name appears more than once, where the pill and its own Card 2 FrontSide echo count
       once.
- **Exemptions.** Each is explicit and has a reason.
- **Acceptance.**
  - Zero failures.
  - The four screenshot cases (ещё, до, чтобы, всё), rebuilt from the pre-change sources, each fail.
    This is the positive control.
- **Test oracle:** `new contract tests`.

### 4.6: Case checks
- **File scope:** new `libs/python/anki-tools/tests/test_case_ban.py`, new `tests/test_case_coverage.py`.
- **Ban pattern.** Case-insensitive, whole-word, over every free-text field (Convention 4). It matches:
  - the six case names;
  - abbreviations `nom.`, `gen.`, `dat.`, `acc.`, `instr.`, `inst.`, `prep.`, `prepl.`, optionally
    followed by `sg.`/`pl.`;
  - the phrases `takes (the) (direct|indirect) object`, `(direct|indirect) object`, `with the
    <case>`, `in the <word> case`, `governs`, and `takes <case>`.
- **What it catches on today's data** (probe 11-03-26):
  - 28 `English Distinction` cues;
  - 10 immutable `Additional Info` values;
  - 33 mutable `Additional Info` values (adjectives 2, adverbs 9, nouns 13, numerals 4, pronouns 5);
  - the `Case / Preposition` strings.
  - The abbreviation arm alone catches `acc.` (бежать), `prep.` ×9 (nouns), `gen. sg./pl.` (рубль,
    сторона, раз) and `nom./acc.` (сорок, девяносто, сто).
  - The phrase arm catches "governs the genitive plural" (пять). The "takes" arm catches "Takes
    genitive" (мало, много).
  - No "object" phrasing exists today. Its arm gets a seeded positive control.
  - The R6 rephrasings ("+ на + what/whom", "+ to whom/what", "на + what") are asserted to pass the
    ban. English question words are not a case name, an abbreviation, or a listed phrase.
- **Coverage check.**
  - Every note in `case-government.tsv` builds with a non-empty `Case`.
  - No immutable note whose source states a government is missing from the file.
- **Exclusion check.**
  - The Nouns, Adjectives, Pronouns and Numerals note types have no `Case` field.
  - Their templates contain no `case-pills` markup.
- **Acceptance.**
  - Zero hits.
  - Positive controls:
    - the ban run over the pre-change sources reproduces the counts above;
    - a seeded noun with pill markup fails;
    - an emptied preposition `Case` fails.
- **Test oracle:** `new contract tests`.

### 4.7: Centre-line render assertion
- **File scope:** new `libs/python/anki-tools/tests/test_card_layout.py`. It is marked so the suite
  skips it cleanly only when WebKit cannot launch, and the skip is reported.
- **Method.**
  1. For every mutable note type and every answer template, render one note with all fields filled
     and one with most of them empty, through `card.render_output()`.
  2. Load the HTML plus the note type's CSS into a WebKit page at phone width (390px) and at 768px.
  3. Measure `getBoundingClientRect()`.
- **Acceptance.**
  - The details block's horizontal centre equals `#russian`'s centre, within 1px.
  - Within the block, label right edges are equal, and value left edges are equal.
  - No empty field produces an element of non-zero height.
  - Positive control: the pre-change template fails the centre assertion.
- **Test oracle:** `new contract tests`.

### 4.8: Retire the workbook importer
- **File scope:**
  - delete `libs/python/anki-tools/anki_tools/vocabulary_source.py` and `tests/test_vocabulary_source.py`;
  - remove its `bin` entry from `package.json`, and its row in `tests/test_entry_point_bins.py`
    (line 16);
  - `tests/test_mutable_words_e2e.py`: remove the `vocabulary_source` import (line 29) and
    `test_full_pipeline_regenerates_byte_identical_tsvs` (lines 143-157). That test regenerates TSVs
    from the workbook, which is retired;
  - `tests/test_vocabulary_data.py`: its line-190 assertion that the README names
    `vocabulary_source` is replaced by one that the README states the TSVs are the only source;
  - remove `openpyxl` from `pyproject.toml` `[project] dependencies` and from the root `uv.lock`;
  - remove the regeneration section of `anki_tools/data/russian-vocabulary/README.md`, and state there
    that the TSVs are the only source.
- **Why.** D8 retired the workbook. The importer would overwrite the TSVs' edits on its next run.
- **Acceptance.**
  - Dangling-reference sweep: `git grep -n -e vocabulary_source -e openpyxl` exits 1 (no match) over
    code and tests.
  - Positive control: the same command, run before deletion, finds both names.
- **Test oracle:** `existing suite`.

### 4.9: Delete the shared replaced paths
- **Ownership.** 4.9 owns only the symbols that both families reference. The 3.3 symbols are swept
  for here, not deleted here.
- **File scope:**
  - `case_field.py`: delete `CASE_CSS` and `CASE_ID` (the labelled row's CSS). `CASE_FIELD` stays;
    the field stays.
  - `immutable_words.py`: its `case_field.CASE_CSS` concatenation.
  - `mutable_words.py`: its `case_field.CASE_CSS` concatenation at line 82.
  - `mutable_words_plan.py`: `_ADD_TITLE_FUNCTION`, if 4.1 left nothing calling it.
  - their tests (`test_case_field.py`, `test_immutable_words.py`, `test_mutable_words.py`).
  - Docs references are left to Record.
- **Acceptance.**
  - `git grep -n -e prompt-case -e PROMPT_CASE_ID -e unless_field -e add_case_row -e CASE_CSS` exits 1.
    An exit of 128 means the check itself broke.
  - Positive control: the same grep finds each name before deletion.
  - The full suite and ruff are green.
- **Test oracle:** `existing suite`.

## Phase 5: Integration, serialized

### 5.1: Re-pull, rebuild both packages, verify GUIDs, import locally
- **File scope:**
  - none in the repo;
  - writes `~/Desktop/anki-rebuild/*.apkg` (`anki_sync_and_restore.PACKAGES`) and, through the script
    only, the local collection.
- **Steps.**
  1. Run `--stage pull`.
  2. Run the drift tool. New user edits are adopted first, as at 1.3, for those rows only.
  3. Build both packages (`anki-immutable-words --source tests/data/source-word-list.md --audio-dir …`
     and `anki-mutable-words`).
  4. Assert every GUID matches its pin.
  5. Run `--stage rebuild`.
- **Acceptance.**
  - The import reports 0 new, 0 conflicting, and updated equal to the note count.
  - The script's scheduling guard passes.
- **Test oracle:** `existing implementation`.

### 5.2: Regenerate audio for flagged cards
- **File scope:** none in the repo. It writes media through `word_audio --replace`, which archives the
  old files first.
- **Steps.**
  1. Run `python -m anki_tools.flagged_audio_cli` (report mode).
  2. Run it again with `--fix`. The collection is opened read-only, and the flags are left for the user
     (module docstring).
- **Acceptance.** Every flagged word reported has a regenerated file, and its archived predecessor
  exists.
- **Test oracle:** `existing implementation`.
- **Outcome (11-05-26): done differently.** Deferred to the user for the same reason as 4.4 (no `ELEVENLABS_API_KEY`); flagged-audio regeneration was not run.

### 5.3: Verify the live collection
- **File scope:** none.
- **Steps, all read-only against the local collection.**
  1. Run 4.5's duplicate check, 4.6's ban, coverage and exclusion checks, and 4.7's layout check on
     sample notes.
  2. The drift tool shows zero drift.
  3. Compare `review_state` before and after. The only change allowed is the phrase set-due growth the
     script already permits.
  4. The user looks at до, ещё, чтобы, всё and жизнь on desktop Anki before the push.
- **Acceptance.** Every check is clean, and the user says the five cards look right.
- **Test oracle:** `equivalence check`.

### 5.4: Push to AnkiWeb, gated on the user's explicit confirmation
- **File scope:** none.
- **Steps.**
  1. The user explicitly says "push". The push is outward-facing and replaces the server copy.
  2. Run `--stage push`. The snapshot guard refuses if anything was reviewed locally since 5.1.
  3. Run `push_media`.
  4. Run the final `in sync` check.
- **Acceptance.**
  - `mod == ls`.
  - The revlog count is no lower than after 5.1.
  - After a sync on the phone, до shows one red "Genitive" pill and no "(Genitive)".
- **Test oracle:** `existing implementation`.

## Phase 6: Fill the empty mutable form fields

### 6.1: Field census per mutable note type
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/form_census.py` (pure)
  - new `tests/test_form_census.py`
- **Inflection fields per note type** (`mutable_words_plan.FIELD_NAMES`):

  | Note type | Inflection fields |
  |---|---|
  | Nouns | Plural, Genitive Sg, Genitive Pl |
  | Adjectives | Feminine, Neuter, Plural, Short Form, Comparative |
  | Adverbs | Comparative |
  | Pronouns | Gender Forms, Oblique Forms |
  | Numerals | Gender Forms, Genitive |
  | Verbs | Perfective, Conjugation, я (1sg), ты (2sg), они (3pl), Past (m / f) |

  Opposite, Additional Info, Examples and the cue fields are not inflection fields.
- **Planning-time census: empty cells, TSV and live collection** (live collection read read-only, 11-03-26):

  | Note type | Notes | Empty cells |
  |---|---|---|
  | Nouns | 631 TSV rows / 636 notes | Plural 134; Genitive Sg 622 TSV / 627 collection; Genitive Pl 623 / 628. The 5-note gap is the orphaned notes. |
  | Adjectives | 172 | Short Form 158; Comparative 165 |
  | Adverbs | 134 notes | Comparative 40. `adverbs.tsv` shows 22 rows with an empty headword, which the census must explain before counting. |
  | Pronouns | 29 | Gender Forms 11 |
  | Numerals | 55 | Gender Forms 44 |
  | Verbs | 214 | Perfective 4; Conjugation 160; я/ты/они 162 each; Past 177 |

  That is about 2,600 cells.
- **What counts as empty.** The TSVs mark many empty cells with a dash, the way the immutable
  source's `_EMPTY_INFO` does. The census treats `""`, `—`, `–`, `-` and `--` as empty, which is the
  set the planning count used.
  - It asserts that the TSV count and the collection count for a field reconcile under that rule.
  - Positive control: counting only `""` breaks the reconciliation for at least one field. That proves
    the dash rule is load-bearing.
- **Not every empty cell is missing data.** An imperfective-only verb has no Perfective. Most numerals
  have no gender forms. Personal pronouns like я have no gender forms. Many adjectives have no short
  form or synthetic comparative.
- **Classification.** The census classifies each empty cell as `missing` or `not-applicable`, and gives
  the reason.
- **Acceptance.**
  - The TSV census and the collection census agree, except for the listed orphans. This is the positive
    control.
  - The counts are asserted.
- **Test oracle:** `new contract tests`.

### 6.2: Reference spike: stressed-form source, license, coverage
- **File scope:**
  - run dir only: downloaded dumps in their own empty directory, read with `python -I`;
  - findings recorded in the 6.3 artifact header.
- **Candidates.**
  - Wiktionary's Russian inflection tables via the wiktextract dump at kaikki.org. These carry stress
    marks and are CC BY-SA.
  - The OpenRussian.org dataset (github.com/Badestrand/russian-dictionary), with stressed forms in
    CSV.
  - `pymorphy3` (OpenCorpora) gives unstressed forms only, so at most it cross-checks spelling. It is
    not a source.
- **Selection.** Pick the source with the best lemma coverage of the `missing` cells whose stress
  format can be mapped to U+0301.
- **Acceptance.**
  - Coverage per note type and field is reported.
  - Every `missing` cell the chosen source cannot supply is listed for hand-citing.
  - The license is recorded.
- **Test oracle:** `equivalence check`. On the cells that are already filled, the chosen source must
  reproduce the existing value (normalized for stress-mark encoding) at an agreement rate the report
  states. Every disagreement is listed.

### 6.3: Form generator and the reviewable fill artifact
- **File scope:**
  - new `libs/python/anki-tools/anki_tools/form_fill.py` (pure: maps a reference record to each
    field's exact house format)
  - new `tests/test_form_fill.py`
  - new `anki_tools/data/russian-vocabulary/form-fill.tsv`
- **Pattern.** Formats are learned from existing filled rows. Examples: Verbs Past `де́лал / де́лала`;
  Conjugation `1st (-ешь)`; Plural `жи́зни`.
- **Columns:** `note type, headword, guid, field, generated value, reference (source + entry URL), status
  (missing-filled | not-applicable | unresolved)`.
- **The user's hand-edited values are never touched.** A cell is a candidate only if it is empty in
  BOTH the TSV and the collection.
- **Cells the approved artifacts already fill are excluded.** Any cell that a 2.5 routing row or 4.3
  writes is excluded from 6.3, so the generator never competes with an approved hand route. Examples:
  - Numerals `Gender Forms` and `Genitive`, which receive the сорок/девяносто/сто forms;
  - Pronouns `Oblique Forms`;
  - Adverbs `Formation`.
- 6.3 computes the exclusion from the committed `case-text-routing.tsv` and asserts it. Positive
  control: a seeded overlap is rejected.
- **Acceptance.**
  - Run against the already-filled cells, `form_fill` reproduces them exactly. The shipped data is the
    oracle.
  - Every generated value carries U+0301 stress where the house format does, and never on `ё`.
  - No row targets a non-empty cell. Positive control: a seeded non-empty target is rejected.
- **Test oracle:** `existing implementation` (existing filled values are the truth source for the
  generator) + `new contract tests` (format and no-overwrite).

### 6.4: Write the approved fills into the TSVs
- **File scope:** `anki_tools/data/russian-vocabulary/{nouns,adjectives,adverbs,pronouns,numerals,verbs}.tsv`.
  This runs after 4.3, so the TSV writes stay serialized.
- **Change.** Apply the 2.7-approved `form-fill.tsv` rows whose status is `missing-filled`. Commit
  `form-fill.tsv` as the record.
- **Acceptance.**
  - Every applied cell equals its approved value.
  - No previously non-empty cell changed (diff check against the 4.3 state).
  - GUIDs are unchanged.
  - The 4.5 duplicate check and the 4.7 layout check still pass.
- **Test oracle:** `equivalence check`.

## Risks, open questions

**Risks**
- **R1. Phone reviews can be lost.** The appended `Case` field on Verbs and Adverbs is a schema change
  and forces a one-way full sync. Any phone review between the 5.1 pull and the 5.4 push is lost.
  - Mitigation: the user does not study in that window, and 5.1 re-pulls first.
  - The snapshot guard catches local reviews only.
- **R2. An import overwrites field edits.** The drift tool runs at 1.3 and 5.1, and the import waits
  until no unadopted user drift remains.
- **R3. Verb colours can clash.** On Verbs cards the aspect colours (imperfective blue `#1565c0`,
  perfective red `#c62828`, `mutable_words_plan.ASPECT_COLOURS`) equal the textbook Accusative blue
  and Genitive red.
  - Pills are visually distinct (badge shape, text label), and the aspect is a coloured word, not a
    pill.
  - The user sees this at 5.3. If it confuses, shifting the aspect colours is a separate change.
- **R4. The duplicate heuristic can flag legitimate pairs.** 4.5(b) may do this. Every exemption is
  explicit and reviewed; no silent thresholds.
- **R5. Per-sense attribution is a judgement.** Inside "a / b / c (q)" lines it is not mechanical. 2.3
  records each judgement and its reason for the 2.7 review.
- **R6. Settled at the round-2 gate.** Adjectives похожий and рад, and the noun аллергия, are excluded
  types and get no pill. They keep a government note in `Additional Info` phrased without any case
  name (2.5 routing, checked by 4.6), so the construction stays on the card.
- **R7. Phase 6 stays in this run** (user decision). Two consequences:
  - **The 2.7 review is longer.** About 2,600 form-fill cells are reviewed alongside the other
    artifacts. The artifact sorts by note type and field and reports the 6.2 agreement rate, so the
    user can approve a field wholesale or by sample.
  - **The no-study window is longer.** 5.1 cannot start until 6.4 lands, and R1's window runs from the
    5.1 pull to the 5.4 push. The user should plan to keep from studying on any device for that whole
    stretch.

**Assumptions not verified at planning time**
- That `data-case="{{text:Case}}"` with `[data-case*=… i]` renders as specified on AnkiMobile. 3.2
  proves the HTML; 5.3 checks it on the device.
- That a WebKit build usable by Playwright can be installed in the worktree (4.2).
- That the local collection (mtime 11-02 23:38, `mod == ls`) is stale relative to the phone. 1.3 pulls
  either way.

## Lanes

Five lanes, with disjoint file scopes:
- **Lane 1:** `anki_sync_and_restore.py`, the drift tool, and their tests.
- **Lane 2:** the gloss-edit report. It touches no product file.
- **Lane 3:**
  - `case_field.py`, `case_pill.py`, `immutable_words.py`, `immutable_words_plan.py`, `prompt_hint.py`,
    and their tests;
  - it owns the `prompt_hint` API that is pinned in 3.3.
- **Lane 4:**
  - `mutable_words_plan.py`, `mutable_words.py`, and their tests;
  - the `Case` column header added to `verbs.tsv` and `adverbs.tsv` (it runs after 1.3);
  - it reads `prompt_hint` and `case_pill` (`after: 3.2`) but edits neither.
- **Lane 5:** `form_census.py`, `form_fill.py`, their tests, and `form-fill.tsv`. It reads TSVs and the
  collection, and writes no source.

**Serialized subphases.**
- The data writes: 1.3, then 4.3, then 6.4. 4.1 touches only the two TSV headers.
- 4.2: the manifest and lockfile.
- 4.8: the manifest, lockfile, and bin entry. It runs after 4.2.
- The cross-family checks (4.5, 4.6, 4.7).
- The deletions (4.9).
- All of Phase 5.

**Human gates:** 2.7 and 5.4.

## Skill mapping

| Part | Executor |
|---|---|
| 1.1, 1.2, 3.1–3.3, 4.1, 4.5–4.7, 6.1–6.3 | `builder` per lane (coder and contract-tester packets per oracle) |
| 1.3, 4.3, 4.4, 6.4, 5.1–5.3 | builder in the parent worktree, serialized; 1.3, 5.1 and 5.4 need the user present for credentials |
| 2.1–2.6 | `builder` (analysis, audit and report; the oracle is git history, the data, and cited references) |
| 4.2, 4.8, 4.9 | `builder`, serialized integration (manifest/lock and deletions) |
| 2.7, 5.4 | human gates via the orchestrator; 5.4 is never autonomous |
| Gates | `review-plan` → `review-code` → `review-pr`, or the repo's local merge to `main` per its `CLAUDE.md` |
| Docs | `documenter` → `document-local` at Record: `docs/libs/python/anki-tools/README.md` and `mutable-words.md` (case pills, card spec, staged sync, drift tool, form fill, workbook retirement) |
