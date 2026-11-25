# Pronoun form cards get a Russian and an English side, and the word cards match the verb cards

### Ask of record

**11-22-26** — The orchestrator's brief, verbatim as handed to the planner. It was pasted into the dispatch, not passed as a file path.

> Type: rework.
>
> Repo worktree: /home/icarus64/repos/daedalus-mono/.workflows/mol-deskat (branch bug/mol-deskat, base main; lands by local ff-merge to main, no PRs). Write the plan to project-plans/proposals/ per plan-format. PLANNING ONLY: no code edits, no Anki writes, no commits, no audio generation.
>
> ## Context: what shipped and why it is wrong
> - The previous plan is archived at project-plans/completed/pronoun-case-cards-rework-11-21-26.md and was shipped as commit 83b8aef. Read it.
> - It gave the 30 pronoun notes ("Russian - Mutable Pronouns (Ellis Version)") 24 templates: cards 1–2 are the word cards, and 22 per-form case templates follow. That is 303 cards.
> - Each per-form case card is ONE-SIDED. Front: the headword, the case pill and a coloured qualifier, e.g. "мой [Instrumental] (plural)". Back: ▶ plus the form, e.g. "мои́ми", then the other forms as counterpart lines, the gloss and ⓘ.
>
> The user rejects this. Their words (profanity removed): "Every word card I have ever had you make has a Russian and English side." "They should look like the verbs cards." "Why the fuck is the shape of the new card not the same as every other card in this deck? Why is there not one English and one Russian side?"
>
> Also from a phone screenshot of который card 2: it is plain. который, самый, какой, никакой and такой have no case forms at all, and their "Gender Forms" row packs который / которая / которое / которые on one line that runs off the screen. тот, мой, сам and the rest also still pack their nominative gender forms (та, то, те …) in that one row.
>
> ## What the user approved in principle (they have not seen mockups yet)
> 1. **Every form gets a Russian side and an English side, mirroring verb cards 3/4** (perfective). Live verb cards, rendered from делать/сделать:
>    - Card 3 front: ▶ and сделать. Card 3 back: "do / make (perfective)" with the case pills, then the counterpart line, details, info and examples.
>    - Card 4 front: "do / make (perfective)" with the pills. Card 4 back: ▶ and сделать, then the counterpart and details.
>
>    For a pronoun form:
>    - Russian side front: ▶ and мои́ми. Back: "my / mine (plural)", with the qualifier in coloured brackets exactly where verbs put "(perfective)" (`_translation_div` aspect-tag pattern), then the [Instrumental] case pill where verbs show their case pills, then the other forms of that case as verb-style counterpart lines, then ⓘ.
>    - English side front: "my / mine (plural)" plus the [Instrumental] pill. Back: ▶ and мои́ми, then the counterpart lines and ⓘ.
>    - Single-form pronouns (я…) get the same pair with no qualifier.
>    - Use the SAME HTML structure, ids and classes as the verb templates, so the cards render identically in style. The pronoun palette for the qualifier colours is kept: teal m./n., magenta f., brown pl., #605C8B after a preposition, grey without a preposition.
> 2. **The nominative gender forms get their own form cards**, replacing the packed Gender Forms row on the word cards. For тот, the forms та, то, те are each a form with its own audio and both sides; likewise for мой and the others. Define the nominative slots, including that the headword itself is the m. nominative already drilled by cards 1–2.
> 3. **самый, какой, который, никакой and такой get full declension forms**, about 12 distinct forms each, every one with a field, its own audio and both sides.
>    - Derive the forms carefully, with stress, and list them all in an appendix for review.
>    - его, её and их stay unchanged; they are indeclinable.
>
> ## Migration constraints
> - The pronoun notes stay the same 30 notes; nothing moves to new notes.
> - The existing 243 per-form cards keep their card ids and due dates. They become the RUSSIAN side of their form (one-sided → Russian side), unless you find a strong reason otherwise.
> - All new cards (English sides, nominative forms, the 5 adjective-like pronouns' forms) are dated one per day, continuing after the last existing pronoun date (currently due 2152, `col.sched.today` ≈ 1909). None are left new.
>   - Recommend an order. Default: each form's English side the day after its Russian side wherever possible; otherwise group by pronoun.
>   - Date with `col.sched.set_due_date`.
> - Anki template ord limits and field-count growth: estimate the totals. If the template count gets large, consider whether the Russian/English pair can share a slot template pattern. Keep to one note type.
> - Live migration rules:
>   - pull from AnkiWeb first, then back up;
>   - `pkill -x anki`;
>   - a dry run on a copy using a reusable apply script in `.artifacts/`, with full invariant assertions (existing card ids, due dates and non-slot fields untouched; the new card count and deck);
>   - generate audio for new forms only and gap-check every clip, with a known-bad control (the script logic is in /tmp/claude-1000/-home-icarus64-repos-daedalus-mono/b72e956c-0c9f-4111-a998-9a5abc7d0622/scratchpad/gapcheck.py);
>   - full upload via API, media sync, 0 pending;
>   - the phone then chooses Download.
> - 4.2-style phone-width PNG previews of the REAL rendered templates, both sides, light mode, for the user's approval before any live write:
>   - мой Instrumental plural (Russian + English sides)
>   - тот nominative feminine та
>   - который Genitive feminine
>   - я Genitive
>   - он Genitive after a preposition
>   - and, for comparison, a real verb card 3 and 4 rendered by the same harness
>
> ## Standing rules
> - Never change English glosses, cues or Additional Info.
> - No examples or grammar jargon in cues.
> - The что (pronoun) row must remain.
> - One form per field, one single-word clip per form; never several words in one clip.
> - No attribution trailers of any kind (no Co-Authored-By, no Claude-Session, no session URL).
> - Name the paths you stage; never `git add -A`.
>
> Return the plan path, mockups of the two sides for мой Instrumental pl. and который Genitive f., the card/field/template/audio counts, and any decision the user must make.

**11-22-26 — appended, mid-planning, word cards 1–2 in scope (verbatim as relayed by the orchestrator)** —

> The user added scope. Their words: "i just screenshoted the first one i saw, but every card from before looks like this".
>
> "This" is the который card 2 back. It shows the gloss + cue, then ▶ + который, then a plain "Gender Forms  который / которая / которое / кото…" row cut off at the screen edge, then ⓘ, then Examples. It looks plain and nothing like the verb word cards.
>
> So the plan must also rebuild pronoun cards 1–2 (the word cards, all 30 pronouns) to match verb cards 1/2:
> - the same structure, ids, classes and CSS;
> - the same front/back regions;
> - the details shown the way the verb card shows its counterpart line and details grid, never a packed row that overflows the screen.
>
> The nominative gender forms belong on their own form cards and as counterpart lines, as you are already planning.
>
> Notes:
> - The live pronoun card 1/2 templates were already known to differ from the repo before 67f3256. Diff live against the repo and say what you found.
> - Never change glosses, cues, Additional Info or Examples text.
> - Include card 1 and card 2 previews for который, тот and я, next to verb card 1 and 2 previews, in the 4.2-style preview set.
>
> Same constraints: planning only, no attribution trailers.

**11-22-26 — appended, mid-planning, the no-form-change tag (verbatim as relayed by the orchestrator)** —

> One more user requirement. Their words: "cards with no form changes should show that on the card."
>
> Apply it to the indeclinable pronouns его, её and их, which never change form:
> - Their word cards (1–2) must state visibly that the word does not change.
> - Use a short, plain-English, coloured parenthesised tag in the verb aspect-tag style, e.g. "(never changes)". It goes where other pronouns show their forms or counterpart lines.
> - No grammar jargon like "indeclinable".
> - Propose the exact wording and show it in the mockups and previews: его card 1 and card 2.
>
> Also check for any other card where the asked form is spelled identically to the headword (e.g. что Accusative = что, тот Accusative masculine not-living = тот). Recommend whether a small note like "(same as the base form)" should appear there. Give a mockup and flag it as a user decision.
>
> Same constraints: planning only, no attribution trailers.

**11-22-26 — appended, at the plan gate, the card unit decided by the user (verbatim as relayed by the orchestrator)** — "no if the word is the exact same it should show the word with extra pills. but remember only base form words (genitive/dative/instrumental/etc) get pills (masculine feminine and neuter get coloured () like how verbs do per/imper)"

The orchestrator's accompanying directives, verbatim:

> 1. **Unit: one Russian-side + English-side card pair per DISTINCT word per pronoun, not per case×gender cell.** A spelling that fills several cells gets ONE pair, and its card shows all the cases it covers.
>    - Examples: я → меня́ = [Genitive][Accusative] on one pair; мне = [Dative][Prepositional].
>    - About 205 non-base distinct forms → about 410 form cards, plus 60 word cards, ≈ 470 total. Recompute exactly.
>    - Define "distinct": the same spelling ignoring stress marks, but forms differing in ё/е (всё vs все) are distinct. If the same letters carry a different stress within one pronoun, treat them as distinct and list any such cases.
> 2. **Pills vs parentheses.**
>    - Case names (Nominative…Prepositional) are always the small case pills.
>    - Gender/number/animacy/after-a-preposition are ALWAYS coloured parenthesised tags, exactly like verb (perfective)/(imperfective), placed after the English gloss.
>    - Handle words that span different gender groups in different cases. Give mockups for each of these:
>      - тем = m./n. Instrumental AND pl. Dative
>      - того́ = m./n. Genitive AND m. living Accusative
>      - тех = pl. Genitive, Prepositional AND pl. living Accusative
>      - той = f. Genitive/Dative/Instrumental/Prepositional
>      - меня́
>      - его́ (он: Genitive AND Accusative, plus the separate possessive его note, which is untouched)
>
>      Recommend one clear rendering, e.g. pills grouped per qualifier ("(masculine / neuter) [Instrumental] · (plural) [Dative]"), without breaking the verb-like shape.
> 3. **The base word.** Where a slot is spelled like the headword (тот Accusative m. not living; что Accusative), it does NOT get its own form card. The word cards 1–2 show those extra case pills instead, e.g. тот: (masculine) [Nominative][Accusative not living]. Choose a sensible rendering, show it in the mockups, and keep "(never changes)" for его/её/их. This replaces the earlier "(same as the base form)" D7 idea; drop D7.
> 4. **Fields and templates.** Re-plan the data model for per-distinct-word cards:
>    - e.g. a fixed set of numbered form slots per note (Form 1..N + Audio + a per-form "where used" field holding the pills/qualifiers), with the template pair per slot conditional on that field;
>    - state N and the template count;
>    - keep one note type and the same 30 notes.
> 5. **Migration of the existing 243 one-sided cards.** They have only manual-reschedule history, so nothing real is lost. Plan how card ids/dates map: keep one existing card per distinct word where its ord can be reused, otherwise let them be removed, and say which. Then date every card left new one per day after the last existing date, none left new. Restate the horizon in days.
> 6. Recompute every count (cards, fields, templates, audio requests, tests), and update the mockups and decision list.
>
> Same constraints: planning only, no code, no Anki writes, no commits, no attribution trailers of any kind.

**11-22-26 — appended, at the plan gate, D10 decided by the user (verbatim)** — "replace them and just keep the 60". D10 = B: remove all 243 existing one-sided form cards and date 410 fresh cards; the 60 word cards (ords 0–1) keep ids, history and schedule. The other decisions proceed at the recommended options, with the user approving the rendered previews before any live write.

## Phase syllabus
- [ ] Phase 1: Source data
  - [ ] 1.1: pronouns.tsv: nominative slot columns, the five adjective-like declensions, drop Gender Forms        (lane 1)
- [ ] Phase 2: Pronoun note-type core
  - [ ] 2.1: Distinct-word derivation: form slots, tags, case rows, homograph audio words, 56 fields          (lane 1, after: 1.1)
  - [ ] 2.2: Russian-side and English-side form templates in the verb card 3/4 shape                          (lane 1, after: 2.1)
  - [ ] 2.3: Word cards 1–2 on the verb card 1/2 shape: base pills, "(never changes)", nominative lines        (lane 1, after: 2.1)
  - [ ] 2.4: Pronoun CSS: case rows, verb-identical lines, details-grid overflow fix, delete the old CSS        (lane 1, after: 2.2, 2.3)
  - [ ] 2.5: Build wiring in mutable_words.py                                                                (lane 1, after: 2.1)
- [ ] Phase 3: Dependent tooling
  - [ ] 3.1: Census, fill, phrase and drift tooling read the TSV slot cells, not note fields                  (lane 2, after: 2.1)
  - [ ] 3.2: Audio CLIs: new words, stressed spoken text for homographs, form-slot-aware flags                (lane 3, after: 2.1)
- [ ] Phase 4: Integration and sign-off
  - [ ] 4.1: Cross-lane count updates and a fully green suite                                                (after: 2.2, 2.3, 2.4, 2.5, 3.1, 3.2)
  - [ ] 4.2: Apply script, render previews of real templates on a copy, user sign-off                         (after: 4.1)
- [ ] Phase 5: Live collection migration
  - [ ] 5.1: Pre-flight: phone synced, pull, backup, close Anki, snapshot                                     (after: 4.2)
  - [ ] 5.2: Generate new-word audio, gap-check every pronoun clip, user listens to the homographs            (after: 5.1)
  - [ ] 5.3: Dry run the apply script on a post-pull copy                                                     (after: 5.2)
  - [ ] 5.4: Apply to the live collection                                                                    (after: 5.3)
  - [ ] 5.5: Full upload, media sync, verify zero pending, phone Download                                    (after: 5.4)
- [ ] Phase 6: Record
  - [ ] 6.1: Docs, changelog commit, local ff-merge to main                                                  (after: 5.5)

## Goal & scope

**Goal.** Every pronoun card has the verb cards' shape, with **one card pair per distinct word**:
- **One Russian-side + English-side pair per distinct non-base word of each pronoun.**
  - Russian side = verb card 3. Front: ▶ and the word. Back: gloss + tag, case pills, counterpart lines, ⓘ.
  - English side = verb card 4. Front: gloss + tag and pills. Back: ▶ and the word, lines, ⓘ.
  - A spelling that fills several case×gender cells gets one pair showing all of its cases, e.g. я меня́ = [Genitive][Accusative].
- **Pills vs tags.**
  - Case names are always small case pills.
  - Gender, number, animacy and after-a-preposition are always coloured parenthesised tags, in the verb `(perfective)` style.
- **The base word (headword) has no form card.** Cells spelled like it are shown as extra pills on word cards 1–2, e.g. тот: `(masculine) [Nominative]` · `(masculine, not living) [Accusative]`.
- **Word cards 1–2 of all 30 pronouns are rebuilt on the verb card 1/2 shape.**
  - The packed `Gender Forms` row goes.
  - The nominative f./n./pl. forms become counterpart lines.
  - его, её and их show `(never changes)`.
- **самый, какой, который, никакой and такой are fully declined.**

**In scope**
- `pronouns.tsv`:
  - the 25 case×gender slot columns stay the linguistic source, one form per cell;
  - 3 nominative columns are added;
  - the 5 adjective-like rows are filled;
  - `Gender Forms` is dropped (D1).
- `mutable_words_plan.py`:
  - derive each note's distinct words from those cells;
  - a new 56-field schema with **11 numbered form slots**;
  - **24 templates**: 2 word + 11 Russian + 11 English;
  - CSS;
  - the homograph audio words.
- `case_pill.py`: drop the unused `trailing` argument.
- `mutable_words.py`: wiring.
- Tooling: `form_census.py`, `form_fill.py`, `phrase_words.py`, `source_drift.py`, `mutable_words_audio.py`, `flagged_audio_cli.py`, `audio_naming.py`.
- Live collection:
  - schema change (fields replaced, all 24 templates rewritten);
  - **all 243 one-sided form cards removed; the 60 word cards keep their ids, history and schedule** (D10 = B, decided);
  - **410 new form cards dated one per day from today+1** (due 1910–2319 against the 11-22-26 `today` 1909, a 410-day horizon);
  - 61 new audio words (122 clips);
  - full upload and media sync.
- Tests updated to the new counts (4.1).

**Out of scope**
- Any change to Translation, English Distinction, Russian Distinction, Additional Info, Examples, Pronoun Type, Rank, Stress or `Audio` values. 5.3 compares them byte for byte.
- The separate possessive notes его/её/их, apart from their word-card tag.
- The verb note type. Its live templates and CSS are untouched; see Risks for the shared-CSS fix.
- Alternative instrumental forms in `-ою` (D5).
- Numerals' own `Gender Forms`.

**Supersedes:** nothing. This reworks the design shipped in `83b8aef` (archived plan `project-plans/completed/pronoun-case-cards-rework-11-21-26.md`).

**Classification note.** The type is declared `rework`, but by the user's own direction this changes visible card behaviour and the card set. Most subphases therefore use `new contract tests`.

## What exists today (research findings, read 11-22-26)

The live facts below come from a scratch copy of `~/.local/share/Anki2/User 1/collection.anki2`. It was taken with `pgrep -x anki` empty and an empty WAL. The probes live in the session scratchpad: `live_probe.py`, `shot_probe.py`, `overflow_probe.py`, `forms_probe.py`, `distinct_probe.py`, `survive_probe.py`.

### Live state

- `col.sched.today` = **1909**. The pronoun note type has **55 fields, 24 templates** and 8 640 chars of CSS.
- 303 pronoun cards, all `type=2 queue=2`, none flagged, `usn=-1` = 0.
- Per ord:
  - 0/1 → 30 each;
  - 2–6 → 22 each;
  - 7, 8, 10, 11, 13–17, 19, 20, 22, 23 → 9 each;
  - 9, 12, 18, 21 → 4 each.
- **Max pronoun due = 2152.** The word cards' max due is **1936**.
- **The 243 form cards' only revlog rows are 243 type-4 (manual reschedule) entries, and none has ever been reviewed.** Removing or repurposing them loses no learning history.

### Live vs repo templates (the requested diff)

- **Pronoun ords 0–3** are byte-identical to `build_template("Pronouns", i)` at `83b8aef`. That covers word cards 0–1 too: `83b8aef`'s migration normalised the older drift.
- **Verb ords 0–3** contain the repo output plus a duplicated qualifier script. Affected sides run 294 chars longer, e.g. ord 0 qfmt is 3 587 vs 3 293. Out of scope.
- **CSS.** Live pronoun CSS = live verb CSS + the same `EXTRA_CSS` block + `PRONOUN_CASE_CSS`. Every verb id and class rule is already present in the pronoun sheet.

### Why the pronoun word cards look plain

- Pronoun cards 1–2 come from the generic branch of `build_template` (`mutable_words_plan.py:1228–1300`). They get none of the three things that branch adds for Verbs:
  - the coloured tag in `_translation_div` (`:1187–1205`);
  - the case pills (`:1278–1290`);
  - the `#perfective` counterpart line (`:1251–1266`).
- **20 of the 30 word cards overflow a 390 px screen:** который 581 px, никакой 577, самый 520, его 497, какой 492, такой 491, наш 473, ваш 471, её 465, сам 460, свой 458, твой 455, их 444, мой 432, весь 425, этот 417, он/она/оно/они 411.
  - Cause: `#details { grid-template-columns: max-content max-content; width: max-content }` (`_build_extra_css`, `:1143–1150`). A max-content column never wraps.
  - его/её/их overflow on the Pronoun Type value alone, so the grid itself must be fixed (2.4).
- Verb card 2 for делать at 390 px is centred and fits.

### Distinct words (the new card unit), computed over the TSV plus Appendix A

- **205 distinct non-base words** across the 30 pronouns, so **410 form cards**. Per pronoun:
  - я ты вы мы 3 each;
  - он 7, она 4, оно 7, они 6;
  - его её их 0;
  - кто ничто никто что 4 each;
  - себя 2;
  - сам тот этот мой твой наш ваш свой самый который весь 11 each;
  - какой никакой такой 10 each.

  The full list is Appendix A.
- **"Distinct"** means the same spelling once U+0301 is stripped. ё and е stay distinct letters, so ниче́м ≠ ничём, чем ≠ чём, все ≠ всё.
- **No pronoun has the same letters with two different stresses.** The probe reported an empty conflict list.
- **Max forms per note = 11.** Hence N = 11.
- **Base cells (spelled like the headword, so no form card):**
  - ничто Acc;
  - себя Gen + Acc;
  - Accusative m. not living for сам тот этот мой твой наш ваш свой самый который весь;
  - какой, никакой, такой: Acc, plus feminine Gen/Dat/Ins/Prep (како́й = the headword's spelling);
  - что Acc.
- **Cross-pronoun stress homographs** (separate notes, separate clips needed): са́мого/самого́, са́мой/само́й, са́мому/самому́, са́мом/само́м (самый vs сам). The existing `самого_*.mp3` etc. were voiced for сам from bare text, so their stress is unverified (D4).
- **Audio:**
  - 192 distinct non-base form words once the 205 per-pronoun words are deduplicated across pronouns (он/оно share all 7, for example). Adding the 30 headwords gives **219** distinct pronoun audio words, the figure the plan review recomputed;
  - 57 of the 192 have no clips;
  - plus 4 homograph clips for самый;
  - so **61 new words, 122 ElevenLabs requests**.

### Code to follow

- **Verb card shape:**
  - `build_template` (`:1228–1300`), `_VERB_CARD_CONFIGS` (`:839–864`), `_ASPECT_COUNTERPART` (`:869–872`), `_translation_div` (`:1187–1205`), `_ASPECT_LINE_CSS` (`:991–1031`);
  - `card_audio.audio_block` / `audio_line_block` (`card_audio.py:117, 173`).
- **Shipped pronoun code to replace:**
  - `PRONOUN_SLOTS` (`:63–87`), `PRONOUN_CARD_ENTRIES` (`:94–98`), `_PRIMARY_QUALIFIERS` (`:1306–1312`), `_form_line` / `_pronoun_other_lines` (`:1349–1404`);
  - `_pronoun_case_template` (`:1409–1448`), `PRONOUN_CASE_CSS` (`:1088–1135`), `#case-form`.
- **Audio naming:** `build_filename` (`audio_naming.py:102`), `spoken_text_for` + `SPOKEN_TEXT_OVERRIDES` (`:120–160`), model `eleven_turbo_v2_5` with `language_code=ru` (`elevenlabs_tts.py:99–113`).
- **Migration and preview pattern:** `.artifacts/apply_pronoun_forms.py` (snapshot → migrate → write fields → `set_due_date` → asserts) and `.artifacts/render_preview.py` (Playwright WebKit over `card.question()`/`card.answer()`).

## The shape

### Data model: 11 numbered form slots per note, 56 fields

- **Source stays cell-based.** `pronouns.tsv` keeps one form per case×gender cell: the 22 shipped slot columns plus `Nominative f.`, `Nominative n.` and `Nominative pl.`. That is 375 filled cells.
- **Note fields are derived from the cells by `PronounRow`:**
  1. Order the cells canonically: Nominative f./n./pl., then Genitive, Dative, Accusative, Instrumental and Prepositional, each in slot order.
  2. Group them by stress-stripped spelling. A group's position is its first cell.
  3. Drop the group spelled like the headword. Its cells become the **base cases**.
  4. Number the rest `Form 1 … Form M` (M ≤ 11).
- **Per form k, four fields:**
  - `Form k`: the stressed word;
  - `Audio Form k`: `audio_field_value(audio_names(<audio word>))`;
  - `Form k Tag`: the inline tag HTML, filled only when every cell of the word shares one qualifier;
  - `Form k Cases`: the case-row HTML (below).
- **Per note, two base fields:** `Base Tag` and `Base Cases`, for word cards 1–2.
- **Total:** 10 base fields (the current 11 minus `Gender Forms`) + `Base Tag` + `Base Cases` + 11 × 4 = **56 fields** (55 today).
- **These derived fields are never hand-edited.** The TSV is the source, and `source_drift` checks the derived values.
- **A row with more than 11 forms fails the build loudly** (test).

### Templates: 24, the same count as today

| ords | Template | Cards |
|---|---|---|
| 0 | Word card 1 (audio side), rebuilt | 30 |
| 1 | Word card 2 (text side), rebuilt | 30 |
| 2–12 | Russian side of `Form 1` … `Form 11`, each wrapped in `{{#Form k}}` | 205 |
| 13–23 | English side of `Form 1` … `Form 11` (ord = Russian ord + 11) | 205 |
| | **Total** | **470** (303 today) |

- Cards per Russian ord 2…12, and the same for English ords 13…23: **27, 27, 26, 22, 17, 17, 16, 14, 14, 14, 11** (notes with ≥ k forms). The sum is 205.
- No template is added or removed. All 24 are rewritten.
- **The two sides cannot share one template.** In Anki one template makes at most one card per note, and the Russian and English sides are two cards. They share one generator, `_pronoun_form_template(k, side)`.

### Case rows: how tags and pills render (decided, D9)

A word's cells are grouped **by qualifier**, keeping case order. Each group is one **case row**: the coloured tag, if any, then its pills in case order.

| Cells | Case rows |
|---|---|
| тем (тот) | `(plural) [Dative]` · `(masculine / neuter) [Instrumental]` |
| того́ (тот) | `(masculine / neuter) [Genitive]` · `(masculine, living) [Accusative]` |
| тех (тот) | `(plural) [Genitive][Prepositional]` · `(plural, living) [Accusative]` |
| той (тот) | `(feminine) [Genitive][Dative][Instrumental][Prepositional]` |
| меня́ (я) | `[Genitive][Accusative]`, no tag (one form per case) |
| его́ (он) | `(without a preposition) [Genitive][Accusative]` |
| то (тот) | `(neuter) [Nominative][Accusative]` |
| те (тот) | `(plural) [Nominative]` · `(plural, not living) [Accusative]` |

- **One row → the exact verb shape.** The tag goes after the gloss, inside `#translation` where `(perfective)` sits (`Form k Tag`). The pills go on the `.case-pills` line below (`Form k Cases`). **That row carries no tag span, so a single-qualifier word shows its tag exactly once, after the gloss.** The same rule holds for `Base Tag` / `Base Cases`.
- **Several rows → the gloss line stays bare.** Each row is a centred line under it, tag first and then its pills, in the `.case-pills` position. With different qualifiers per case, a single tag after the gloss would be wrong for some of the cases. Rows keep each tag next to the cases it qualifies, and keep the verb shape of gloss line then pill line(s).
- **Tag texts and colours** are as shipped, plus nominative:
  - `(masculine / neuter)`, `(masculine, not living)`, `(masculine, living)`, `(masculine)` (nominative headword), `(neuter)`: teal `#00796b`;
  - `(feminine)`: magenta `#ad1457`;
  - `(plural)`, `(plural, not living)`, `(plural, living)`: brown `#6d4c41`;
  - `(after a preposition)`: `#605C8B`;
  - `(without a preposition)`: grey `#656565`.
- **A cell gets no tag** when its pronoun has only one form in that case (я, ты, вы, мы, кто, ничто, себя, никто, что, and он-family Prepositional).
- **Pill markup** is the existing `.case-pill.case-<slug>` spans (`case_pill.py`). They are emitted only for the cases present, inside `div.case-row` elements in a `.case-pills` wrapper. CSS shows every pill inside `.case-row`.

### Russian side (ords 2–12), mirroring verb card 3

- **Front:** wrapped in `{{#Form k}}`. It holds `#front` > `#path`, `#deck`, `card_audio.audio_block("Audio Form k", "audio", PRONOUN_FORM_STATE_KEY)` (autoplays), `<div id="russian">{{Form k}}</div>` and the Russian cue (`_add_russian_cue`; only что has one, "(pronoun)", D6).
- **Back:** `{{FrontSide}}`, then `#back` with:
  1. `#translation`: `{{Translation}}`, then `{{Form k Tag}}` in the `.aspect` span position, then `#prompt-hint`;
  2. `<div class="case-pills">{{Form k Cases}}</div>`;
  3. counterpart lines (D11);
  4. `#additional-info`;
  5. one script with `_ADD_TITLE_FUNCTION`, the `addTitle` calls and the line reveal.

### English side (ords 13–23), mirroring verb card 4

- **Front:** `#front` > header, `#translation` (gloss + `{{Form k Tag}}` + `#prompt-hint`), and `.case-pills` with `{{Form k Cases}}`. Wrapped in `{{#Form k}}`.
- **Back:** `#back` > `audio_block("Audio Form k", …)` (autoplays), `#russian` `{{Form k}}` + Russian cue, the counterpart lines, `#additional-info`, script.

### Ids and classes

- These match the verb cards exactly: `#front`, `#back`, `#path`, `#deck`, `#audio*`, `#russian`, `#russian-distinction`, `.cue-row`, `#translation`, `#prompt-hint`, `.aspect`, `.case-pills`, `.case-pill`, `.tappable`, `.audio-line`, `.audio-play.audio-play-sm`, `#additional-info`, `.title`/`.body`.
- Counterpart lines need unique ids (`form-<j>`, `form-<j>-audio`, `form-<j>-word`, `__pronounFormPlay_<j>`) because a card has several. They share the class `form-line`, whose rules copy `_ASPECT_LINE_CSS` declaration for declaration.
- `#case-form` is deleted.

### Counterpart lines on form cards (decided, D11)

- **Rule.** A card for word k lists, one line each, **the other words of the same pronoun that share at least one case with word k**. The headword counts as a word, through its base cases.
- **Line shape.** Each line is the verb counterpart line (small ▶ playing that word's own clip, then the word). Its coloured title is that word's case rows **restricted to the shared cases**, e.g. on тем's card: `(masculine / neuter) [Dative] (▶) тому́`.
- **Order:** case order, then slot order.
- **Size.** At most 7 lines (сами́х, тех and their peers). One-form-per-case pronouns get none, because their words share no case.
- **How it renders.** Mustache cannot test case overlap, so each template carries a line block for every other slot j (in `{{#Form j}}`) plus the headword line. The blocks are hidden by default. The side's script reads the `data-cases` of the case rows and reveals and titles only the overlapping ones. Without JS, no lines show and the card still reads correctly.
- Rejected alternatives: tag-only titles, which are ambiguous for тем (two different "masculine / neuter" cases), and no lines at all.

### Word cards 1–2 (ords 0–1), mirroring verb cards 1/2

The generic branch stays the generator. It gains a pronoun branch that adds the verb card's three extras.

- **Base tag and base pills** (`Base Tag`, `Base Cases`), in the same positions as on a form card:

| Pronoun | Base case rows |
|---|---|
| тот, сам, этот, мой, твой, наш, ваш, свой, весь, самый, который | `(masculine) [Nominative]` · `(masculine, not living) [Accusative]` |
| какой, никакой, такой | `(masculine) [Nominative]` · `(masculine, not living) [Accusative]` · `(feminine) [Genitive][Dative][Instrumental][Prepositional]` |
| что, ничто | `[Nominative][Accusative]` |
| себя | `[Genitive][Accusative]` (no nominative) |
| я ты вы мы он она оно они кто никто | `[Nominative]` |
| его, её, их | no pills; the tag **`(never changes)`** after the gloss, in slate `#546e7a` (D8), rendered by `{{^Form 1}}` (only these 3 notes have no forms; a test pins that) |

- **Counterpart lines on word cards:** only the words whose cases include Nominative, which are the gender forms. For тот that is `(feminine) [Nominative] (▶) та`, `(neuter) [Nominative] (▶) то` and `(plural) [Nominative] (▶) те`. This replaces the packed Gender Forms row. A word card does **not** list every word that shares a case with its base, because for какой that would be 10 lines.
- **`#details`** keeps `Pronoun Type`, with the current `_TYPE_ROW_HIDDEN` behaviour, and no longer overflows (2.4).
- ⓘ and Examples are unchanged.

### Migration of the existing 243 form cards (D10 = B, decided)

- **All 243 one-sided form cards (ords 2–23) are removed, and 410 new form cards are generated.** The user's words: "replace them and just keep the 60".
- **The 60 word cards (ords 0–1) keep id, nid, ord, did, type, queue, due, ivl, flags and revlog untouched.**
- **Deletion is unconditional** (the user: "i never said keep old cards delete all 243 only the original 60 should be there"). On the 11-22-26 copy their only revlog rows are type-4 manual reschedules. 5.1 reports any real-review rows found, as information only; they never block the deletion.
- **Removal before regeneration.** The apply script removes the 243 ids, asserted against the snapshot set, with `col.remove_cards_and_orphaned_notes(ids)`. No note is orphaned, because each keeps its 2 word cards. Only then are the templates rewritten and the fields written, so Anki generates the 410 cards fresh. The script asserts that no removed id reappears.

### Dating order (D3)

- **Decided (D3 = A):** grouped by pronoun in the existing dating order (rank, with что after кто), forms in canonical order. Each Russian side goes on day d and its English side on day d+1.
- **Start date: today+1** relative to `col.sched.today` at apply time, one card per day, none left new. This follows the user's original instruction for pronoun form cards ("one of the new cards due a day … so none are in new"), whose first batch started the next day. It does not start after the word cards' max due.
- **Horizon:** offsets 1…410, so the last form card is due today+410. Against the 11-22-26 snapshot (today 1909) that is due 1910–2319, **410 days**.
- `col.sched.set_due_date([cid], str(offset))` per card, as in `.artifacts/apply_pronoun_forms.py:156`. No word card moves.
- Afterwards, `anki-counterpart-due "Languages::Russian"` (report) should show 0 for the pronoun deck.

## Mockups (text renders; approval required before 4.2)

- `( ▶ )` is the big autoplaying button. `(▶)` is the small line button.
- `[Case]` is a pill in the case colour: Nom grey, Gen red, Dat green, Acc blue, Ins amber, Prep purple.
- Tags are coloured as listed above.
- Every side starts with the header `Languages > Russian > 4. Mutable Words > d. Pronouns` / `Russian - Pronouns`, omitted here.
- Backs repeat their front above (`{{FrontSide}}`). Only the added part is shown.

### тем (тот): two qualifier groups

```
RUSSIAN SIDE — FRONT          BACK
      ( ▶ )  ← clip: тем      that (one) / that (over there) (pointing at something farther)
       тем                           (plural) [Dative]
                              (masculine / neuter) [Instrumental]
                    (masculine / neuter) [Dative]  (▶) тому́
          (feminine) [Dative][Instrumental]        (▶) той
                         (plural) [Instrumental]   (▶) те́ми
                    ⓘ marks distance/contrast, …

ENGLISH SIDE — FRONT                                   BACK
that (one) / that (over there) (pointing at something farther)      ( ▶ )
               (plural) [Dative]                                     тем
        (masculine / neuter) [Instrumental]                (the same three lines, then ⓘ)
```

### того́ (тот)

The Russian side front is `( ▶ )` того́. The back:
- the gloss line, bare;
- the rows `(masculine / neuter) [Genitive]` and `(masculine, living) [Accusative]`;
- 6 lines:
  - `(feminine) [Genitive] (▶) той`;
  - `(plural) [Genitive] · (plural, living) [Accusative] (▶) тех` (one line per word, titled by every shared case);
  - `(masculine, not living) [Accusative] (▶) тот`;
  - `(neuter) [Accusative] (▶) то`;
  - `(feminine) [Accusative] (▶) ту`;
  - `(plural, not living) [Accusative] (▶) те`.
- ⓘ.

The English side front is the gloss and the two rows. The back is `( ▶ )` того́, the lines, ⓘ.

### тех (тот)

The rows are `(plural) [Genitive][Prepositional]` and `(plural, living) [Accusative]`. 7 lines:
- `(masculine / neuter) [Genitive] · (masculine, living) [Accusative]` того́;
- `(feminine) [Genitive][Prepositional]` той;
- `(masculine / neuter) [Prepositional]` том;
- `(masculine, not living) [Accusative]` тот;
- `(neuter) [Accusative]` то;
- `(feminine) [Accusative]` ту;
- `(plural, not living) [Accusative]` те.

The front/back split is the same as above.

### той (тот): one group, so the exact verb shape

```
RUSSIAN SIDE — FRONT         BACK
      ( ▶ )  ← clip: той     that (one) / that (over there) (feminine) (pointing at something farther)
       той                         [Genitive][Dative][Instrumental][Prepositional]
                    (masculine / neuter) [Genitive]                (▶) того́
                     (plural) [Genitive][Prepositional]           (▶) тех
                    (masculine / neuter) [Dative]                  (▶) тому́
                (plural) [Dative] · (masculine / neuter) [Instrumental] (▶) тем
                           (plural) [Instrumental]                (▶) те́ми
                    (masculine / neuter) [Prepositional]           (▶) том
                    ⓘ …
ENGLISH SIDE — FRONT: that (one) / that (over there) (feminine) (pointing at something farther)
                      [Genitive][Dative][Instrumental][Prepositional]
               BACK:  ( ▶ ) той, the same lines, ⓘ
```

### меня́ (я): no tag, two pills, no lines

- Russian: the front is `( ▶ )` меня́. The back is `I`, `[Genitive][Accusative]`, `ⓘ fully suppletive oblique stem (мен-/мн-)`.
- English: the front is `I` and `[Genitive][Accusative]`. The back is `( ▶ )` меня́, ⓘ.
- The other two я pairs are мне `[Dative][Prepositional]` and мной `[Instrumental]`.

### его́ (он): the personal form; the possessive его note is separate and untouched

- Russian: the front is `( ▶ )` его́. The back is `he / it (without a preposition) (masculine)`, with the grey tag before the grey English cue, then `[Genitive][Accusative]`, then the line `(after a preposition) [Genitive][Accusative] (▶) него́`, then `ⓘ the н- prefix appears after any preposition (у него́, к нему́)`.
- English: the front is the same gloss line and `[Genitive][Accusative]`. The back is `( ▶ )` его́, the line, ⓘ.

### мои́ми (мой) and кото́рой (который)

- **мои́ми.**
  - Russian: the front is `( ▶ )` мои́ми. The back is `my / mine (plural)` [brown], then `[Instrumental]`, then the lines `(masculine / neuter) [Instrumental] (▶) мои́м` and `(feminine) [Instrumental] (▶) мое́й`, then ⓘ.
  - English: the front is `my / mine (plural)` and `[Instrumental]`. The back is `( ▶ )` мои́ми, the same lines, ⓘ.
- **кото́рой.**
  - Russian: the front is `( ▶ )` кото́рой. The back is `which / who / that (feminine) (refers back to a noun)`, then `[Genitive][Dative][Instrumental][Prepositional]`, then 6 lines: кото́рого, кото́рых, кото́рому, кото́рым, кото́рыми, кото́ром, each titled by its shared case rows. Then ⓘ.
  - English: the front is the gloss with `(feminine)` and the 4 pills. The back is `( ▶ )` кото́рой, the lines, ⓘ.

### Word cards

**тот card 1 / card 2**
```
CARD 1 FRONT     CARD 1 BACK                                         CARD 2 FRONT = gloss + rows
   ( ▶ )         that (one) / that (over there) (pointing at …)      CARD 2 BACK = ( ▶ ) тот, lines,
    тот                     (masculine) [Nominative]                              details, ⓘ, Examples
                    (masculine, not living) [Accusative]
                          (feminine) [Nominative] (▶) та
                            (neuter) [Nominative] (▶) то
                            (plural) [Nominative] (▶) те
                 Pronoun Type  demonstrative
                 ⓘ marks distance/contrast, …
```

**который card 2.** Before: the live back overflows to 581 px with `Gender Forms  который / которая / которое / которые (m/f/n/pl)`. After, the front is the gloss line `which / who / that (refers back to a noun)`, then `(masculine) [Nominative]` and `(masculine, not living) [Accusative]`. The back is `( ▶ )` который, then the lines `(feminine) [Nominative] (▶) кото́рая`, `(neuter) [Nominative] (▶) кото́рое` and `(plural) [Nominative] (▶) кото́рые`, then ⓘ and Examples. There is no Pronoun Type row, since which is hidden for который today.

**какой card 2 front.** `which / what kind of / what a (asking about qualities)`, then three rows: `(masculine) [Nominative]`, `(masculine, not living) [Accusative]` and `(feminine) [Genitive][Dative][Instrumental][Prepositional]`.

**что card 2 front.** `what (asking about a thing)`, then `[Nominative][Accusative]`.

**я card 2.** The front is `I` with `[Nominative]`. The back is `( ▶ )` я, `Pronoun Type  personal (1st sg.)`, ⓘ. The `Gender Forms  —` row is gone.

**его card 1 / card 2**
```
CARD 1 FRONT   CARD 1 BACK                                   CARD 2 FRONT
  ( ▶ )        his / its (never changes)   ← slate tag       his / its (never changes)
   его         Pronoun Type  possessive (3rd sg. m./n.,      CARD 2 BACK: ( ▶ ) его, details,
                             indeclinable)  ← now wraps                    ⓘ, Examples
               ⓘ As a possessive it never changes form: …
```
её and их read the same way.

## Stack & MAJOR versions

- Python `>=3.11` (`libs/python/anki-tools/pyproject.toml`), in a uv workspace with `uv.lock` at the repo root.
- `anki` **26.8.1** (`/home/icarus64/repos/daedalus-mono/uv.lock:239–240`). It is used via:
  - `Collection`;
  - `col.models.add_field` / `remove_field` / `reposition_field` / `update_dict`;
  - `col.sched.set_due_date`;
  - `col.remove_cards_and_orphaned_notes` (confirmed present in the installed 26.8.1 by the plan review, `anki/collection.py:627`);
  - `col.sync_collection`, `col.full_upload_or_download`, `SyncAuth`.
- `playwright==1.61.0` (WebKit) and `pytest` (`pyproject.toml:27`).
- ElevenLabs via `requests`, model `eleven_turbo_v2_5`.
- `ffmpeg` and Anki desktop.
- Scripts: `pnpm run test` → `py-test`, `pnpm run lint` → `py-lint` (`package.json`).

## Conventions to enforce (hard constraints)

- **Frozen text.** Never change Translation, English Distinction, Russian Distinction, Additional Info, Examples, Pronoun Type, Rank, Stress or Audio. The migration writes only the new derived fields, and 5.3 compares the rest byte for byte.
- **No cue edits and no grammar jargon on cards.** Template and derived strings never contain "indeclinable", "nominative case" prose or examples. Case names appear only as pills.
- **Pills only for case names; tags only for gender, number, animacy and preposition** (the user's 11-22-26 rule).
- **`что (pronoun)`** (GUID `gJ6S@(5[xc`) remains, with its 4 form pairs.
- **One form per field, one single-word clip per form.** The gap-check expects one word for every pronoun clip, whatever the filename.
- **Card text is approved first:** at the plan gate, then at 4.2, before any live write.
- **Existing cards.**
  - Exactly the 243 snapshot form cards are removed. No other card is removed.
  - The 60 word cards keep id, nid, ord, did, type, queue, due, ivl, flags and revlog.
- **Sync discipline.**
  - Phone-synced confirmation first.
  - Pull → back up → `pkill -x anki`.
  - Full upload via the API.
  - `anki_sync.sync(names)` for media.
  - Pending = 0 from a fresh copy.
  - Never hand the one-way dialog to the user; the phone then chooses Download.
- **Delete the old path.** None of these survive: the 44 case-slot note fields, `Gender Forms` (pronouns), `#case-form`, `pill_block(trailing=…)`, the one-sided `_pronoun_case_template`, `PRONOUN_CARD_ENTRIES` as a card map. No shims, no versioned names.
- **Minimal code comments.** `check-diff-hygiene.sh` runs at builder teardown.
- **Lint and format green.** The smart-lint hook fires repo-wide, so route bulk edits through Bash and restore collateral. Pre-existing debt is out of scope.
- **Lanes never run git state commands** (`checkout`, `restore`, `stash`, `reset`) in the shared worktree.
- **Git.**
  - Name staged paths; never `git add -A`.
  - No attribution trailers of any kind: no `Co-Authored-By`, no `Claude-Session`, no session URL.
  - Land by local ff-merge of `bug/mol-deskat` into `main`, and push `main` on the user's yes. No PR (`/home/icarus64/repos/daedalus-mono/CLAUDE.md`).
- **Pure modules stay Anki-free:** `mutable_words_plan.py`, `case_pill.py`, `phrase_words.py`.
- **Re-rolls** go through `anki-word-audio --replace` / `anki-flagged-audio --fix`. A pink flag means the female audio is bad; a blue flag means the male audio is bad.

## Phase 1: Source data

### 1.1: pronouns.tsv: nominative slot columns, the five adjective-like declensions, drop Gender Forms
- **File scope:** `libs/python/anki-tools/anki_tools/data/russian-vocabulary/pronouns.tsv`, `libs/python/anki-tools/tests/test_vocabulary_data.py`.
- **Change.**
  - Remove `Gender Forms` (D1).
  - Insert `Nominative f.`, `Nominative n.` and `Nominative pl.` before `Genitive`.
  - Fill the 42 nominative cells and the 90 oblique cells exactly as in Appendix B.
  - Every other cell stays byte-identical.
- **Pattern to follow:** the `83b8aef` TSV rewrite (`csv.DictReader`/`DictWriter`, tab, `lineterminator="\n"`).
- **Acceptance:**
  - 33 columns and 31 lines.
  - **375** filled slot cells (`test_vocabulary_data.py:368`, previously 243).
  - The `("pronouns.tsv","Gender Forms"): 12` entry (`:151`) is removed.
  - No cell contains a space, `/` or `,`.
  - The 25 non-adjective-like rows' pre-existing columns diff empty against `83b8aef`.
- **Test oracle:** `new contract tests`. Spot-check тот `Nominative f.`=та, который `Genitive f.`=кото́рой, какой `Instrumental pl.`=каки́ми, самый `Genitive`=са́мого.

## Phase 2: Pronoun note-type core

### 2.1: Distinct-word derivation: form slots, tags, case rows, homograph audio words, 56 fields
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py` (slot, field, row and parser sections: `:44–200`, `:473–540`, `:780–820`), `libs/python/anki-tools/tests/test_mutable_words_plan.py`, `libs/python/anki-tools/tests/test_mutable_words.py` (pronoun fixtures, `:405–455`).
- **Change.**
  - `PRONOUN_SLOTS` gains the 3 nominative slots (case `Nominative`). These keep the per-cell qualifier, role and case. Add the primary-slot qualifier logic, which today lives in `_PRIMARY_QUALIFIERS`, as data on the derived cells:
    - a gendered primary is `masculine / neuter`, or `masculine, not living` for the Accusative;
    - он-family primaries are `without a preposition`;
    - single-form cells have no qualifier;
    - the headword's nominative is `masculine` for gendered pronouns.
  - `PRONOUN_FORM_SLOTS = 11`, and `PRONOUN_NOTE_FORM_FIELDS = ("Form 1", …, "Form 11")`, exported for `phrase_words` (3.1).
  - `PronounRow.forms()` returns the ordered distinct words. Each has its stressed text, audio word, case rows `[(qualifier|None, role|None, [cases])]`, and the cells it covers. `PronounRow.base_rows()` returns the base case rows.
  - Rendering helpers emit `Form k Tag` (only when there is exactly one row and it has a qualifier) and `Form k Cases` (`div.case-row[data-cases][data-qual]` > optional tag span + pill spans). **When `Form k Tag` is filled, the single row in `Form k Cases` has no tag span.** A tag span appears in `Form k Cases` only when there are two or more rows. `Base Tag`/`Base Cases` follow the same rule.
  - `FIELD_NAMES["Pronouns"]` = the 10 base fields + `Base Tag` + `Base Cases` + for k in 1..11 (`Form k`, `Audio Form k`, `Form k Tag`, `Form k Cases`) = **56**.
  - **Homograph audio words:** самый's са́мого/са́мой/са́мому/са́мом map to `самого-самый` / `самой-самый` / `самому-самый` / `самом-самый`. Everything else is `bare_form`.
  - Delete `PRONOUN_CARD_ENTRIES`, `PRONOUN_CARD_SLOTS`, `PRONOUN_FORM_AUDIO_FIELDS` and the 44 slot names from `FIELD_NAMES`. `PRONOUN_FORM_FIELDS` remains only as the TSV column list.
- **Pattern to follow:** `PronounRow.fields()` (`:520–536`), `audio_field_value`.
- **Acceptance:**
  - 56 fields, aligned with `row.fields()`.
  - Distinct-word counts per pronoun equal Appendix A (205 in all), and the max is 11.
  - A synthetic row with 12 forms raises.
  - The rows equal the "Case rows" table for тем, того́, тех, той, меня́, его́, то and те.
  - **No duplicate tag:**
    - той: `Form k Tag` = `(feminine)`, and its `Form k Cases` contains pill spans and no `.aspect` span;
    - тем: `Form k Tag` is empty, and `Form k Cases` has 2 rows, each with its tag;
    - тот base: `Base Tag` is empty, with 2 rows;
    - я base: no tag anywhere;
    - a property test over every real row: for each form, `Form k Tag` is non-empty if and only if `Form k Cases` has exactly one row and that row has no tag span. The rendered text of each side contains each tag string at most once per row.
  - Base rows equal the word-card table, including себя (no Nominative) and какой (3 rows).
  - Only его/её/их have an empty `Form 1`.
  - самый `Audio Form k` for са́мого references `самого-самый_{f1,m2}.mp3`, and сам's самого́ references `самого_*`.
  - Derivation: **470** pronoun cards (`test_mutable_words_plan.py:174`) and **3328** in total (`:183`).
- **Test oracle:** `new contract tests` (derivation, grouping, tags, rows); `existing suite` for the counts.

### 2.2: Russian-side and English-side form templates in the verb card 3/4 shape
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py` (template section `:1300–1448`), `libs/python/anki-tools/anki_tools/case_pill.py`, `libs/python/anki-tools/tests/test_card_layout.py` (form-card cases), `libs/python/anki-tools/tests/test_card_dedup.py`, `libs/python/anki-tools/tests/test_case_pill.py`.
- **Change.**
  - `build_template("Pronouns", i)` for i in 2..23 returns `_pronoun_form_template(k, side)`, with k = i − 1 (Russian) or i − 12 (English), using the layouts above.
  - `_translation_div` takes an optional tag-HTML argument, which is `{{Form k Tag}}` here. One function serves verbs and pronouns.
  - Counterpart lines follow D11-A: a line block per other slot j plus the headword line, hidden; the side script reveals and titles the case-sharing ones from the `data-cases`/`data-qual` of the rows.
  - Delete `pill_block`'s `trailing` argument, `#case-form` and the one-sided template.
- **Pattern to follow:** the Verbs branch of `build_template` (`:1238–1300`).
- **Acceptance:**
  - 22 form templates, each wrapped in `{{#Form k}}`.
  - Russian qfmt has `{{Audio Form k}}` and `id="russian"` and no `id="translation"`. English qfmt has `id="translation"` and `{{Form k Cases}}` and no audio.
  - No duplicate ids per side (`test_no_duplicate_ids_or_addtitle_per_side`; `SHEET_CARD_COUNTS["Pronouns"]` stays 24 and sides stay 72).
  - Headless renders of the real rows show, for тем, exactly the lines тому́/той/те́ми with the titles in the mockup. For меня́ there are no lines.
  - No `case-form` or "indeclinable" in any template.
  - `test_card_dedup.PRONOUN_CASE_CARDS` → **410**.
- **Test oracle:** `new contract tests` (structure per side, tag and pill placement, line reveal); `existing suite` (dedup, no-av, centring).

### 2.3: Word cards 1–2 on the verb card 1/2 shape: base pills, "(never changes)", nominative lines
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py` (generic word-card branch), `libs/python/anki-tools/tests/test_card_layout.py` (word-card cases; same lane as 2.2).
- **Change.**
  - For Pronouns ords 0/1, add `{{Base Tag}}` in the `_translation_div` tag slot.
  - Add `(never changes)` in `{{^Form 1}}…{{/Form 1}}` (D8).
  - Add `.case-pills` with `{{Base Cases}}` and the nominative counterpart lines (words whose rows include Nominative).
  - Place them in verb card 1/2 region order: card 1 back is translation, pills, lines, details, standalone; card 2 back is audio, russian, lines, details, standalone.
- **Pattern to follow:** the verb `aspect_div` / `has_case` handling (`:1251–1290`).
- **Acceptance:**
  - тот shows rows `(masculine) [Nominative]` and `(masculine, not living) [Accusative]`, plus the lines та/то/те.
  - его shows `(never changes)` and no pills or lines.
  - я shows `[Nominative]` only. себя shows `[Genitive][Accusative]`.
  - No `Gender Forms` row.
  - Region order equals verb cards 1/2.
- **Test oracle:** `new contract tests`.

### 2.4: Pronoun CSS: case rows, verb-identical lines, details-grid overflow fix, delete the old CSS
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_plan.py` (`_FORM_ROLE_COLOURS`, `PRONOUN_CASE_CSS` → `PRONOUN_FORM_CSS`, `_build_extra_css`), `libs/python/anki-tools/tests/test_card_layout.py` (overflow sweep).
- **Change.**
  - `.case-row`: a centred line, with every `.case-pill` inside it visible.
  - The `fixed` role colour (D8).
  - Keep the `.form-line` rules, copied from `_ASPECT_LINE_CSS`. Hidden lines use the `hidden` attribute.
  - Remove `#case-form`.
  - **Fix `#details`** so values wrap: `grid-template-columns: max-content minmax(0, auto)`, or an equivalent the sweep proves.
  - Record the `83b8aef` `PRONOUN_CASE_CSS` and details-block text in the run dir, for the 4.2 script's exact-text replace.
- **Pattern to follow:** `_ASPECT_COLOUR_CSS` / `_ASPECT_LINE_CSS` (`:975–1031`).
- **Acceptance:**
  - At 390 px, every pronoun card side for every real row has no element whose right edge exceeds the viewport.
  - A screenshot of verb делать/сделать cards 1–4 is unchanged.
- **Test oracle:** `new contract tests` (sweep); `equivalence check` (verb renders).

### 2.5: Build wiring in mutable_words.py
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words.py`.
- **Change.**
  - `TEMPLATE_COUNTS_BY_SHEET["Pronouns"]` (`:47`) = `2 + 2 * PRONOUN_FORM_SLOTS` = 24.
  - `_AUDIO_FIELD_NAMES` = `Audio` + the 11 `Audio Form k`.
  - The CSS assembly picks up the renamed block.
- **Pattern to follow:** the `css_parts` assembly (`:80–91`).
- **Acceptance:** a scratch build gives 56 fields, 24 templates and 470 pronoun cards. `attach_media` includes `та_f1.mp3` and `самого-самый_m2.mp3`.
- **Test oracle:** `existing suite`.

## Phase 3: Dependent tooling

### 3.1: Census, fill, phrase and drift tooling read the TSV slot cells, not note fields
- **File scope:** `libs/python/anki-tools/anki_tools/form_census.py`, `libs/python/anki-tools/anki_tools/form_fill.py`, `libs/python/anki-tools/anki_tools/phrase_words.py`, `libs/python/anki-tools/anki_tools/source_drift.py`, and the tests `tests/test_form_census.py`, `tests/test_form_fill.py`, `tests/test_phrase_words.py`, `tests/test_source_drift.py`, `tests/test_source_drift_cli.py`.
- **Change.**
  - `form_census.INFLECTION_FIELDS["Pronouns"]` yields no cells, since Gender Forms is gone.
  - Drop the Pronouns Gender Forms test entries (`test_form_census.py:105, 250, 262, 819`; `test_form_fill.py:493`).
  - **`phrase_words` mechanism.** `taught_word(note_id, field_names, fields)` (`phrase_words.py:232–260`) is a pure function over one note's fields that reads `INFLECTION_FIELDS` (`:58–72`). Replace the `*PRONOUN_FORM_FIELDS` entry (the 44 note fields being deleted) with `*PRONOUN_NOTE_FORM_FIELDS`. That is `("Form 1", …, "Form 11")`, exported by the pure `mutable_words_plan` (2.1). The headword still comes from `HEADWORD_FIELDS` (`Russian`). No other note type has `Form k` fields. Stress is stripped by the module's existing `STRESS_MARKS` handling.
  - `source_drift` compares all 56 derived fields. `test_source_drift.py:277` changes from 55 to **56**.
- **Pattern to follow:** the `83b8aef` Oblique Forms retirement in the same files.
- **Acceptance:**
  - `"Gender Forms"` appears only in Numerals paths, with a positive control at `83b8aef`.
  - A phrase containing `кото́рой` or `та` resolves to its pronoun. A new test builds a pronoun note with the 56-field schema and asserts that `taught_word` matches `Form 3`. With `Form k` removed from `INFLECTION_FIELDS` the test fails, which is the positive control.
  - A grep for `PRONOUN_FORM_FIELDS` in `phrase_words.py` returns nothing.
  - Zero drift for a collection built from the same rows.
- **Test oracle:** `existing suite` (updated) + `new contract tests` (surface resolution, field set).

### 3.2: Audio CLIs: new words, stressed spoken text for homographs, form-slot-aware flags
- **File scope:** `libs/python/anki-tools/anki_tools/mutable_words_audio.py`, `libs/python/anki-tools/anki_tools/flagged_audio_cli.py`, `libs/python/anki-tools/anki_tools/audio_naming.py`, `libs/python/anki-tools/tests/test_mutable_words_audio.py`, `libs/python/anki-tools/tests/test_flagged_audio_cli.py`, `libs/python/anki-tools/tests/test_audio_naming.py`.
- **Change.**
  - `load_base_words` uses `row.audio_words`, which now comes from the derived forms.
  - Add `SPOKEN_TEXT_OVERRIDES` for `самого-самый` → `са́мого`, and likewise for самой, самому and самом.
  - `flagged_audio_cli.scan` (`:84–86`) resolves Pronouns ord 2..12 to `Form (ord − 1)` and ord 13..23 to `Form (ord − 12)`, reading that slot's audio word.
- **Pattern to follow:** `SPOKEN_TEXT_OVERRIDES` (`audio_naming.py:120–131`), `scan` (`flagged_audio_cli.py:71–94`).
- **Acceptance:**
  - Audio words and pairs go from 1603 / 3206 to **1664 / 3328** (expected, re-derived independently, `test_mutable_words_audio.py:129, 156, 224`).
  - `spoken_text_for("самого-самый") == "Са́мого."`
  - A flagged тот English card resolves to its own form word. Under canonical order тот's Form 8 is тем, so ord 20 resolves to `[тем]`.
  - A flagged ord 0 still resolves to the headword.
- **Test oracle:** `new contract tests`.

## Phase 4: Integration and sign-off

### 4.1: Cross-lane count updates and a fully green suite
- **File scope:** `libs/python/anki-tools/tests/test_mutable_words_e2e.py`, plus any test failing only on a schema-derived count. Each is named in the exit report.
- **Count table** (current values verified in `tests/` at `83b8aef`; new values re-derived by the builder):

| Assertion | Now | After |
|---|---|---|
| pronoun cards (`test_mutable_words_plan.py:174`, e2e `:61`) | 303 | **470** |
| all mutable cards (`test_mutable_words_plan.py:183`, e2e `:114`) | 3161 | **3328** |
| form cards (`test_card_dedup.py:515`) | 243 | **410** |
| pronoun templates (`test_card_layout.py:127, 286, 340, 350`) | 24 | 24 (ord meaning changes; `CASE_ORDS` becomes "form ords") |
| template sides (`test_mutable_words_plan.py:231`) | 72 | 72 |
| `FIELD_NAMES["Pronouns"]` (`test_mutable_words_plan.py:1409, 1426`; `test_source_drift.py:277`) | 55 | **56** |
| pronouns.tsv columns / lines | 31 / 31 | **33** / 31 |
| filled slot cells (`test_vocabulary_data.py:368`) | 243 | **375** |
| audio words / pairs | 1603 / 3206 | **1664 / 3328** (expected) |
| e2e dry-run total (`:326`) | 3206 | **3328** (expected) |
| predicted filenames (e2e `:286`) | 3180 | re-derived (expected +122) |

- **Acceptance:**
  - `pnpm run test` and `pnpm run lint` are fully green, with output in the exit report.
  - Package-wide dangling-reference greps for `case-form`, `trailing=`, `PRONOUN_CARD_SLOTS`, `Audio Genitive`, pronoun `Gender Forms` and `indeclinable` in templates, each with a positive control at `83b8aef`.
- **Test oracle:** `existing suite`.

### 4.2: Apply script, render previews of real templates on a copy, user sign-off
- **File scope:** run dir only: `<worktree>/.artifacts/apply_pronoun_sides.py` (authored here, reused unchanged in 5.3/5.4), `<worktree>/.artifacts/render_preview.py`, `<worktree>/.artifacts/preview/`.
- **Change.**
  - Author the script per 5.3. It needs an explicit path and `--live` for the live file. There is no mode flag; D10 = B is the only path.
  - Run it on a fresh scratch copy and render with `card.question()`/`card.answer()` in light mode at 390 px. Both sides of:
    - тот тем, того́, тех, той;
    - я меня́;
    - он его́ and него́ (after a preposition);
    - мой мои́ми;
    - который кото́рой;
    - тот та.
  - Word cards 1 and 2 of который, тот, я, его, что, какой.
  - Verb делать/сделать cards 1–4 from the same harness.
  - Show the user the PNGs and the extracted text.
- **Acceptance:**
  - The rendered text equals the approved mockups with the decided options.
  - The 390 px overflow sweep over every pronoun card is clean.
  - **The user explicitly approves.** Phase 5 does not start without it.
- **Test oracle:** `equivalence check` + human sign-off.

## Phase 5: Live collection migration

All of Phase 5 runs in the main session, never in a builder. Every step is confirmed and runs in the foreground. Scripts stay in the run dir and are never committed.

### 5.1: Pre-flight: phone synced, pull, backup, close Anki, snapshot
- **File scope:** the live Anki profile (read/sync only); the run dir.
- **Steps.**
  1. Explain that this forces a one-way full upload, and get explicit confirmation that the phone has synced with nothing unsynced.
  2. Pull: launch Anki detached (`setsid nohup anki >/dev/null 2>&1 </dev/null & disown`), let it sync, then close it.
  3. `pkill -x anki`, then confirm `pgrep -x anki` is empty.
  4. Back up to `~/anki-backups/collection-before-pronoun-sides-<timestamp>.anki2` (plus a non-empty `-wal`), and confirm `PRAGMA integrity_check` = `ok`.
  5. Snapshot every pronoun card `(id, nid, ord, did, type, queue, due, ivl, flags)`, every note's fields, the note type JSON and today. Also snapshot the 243 form-card ids to remove, and the revlog types on those ids, which must all be type 4.
- **Acceptance:**
  - Integrity is `ok`.
  - 30 notes, 303 cards and 243 form cards. Any form card with real-review revlog rows (types 0–3) is listed **as information only**. The run continues, and all 243 are deleted regardless. Other drift is reported, and the snapshot becomes the truth.
- **Test oracle:** `equivalence check`.

### 5.2: Generate new-word audio, gap-check every pronoun clip, user listens to the homographs
- **File scope:** the Anki media dir; the run dir.
- **Steps.**
  1. `uv run anki-mutable-words-audio --sheet Pronouns --dry-run`. Expect 61 words / 122 requests, and explain any difference.
  2. Get the user's yes for the request count.
  3. Run it with the repo `.env` key (`set -a; . ./.env; set +a`).
  4. Validate the gap-checker on a known-bad take. The logic is `gapcheck.py`'s (`silencedetect=n=-35dB:d=0.15`, a silence starting after 0.03 s with more than 0.12 s of audio after it), with an **expected word count of 1 for every pronoun clip**.
  5. Gap-check every clip referenced by any pronoun `Audio` / `Audio Form k`, both voices.
  6. Re-roll broken clips via `uv run anki-word-audio --mode single --replace --no-sync -- <word>` until none are broken.
  7. **Listening check.** Play these clips, both voices, to the user, and re-roll any with the wrong word or stress:
     - the 8 homograph clips (сам's самого/самой/самому/самом and самый's `…-самый`);
     - **every pronoun form clip that predates this run and is also referenced by a non-pronoun note**: всего, всё, ничего, то, чем, это. That list came from a probe over all non-pronoun notes' `src="…"` and `[sound:…]` references on the 11-22-26 copy; 5.1 re-runs the probe on the snapshot, and the live result replaces this list. `то` was recorded for the particle "-то".

     If ElevenLabs ignores U+0301, stop for a decision.
- **Acceptance:** every clip exists for f1 and m2; `broken 0`, with the control reported broken; the user has confirmed every clip on the listening list.
- **Test oracle:** `equivalence check` + listening check.

### 5.3: Dry run the apply script on a post-pull copy
- **File scope:** a fresh copy of the post-5.1 collection; the run dir. `apply_pronoun_sides.py` is unchanged from 4.2. Fixes go into the same file and are re-run on a new copy.
- **The script, in order:**
  1. Unconditionally remove every pronoun card with ord ≥ 2, which is all 243 snapshot form cards whatever their review history, with `col.remove_cards_and_orphaned_notes`. Before removing, assert that the id set equals the snapshot's and that it contains no ord 0–1 card. Afterwards, the only pronoun cards left from before are the 60 word cards.
  2. Add the 46 new fields (`Base Tag`, `Base Cases`, 4 × 11 form fields).
  3. Set all 24 templates to `word_qualifier.add_qualifier_script(build_template("Pronouns", i))`.
  4. Replace the recorded pronoun CSS and details blocks by exact text, asserting each occurs once.
  5. `update_dict`.
  6. Write the derived fields per note by GUID, by name. Anki generates the form cards.
  7. Remove the 45 old fields (44 case slots + `Gender Forms`), reposition to `FIELD_NAMES` order, and `update_dict`.
  8. Assert exactly 410 new form cards exist. A shortfall stops the script; it never retries silently.
  9. Date the 410 `queue=0` pronoun cards in D3 order with `set_due_date([cid], str(k))`, k = 1, 2, … 410, relative to `col.sched.today` at run time.
  10. Touch nothing else.
- **Acceptance** (asserted by the script, with the output saved):
  - 56 fields equal to `FIELD_NAMES["Pronouns"]`, and 24 templates equal to the repo output.
  - Every frozen field of all 30 notes is byte-identical.
  - **The 60 word cards keep id, nid, ord, did, type, queue, due, ivl, flags and revlog rows.**
  - None of the 243 removed ids exists.
  - **470 pronoun cards.** Per ord 2–12 and 13–23: 27, 27, 26, 22, 17, 17, 16, 14, 14, 14, 11.
  - **410 new form cards**, all `type=2 queue=2`, on days today+1 … today+410, one per day, in D3 order: each Russian side is immediately followed by its English side, grouped by pronoun.
  - Each new card's `did` equals its note's word-card `did`. There are 0 `queue=0` cards for these notes collection-wide.
  - что has 4 form pairs.
  - Every referenced audio file exists, and `col.media.check()` reports 0 missing for them.
  - The 4.2 renders equal the approved text.
  - `anki-counterpart-due "Languages::Russian"` shows 0 for the pronoun deck.
- **Test oracle:** `equivalence check`.

### 5.4: Apply to the live collection
- **File scope:** the live `collection.anki2`.
- **Steps.** Confirm `pgrep -x anki` is empty, run the identical script with `--live`, and re-run every 5.3 assertion.
- **Acceptance:** the 5.3 assertions pass on the live file.
- **Test oracle:** `equivalence check`.

### 5.5: Full upload, media sync, verify zero pending, phone Download
- **File scope:** the live profile; AnkiWeb.
- **Steps.**
  1. Read `syncKey`/`currentSyncUrl` for `User 1` from `prefs21.db`.
  2. `col.sync_collection(SyncAuth(...), False)`. On a full-sync requirement: `close_for_full_sync()` → `full_upload_or_download(..., upload=True)` → `reopen(after_full_sync=True)`.
  3. `anki_sync.sync(<generated or re-rolled names>)`.
  4. On a fresh copy, confirm `usn=-1` = 0 for notes, cards, revlog and graves.
  5. Tell the user to choose **Download** on the phone and to open one Russian-side and one English-side pronoun card.
- **Acceptance:** pending = 0, the media sync succeeded, and the phone renders.
- **Test oracle:** `equivalence check`.

## Phase 6: Record

### 6.1: Docs, changelog commit, local ff-merge to main
- **File scope:** `docs/libs/python/anki-tools/mutable-words.md` and `docs/libs/python/anki-tools/mutable-words-runbook.md` (pronoun sections, via `documenter` → `document-local`); the branch commit of the lane changes.
- **Change.**
  - Document the per-distinct-word card unit, the 11 form slots and derived fields, the ord map (Russian 2–12, English 13–23), case rows, word cards, `(never changes)`, the palette, the dating, and the homograph audio. Update in place.
  - Commit named paths with no attribution trailers.
  - Ff-merge into `main` locally, and push only on the user's yes. No PR.
- **Acceptance:** the docs match what shipped, and the syllabus is ticked at Record.
- **Test oracle:** `existing suite`.

## Risks, open questions, decision points

### Decided (11-22-26)

The user decided the card unit, the pill/tag rule, the base-word handling and D10 explicitly. They accepted every other decision at the recommended option, and they approve the rendered previews (4.2) before any live write.

- **Card unit:** one pair per distinct word.
- **Pill/tag rule:** case names are pills; gender, number, animacy and preposition are coloured tags.
- **Base-word cells** go on the word cards. **"(never changes)"** for его/её/их.
- **D1:** drop the pronoun `Gender Forms` field.
- **D3:** grouped by pronoun, each Russian side followed the next day by its English side, starting today+1.
- **D4:** separate stressed clips for самый's four homographs, and a listening check (5.2 step 7).
- **D5:** no `-ою` instrumental variants.
- **D6:** the Russian cue shows on form cards (что "(pronoun)").
- **D7:** dropped (the same-as-base note).
- **D8:** `(never changes)` in slate `#546e7a` / night `#b0bec5`.
- **D9:** one case row per qualifier under a bare gloss; a single-qualifier word keeps the exact verb shape, with the tag shown only after the gloss.
- **D9b:** the base Accusative is its own row, `(masculine, not living) [Accusative]`.
- **D10 = B:** remove all 243 one-sided form cards and create 410. The 60 word cards keep ids, history and schedule ("replace them and just keep the 60").
- **D11:** counterpart lines on form cards are the other words sharing a case, each titled by its case rows restricted to the shared cases (up to 7 lines).
- **D12:** `[Nominative]` pill on every word card whose base is nominative.

No decision is open. The user's remaining gate is visual sign-off on the 4.2 previews.

### Risks and observations

- **Horizon:** 410 days to the last form card (today+1 … today+410) at one card per day.
- **Removing 243 cards** is unconditional, by the user's decision. Any real-review history on them (none on the 11-22-26 copy) is deleted with them; 5.1 reports it beforehand as information only.
- **Unverified:** whether ElevenLabs honours U+0301 on `eleven_turbo_v2_5`. 5.2 step 7 is the gate.
- **Unverified:** the stress and word of reused clips: сам's four homographs, and the six shared with non-pronoun notes (всего, всё, ничего, то, чем, это). 5.2 step 7 is the gate.
- **Derived HTML in fields** (`Form k Tag`, `Form k Cases`, `Base …`). It is visible in the note editor and browser columns. The TSV stays the source, and `source_drift` keeps it honest.
- **Line reveal depends on JS.** Without JS no lines show, but the gloss, tags, pills and word remain correct.
- **Template size:** each form template carries 10 hidden line blocks plus the headword line. 2.2 reports the max `afmt` size.
- **Shared CSS:** the `#details` fix lives in the repo's shared `EXTRA_CSS`, while live only the pronoun sheet is migrated.
- **One-way upload:** the 5.1 step 1 phone confirmation cannot be skipped.
- **Short TTS clips** (та, то, те, вся) can be wrong in ways a gap-check cannot see. The flags + `--fix` route covers them.

## Skill mapping

| Work | Executor |
|---|---|
| 1.1, 2.1, 2.2, 2.3, 2.4, 2.5 | `builder` lane 1 |
| 3.1 | `builder` lane 2 |
| 3.2 | `builder` lane 3 |
| 4.1 | integration builder after the merge-backs |
| Code review gate | `review-code` after 4.1 |
| 4.2, Phase 5 | main session, confirmation-gated, foreground |
| 6.1 docs | `documenter` → `document-local` |
| 6.1 merge | main session: ff-merge to `main`, push on the user's yes, no PR |

**Lanes.**
- Lane 1 is serial, because everything in it shares `mutable_words_plan.py`.
- Lanes 2 and 3 start after 2.1, on disjoint file scopes. `audio_naming.py` belongs to lane 3 only.
- `test_mutable_words_e2e.py` is hoisted into 4.1.

## Appendix A — distinct non-base words per pronoun (205; one card pair each)

Each word is shown with its case rows. Tags in parentheses, cases in brackets.

| Pronoun | n | Words |
|---|---|---|
| я | 3 | меня́ [Gen][Acc] · мне [Dat][Prep] · мной [Ins] |
| ты | 3 | тебя́ [Gen][Acc] · тебе́ [Dat][Prep] · тобо́й [Ins] |
| вы | 3 | вас [Gen][Acc][Prep] · вам [Dat] · ва́ми [Ins] |
| мы | 3 | нас [Gen][Acc][Prep] · нам [Dat] · на́ми [Ins] |
| он, оно | 7 each | его́ (without a prep.) [Gen][Acc] · него́ (after a prep.) [Gen][Acc] · ему́ (without) [Dat] · нему́ (after) [Dat] · им (without) [Ins] · ним (after) [Ins] · нём [Prep] |
| она | 4 | её (without) [Gen][Acc] · неё (after) [Gen][Acc] · ей (without) [Dat][Ins] · ней (after) [Dat][Ins] · [Prep] |
| они | 6 | их (without) [Gen][Acc] · них (after) [Gen][Acc] · [Prep] · им (without) [Dat] · ним (after) [Dat] · и́ми (without) [Ins] · ни́ми (after) [Ins] |
| его, её, их | 0 | — (never changes) |
| кто | 4 | кого́ [Gen][Acc] · кому́ [Dat] · кем [Ins] · ком [Prep] |
| ничто | 4 | ничего́ [Gen] · ничему́ [Dat] · ниче́м [Ins] · ничём [Prep] |
| никто | 4 | никого́ [Gen][Acc] · никому́ [Dat] · нике́м [Ins] · нико́м [Prep] |
| что (pronoun) | 4 | чего́ [Gen] · чему́ [Dat] · чем [Ins] · чём [Prep] |
| себя | 2 | себе́ [Dat][Prep] · собо́й [Ins] |
| тот | 11 | та (f.) [Nom] · то (n.) [Nom][Acc] · те (pl.) [Nom] · (pl., not living) [Acc] · того́ (m./n.) [Gen] · (m., living) [Acc] · той (f.) [Gen][Dat][Ins][Prep] · тех (pl.) [Gen][Prep] · (pl., living) [Acc] · тому́ (m./n.) [Dat] · тем (pl.) [Dat] · (m./n.) [Ins] · ту (f.) [Acc] · те́ми (pl.) [Ins] · том (m./n.) [Prep] |
| сам, этот, мой, твой, наш, ваш, свой, весь, самый, который | 11 each | the same 11-word pattern as тот, with the forms in Appendix B and the TSV |
| какой, никакой, такой | 10 each | the тот pattern minus the f. oblique word, which equals the headword (како́й) and moves to the word cards |

Notes:
- **ё/е pairs stay distinct:** ниче́м/ничём (ничто), чем/чём (что), все/всё (весь).
- **No same-letters, different-stress pair exists within any one pronoun.**
- **Across pronouns,** сам/самый share four spellings with different stress, hence the separate clips (D4).

## Appendix B — new cells added to pronouns.tsv (132; stress marked)

**Nominative (f. · n. · pl.).** The headword is the masculine.

| Pronoun | f. | n. | pl. |
|---|---|---|---|
| сам | сама́ | само́ | са́ми |
| тот | та | то | те |
| этот | э́та | э́то | э́ти |
| мой | моя́ | моё | мои́ |
| твой | твоя́ | твоё | твои́ |
| наш | на́ша | на́ше | на́ши |
| ваш | ва́ша | ва́ше | ва́ши |
| свой | своя́ | своё | свои́ |
| весь | вся | всё | все |
| самый | са́мая | са́мое | са́мые |
| какой | кака́я | како́е | каки́е |
| который | кото́рая | кото́рое | кото́рые |
| никакой | никака́я | никако́е | никаки́е |
| такой | така́я | тако́е | таки́е |

**Oblique cells of the five adjective-like pronouns.** Order:
- Gen, Dat, Ins and Prep: m./n. · f. · pl.
- Acc: m. not living · m. living · n. · f. · pl. not living · pl. living.

| Pronoun | Genitive | Dative | Accusative | Instrumental | Prepositional |
|---|---|---|---|---|---|
| самый | са́мого · са́мой · са́мых | са́мому · са́мой · са́мым | са́мый · са́мого · са́мое · са́мую · са́мые · са́мых | са́мым · са́мой · са́мыми | са́мом · са́мой · са́мых |
| какой | како́го · како́й · каки́х | како́му · како́й · каки́м | како́й · како́го · како́е · каку́ю · каки́е · каки́х | каки́м · како́й · каки́ми | како́м · како́й · каки́х |
| который | кото́рого · кото́рой · кото́рых | кото́рому · кото́рой · кото́рым | кото́рый · кото́рого · кото́рое · кото́рую · кото́рые · кото́рых | кото́рым · кото́рой · кото́рыми | кото́ром · кото́рой · кото́рых |
| никакой | никако́го · никако́й · никаки́х | никако́му · никако́й · никаки́м | никако́й · никако́го · никако́е · никаку́ю · никаки́е · никаки́х | никаки́м · никако́й · никаки́ми | никако́м · никако́й · никаки́х |
| такой | тако́го · тако́й · таки́х | тако́му · тако́й · таки́м | тако́й · тако́го · тако́е · таку́ю · таки́е · таки́х | таки́м · тако́й · таки́ми | тако́м · тако́й · таки́х |

Review notes:
- самый keeps stem stress (са́м-), unlike end-stressed сам.
- какой, никакой and такой are velar stems: -и- in place of -ы-, with the stress on the ending.
- который is a regular hard stem stressed on -то́р-.
- `-ою` variants are omitted (D5).
