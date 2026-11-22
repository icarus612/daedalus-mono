# Pronoun case cards, rebuilt in the verb cards' shape

### Ask of record

**11-21-26** — The user's complaints about the shipped pronoun case cards, verbatim as relayed (profanity removed by the relaying orchestrator):

"Why did you put multiple forms on the same line? ... why would I want three different words on one audio, these cards look like shit. I told you to make them look like the verb cards. I literally said make them look like the verb cards. ... the styles look like shit ... You kept all these extra fields and merged all the stuff together on one field. None of the fields are even legible ... a planner should have reviewed this and made it look like the verb cards in terms of style, obviously with different colors and a slightly different format, but the same basic shape."

The user's original ask for the pronoun case cards: "If the rules are not generic, you can just do like you did for perfective/imperfective verb cards."

**11-21-26 — the orchestrator's brief, as handed to the planner (verbatim)** —

> ## What the plan must deliver
> 1. **Research the verb cards first, in the repo AND live.**
>    - Look at the "Mutable Verbs" note type: its fields, templates, CSS, how each form gets its own field and its own audio, and how cards 3/4 (perfective) are laid out.
>    - Live templates may differ from the repo. Read the live note types from a COPY of `~/.local/share/Anki2/User 1/collection.anki2`, never the original.
>    - The plan must state the concrete shape you found, with file/line citations.
> 2. **Redesign the pronoun case content to mirror that shape.**
>    - One form per field.
>    - One audio clip per form, never several words in one clip.
>    - The same layout and structure as the verb cards, in a distinct pronoun color palette and with a slightly adapted format.
>    - Decide how gendered pronouns split: m/n vs f vs pl, and animate/inanimate accusative. Weigh field count against card count and give a recommendation.
>    - Drop the merged fields and any fields that become redundant.
>    - Cover он/она/оно/они н- forms.
>    - Note that the TSV gives "ни о ком"/"ни о чём" for никто/ничто prepositional; the bare forms are ником/ничём.
> 3. **Before→after mockups.** Include, for at least тот, он and я, the front and back of each card type, rendered as text/HTML. The user must approve card text before anything is written.
> 4. **Migration of the live collection.** This is a schema change, so it forces a one-way upload. Cover:
>    - pull from AnkiWeb first, and back up
>    - `pkill -x anki`
>    - keep the existing due dates of the 112 case cards, or map them onto the new cards (one per day, none left new)
>    - audio regeneration with gap-check (`gapcheck.py` logic: silencedetect n=-35dB d=0.15)
>    - media sync
>    - full upload via API
>    - verifying 0 pending
> 5. **Tests to update**, using the counts in `tests/`.
>
> ## Standing rules
> - Never change English glosses.
> - Never overwrite the user's cues.
> - No examples or grammar jargon in cues.
> - Pink flag = female audio bad; blue flag = male audio bad.
> - The pronoun что row must remain.
> - No attribution trailers of any kind (no Co-Authored-By, no Claude-Session, no session URL) in anything.
> - Name the paths you stage; never `git add -A`.


**11-21-26 — appended, at the plan gate, D1 decided by the user (verbatim as relayed)** — "No, one per form. Thats the whole point is to learn each form"

**11-21-26 — appended, at the plan gate, front-layout rule from the user (verbatim as relayed)** — "Put case first, then the other part like feminine masculine plural whatever since all used case case should be the first one that shows and it should just be a little pill and if more is needed do it colored and in parentheses like how perfective/imperfective verbs show"

**11-21-26 — appended, at the plan gate, all pending decisions confirmed by the user (verbatim)** — "cofirmed but also pull down the new stuff" (reply to a list presenting D2–D10 and the labels with the recommended options; "pull down" refers to an AnkiWeb pull, done before review)

## Phase syllabus
- [x] Phase 1: Source data
  - [x] 1.1: Split pronouns.tsv case cells into one-form slot columns            (lane 1)
- [x] Phase 2: Pronoun note-type core
  - [x] 2.1: Slot fields, card-slot order, PronounRow and parser; delete merged-cell code (lane 1, after: 1.1)
  - [x] 2.2: Fixed-case pill block                                               (lane 1)
  - [x] 2.3: Twenty-two per-form case templates and pronoun palette CSS          (lane 1, after: 2.1, 2.2)
  - [x] 2.4: Build wiring in mutable_words.py                                    (lane 1, after: 2.1)
- [x] Phase 3: Dependent tooling
  - [x] 3.1: Retire Oblique Forms from the census, fill and phrase tooling       (lane 2, after: 2.1)
  - [x] 3.2: Per-form audio in the audio and flagged-audio CLIs                  (lane 3, after: 2.1)
- [x] Phase 4: Integration and sign-off
  - [x] 4.1: Cross-lane count updates and a fully green suite                    (after: 2.3, 2.4, 3.1, 3.2)
  - [x] 4.2: Phone-width render preview for the user's visual sign-off           (after: 4.1)
- [x] Phase 5: Live collection migration
  - [x] 5.1: Pre-flight: phone synced, pull, backup, close Anki                  (after: 4.2)
  - [x] 5.2: Generate and gap-check the per-form audio                           (after: 5.1)
  - [x] 5.3: Dry-run the migration and new-card dating on a collection copy      (after: 5.2)
  - [x] 5.4: Apply to the live collection                                        (after: 5.3)
  - [x] 5.5: Full upload, media sync, verify zero pending                        (after: 5.4)
- [x] Phase 6: Record
  - [x] 6.1: Docs, changelog commit, local merge to main                         (after: 5.5)

## Goal & scope

**Goal.** Rebuild the pronoun case cards so that **every form is its own card**. The user decided D1: "one per form ... the whole point is to learn each form". Each card is in the verb cards' shape:
- the front names one pronoun, one case and exactly one slot;
- the back plays and shows that one form, at the verb card's big-word size, with its own audio clip;
- the case's other forms appear as separate coloured counterpart lines, each with its own small play button.

The packed cells ("m./n. того́ · f. той · pl. тех") and the multi-word clips ("того, той, тех") are removed completely.

**In scope**
- `pronouns.tsv`: the five packed case columns become 22 one-form slot columns. The `Oblique Forms` column is dropped (D3, pending confirmation). никто/ничто prepositional become bare forms (D4, pending confirmation).
- `mutable_words_plan.py` / `mutable_words.py`:
  - pronoun fields, row and parser;
  - **22 case templates (one per slot) plus the 2 word templates, 24 in all**;
  - pronoun CSS and build wiring;
  - deleting the merged-cell code (`spoken_case_text`, `_CASE_LABELS`, `#case-prompt`).
- `case_pill.py`: a fixed-case pill block, so the case card front reuses the verb cards' case-pill component.
- Tooling that reads `Oblique Forms`: `form_census.py`, `form_fill.py`, `phrase_words.py`.
- Audio tooling:
  - `mutable_words_audio.py` plans per-form clips;
  - `flagged_audio_cli.py` resolves a flagged case card to that card's one form (D8).
- Live collection:
  - the schema change (fields + 17 new templates);
  - per-form audio with gap-check;
  - the 110 existing case cards keep their ids and dates;
  - **133 new case cards dated one per day after the last existing case date, none left new**;
  - one-way full upload, media sync, verification.
- Tests updated to the new counts (4.1 has the full table).

**Out of scope**
- Any change to Translation, English Distinction, Russian Distinction, Additional Info, Examples, Pronoun Type or Audio values. The migration writes only the 44 case slot fields; 5.3 asserts that.
- Cards 1–2 of the pronoun note type, except that the `Oblique Forms` detail row disappears with the field.
- The verb note type. Its live templates carry a duplicated qualifier `<script>`, which is left alone.
- `Gender Forms`, which stays a packed detail row on cards 1–2 (D3).
- The existing 110 case cards' due dates. They are kept, not re-spread.
- `flagged_audio_cli` regenerating both voices for any flag colour. That is existing behaviour and is not changed here.
- Historical data records that mention `Oblique Forms` in prose: `anki_tools/data/case-text-routing.tsv` rows 98/102, and the `#` comment on line 5 of `form-fill.tsv`.

**Supersedes:** nothing. This reworks the design shipped in commit `67f3256`, which had no plan of record.

**Classification note.** The type is declared `rework`, but card behaviour visibly changes, by the user's own direction, and 133 cards are added. Most subphases therefore use `new contract tests` as their oracle, not the rework default `existing suite`.

## What exists today (research findings)

### Verb card shape — repo (`anki_tools/mutable_words_plan.py` at `67f3256`) and live (identical apart from one duplicated script)

Live was read from a copy of `collection.anki2` taken on 11-21-26 into the session scratchpad. `build_template()` + `word_qualifier.add_qualifier_script` output was diffed against the live `qfmt`/`afmt` of all 4 verb templates. They match byte for byte, except that the side holding `#russian` carries the qualifier `<script>` twice in live. The live verb CSS (6 756 chars) has been patched cumulatively and does not contain the current `EXTRA_CSS` verbatim. The rules below were read from the live copy.

- **Fields: one form per field, one audio field per form.** `FIELD_NAMES["Verbs"]` (lines 85–104) has `Imperfective` and `Perfective`, and separately `Audio Imperfective` and `Audio Perfective`. `VerbRow.fields()` (lines 303–325) fills each audio field with `audio_field_value(audio_names(word))`: one `<audio src="<word>_f1.mp3">` plus `…_m2.mp3`, and the card picks one voice per render.
- **Two templates per form, each conditional on its form.** `_VERB_CARD_CONFIGS` (lines 804–829) makes cards 1/2 Imperfective and cards 3/4 Perfective. Cards 3/4 are wrapped in `{{#Perfective}}…{{/Perfective}}` (line 1201), so a verb without a perfective makes no cards 3/4. That is the precedent for "a template per form, conditional on its field".
- **Audio-side card (1 and 3)** (lines 1186–1191).
  - Front: `#path`, `#deck`, the big autoplaying audio button (`card_audio.audio_block`, voice kept across sides by a state key), then the `cue-row` with `#russian` (2.2rem) and `#russian-distinction`.
  - Back: translation `cue-row` with the coloured aspect tag, case pills, the counterpart line, `#details`, `#additional-info`, `#examples`.
- **Text-side card (2 and 4)** (lines 1192–1199).
  - Front: translation `cue-row` with its coloured aspect tag, and case pills.
  - Back: **the big audio button, then `#russian` at 2.2rem** with its cue, then the counterpart line, details, info and examples.
- **The counterpart line** (lines 1162–1176). A `div#perfective` (or `#imperfective`) with `class="tappable" onclick="__mutableVerbAspectPlay(event)"`, holding:
  - `card_audio.audio_line_block`, a small ▶ that never autoplays (`card_audio.py:173`);
  - `div#perfective-word`, which `addTitle` turns into a coloured `.title` + `.body`.

  Live CSS makes it a centred flex row with `gap: .4rem` and 1.2rem text. Colours come from `ASPECT_COLOURS` (line 975): `#1565c0` / `#c62828`. There are no night variants.
- **Case pills** (`case_pill.py:39`). `pill_block()` emits six pills in `div.case-pills[data-case="{{text:Case}}"]`, and CSS shows only the named one. Palette (`case_pill.py:25–30`): Gen `#c62828`, Dat `#2e7d32`, Acc `#1565c0`, Ins `#9a6700`, Prep `#6a1b9a`, with `.nightMode` variants. They are **absent** from the live pronoun CSS, because `mutable_words.py:89–90` adds them only to sheets with a `Case` field.

### Pronoun case cards as shipped (`67f3256`)

- `PRONOUN_CASES` (line 48) has 5 cases. `FIELD_NAMES["Pronouns"]` (line 139) appends `Genitive…Prepositional` + `Audio Genitive…Audio Prepositional`.
  - Each cell packs several forms.
  - Each audio field holds one clip of all of them joined (`spoken_case_text`, line 494), e.g. `того-той-тех_f1.mp3`.
- `_pronoun_case_template` (line 1211) builds cards 3–7, one per case. Front: `#russian` + grey `#case-prompt`. Back: audio + the packed cell at 2rem + the translation.
- `Oblique Forms` still shows as a detail row on cards 1–2.

### Live collection state (copy read 11-21-26, `col.sched.today` = 1908)

- 30 pronoun notes. Cards per ord: 0 → 30, 1 → 30, 2–6 → 22 each. That is **110 case cards, not the 112 the brief states**.
  - All 170 pronoun cards are `type=2 queue=2`.
  - The 110 case cards have `ivl=0` and `due` 1909…2019, **one per day**, all on different days.
  - Their only revlog rows are 110 type-4 (manual reschedule) entries.
  - None is flagged. `usn=-1` = 0.
- **Live precedent for conditional templates generating cards.** The previous session added templates 3–7 (conditional on `{{#<Case>}}`) to this live note type. Anki 26.8.1 generated exactly 22 cards per template, one per note whose field was filled, and none for the 8 non-declining notes. Those new cards arrived as `queue=0` and were then dated (scratchpad `pron_apply.py` step 5). Adding 17 more templates conditional on their slot fields works the same way.
- The live templates' `qfmt`/`afmt` for ords 2–6 equal the repo output. Ords 0–1 differ only by the duplicated qualifier script.
- `что (pronoun)` (row 30) is present with its 5 case cards.
- Media: of the 147 distinct one-word forms needed, **54 already exist** for both voices and **93 must be generated** (186 ElevenLabs requests). The 54 hyphenated multi-word clips (108 files) become orphans.

### The previous session's ad-hoc scripts

These exist only in the session scratchpad and are not committed: `pron_apply.py`, `pushup.py`, `gapcheck.py`. They are the pattern to follow. The logic this plan needs from them is restated below, so the plan doesn't depend on them surviving.

## The shape: one card per form (D1 = B, decided)

### What makes a card

**One card per filled case+slot cell.** That gives 243 case cards, listed in full in Appendix A.

| Pronoun group | Members | Filled cells per pronoun | Case cards |
|---|---|---|---|
| One form per case | я ты вы мы кто ничто себя никто что (pronoun) | 5 (one per case) | 9 × 5 = **45** |
| н- forms | он она оно они | 5 plain + 4 after a preposition | 4 × 9 = **36** |
| Gendered | сам тот этот мой твой наш ваш свой весь | 3+3+6+3+3 | 9 × 18 = **162** |
| | | | **243** (110 existing + **133 new**) |

A pronoun with one form per case keeps exactly its five existing cards, one per case, unlabelled. Nothing new is created for those 9 pronouns.

**Repeated spellings (a fact, not a question).** 87 of the 243 cells spell a form that another case card of the same pronoun also asks for. Examples:
- тот: той ×4 (f. Gen/Dat/Ins/Prep), тех ×3, тем ×2, того ×2;
- оно's 9 cards are identical in spelling to он's.

Each card still asks a distinct case+slot question, so one card per cell stands.

### Slot fields (unchanged from the previous revision)

| Case | Slots, in field order |
|---|---|
| Genitive | `Genitive` · `Genitive f.` · `Genitive pl.` · `Genitive (н-)` |
| Dative | `Dative` · `Dative f.` · `Dative pl.` · `Dative (н-)` |
| Accusative | `Accusative` · `Accusative m. living` · `Accusative n.` · `Accusative f.` · `Accusative pl.` · `Accusative pl. living` · `Accusative (н-)` |
| Instrumental | `Instrumental` · `Instrumental f.` · `Instrumental pl.` · `Instrumental (н-)` |
| Prepositional | `Prepositional` · `Prepositional f.` · `Prepositional pl.` |

That is 22 form fields, each paired with `Audio <slot>` in the same order: 44 slot fields in all, and the pronoun note type has 55 fields in total.

The **primary** slot (named after the case) holds:
- the m./n. form for gendered pronouns, or m. not-living for Accusative;
- the only form for the one-form pronouns;
- the form without a preposition for он/она/оно/они. Their н- forms go in `(н-)`. Prepositional нём/ней/них has only one form, so it sits in the primary slot.

### Templates, ords and card ids

- Each slot is one Anki card type, so the note type gets **24 templates**: ords 0–1 are the word cards, and ords 2–23 are the 22 case templates.
- Every case template is wrapped in its slot field's conditional (`{{#Genitive f.}}…{{/Genitive f.}}`), exactly as verb cards 3/4 are wrapped in `{{#Perfective}}`. A template whose slot is empty for a note renders an empty front, so Anki makes no card. The live precedent above confirms this works on this note type with Anki 26.8.1.
- **Ord mapping keeps every existing card.**
  - Ords 2–6 stay `Genitive, Dative, Accusative, Instrumental, Prepositional`. These are the primary-slot templates, still conditional on the same five fields, so the 110 existing case cards keep their ids, ords and due dates.
  - The 17 new templates are **appended at ords 7–23** in slot field order:
    - 7–9: `Genitive f.`, `Genitive pl.`, `Genitive (н-)`;
    - 10–12: `Dative f.`, `Dative pl.`, `Dative (н-)`;
    - 13–18: `Accusative m. living`, `Accusative n.`, `Accusative f.`, `Accusative pl.`, `Accusative pl. living`, `Accusative (н-)`;
    - 19–21: `Instrumental f.`, `Instrumental pl.`, `Instrumental (н-)`;
    - 22–23: `Prepositional f.`, `Prepositional pl.`.

  Existing templates are never repositioned, so no ord remap is involved. The repo's `build_template("Pronouns", i)` follows the same order, through one ordered table `PRONOUN_CARD_SLOTS` (the 5 primaries, then the 17 others).

### Card direction: one card per form, text side only

- Verbs have two cards per form (audio side, text side). Doubling would make 486 case cards and would mostly re-drill the headword's sound.
- **Recommendation: each form gets one card, mirroring the verb text-side card (2 and 4).**
  - The prompt (headword, case, slot) is on the front, with no audio.
  - The back has **the big autoplaying audio button with the form at 2.2rem** (`#case-form`, same size as `#russian`).
  - The front also has no audio because the headword clip is drilled by cards 1–2, and a second `audio_block` would collide with the answer's own on the back.

### Back of a case card: the case's other forms as counterpart lines

**Recommendation: yes.** After the asked form, the back lists the **other filled slots of the same case**, each on its own line built exactly like the verb counterpart line: coloured title, small ▶ playing that slot's own clip, a tappable row, never autoplaying. The asked slot itself is not repeated.

- This mirrors the verb text-side back, which shows the counterpart aspect after the answer.
- The user sees the whole case, one form per line with one clip each, only after answering.
- One-form pronouns (я, кто…) and он's Prepositional have no lines.
- Alternative (D5): show only the asked form, then the gloss and ⓘ.

### Front: the case pill first, then the slot qualifier in coloured parentheses (the user's rule)

Under the headword, the front has **one line**:
1. **The case comes first, as the small existing case pill**, in the case-pill colours (Gen red, Dat green, Acc blue, Ins amber, Prep purple). Nothing comes before it on that line.
2. **After it, on the same line, the slot qualifier**, only where the card needs one. It is coloured text in parentheses, e.g. `(feminine)`, rendered exactly like the verb aspect tag `(imperfective)` from `_translation_div` (`mutable_words_plan.py:1092–1106`): a `<span class="aspect …">` using the existing `.aspect` rule (0.85em, `white-space: nowrap`), plus a palette colour class. It is not a second pill and not a separate title line.
3. **Single-form cells** (all of я ты вы мы кто ничто себя никто что, and он/она/оно/они Prepositional) show **only the pill**.

The headword `cue-row` stays above the line. Reading "case first" as "first on the pill line, ahead of the qualifier", with the headword still the card's main word, is an interpretation. The mockups show it so the user can confirm.

The qualifier appears only when the pronoun has more than one form in that case:

| Slot | Qualifier on the front (the same words, without parentheses, title that slot's counterpart line on other cards) | Colour (D2) |
|---|---|---|
| primary, gendered, not Accusative | (masculine / neuter) | teal `#00796b` |
| `Accusative`, gendered | (masculine, not living) | teal |
| `Accusative m. living` | (masculine, living) | teal |
| `Accusative n.` | (neuter) | teal |
| `… f.` | (feminine) | magenta `#ad1457` |
| `… pl.` (Gen/Dat/Ins/Prep) | (plural) | brown `#6d4c41` |
| `Accusative pl.` | (plural, not living) | brown |
| `Accusative pl. living` | (plural, living) | brown |
| `… (н-)` | (after a preposition) | accent `#605C8B` |
| primary of он/она/оно/они, where `(н-)` exists | (without a preposition) | grey `#656565` |

Night tints (`.nightMode`): teal `#4db6ac`, magenta `#f48fb1`, brown `#bcaaa4`, accent `#b3aee0`, grey `#9e9e9e`.

The primary template's qualifier is field-driven. For example, the Genitive template renders `{{#Genitive f.}} <span class="aspect form-mn">(masculine / neuter)</span>{{/Genitive f.}}{{#Genitive (н-)}} <span class="aspect form-plain-prep">(without a preposition)</span>{{/Genitive (н-)}}`. One template therefore serves all three pronoun groups and shows only the pill for single-form pronouns.

The palette, the labels ("living", "after a preposition", and the two new ones this revision adds, "not living" and "without a preposition"), the Oblique Forms removal and the нико́м/ничём forms are all **still pending the user's confirmation** (D2, D3, D4, labels).

### Dating the 133 new cards

- **Rule (from the brief):** one new card per day, none left new, continuing after the last existing case-card date. At the 11-21-26 copy the last existing date is due 2019, so the new cards take due 2020 … 2152 (day offsets 112 … 244 from today 1908). 5.3 recomputes from the 5.1 snapshot and never hardcodes these numbers.
- **Recommended order: grouped by pronoun.** Pronouns go in the same order the existing case cards were dated (rank order, with что after кто). Within a pronoun, cards follow case order and then slot field order.
  - Only the 13 pronouns with non-primary slots get new cards: он она оно они (4 each), then сам тот этот мой твой наш ваш свой весь (13 each).
  - Each pronoun's remaining paradigm therefore arrives on consecutive days and reads as one table being completed.
- The alternative, interleaving round-robin across pronouns, spreads one pronoun's forms out but scatters each paradigm over months. Not recommended.
- **Tool route.** `anki-rebalance-due` skips new cards (project memory, 11-11-26), and these dates come straight from the user's instruction (none new, one per day). So the apply script dates them with `col.sched.set_due_date([cid], str(offset))`, the same call the previous pronoun dating used, and moves no existing card.
- **Counterpart check.** After dating, `anki-counterpart-due "Languages::Russian"` (report mode) must show 0 for the pronoun deck. This is the standing post-change check (project memory, 11-06-26).

## Before → after mockups (for approval before anything is written)

In the text renders below, `( ▶ )` is the big audio button and `(▶)` is the small counterpart-line button. Colours are given in brackets. Every card starts with the header `Languages > Russian > 4. Mutable Words > d. Pronouns` / `Russian - Pronouns`, shown here once. The back repeats the front above it, as all cards do.

### тот · Genitive · feminine (new card, ord 7)

**Before:** no such card. Its form only appeared inside the packed Genitive card ("m./n. того́ · f. той · pl. тех", one clip "того, той, тех").

**After**
```
FRONT                                   BACK
               тот                                   ( ▶ )     ← clip: той
   [Genitive] (feminine)                              той       [2.2rem]
   red pill   magenta                    masculine / neuter  (▶) того́   [teal]
                                                    plural  (▶) тех    [brown]
                                    that (one) / that (over there) (pointing at something farther)
                                    ⓘ marks distance/contrast, opposed to этот; oblique cases are
                                      END-stressed (того́), unlike этот's stem-stressed этого
```

### тот · Accusative · masculine, living (new card, ord 13)

**Before:** no such card. Part of "m. тот, living того́ · n. то · f. ту · pl. те, living тех", with one six-word clip.

**After**
```
FRONT                                   BACK
               тот                                   ( ▶ )     ← clip: того
   [Accusative] (masculine, living)                   того́      [2.2rem]
   blue pill    teal                    masculine, not living  (▶) тот   [teal]
                                                     neuter  (▶) то    [teal]
                                                   feminine  (▶) ту    [magenta]
                                         plural, not living  (▶) те    [brown]
                                             plural, living  (▶) тех   [brown]
                                    that (one) / that (over there) (pointing at something farther)
                                    ⓘ (Additional Info, unchanged)
```

### он · Genitive · after a preposition (new card, ord 9)

**Before:** no such card. Part of "его́ / него́", with one clip "его, него".

**After**
```
FRONT                                   BACK
               он                                    ( ▶ )     ← clip: него
   [Genitive] (after a preposition)                   него́      [2.2rem]
   red pill   #605C8B                    without a preposition  (▶) его́   [grey]
                                    he / it (masculine)
                                    ⓘ the н- prefix appears after any preposition (у него́, к нему́)
```

The matching primary card (existing, ord 2) has the front `он` / `[Genitive] (without a preposition)`, with the qualifier in grey. Its back is `его́`, with the line `after a preposition (▶) него́`.

### я · Genitive (existing card, ord 2: same card id and date, new layout)

**Before**
```
FRONT              BACK
      я                 ( ▶ )  ← clip: меня
   Genitive  [grey]     меня́   [2rem]
                        I
```
**After**
```
FRONT                                   BACK
               я                                     ( ▶ )     ← clip: меня
          [Genitive]                                  меня́      [2.2rem, no qualifier, no lines]
          red pill only (one form)   I
                                    ⓘ fully suppletive oblique stem (мен-/мн-)
```

я's other four cases look the same: мне, меня́, мной, мне. It has no new cards.

### тот · Genitive · masculine / neuter (existing card, ord 2: same id and date, new layout)

The front is `тот` / `[Genitive] (masculine / neuter)`, with the qualifier in teal. The back is `( ▶ )` with the clip того, `того́` at 2.2rem, then the lines `feminine (▶) той` [magenta] and `plural (▶) тех` [brown], then the gloss and ⓘ.

### Cards 1–2 (word cards) for тот, он, я: the only change is the Oblique Forms row (D3)

| Pronoun | Card 1 / card 2 back details, before | After |
|---|---|---|
| тот | Gender Forms: тот / та / то / те (m/f/n/pl) · **Oblique Forms: того́ (G/A m./n.), той (G/D/I/P f.), тех (G/P pl.)** | Gender Forms row only |
| он | Pronoun Type: personal (3rd sg.) · Gender Forms: он / она́ / оно́ / они́ (m/f/n/pl) · **Oblique Forms: его́/него́ (G/A), ему́/нему́ (D), им/ним (I), о нём (P)** | Pronoun Type + Gender Forms rows |
| я | Pronoun Type: personal (1st sg.) · **Oblique Forms: меня́ (G/A), мне (D/P), мной/мно́ю (I)** | Pronoun Type row only |

The card 1–2 fronts are unchanged.

### Template HTML (the `Genitive f.` template, ord 7; scripts elided)

```html
{{#Genitive f.}}<div id="front">
<div id="path"></div>
<div id="deck">{{Deck}}</div>
<div class="cue-row"><span id="russian">{{Russian}}</span>
<span id="russian-distinction">{{#Russian Distinction}}({{Russian Distinction}}){{/Russian Distinction}}</span></div>
<div class="case-pills" data-case="Genitive"><span class="case-pill case-nominative">Nominative</span>…six pills… <span class="aspect form-f">(feminine)</span></div>
</div><script>/* deck header */</script>{{/Genitive f.}}
```
```html
{{FrontSide}}
<div id="back">
<div id="audio"><span id="audio-data" class="hidden">{{Audio Genitive f.}}</span><span id="audio-controls"></span></div><script>/* audio_block */</script>
<div class="cue-row"><span id="case-form">{{Genitive f.}}</span></div>
{{#Genitive}}<div id="form-genitive" class="form-line form-mn tappable" onclick="__pronounFormPlay_genitive(event)">
<span id="form-genitive-audio">…{{Audio Genitive}}…</span><script>/* audio_line_block */</script>
<div id="form-genitive-word">{{Genitive}}</div></div>{{/Genitive}}
{{#Genitive pl.}}…same shape, form-pl…{{/Genitive pl.}}
{{#Genitive (н-)}}…same shape, form-after-prep…{{/Genitive (н-)}}
<div class="cue-row"><span id="translation">{{Translation}}</span>
<span id="prompt-hint">{{#English Distinction}}({{English Distinction}}){{/English Distinction}}</span></div>
<div id="additional-info">{{Additional Info}}</div>
</div>
<script>/* addTitle: each line's word gets its slot label as title; additional-info "&#9432;" */</script>
```

- A primary template's line for the primary slot is omitted, and its own label is the field-driven one shown in the label table.
- The line titles reuse the front labels.
- Ids and JS function names are ASCII and unique per slot: keys `mn`, `m-living`, `neut`, `f`, `pl`, `pl-living`, `after-prep`.

## Stack & MAJOR versions

- Python `>=3.11` (`libs/python/anki-tools/pyproject.toml` `requires-python`). uv workspace (`[tool.uv]`; `uv.lock` at the repo root).
- `anki` **26.8.1** (`/home/icarus64/repos/daedalus-mono/uv.lock`). Used via `Collection`, `col.models.*` (`add_field`, `remove_field`, `reposition_field`, `new_template`, `add_template`, `update_dict`), `col.sched.set_due_date`, `col.sync_collection`, `col.full_upload_or_download`, `anki.sync_pb2.SyncAuth`, matching patterns already in the repo and the previous scripts.
- `pytest`, and `playwright==1.61.0` (headless WebKit) in the dev group.
- `requests>=2.28.0` (ElevenLabs via `elevenlabs_tts`).
- External: `ffmpeg` (silencedetect), Anki desktop (`anki_sync.sync`).
- Package scripts: `pnpm run test` → `py-test`, `pnpm run lint` → `py-lint` (`libs/python/anki-tools/package.json`).

## Conventions to enforce (hard constraints)

- **Card text is frozen except the case slots.** Never change Translation (English glosses), English Distinction or Russian Distinction (cues), Additional Info, Examples, Pronoun Type or Audio. 5.3 and 5.4 check every non-slot field of all 30 notes byte for byte.
- **No cue edits of any kind.** No examples and no grammar jargon in cues. Slot labels are template text, not cue fields.
- **The `что (pronoun)` row and its 5 case cards remain** (GUID `gJ6S@(5[xc`).
- **Card text is approved first.** The mockups are approved at the plan gate and the rendered preview at 4.2, before any live write.
- **Pink flag = female audio bad, blue flag = male audio bad.** Re-rolls go through `anki-flagged-audio --fix` / `anki-word-audio --replace`, never `elevenlabs_tts` plus hand copying.
- **Audio filenames come from the stress-stripped form.** Strip U+0301 before `build_filename`; otherwise `э́того` would slug to `э-того` (`audio_naming.py:76–99`).
- **Gap-check every clip a slot references.** Use ffmpeg `silencedetect=n=-35dB:d=0.15`. A take is broken when a silence starts at `t > 0.03` s with more than `0.12` s of audio after it. A one-word clip may have zero such gaps. Validate the checker against a known-bad take first.
- **Existing cards are untouched.** The 170 existing pronoun cards keep id, ord, type, queue, due and ivl. Only the 133 new cards are dated, one per day, none left new.
- **Sync discipline.**
  - Get the user's confirmation that the phone has synced before the schema change.
  - Pull, then back up, then `pkill -x anki`.
  - Do the full upload through the API (`SyncAuth` from `prefs21.db`), and media through `anki_sync.sync(names)`.
  - Done means pending = 0, read from a fresh copy. Never hand the one-way dialog to the user.
- **Delete the old path.** No `spoken_case_text`, `_CASE_LABELS`, `#case-prompt` or old `PRONOUN_CASE_CSS` content survives. No shims, no versioned names. Orphaned multi-word clips are trashed.
- **Minimal code comments** (`~/.claude/rules/minimal-code-comments.md`). `check-diff-hygiene.sh` runs at builder teardown.
- **Lint and format green** (`py-lint`, ruff via `ruff.toml`). The smart-lint hook fires repo-wide, so route bulk edits through Bash and restore any collateral it touches. Pre-existing lint debt elsewhere is out of scope.
- **Lanes never run git state commands** (`git checkout`, `git restore`, `git stash`, `git reset`) in the shared worktree.
- **Git.**
  - Name staged paths explicitly; never `git add -A`.
  - No attribution trailers of any kind (no `Co-Authored-By`, no `Claude-Session`, no session URL).
  - Work lands by local ff-merge of `bug/mol-deskat` into `main`, then pushing `main` after the user confirms. No PR (`/home/icarus64/repos/daedalus-mono/CLAUDE.md`).
- **Pure modules stay Anki-free** (`mutable_words_plan.py`, `case_pill.py`, `phrase_words.py`). Reuse the existing components: `card_audio.audio_block`, `card_audio.audio_line_block`, `case_pill`, `prompt_hint`, `_ADD_TITLE_FUNCTION`.

## Phase 1: Source data

### 1.1: Split pronouns.tsv case cells into one-form slot columns
- **File scope:** `libs/python/anki-tools/anki_tools/data/russian-vocabulary/pronouns.tsv`, `libs/python/anki-tools/tests/test_vocabulary_data.py`.
- **Change.**
  - The header becomes `#, Russian, English, Stress, Pronoun Type, Gender Forms, Additional Info, Examples, <22 slot columns in field order>, Status`. `Oblique Forms` is removed (D3).
  - Each packed cell is split into its slots exactly as in Appendix A, with stress marks preserved.
  - никто Prepositional becomes `нико́м` and ничто Prepositional becomes `ничём` (D4).
  - Every other column stays byte-identical, and so does every non-declining row.
- **Pattern to follow:** the previous TSV rewrite: `csv.DictReader`/`DictWriter`, tab delimiter, `lineterminator="\n"`, row order preserved.
- **Acceptance:**
  - New `EXPECTED_HEADERS["pronouns.tsv"]` (31 columns).
  - 31 lines. `("pronouns.tsv","Gender Forms"): 12` is unchanged.
  - No slot cell contains ` · `, ` / `, `, `, `living ` or `ни о`.
  - Exactly 243 non-empty slot cells.
  - The English and Additional Info columns diff empty against `67f3256`.
- **Test oracle:** `new contract tests`.
  - Assert one form per cell and the 243 count.
  - Spot-check тот: `Genitive f.`=той, `Accusative m. living`=того́, `Accusative n.`=то.
  - Spot-check он: `Genitive`=его́, `Genitive (н-)`=него́, `Prepositional`=нём.
  - Spot-check я: `Genitive`=меня́.
  - Check the bare нико́м/ничём.

## Phase 2: Pronoun note-type core

### 2.1: Slot fields, card-slot order, PronounRow and parser; delete merged-cell code
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py`, `libs/python/anki-tools/tests/test_mutable_words_plan.py`, `libs/python/anki-tools/tests/test_mutable_words.py` (`_write_pronouns_tsv` and the pronoun field assertions near lines 405–455).
- **Change.**
  - Keep `PRONOUN_CASES` (5).
  - Add one ordered slot table giving each slot's field name, case, front label and palette role. Derive from it:
    - `PRONOUN_FORM_FIELDS` (22, field order);
    - `PRONOUN_FORM_AUDIO_FIELDS` (22);
    - `PRONOUN_CARD_SLOTS` (22, card order: the 5 primaries, then the other 17 in field order).

    These replace `PRONOUN_CASE_AUDIO_FIELDS`.
  - `FIELD_NAMES["Pronouns"]` = the 11 base fields (without `Oblique Forms`), then the 22 form fields, then the 22 audio fields.
  - `PronounRow`:
    - drop `oblique_forms`;
    - `case_forms` becomes a 22-tuple in field order;
    - `fields()` emits each form and, for each filled slot, `audio_field_value(audio_names(bare_form(form)))`, or `""` for an empty one;
    - add an `audio_words` property for 3.2: `base_words` plus each distinct stress-stripped slot form (`bare_form`) that is not equal to `audio_naming.strip_qualifier(self.russian)`, in field order. The comparison must use the qualifier-stripped headword: `что (pronoun)` matches its Accusative `что` only after `strip_qualifier`, and a literal comparison gives 145 extra words instead of 144. That would break the 1603 / 3206 / 3180 targets.
  - `parse_pronouns` reads the 22 columns.
  - Add a `bare_form` helper that strips U+0301 only.
  - **Delete** `spoken_case_text` and `_CASE_LABELS` (lines 491–505), and the `re` import if nothing else uses it.
  - `_detail_fields` excludes all 44 slot fields.
- **Pattern to follow:** `VerbRow.fields()` (lines 303–325), `FIELD_NAMES["Verbs"]`.
- **Acceptance:**
  - `len(FIELD_NAMES["Pronouns"]) == 55`, aligned with `row.fields()` for every row.
  - `PRONOUN_CARD_SLOTS[:5] == PRONOUN_CASES`.
  - тот `Audio Genitive f.` references `той_{f1,m2}.mp3`.
  - этот `Audio Genitive` references `этого_*.mp3`, never `э-того`.
  - No hyphenated multi-word audio name appears.
  - A grep for `spoken_case_text|_CASE_LABELS|PRONOUN_CASE_AUDIO_FIELDS` over `anki_tools/` and `tests/` returns nothing, with a positive control at `67f3256` that does hit.
  - The derivation (`test_mutable_words_plan.py:150–183`) yields **303** pronoun cards and **3161** in total. It already sums the filled `case_forms`, now 22 slots, which gives 243.
  - `test_field_name_legality` (line 197) asserts the new 44-name tail.
- **Test oracle:** `new contract tests` for the slot table, card order, alignment and audio names; `existing suite` for the updated derivation.

### 2.2: Fixed-case pill block
- **File scope:** `libs/python/anki-tools/anki_tools/case_pill.py`, `libs/python/anki-tools/tests/test_case_pill.py`.
- **Change.** `pill_block()` (line 39) takes an optional fixed case and an optional trailing HTML fragment. Given a case, it emits the six pills with a literal `data-case="<Case>"` and no `{{#Case}}` wrapper, then the fragment inside the same `.case-pills` div, after the pills. The fragment is the slot qualifier, so the pill comes first and the coloured `(qualifier)` sits beside it on one line. The no-argument output stays byte-identical.
- **Pattern to follow:** `pill_block()`. The `data-case*="<name>" i` CSS (lines 85–95) already lights a literal value.
- **Acceptance:**
  - The no-argument output equals `67f3256`.
  - A fixed call contains `data-case="Genitive"` and all six spans, with no `{{#Case}}`. A given fragment appears after the last pill span, inside the wrapper.
  - It raises on a name outside `CASE_ORDER`.
- **Test oracle:** `new contract tests`.

### 2.3: Twenty-two per-form case templates and pronoun palette CSS
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py`, `libs/python/anki-tools/tests/test_card_layout.py`, `libs/python/anki-tools/tests/test_card_dedup.py`.
- **Change.**
  - `build_template("Pronouns", i)` for `i` in `2..23` returns the case template of `PRONOUN_CARD_SLOTS[i-2]`. `_pronoun_case_template` is rewritten to take a slot and produce the layout in "Template HTML":
    - **front:** header, headword `cue-row` via `_add_russian_cue`, the fixed-case pill block carrying, after the pills on the same line, the qualifier `<span class="aspect form-<role>">(<qualifier>)</span>` (field-driven for primaries, absent for single-form cells), all wrapped in `{{#<slot>}}`;
    - **back:** `card_audio.audio_block(f"Audio {slot}", "audio", PRONOUN_CASE_STATE_KEY)`, then the `#case-form` `cue-row`, then one `card_audio.audio_line_block` line per **other** slot of the same case (each in its own conditional, with unique ASCII slot id, line id and `window` play function), then the translation `cue-row` + `prompt_hint`, then `#additional-info`, then one script with `_ADD_TITLE_FUNCTION` and the `addTitle` calls.
  - Replace `PRONOUN_CASE_CSS` (line 1025):
    - `#case-form` at 2.2rem;
    - `.form-line` and its `.title`/`.body`/audio-slot rules, copied from the `_ASPECT_LINE_CSS` declarations (line 991);
    - the five palette roles (`form-mn`, `form-f`, `form-pl`, `form-after-prep`, `form-plain-prep`) with `.nightMode` variants.
    - Each role colours both the front qualifier (`.aspect.form-<role>`, which reuses the existing `.aspect` rule for size and nowrap, as `.aspect-imperfective` does) and its counterpart-line `.title`/`.body`. No new tag style is introduced.
  - Front acceptance: every case qfmt contains the pill block before the qualifier span. The qualifier text equals the table in "Front" for its slot. Single-form cells render no qualifier span.
  - Delete `#case-prompt`.
  - Record the `67f3256` text of `PRONOUN_CASE_CSS` in the run dir before the build, for 5.3.
- **Pattern to follow:** the `build_template` verb branch (lines 1158–1176) and the `_ASPECT_LINE_CSS` / `_ASPECT_COLOUR_CSS` block (lines 975–1022).
- **Acceptance:**
  - 22 distinct case templates, each qfmt wrapped in its slot's conditional.
  - Each back carries `{{Audio <slot>}}` for its own slot exactly once, and lines for exactly the other slots of that case.
  - No id repeats on any side (`test_no_duplicate_ids_or_addtitle_per_side`, `test_mutable_words_plan.py:231`), checked across all 24 templates. To do that, its `SHEET_CARD_COUNTS["Pronouns"]` (line 52, currently 2) becomes 24, which makes `test_no_av_tag_in_any_template`'s side count **72** (was 28).
  - `test_card_layout._template_count` (line 125) returns 24.
  - Headless WebKit at 390 and 768 px: the form, every line and the gloss are centred within `TOLERANCE`, with no overflow.
  - `test_card_dedup` (line 324) counts **243** case cards × 2 sides.
- **Test oracle:** `new contract tests` for template structure, conditionals, labels, CSS and palette; `existing suite` for dedup, no-av and centring.

### 2.4: Build wiring in mutable_words.py
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words.py`.
- **Change.**
  - `TEMPLATE_COUNTS_BY_SHEET["Pronouns"]` (line 47) = `2 + len(PRONOUN_CARD_SLOTS)` = **24**.
  - `_AUDIO_FIELD_NAMES` (line 51) uses `PRONOUN_FORM_AUDIO_FIELDS`.
  - Pronouns get `case_pill.CASE_PILL_CSS`: the line 89 condition becomes a named set of pill sheets.
- **Pattern to follow:** the existing `css_parts` assembly (lines 80–91).
- **Acceptance:**
  - A scratch build makes a pronoun note type with 55 fields and 24 templates, case-pill CSS and the new pronoun CSS, and no `#case-prompt`.
  - `attach_media` references include `той_f1.mp3`.
  - The dry-run deck table prints 24 cards per pronoun note.
- **Test oracle:** `existing suite` (build tests and e2e, counts in 4.1).

## Phase 3: Dependent tooling

### 3.1: Retire Oblique Forms from the census, fill and phrase tooling
- **File scope:** `libs/python/anki-tools/anki_tools/form_census.py`, `libs/python/anki-tools/anki_tools/form_fill.py`, `libs/python/anki-tools/anki_tools/phrase_words.py`, `libs/python/anki-tools/anki_tools/source_drift.py`, `libs/python/anki-tools/tests/test_form_census.py`, `libs/python/anki-tools/tests/test_form_fill.py`, `libs/python/anki-tools/tests/test_phrase_words.py`, `libs/python/anki-tools/tests/test_source_drift.py`, `libs/python/anki-tools/tests/test_source_drift_cli.py`. No other lane touches these files: lane 1 owns `mutable_words_plan.py` and its tests, lane 3 owns the audio CLIs, and 4.1 no longer lists `test_source_drift*`.
- **Change.**
  - `form_census.INFLECTION_FIELDS["Pronouns"]` (line 33) becomes `("Gender Forms",)`.
  - Drop `("Pronouns", "Oblique Forms")` from `form_fill.EXCLUDED_BY_PLAN` (line 40).
  - In `phrase_words.INFLECTION_FIELDS` (lines 55–70), `"Oblique Forms"` becomes the 22 `PRONOUN_FORM_FIELDS`, imported from the pure `mutable_words_plan`. Update the stdlib-only docstring line to match.
  - Update the fixture headers (`test_form_census.py:105, 245–262`; `test_form_fill.py:87, 494`).
  - **`form_fill` and the new slot columns.** `form_fill.candidate_cells` takes its cells from `form_census.census_cells` → `classify_cells`, which iterates `INFLECTION_FIELDS[sheet]` only (`form_census.py:241`). `GENERATED_FIELDS` (`form_fill.py:27`) has no Pronouns entry. So once `INFLECTION_FIELDS["Pronouns"] == ("Gender Forms",)`, none of the 22 slot columns can become a fill candidate. Pin that with a test; no code change beyond the `EXCLUDED_BY_PLAN` entry is expected.
  - **`source_drift.py`.** It builds expected notes as `zip(FIELD_NAMES[sheet], row.fields())` with `parse_pronouns` (`source_drift.py:21` and `expected_notes`). That reads the new schema generically, so no code change is expected. Only its tests' pronoun fixtures (`test_source_drift.py:120`, `test_source_drift_cli.py:17`) need the new header/fields if they hard-code the old ones. If a code change does turn out to be needed, it stays inside this file scope.
- **Pattern to follow:** the existing per-sheet field tuples in those modules.
- **Acceptance:**
  - `grep -rn "Oblique Forms" anki_tools/*.py tests/*.py` returns nothing, with a positive control at `67f3256`.
  - A phrase containing `него` resolves to он via the surface tier.
  - Over the real TSVs, `form_fill.candidate_cells` yields no Pronouns cell whose field is one of the 22 slot fields (new test).
  - `source_drift.expected_notes` gives every pronoun note exactly the 55 `FIELD_NAMES["Pronouns"]` keys. A collection note built from the same rows reports zero Pronouns drift (new or updated test). `test_source_drift.py` and `test_source_drift_cli.py` are green.
- **Test oracle:** `existing suite` (updated), plus `new contract tests` for н- surface resolution, the no-slot-candidate check and the source-drift field set.

### 3.2: Per-form audio in the audio and flagged-audio CLIs
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_audio.py`, `libs/python/anki-tools/anki_tools/flagged_audio_cli.py`, `libs/python/anki-tools/tests/test_mutable_words_audio.py`, `libs/python/anki-tools/tests/test_flagged_audio_cli.py`.
- **Change.**
  - `load_base_words` (line 69) uses `row.audio_words` for Pronouns. Fix its stale "four sheets" help text.
  - `flagged_audio_cli.scan` (line 68): for a Pronouns card with `ord >= 2`, yield the stress-stripped form of that card's one slot, `PRONOUN_CARD_SLOTS[ord - 2]`, instead of the headword. Other cards are unchanged.
- **Pattern to follow:** `scan`'s read-by-name (lines 68–83).
- **Acceptance:**
  - Real-data audio words go from `1459` to `1603`, and pairs from `2918` to `3206` (`test_mutable_words_audio.py:129, :134, :202`), re-derived independently in the test.
  - A flagged тот `Genitive f.` card (ord 7) resolves to `[той]`.
  - A flagged он `Genitive (н-)` card (ord 9) resolves to `[него]`.
  - A flagged тот card 1 still resolves to `[тот]`.
- **Test oracle:** `new contract tests`.

## Phase 4: Integration and sign-off

### 4.1: Cross-lane count updates and a fully green suite
- **File scope:** `libs/python/anki-tools/tests/test_mutable_words_e2e.py`, plus any remaining existing test that fails only on a schema-derived count. Expected to need no change: `test_case_ban.py`, `test_case_government.py`, `test_qualifier_classification.py`. The `test_source_drift*` files belong to 3.1. Any extra file is named in the exit report.
- **Change.**
  - `_PER_DECK_CARDS["Pronouns"]` (line 61) goes from 170 to **303**, and the total (line 114) from 3028 to **3161**.
  - The dry-run `total == 2918` (line 326) becomes **3206**.
  - The predicted-filenames test (line 278) also counts slot audio, giving **3180**; rename its stale `_2896` suffix.
- **Count table (current values verified in `tests/` at `67f3256`):**

| Assertion | Now | After |
|---|---|---|
| pronoun cards (`test_mutable_words_plan.py:173`, e2e `:61`) | 170 | **303** (60 word + 243 case) |
| all mutable cards (`test_mutable_words_plan.py:182`, e2e `:114`) | 3028 | **3161** |
| case cards rendered ×2 sides (`test_card_dedup.py:332`) | 110 × 2 | **243 × 2** |
| pronoun templates (`TEMPLATE_COUNTS_BY_SHEET`, `test_card_layout.py:127`) | 7 | **24** |
| template sides (`test_mutable_words_plan.py:228`, with `SHEET_CARD_COUNTS["Pronouns"]` 2 → 24) | 28 | **72** |
| `FIELD_NAMES["Pronouns"]` length | 22 | **55** |
| pronouns.tsv header columns (`test_vocabulary_data.py:75–91`) | 15 | **31** |
| pronouns.tsv lines | 31 | 31 |
| audio words / pairs (`test_mutable_words_audio.py:129, 134, 202`) | 1459 / 2918 | **1603 / 3206** |
| e2e dry-run total (`:326`) | 2918 | **3206** |
| predicted filenames (e2e `:286`) | 2916 | **3180** |
| base-word slug checks (`test_mutable_words_plan.py:258, 263`; e2e `:124, :129`) | 1459 / 1458 | unchanged |

- **Acceptance:**
  - `pnpm run test` and `pnpm run lint` are fully green, with the full output in the exit report and counts read from the output.
  - The 2.1 and 3.1 dangling-reference greps are re-run across the whole package.
- **Test oracle:** `existing suite`.

### 4.2: Phone-width render preview for the user's visual sign-off
- **File scope:** run dir only: `<worktree>/.artifacts/apply_pronoun_forms.py` (authored here) and `<worktree>/.artifacts/preview/`.
- **Change.**
  - **Author the apply script `apply_pronoun_forms.py`** with the exact behaviour and assertions specified in 5.3. It takes the collection path as an argument and never defaults to the live path.
  - Take a **fresh** scratch COPY of the live collection (`collection.anki2` plus a non-empty `-wal`) and run the script on it. This copy predates the 5.1 pull and serves only the preview and a first pass of the assertions; 5.3 re-runs the same script on the post-pull copy.
  - Render these cards with `card.question()`/`card.answer()` inside the live pronoun CSS:
    - тот cards 1, 3, 7 (`Genitive f.`), 13 (`Accusative m. living`);
    - он cards 3 and 9 (`Genitive (н-)`);
    - я cards 1 and 3;
    - сам card 5.
  - Screenshot in headless WebKit at 390 and 768 px, light and `.nightMode`.
  - Show the user the PNGs and the text.
- **Acceptance:**
  - The rendered text matches the approved mockups word for word.
  - **The user explicitly approves.** Phase 5 does not start without that approval.
- **Test oracle:** `equivalence check` (render against the approved mockups), plus human sign-off.

## Phase 5: Live collection migration

All of Phase 5 runs in the main session, never in a builder. Each step is confirmed, and foreground only. Scripts go to the run dir and are never committed.

### 5.1: Pre-flight: phone synced, pull, backup, close Anki
- **File scope:** the live Anki profile (read/sync only); the run dir.
- **Steps.**
  1. Tell the user that this schema change **forces a one-way full upload**. Get explicit confirmation that the phone has synced and holds nothing unsynced.
  2. Pull: launch Anki desktop detached (`setsid nohup anki >/dev/null 2>&1 </dev/null & disown`), let it sync down, then close it.
  3. Run `pkill -x anki`, then confirm `pgrep -x anki` prints nothing.
  4. Back up `collection.anki2` (plus `-wal` if non-empty) to `~/anki-backups/collection-before-pronoun-forms-<timestamp>.anki2`, and confirm `PRAGMA integrity_check` = `ok`.
  5. Snapshot to the run dir:
     - every pronoun card `(id, nid, ord, type, queue, due, ivl, flags)`;
     - every pronoun note's fields;
     - the pronoun note type JSON;
     - the max `due` among case cards (ords 2–6);
     - the list of the 108 hyphenated clip names to orphan.
- **Acceptance:**
  - The backup passes the integrity check.
  - The snapshot shows 30 notes, 170 cards, 110 case cards on unique days, none new.
  - Any drift from the 11-21-26 figures is reported, and the snapshot becomes the truth.
- **Test oracle:** `equivalence check`.

### 5.2: Generate and gap-check the per-form audio
- **File scope:** the Anki media dir; the run dir.
- **Steps.**
  1. Run `uv run anki-mutable-words-audio --sheet Pronouns --dry-run`. Expect about 93 words / 186 pairs pending.
  2. Show the user the request count and get a yes (`CONFIRM_ABOVE_REQUESTS = 1`, `elevenlabs_tts.py:152`).
  3. Run it for real, with the key from the repo `.env` (`set -a; . ./.env; set +a`).
  4. Validate the gap-check against a known-bad take.
  5. Gap-check **every** clip referenced by a pronoun slot (147 words × 2 voices), including the 54 reused ones such as `то_*.mp3`, the clip recorded for the particle "-то".
  6. Re-roll each broken clip with `uv run anki-word-audio --mode single --replace --no-sync -- <word>`, then re-check, until the broken count is 0.
- **Acceptance:**
  - Every referenced clip exists for f1 and m2.
  - The gap-check reports `broken 0` over the full set, and the control did report broken.
  - The generated, reused and re-rolled lists are saved to the run dir.
- **Test oracle:** `equivalence check`.

### 5.3: Dry-run the migration and new-card dating on a collection copy
- **File scope:** a fresh scratch copy of the post-5.1 (pulled, backed-up) collection; the run dir. The script itself, `apply_pronoun_forms.py`, was authored in 4.2 and is **reused unchanged**. Any fix found here goes into that same file and is re-run on a new copy.
- **The apply script.** It runs on the path it is given, in this order:
  1. Add the 34 new fields and remove `Oblique Forms`. Reposition fields to `FIELD_NAMES["Pronouns"]` order.
  2. Add 17 templates (`new_template` + `add_template`) so the note type has 24.
  3. Set all 24 templates' `qfmt`/`afmt` to `word_qualifier.add_qualifier_script(build_template("Pronouns", i))`. Existing ords 0–6 are never repositioned.
  4. Replace the recorded `67f3256` `PRONOUN_CASE_CSS` text in the live CSS with the new block. Assert it occurs exactly once. Append `case_pill.CASE_PILL_CSS` if it is absent.
  5. Call `update_dict` once.
  6. For each of the 30 notes, matched by GUID, write **only** the 44 slot fields from `PronounRow.fields()`, by name. Anki then generates the new cards.
  7. Collect the pronoun cards with `queue=0`. Order them by the 5.1 pronoun order (the existing case-card dating order: rank, with что after кто), then by `PRONOUN_CARD_SLOTS` index (ord). Assign each `col.sched.set_due_date([cid], str(k))` with `k = (snapshot max case due − today) + 1, +2, …`.
  8. Touch no other card.
- **Acceptance** (asserted by the script, with the output saved):
  - The fields equal `FIELD_NAMES["Pronouns"]` and the 24 templates equal the repo output.
  - Every non-slot field of all 30 notes is byte-identical to the snapshot.
  - **All 170 snapshot cards** keep id, nid, ord, type, queue, due and ivl. The 110 old case cards are still at ords 2–6 with their dates.
  - **Exactly 133 new cards** exist: ords 7–23, with per-ord counts matching the filled cells in Appendix A.
    - ord 7–8 (`Genitive f./pl.`): 9 each; ord 9 (`Genitive (н-)`): 4;
    - the same 9 / 9 / 4 for Dative (10–12);
    - Accusative 13–17: 9 each; ord 18 (`Accusative (н-)`): 4;
    - Instrumental 19–21: 9 / 9 / 4;
    - Prepositional 22–23: 9 each.
    - Total 133.
  - The new cards are all `type=2 queue=2 ivl=0`, on consecutive days from max+1 to max+133, one per day.
  - **Each new card's `did` equals the `did` of that note's existing cards**, all in the Pronouns subdeck (`mutable_words_plan.subdeck_name("Pronouns")`). Without this check, the `queue=0` count could pass vacuously if Anki generated the new cards into another deck. The script also asserts that the count of `queue=0` cards across the **whole collection** for these 30 notes is 0.
  - The pronoun deck has 0 cards in `queue=0`.
  - `что (pronoun)` still has 5 case cards.
  - Every slot audio filename exists in the media dir, and the media check reports 0 missing Cyrillic names.
  - The 4.2 sample renders equal the approved text.
  - `anki-counterpart-due "Languages::Russian"` (report) shows 0 for the pronoun deck.
- **Test oracle:** `equivalence check` (pre/post snapshot invariants plus the dating rule).

### 5.4: Apply to the live collection
- **File scope:** the live `collection.anki2`; the media dir.
- **Steps.**
  1. Confirm `pgrep -x anki` prints nothing.
  2. Run the identical script on the live path and re-run every 5.3 assertion.
  3. Trash the 108 orphaned hyphenated clips via `col.media.trash_files`, after a fresh `col.media.check()` confirms each one is unused.
- **Acceptance:** the 5.3 assertions pass on the live file, and the orphans are trashed and listed.
- **Test oracle:** `equivalence check`.

### 5.5: Full upload, media sync, verify zero pending
- **File scope:** the live profile; AnkiWeb.
- **Steps.**
  1. With Anki closed, read `syncKey`/`currentSyncUrl` from the `User 1` row of `~/.local/share/Anki2/prefs21.db` (pickle).
  2. Run `col.sync_collection(SyncAuth(hkey, endpoint), False)`. On a full-sync requirement, run `close_for_full_sync()`, then `full_upload_or_download(..., upload=True)`, then `reopen(after_full_sync=True)`.
  3. Run `anki_sync.sync(<every generated or re-rolled filename>)`.
  4. Make a fresh copy and confirm `usn=-1` = 0 for notes, cards, revlog and graves.
  5. Optional: verify media on AnkiWeb by syncing into an empty scratch profile and comparing sha1s, then delete the scratch profile.
  6. Tell the user to choose **Download** on the phone. That is safe because 5.1 confirmed it had nothing unsynced.
- **Acceptance:** pending = 0 from the fresh copy, `anki_sync.sync` succeeded, and the user has been told about the one-time phone download.
- **Test oracle:** `equivalence check`.

## Phase 6: Record

### 6.1: Docs, changelog commit, local merge to main
- **File scope:** `docs/libs/python/anki-tools/mutable-words.md` (pronoun section, via `documenter` → `document-local`), and the branch commit of the lane changes.
- **Change.**
  - Document the one-card-per-form shape, the slot fields, the template/ord map, the palette and labels, the dating rule, and the per-form audio and flagged-case-card behaviour, updated in place.
  - Commit with named paths and no attribution trailers.
  - Ff-merge `bug/mol-deskat` into `main` locally, and push `main` only after the user says yes. No PR.
- **Acceptance:** the docs page matches what shipped, `main` has a clean commit, and the syllabus is ticked at Record.
- **Test oracle:** `existing suite`.

## Risks, open questions, decision points

### Decided
- **D1: shape = B, one card per form** (the user, 11-21-26). 243 case cards: 110 kept, 133 new.

### Confirmed by the user 11-21-26 (all at the recommended option)
- D2 palette incl. grey for "without a preposition"; D3 drop Oblique Forms, keep Gender Forms; D4 нико́м / ничём; all labels as listed; D5 counterpart lines on the back; D6 headword above the pill line; D7 run-dir gap-check script; D8 flagged-audio change included; D9 grouped by pronoun; D10 one text-side card per form.

### Risks and observations
- **The brief says 112 case cards; the live copy has 110.** 5.1 re-snapshots and reports any difference.
- **The new cards land far out.** At the 11-21-26 snapshot the 133 new cards occupy days 112–244 from today, because they continue after the existing dates as instructed. Re-spreading all 243 would need the existing dates to move, which this plan does not do.
- **Short TTS clips** (то, ту, те, им, ей) can be wrong in ways a gap-check can't detect. Pink/blue flags plus `anki-flagged-audio --fix` (now card-precise) are the follow-up route.
- **Reused clip:** `то_*.mp3` was recorded for the particle "-то". The spoken text is the same ("То."), so it is reused, not regenerated, and it is gap-checked like every other clip.
- **The live CSS has been patched over time.** The migration replaces only the old pronoun block, by exact text, and stops if it doesn't find that block exactly once.
- **Duplicated qualifier script** in live verb templates (cards 1–4) and pronoun templates (cards 1–2). The pronoun ones are normalised by the 5.3 template rewrite; the verb ones are left alone.
- **One-way upload.** 5.1 step 1 (the phone confirmation) is the mitigation and cannot be skipped.
- **Editor and browser clutter:** 55 fields and 24 card types. Field order is grouped by case. The template names stay "Card N".
- **Unverified assumption:** adding and removing fields plus appending templates leaves every existing card id intact. Anki's model and the earlier live template addition both point that way, and 5.3 verifies it on a copy first.
- **Unverified assumption:** `anki-word-audio` can re-roll a single voice. If it can't, both voices are re-rolled.

## Skill mapping

| Work | Executor |
|---|---|
| 1.1, 2.1, 2.2, 2.3, 2.4 | `builder` lane 1 |
| 3.1 | `builder` lane 2 |
| 3.2 | `builder` lane 3 |
| 4.1 | integration builder after lane merge-backs |
| Code review gate | `review-code` after 4.1 |
| 4.2, Phase 5 | main session, confirmation-gated, foreground only |
| 6.1 docs | `documenter` → `document-local` |
| 6.1 merge | main session: local ff-merge to `main`, push on the user's yes, no PR |

Lanes 2 and 3 run alongside lane 1's 2.2–2.4 once 2.1 lands, on disjoint file scopes. `test_mutable_words_e2e.py`, the one test file all three lanes touch, is hoisted into the serialized subphase 4.1.

## Appendix A — slot contents per pronoun (243 cells, one card each; stress as in the TSV)

| Pronoun | Cells (cards) |
|---|---|
| я | Gen меня́ · Dat мне · Acc меня́ · Ins мной · Prep мне (5) |
| ты | Gen тебя́ · Dat тебе́ · Acc тебя́ · Ins тобо́й · Prep тебе́ (5) |
| вы | Gen вас · Dat вам · Acc вас · Ins ва́ми · Prep вас (5) |
| мы | Gen нас · Dat нам · Acc нас · Ins на́ми · Prep нас (5) |
| он | Gen его́, (н-) него́ · Dat ему́, (н-) нему́ · Acc его́, (н-) него́ · Ins им, (н-) ним · Prep нём (9) |
| она | Gen её, (н-) неё · Dat ей, (н-) ней · Acc её, (н-) неё · Ins ей, (н-) ней · Prep ней (9) |
| оно | as он (9) |
| они | Gen их, (н-) них · Dat им, (н-) ним · Acc их, (н-) них · Ins и́ми, (н-) ни́ми · Prep них (9) |
| кто | Gen кого́ · Dat кому́ · Acc кого́ · Ins кем · Prep ком (5) |
| ничто | Gen ничего́ · Dat ничему́ · Acc ничто́ · Ins ниче́м · Prep **ничём** (was "ни о чём") (5) |
| себя | Gen себя́ · Dat себе́ · Acc себя́ · Ins собо́й · Prep себе́ (5) |
| никто | Gen никого́ · Dat никому́ · Acc никого́ · Ins нике́м · Prep **нико́м** (was "ни о ко́м") (5) |
| что (pronoun) | Gen чего́ · Dat чему́ · Acc что · Ins чем · Prep чём (5) |
| сам | Gen самого́ / само́й / сами́х · Dat самому́ / само́й / сами́м · Acc сам / самого́ / само́ / саму́ / са́ми / сами́х · Ins сами́м / само́й / сами́ми · Prep само́м / само́й / сами́х (18) |
| тот | Gen того́ / той / тех · Dat тому́ / той / тем · Acc тот / того́ / то / ту / те / тех · Ins тем / той / те́ми · Prep том / той / тех (18) |
| этот | Gen э́того / э́той / э́тих · Dat э́тому / э́той / э́тим · Acc э́тот / э́того / э́то / э́ту / э́ти / э́тих · Ins э́тим / э́той / э́тими · Prep э́том / э́той / э́тих (18) |
| мой | Gen моего́ / мое́й / мои́х · Dat моему́ / мое́й / мои́м · Acc мой / моего́ / моё / мою́ / мои́ / мои́х · Ins мои́м / мое́й / мои́ми · Prep моём / мое́й / мои́х (18) |
| твой | as мой with тво- (18) |
| свой | as мой with сво- (18) |
| наш | Gen на́шего / на́шей / на́ших · Dat на́шему / на́шей / на́шим · Acc наш / на́шего / на́ше / на́шу / на́ши / на́ших · Ins на́шим / на́шей / на́шими · Prep на́шем / на́шей / на́ших (18) |
| ваш | as наш with ва́ш- (18) |
| весь | Gen всего́ / всей / всех · Dat всему́ / всей / всем · Acc весь / всего́ / всё / всю / все / всех · Ins всем / всей / все́ми · Prep всём / всей / всех (18) |

Slot order in the gendered rows:
- Gen, Dat, Ins and Prep: masculine / neuter, then feminine, then plural.
- Acc: masculine, not living; masculine, living; neuter; feminine; plural, not living; plural, living.

The primary slot (first in each case) is the existing card at ords 2–6. Every other cell is a new card at ords 7–23. Every value is the TSV's existing form moved into its own cell. The only changed spellings are the two bold prepositional forms (D4).
