### Ask of record

**10-29-26** — "1. I'm not seeing any of the fucking changes next to any of the fucking English fields. And now because I've been studying and reviewing cards and updating some of the wording for the cards you need to pull down again and re-sync with remote again to make sure you have my latest field updates and card reviews.

2. I swear to fucking God I am so goddamn close to fucking murdering you. It is incredible. You are such a piece of fucking shit. How am I still finding fucking words in new that should have been set to due????!!!!!!!  Fuck how many fucking times am I going to have to tell you to get the goddamn words from those two fucking decks that I had you merge get all the fucking words get every fucking word that's by itself and every fucking word from a fucking phrase and send it to me do you piece of goddamn shit!!!!! why is the fucking phrase? May I take your photograph? Have words may I and photograph not said to fucking do the new immutable deck you piece of shit!?!?"

**10-29-26 — appended** — "Diagnose all the fucking issues. Make a goddamn plan for fixing all of the fucking issues and don't you dare start doing one issue and forget about the rest of what I said. Make a goddamn plan pull down from Web and start with this fucking bullshit. I am so fucking over it."

**10-29-26 — appended** — "And don't you dare just do one fucking phrase. That was a fucking example you fuck find them all."

**10-29-26 — appended** — "And make a goddamn plan that some agents can follow and run like this is a fucking /dae run!"

## Phase syllabus
- [ ] Phase 1: Sync down
  - [ ] 1.1: Pull from AnkiWeb; verify reviews and wording edits landed
- [ ] Phase 2: Make the distinction cues visible
  - [ ] 2.1: Immutable question side renders English Distinction, not Case   (lane 1)
  - [ ] 2.2: Immutable gains the Russian-side distinction div                (lane 1, after: 2.1)
  - [ ] 2.3: Cross-family render assertion, both sides, every template       (lane 1, after: 2.2)
- [ ] Phase 3: Extract every phrase word
  - [ ] 3.1: Phrase-word extractor over BOTH decks, lemma-aware              (lane 2)
  - [ ] 3.2: Audit CLI: missing / all-new / studied, with positive control    (lane 2, after: 3.1)
  - [ ] 3.3: Hand the user the complete word list                            (lane 2, after: 3.2)
- [ ] Phase 4: Nothing phrase-sourced left in new
  - [ ] 4.1: Re-runnable set-due tool, suspended-safe                        (lane 3)
- [ ] Phase 5: Verb aspect rule
  - [ ] 5.1: Perfective-side gating (DP-1 decides the rule)                  (lane 4)
- [ ] Phase 6: Add the genuinely missing words
  - [ ] 6.1: Append rows to TSV + workbook + immutable source                (lane 5, after: 3.3)
  - [ ] 6.2: Generate audio for every added word                             (lane 5, after: 6.1)
- [ ] Phase 8: Cues the user still cannot see (found by lane 1 while fixing 2.1)
  - [x] 8.1: Qualifier lives only in Russian Distinction, immutable side  (lane 5)
  - [ ] 8.2: Mutable forward card carries the Russian cue on its prompt   (lane 6)
  - [ ] 8.3: Re-key the 6 immutable e2e lookups off the qualified text    (lane 7, after: 8.1)
- [ ] Phase 7: Integration — serialized, single owner
  - [ ] 7.1: Rebuild packages, import once                                   (after: 1.1, 2.3, 6.2, 8.2, 8.3)
  - [ ] 7.2: Run set-due, aspect rule, flagged audio against the collection   (after: 7.1, 4.1, 5.1)
  - [ ] 7.3: Sync up (FULL sync, UPLOAD) and verify on remote                (after: 7.2)

## Goal & scope

**In:** the six defects measured below, all of which are regressions or
omissions from prior runs in this repo.

**Out:** `Languages::Russian::4. Sentences (lingo llama)` -- a third-party
sentence deck the user never asked about and never merged. Sweeping its 2,549
sentences would add ~290 words of unrequested vocabulary. It is named here only
so nobody re-adds it by inference; it is NOT in scope.

Also out: new vocabulary judgement beyond what the phrase deck contains;
re-wording glosses the user has since edited by hand (his edits win -- the pull
in 1.1 is what makes them visible, and no lane may overwrite a Translation it
did not add).

## Stack & MAJOR versions
- Python 3.11.7 (running interpreter)
- `anki` library, installed (`anki.collection.Collection`)
- pytest 7.4.3, ruff 0.16.2 (`pyproject.toml`, `python3 -m ruff --version`)
- openpyxl (used for the source workbook)

## Conventions to enforce
- **Minimal code comments.** Rationale belongs in docs, never inline. Tests are
  not exempt.
- **Never weaken a test assertion.** Update expected values only. Several
  existing tests carry deliberate positive controls; they stay exact.
- **Never run `git checkout`/`restore`/`stash`/`reset`/`clean`/`add`/`commit`/
  `push`.** Lanes share one working tree. A prior run destroyed four lanes'
  work this exact way. Read-only `git diff`/`status` is fine.
- **Pure logic modules + a thin CLI**, mirroring `counterpart_due.py` /
  `counterpart_due_cli.py`: the logic module imports only the standard library
  so it unit-tests without a collection; the CLI owns the `anki` import.
- **A test file is mandatory** -- a `PostToolUse` hook blocks any new
  `anki_tools/x.py` lacking `tests/test_x.py`.
- **Never write to the collection.** No lane opens the live collection for
  writing; Phase 7 is the single writer, and only after 1.1.
- **`set_due_date` silently unsuspends.** Any due-setting code must exclude
  `queue == -1` and report the count it skipped. This caused a real incident.
- Translation fields stay Cyrillic-free (enforced by `test_examples_field.py`).
- Edit the source workbook alongside any TSV change or regeneration reverts it
  (`test_full_pipeline_regenerates_byte_identical_tsvs` catches it).

## Measured facts (do NOT re-derive; measured 10-29-26 against the Oct-26 collection)

**The phrase deck ("those two decks that I had you merge" -- the consolidated
deck plus its two predecessors):**

| deck | did | notes | cards | note type |
|---|---|---|---|---|
| `Languages::Russian::5. Russian Phrases` | 1790710159549 | 38 | 76 | `Russian - Common Words (Ellis Version)` |

Fields: `Russian, Translation, Pronunciation, Part of Speech, Audio, Additional Info`.

**This deck IS the consolidation.** Its two predecessors were merged into it and
no longer exist as decks -- verified: all 38 notes of that note type live here
and the type has exactly 38 notes collection-wide, so no predecessor notes are
stranded elsewhere. The scope is these 38 notes and nothing else.

- Distinct word tokens across all 38 entries: **70**.
- Taught-word index (Mutable + Immutable, excluding `Common Words`): **1,670** surface forms.

**Card-state audit of those 70 tokens:**
| bucket | count |
|---|---|
| already taught, studied or suspended | 30 |
| taught but **ALL CARDS NEW** | **9** |
| not resolving to any taught word | 31 (tokens, un-lemmatized -- upper bound) |

- The 9 all-new words: `добро, доступ, можно, по-английски, познакомиться, приятно, сфотографировать, туалет, чек`.
  `можно` and `сфотографировать` are the user's named example from
  "Можно сфотографировать?" -- they exist and every card is new.
- The 31 is an **upper bound**: deck 5 was tokenized, not lemmatized, so
  `говорю, люблю, зовут, мне, тебя, меня, находится, нравится, понимаю, ...`
  are counted missing while their lemmas are very likely taught. 3.1 fixes this.

**Template defect (the "not seeing changes next to the English fields"):**
- `Russian - Immutable Words (Ellis Version)`, templates 0 and 1:
  `<div id="prompt-hint">{{#Case}}({{Case}}){{/Case}}</div>` -- renders **Case**,
  and neither template mentions `English Distinction` or `Russian Distinction`.
- Every Mutable type renders both correctly:
  `<div id="prompt-hint">{{#English Distinction}}({{English Distinction}}){{/English Distinction}}</div>`
  plus `<div id="russian-distinction">{{Russian Distinction}}</div>`.
- So the defect is **Immutable-only**, and it hides the cues on exactly the words
  first complained about (`о / об` vs `насчёт`, `который` vs `что`).
- Field state is fine: 1,474 notes carry both fields; **369** English cues and
  **16** Russian cues populated.

**Verbs:** 214 notes. **18** have both perfective cards review-due today; **192**
have all four cards new together. Templates: ord 0/1 imperfective, 2/3 perfective.

**Collection:** last written Oct 26 22:14 (3 days stale). revlog 324,506;
cards studied 8,065. `scm > ls`, so the next sync is a FULL sync.

## Phase detail

### 1.1 Pull from AnkiWeb  (no lane -- orchestrator, blocking)
Files: none. Run `sync_ankiweb.py` with `ANKI_SYNC_USER`/`ANKI_SYNC_PASS`.
**BLOCKED:** credentials absent from `.env`; only `ELEVENLABS_API_KEY` is set.
Reading them from Anki's prefs database is forbidden (refused as credential
exploration). Either the user adds the two vars, or he syncs in the GUI.
Acceptance: `mod == ls`; revlog strictly > 324,506; Anki not running during it.

### 2.1 Immutable question side renders English Distinction  (lane 1)
Files: `anki_tools/immutable_words.py`, `tests/test_immutable_words.py`.
Pattern: `anki_tools/prompt_hint.add_prompt_hint`, already applied by
`mutable_words_plan.build_template`. The Case cue must NOT be lost -- Case and
English Distinction are different cues and both belong on the prompt. Emit the
hint div for English Distinction and keep Case's own div.
Acceptance: both templates' config contains `{{#English Distinction}}`; `о / об`
renders "Prepositional" on the side showing its English.
Test: assert on the built template strings, both `qfmt` and `afmt`.

### 2.2 Immutable Russian-side div  (lane 1, after 2.1)
Files: same as 2.1, plus `anki_tools/prompt_hint.py` only if a helper is needed.
Mirror `russian-distinction` from `mutable_words_plan`. Acceptance:
`как (conjunction)` shows "conjunction" beside its headword.

### 2.3 Cross-family render assertion  (lane 1, after 2.2)
Files: `tests/test_immutable_words.py`, `tests/test_prompt_hint.py`.
One table-driven test over EVERY note type carrying the fields and EVERY
template ord: the side showing `{{Translation}}` also shows English Distinction;
the side showing the headword also shows Russian Distinction.
**Positive control required:** a note with an empty cue must render no stray
parentheses -- prove the conditional wrapper works, or the test passes vacuously.

### 3.1 Phrase-word extractor  (lane 2)
Files: `anki_tools/phrase_words.py`, `tests/test_phrase_words.py`.
Pure logic, standard library only. One deck shape: `Russian - Common Words`.
Tokenize the `Russian` field of each of the 38 notes, then resolve each token
against the taught index -- exact, then stress-stripped, then `ё`->`е` folded.
A token that resolves is NOT missing. Entries that are a single word and entries
that are phrases both go through the same path, which is what "every word that's
by itself and every word from a phrase" requires.
Normalization: NFC, lowercase, strip U+0301/U+0300, fold `ё`->`е`, then NFC
again. A prior run reported 32 false "missing" by skipping the re-normalization.
Acceptance: every word reported missing is a dictionary form. `говорю` must
resolve to `говорить` and not be reported.
Test: fixtures for both note shapes; a positive control proving a genuinely
absent word IS reported.

### 3.2 Audit CLI  (lane 2, after 3.1)
Files: `anki_tools/phrase_words_cli.py`, `tests/test_phrase_words_cli.py`.
Opens the collection READ-ONLY. Reports per deck: studied, all-new, part-new,
missing. Fake-collection tests as in `tests/test_flagged_audio_cli.py`.
Acceptance: run against the real collection reproduces the measured table above
(70 distinct tokens, 30 studied, 9 all-new) before lemmatization shrinks the
missing count.

### 3.3 Hand the user the list  (lane 2, after 3.2)
Deliverable: a written list of every word in the phrase deck, grouped
missing / all-new / studied, covering ALL 38 entries and every token in them --
not a sample, and not just the one phrase the user used as an example. No rows
are added before the user sees it.

### 4.1 Re-runnable set-due tool  (lane 3)
Files: `anki_tools/phrase_due.py`, `anki_tools/phrase_due_cli.py`,
`tests/test_phrase_due.py`, `tests/test_phrase_due_cli.py`.
Pattern: `counterpart_due.py` -- same shape, same suspended-exclusion rule.
Selects cards of phrase-sourced words whose every card is new, and sets them due.
MUST exclude `queue == -1` and report the skip count.
Acceptance: zero phrase-sourced words with all cards new afterwards; suspended
count unchanged. Test: table-driven over (type, queue) combinations, plus a
positive control that an all-new unsuspended word IS selected.

### 5.1 Verb aspect gating  (lane 4)
Files: `anki_tools/aspect_due.py`, `anki_tools/aspect_due_cli.py`,
`tests/test_aspect_due.py`, `tests/test_aspect_due_cli.py`.
Template ords 0/1 are imperfective, 2/3 perfective. **DP-1 below decides the
rule; do not guess.** Build the logic parameterized on the rule so either
choice is a one-line switch, and unit-test both.
Acceptance: no note has both perfective cards due on the same day.

### 6.1 / 6.2 Add missing words  (lane 5, after 3.3)
Files: `anki_tools/data/russian-vocabulary/*.tsv`, the source workbook at
`~/Downloads/russian_vocabulary.xlsx`, `tests/data/source-word-list.md`.
Immutable-class words (prepositions, conjunctions, particles, indeclinable
nouns, base adverbs) go to the markdown source; the rest to the TSVs.
Audio via `python3 -m anki_tools.word_audio` -- `--mode single` for mutable
(f1/m2), `--mode double` for immutable (f1/f2/m1/m2).
Acceptance: byte-identical pipeline test passes (workbook edited too); every
added word has its audio files present and non-empty.

### 7.1-7.3 Integration  (no lane -- single owner, serialized)
Rebuild both packages, import once with `merge_notetypes=True`,
`with_scheduling=False`, update_notes/notetypes ALWAYS. Then run set-due, the
aspect rule, and `anki-flagged-audio --fix`. Then sync up.
Acceptance: revlog and studied-card counts unchanged by the import; 0 conflicts;
remote carries the fields; `scm > ls` means the sync prompt is FULL -- choose
**UPLOAD**, never Download. Downloading is what destroyed this work on Oct 26.

### Phase 8 detail — defects lane 1 surfaced while fixing the render

**8.1 (lane 5, DONE).** `immutable_words_plan.WordRow.fields()` wrote the
qualified headword to `Russian` AND derived `Russian Distinction` from it, so 11
words rendered the qualifier twice: inline in the headword (greyed by
`word_qualifier`) and again from the new cue div. `distinction.py`'s docstring
had claimed the field "supersedes" the baked-in parenthetical; it never did on
this family. `Russian` now holds the bare word.
**GUIDs are unchanged and must stay so:** `WordRow.guid` keeps hashing the
QUALIFIED text, pinned to 11 hard-coded literals in
`tests/test_immutable_words_plan.py` and verified byte-identical by a
before/after probe. Audio filenames were never at risk --
`audio_naming.sanitize_word_slug` already calls `strip_qualifier`.
`mutable_words_plan.headword_text` has done exactly this for a while, so 8.1 is
the missed half of an established pattern, not a new invention.

**8.2 (lane 6).** Mutable FORWARD cards (Nouns/Adjectives/Adverbs/Pronouns/
Numerals ord 0; Verbs ords 0 and 2) show the headword on the QUESTION side with
no `Russian Distinction` cue, so `как` conjunction-vs-adverb and `первый`
adjective-vs-numeral stay indistinguishable on the prompt -- the user's original
complaint, unfixed on this family. The answer-side labelled detail row that
`_detail_block` already emits is a different thing and stays.

**8.3 (lane 7).** 8.1 broke 6 tests in `tests/test_immutable_words.py`: all
lookups or expected values keyed on the old qualified `Russian` text
(`find_notes('Russian:как (*)')`, a `<Russian>||<deck>` reconciliation key, and
`_EXPECTED_CUES`). Mechanical re-keying; no GUID assertion is touched. Note
`как` now yields two notes sharing the bare headword, so any dict keyed on it
must also key on `Russian Distinction` or the deck, or one sense silently
overwrites the other.

### Case vs English Distinction — ruled on, 10-29-26

Lane 1 found that 28 immutable rows carry both `Case` and `English Distinction`,
and in **13** the two strings are IDENTICAL -- including `о / об` ->
"Prepositional" in both, the very word the user first complained about. Twelve
more open the English cue with the case and continue ("Genitive; out of"), so an
unconditional Case div would repeat its first word. Only 16 prepositions have a
Case with no English cue.

**Decision:** the Case div renders only when there is no English cue
(`{{^English Distinction}}`). Unconditional divs would have printed
`(Prepositional)(Prepositional)` on the user's own example. The governed case is
never lost -- `case_field.add_case_row`'s labelled row stays on the answer side.
Reverting is one line (drop `unless_field=` in `immutable_words.py`).

## Parallel lanes

Five lanes, disjoint file scopes, all buildable and testable WITHOUT the pull
because every logic module is standard-library-only and every CLI is tested
against a fake collection.

| lane | subphases | files owned |
|---|---|---|
| 1 | 2.1, 2.2, 2.3 | `anki_tools/immutable_words.py`, `anki_tools/prompt_hint.py`, `tests/test_immutable_words.py`, `tests/test_prompt_hint.py` |
| 2 | 3.1, 3.2, 3.3 | `anki_tools/phrase_words.py`, `anki_tools/phrase_words_cli.py`, `tests/test_phrase_words.py`, `tests/test_phrase_words_cli.py` |
| 3 | 4.1 | `anki_tools/phrase_due.py`, `anki_tools/phrase_due_cli.py`, `tests/test_phrase_due.py`, `tests/test_phrase_due_cli.py` |
| 4 | 5.1 | `anki_tools/aspect_due.py`, `anki_tools/aspect_due_cli.py`, `tests/test_aspect_due.py`, `tests/test_aspect_due_cli.py` |
| 5 | 6.1, 6.2 | `anki_tools/data/russian-vocabulary/*.tsv`, the workbook, `tests/data/source-word-list.md`, `tests/test_vocabulary_data.py` |

Lanes added 10-29-26 after lane 1's findings (lane numbers continue; the data
lane above keeps its number):

| lane | subphases | files owned |
|---|---|---|
| 5 (qualifier) | 8.1 | `anki_tools/immutable_words_plan.py`, `tests/test_immutable_words_plan.py` |
| 6 | 8.2 | `anki_tools/mutable_words_plan.py`, `tests/test_mutable_words_plan.py` |
| 7 | 8.3 | `tests/test_immutable_words.py` |

**Shared touchpoints, serialized, owned by the orchestrator alone:** the live
collection (Phase 7 only), `package.json` if a new CLI needs a `bin` entry, and
`anki_tools/distinction.py` (no lane touches it).

Lane 5 is gated on 3.3 and on the user's sign-off; lanes 1-4 start immediately.

## Risks, open questions, decision points

- **DP-1 — the verb aspect rule. NEEDS THE USER.** Either
  **(a)** hold each perfective card until its imperfective counterpart has been
  studied, or **(b)** allow both aspects but never schedule the two perfective
  cards on the same day. (a) changes what is available to learn; (b) only changes
  spacing. The ask ("if a perfective side is due, only an imperfective side can
  be due") reads closer to (a), but it is not derivable with confidence, and 192
  notes have all four cards new, so the choice has wide effect. Lane 4 builds both
  and the switch is one line.
- **DP-2 — the 31 "missing" tokens.** Expected to shrink sharply once
  lemmatized: `говорю, люблю, зовут, мне, тебя, меня, находится, нравится,
  понимаю, повторите, посоветуете, значит, заблудился, ...` are inflections whose
  lemmas are very likely already taught. Whatever genuinely remains is shown to
  the user at 3.3 before any row is added.
- **Risk — a wrong sync direction wipes everything again.** Mitigated: packages
  persist on disk and `main` is pushed, so re-import is one command.
- **Risk — the user's hand-edited wording gets overwritten by an import.**
  The import updates fields from source; his Oct 27-29 Translation edits are NOT
  in the source. 1.1 must precede 7.1, and 7.1's diff must be inspected for
  Translation changes the source did not author. **This is the highest-value
  check in the plan** -- it is how his edits get destroyed.
- **Risk — adding inflected forms as headwords.** Mitigated by 3.1 before 6.1
  and by 3.3's sign-off gate.

## Skill mapping
Lanes 1-5: `builder` agents, one per lane, each handed its subphase IDs, its
file scope, and the measured facts above. Phases 1 and 7: orchestrator only --
they touch the live collection and must not run concurrently with anything.
