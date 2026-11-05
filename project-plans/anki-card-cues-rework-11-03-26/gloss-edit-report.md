# Gloss-edit report: English meaning text changed by agent commits

Subphase 2.1 of `anki-card-cues-rework-11-03-26`. Built by lane l2. This report changes no data and nothing is reverted (ask: "Do not modify them back").

## 1. Scope, method, authorship

- **Walked.** All 718 non-merge commits in the branch history; 50 of them touch a tracked source of English text: `libs/python/anki-tools/tests/data/source-word-list.md` (and its earlier path `project-plans/russian-immutable-words-08-31-26/source-word-list.md`; `46fb310` is a pure R100 rename and counts as no change), the six TSVs in `anki_tools/data/russian-vocabulary/`, `ROW_SPLITS`/`TRANSLATION_OVERRIDES` in `immutable_words_plan.py`, and `ROW_SPLITS` in `mutable_words_plan.py`.
- **Diffed.** For each such commit the English column was parsed at `<commit>^` and `<commit>` and compared per headword (md: the Russian cell; TSV: the headword cell, or imperfective/perfective for verbs; dicts: the dict key). Headwords are matched by exact text across sections and files within a commit; identity changes (`как` to `как (conjunction)`, `так` to `так (adverb)`, `правда` to `правда (noun)`) were paired by hand (section 7), because exact-headword keying hides them.
- **Classes.** `meaning`: the words outside parentheses changed, or senses were added, dropped or reworded. `parenthesis-only`: equal once parentheticals are deleted, and a parenthetical was added or removed on one side only. `parenthetical rewritten`: equal once parentheticals are deleted, and both sides have a parenthetical. `reorder-only`: same senses, different order. `separator-only`: equal once `,` `;` `<br>` `<div>` and ` / ` are treated as one separator. `row added`, `row removed/split`, `user hand-edit adopted` as in the plan. Classification is mechanical (regex on parentheses and top-level separators) and was reviewed by hand against every `meaning` and `parenthetical rewritten` row.
- **Authorship.** Every commit carries the same git author identity (`icarus64`), except three squash-merge commits whose committer is `GitHub` (`4e0bcce`, `706590b`, `4794da4`; their bodies carry `Claude-Session` trailers or describe agent lanes). Git therefore cannot say who wrote a gloss; attribution rests on commit messages. A commit is treated as a user-edit adoption only when its message says the text came from the collection or was hand-edited in Anki: `4794da4`, `85e4a42`, `52478b6`, `62b5157`. Every other commit is agent-made. The adoption commits are themselves agent-run, but the English text they write is the user's, so they are reported separately (section 8).
- **Not covered.** The workbook is untracked and has no history. The first TSV commit `92baf55` introduces the six TSVs from it, so TSV English text before that commit cannot be diffed; changes the workbook-era text underwent are invisible here. `92baf55` rows are counted as added, nothing more.

## 2. Summary

| commit | date | actor | meaning | paren. rewritten | paren.-only | reorder | separator | added | removed/split | subject |
|---|---|---|---|---|---|---|---|---|---|---|
| 6fabf2a | 2026-09-01 | agent | 0 | 0 | 0 | 0 | 0 | 156 | 0 | feat(anki-tools): Russian immutable words deck builder + ElevenLabs TT |
| 4e0bcce | 2026-09-03 | agent | 4 | 1 | 38 | 0 | 0 | 0 | 0 | fix(anki-tools): make the Immutable Words package re-importable in pla |
| 706590b | 2026-09-17 | agent | 2 | 1 | 0 | 0 | 0 | 0 | 0 | fix(anki-tools): shorten the three over-long particle glosses (#20) |
| 4794da4 | 2026-09-19 | user adoption | 11 | 0 | 1 | 2 | 0 | 0 | 4 | fix(project-plans): make the word list match the real collection (#22) |
| 8fd2ab8 | 2026-09-22 | agent | 0 | 0 | 0 | 0 | 0 | 58 | 3 | feat(anki-tools): add Base Adverbs to the Immutable Words deck |
| 85e4a42 | 2026-09-24 | user adoption | 1 | 1 | 0 | 0 | 0 | 0 | 0 | feat(anki-tools): fill Additional Info across the Immutable Words deck |
| 92baf55 | 2026-09-26 | agent | 0 | 0 | 0 | 0 | 0 | 1003 | 0 | feat(anki-tools): commit the four Russian vocabulary TSVs + README |
| 13b2b41 | 2026-09-26 | agent | 0 | 0 | 0 | 0 | 0 | 2 | 0 | feat(anki-tools): add mutable_words_plan.py Anki-free pure core |
| 50a9de0 | 2026-09-30 | agent | 0 | 0 | 0 | 0 | 0 | 138 | 0 | feat(anki-tools): add the 139 missing base words, plus Pronouns and Nu |
| 572194a | 2026-10-05 | agent | 0 | 0 | 0 | 0 | 0 | 2 | 0 | feat(anki-tools): add two adjectives and fill three short forms |
| a64f3bd | 2026-10-07 | agent | 0 | 6 | 4 | 0 | 0 | 0 | 0 | feat(anki-tools): add an Examples field and move standalone Russian ex |
| 808c0c4 | 2026-10-08 | agent | 0 | 0 | 0 | 0 | 371 | 0 | 0 | feat(anki-tools): normalize English gloss separators to a single slash |
| e0e53ba | 2026-10-10 | agent | 2 | 0 | 0 | 0 | 0 | 2 | 1 | feat(anki-tools): Russian deck polish — aspect colours, gloss port, пр |
| 7ceeac1 | 2026-10-11 | agent | 1 | 2 | 18 | 0 | 0 | 99 | 0 | feat(anki-tools): English prompts that name one word, plus 99 new word |
| 92f72f2 | 2026-10-11 | agent | 0 | 0 | 103 | 0 | 0 | 6 | 5 | fix(anki-tools): make every English prompt name exactly one Russian wo |
| 8cc9946 | 2026-10-11 | agent | 0 | 0 | 89 | 0 | 0 | 0 | 0 | fix(anki-tools): no English prompt is answerable by two words any more |
| 45f3612 | 2026-10-11 | agent | 0 | 0 | 0 | 0 | 0 | 0 | 5 | fix(anki-tools): indeclinable nouns belong in one deck, not two |
| a885261 | 2026-10-12 | agent | 1 | 11 | 0 | 0 | 2 | 0 | 0 | fix(anki-tools): put each sense on its own line, as the prepositions d |
| c9a2bd1 | 2026-10-13 | agent | 0 | 0 | 1 | 0 | 0 | 0 | 0 | fix(anki-tools): say which "if" если is |
| 1693389 | 2026-10-13 | agent | 1 | 0 | 4 | 0 | 0 | 2 | 1 | feat(anki-tools): give так its particle card, and stop tagging twice |
| d87b9db | 2026-10-14 | agent | 26 | 16 | 42 | 0 | 0 | 0 | 0 | fix(anki-tools): no part-of-speech word on an English field |
| a8ee0cb | 2026-10-17 | agent | 1 | 0 | 0 | 0 | 0 | 0 | 0 | fix(anki-tools): give the particle ни its own meaning |
| ed85df8 | 2026-10-18 | agent | 0 | 0 | 0 | 0 | 0 | 6 | 0 | feat(anki-tools): add the six missing pronouns |
| 57d7b4c | 2026-10-18 | agent | 0 | 8 | 0 | 0 | 0 | 0 | 0 | fix(anki-tools): spell out gender and number on the English side |
| 7e584f7 | 2026-10-22 | agent | 1 | 0 | 0 | 0 | 0 | 0 | 0 | fix(anki-tools): let привет read as a form of hello |
| ce413d3 | 2026-10-26 | agent | 20 | 0 | 0 | 0 | 0 | 15 | 0 | feat(anki-tools): distinction fields, Russian TTS, corrected adverb gl |
| 52478b6 | 2026-11-01 | user adoption | 9 | 1 | 2 | 1 | 0 | 0 | 0 | fix(anki-tools): adopt the hand-edited glosses as source |
| 62b5157 | 2026-11-04 | user adoption | 1 | 0 | 0 | 0 | 0 | 0 | 0 | fix(anki-tools): adopt the hand-edited gloss for это as source |

Counts above are before the hand pairings of section 7. Agent `meaning` rows by this classifier: **59**. After section 7 (как lost 'how' in `8fd2ab8`; будто counted by the plan with the `706590b` trio though its change is a parenthetical rewrite) the reconciled figure is in section 10.

## 3. Agent meaning edits (English words changed)

`HEAD source` says whether the agent's new text is still what the source holds now (HEAD of this branch), or what replaced it. A superseded row was later overwritten by a user adoption.

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 4e0bcce | 2026-09-03 | source-word-list.md | вне | outside | outside of (what/where) | still current |
| 2 | 4e0bcce | 2026-09-03 | source-word-list.md | по | along, by, according to | along / around (where)<br>according to (what/whom) | still current |
| 3 | 4e0bcce | 2026-09-03 | source-word-list.md | с / со | with, from | with (whom/what)<br>from / off of (where/what) | superseded: with (whom/what)<br>from / off of (where/what)<div>since (when)</div> |
| 4 | 4e0bcce | 2026-09-03 | source-word-list.md | у | by, at (used for "to have") | by / at (where/whom)<br>to have (possessed by whom) | still current |
| 5 | 706590b | 2026-09-17 | override dict | -ка | softening particle on imperatives: turns an order into a nudge — скажи-ка "go on, tell me", дай-ка "give it here", посмотрим-ка "let's have a look". Informal, ты-level. | go on, just (softens an imperative: скажи-ка "go on, tell me"; informal) | override dict entry removed by 4794da4; text now lives in the document (section 8b) |
| 6 | 706590b | 2026-09-17 | override dict | -то | indefinite particle: makes a word specific-but-unknown — кто-то "someone", что-то "something", где-то "somewhere". Contrast -нибудь, which is non-specific: кто-то позвонил "someone called" (a particular person) vs позови кого-нибудь "call anyone". | some- (indefinite: кто-то "someone", где-то "somewhere"; contrast -нибудь = any-) | override dict entry removed by 4794da4; text now lives in the document (section 8b) |
| 7 | e0e53ba | 2026-10-10 | TSV | идти/пойти | go (on foot) | go (on foot) / set off | still current |
| 8 | e0e53ba | 2026-10-10 | TSV | прощать/простить | forgive | forgive / excuse | still current |
| 9 | 7ceeac1 | 2026-10-11 | TSV | правда (noun) | truth | truth / justice | still current |
| 10 | a885261 | 2026-10-12 | TSV | вид | view / kind / appearance (what something looks like) | view / appearance (what something looks like)<br>kind (a type or species) | still current |
| 11 | 1693389 | 2026-10-13 | source-word-list.md | всё | still / constantly (keeps on) | still / all / constantly (keeps on) | still current |
| 12 | d87b9db | 2026-10-14 | source-word-list.md | ладно | OK / all right / fine (particle) | OK / all right (agreeing) | still current |
| 13 | d87b9db | 2026-10-14 | TSV | плач | crying (noun) | weeping / crying (the sound) | still current |
| 14 | d87b9db | 2026-10-14 | TSV | такой | such / this/that kind of / so (pronoun) | such / that kind of / so (so + adjective) | still current |
| 15 | d87b9db | 2026-10-14 | TSV | двигаться/двинуться | move (verb) | to move | still current |
| 16 | d87b9db | 2026-10-14 | TSV | желать/пожелать | wish (verb) | to wish | still current |
| 17 | d87b9db | 2026-10-14 | TSV | заканчивать/закончить | finish / end (verb) | to finish / to end | still current |
| 18 | d87b9db | 2026-10-14 | TSV | летать/полететь | fly (verb) | to fly | still current |
| 19 | d87b9db | 2026-10-14 | TSV | любить/полюбить | love / like (verb) | to love / to like | still current |
| 20 | d87b9db | 2026-10-14 | TSV | мечтать/помечтать | dream (verb) | to dream (to aspire) | still current |
| 21 | d87b9db | 2026-10-14 | TSV | надеяться/понадеяться | hope / rely on (verb) | to hope / to rely on | still current |
| 22 | d87b9db | 2026-10-14 | TSV | нападать/напасть | attack (verb) | to attack | still current |
| 23 | d87b9db | 2026-10-14 | TSV | начинать/начать | begin / start (verb) | to begin / to start | still current |
| 24 | d87b9db | 2026-10-14 | TSV | отвечать/ответить | answer (verb) | to answer | still current |
| 25 | d87b9db | 2026-10-14 | TSV | отдыхать/отдохнуть | rest / relax (verb) | to rest / to relax | still current |
| 26 | d87b9db | 2026-10-14 | TSV | открывать/открыть | open (verb) | to open | still current |
| 27 | d87b9db | 2026-10-14 | TSV | подозревать/заподозрить | suspect (verb) | to suspect | still current |
| 28 | d87b9db | 2026-10-14 | TSV | показывать/показать | show (verb) | to show | still current |
| 29 | d87b9db | 2026-10-14 | TSV | помогать/помочь | help (verb) | to help | still current |
| 30 | d87b9db | 2026-10-14 | TSV | приказывать/приказать | order / command (verb) | to order / to command | still current |
| 31 | d87b9db | 2026-10-14 | TSV | работать/поработать | work (verb) | to work | still current |
| 32 | d87b9db | 2026-10-14 | TSV | спасать/спасти | save / rescue (verb) | to save / to rescue | still current |
| 33 | d87b9db | 2026-10-14 | TSV | спать/поспать | sleep (verb) | to sleep | still current |
| 34 | d87b9db | 2026-10-14 | TSV | спорить/поспорить | argue / bet (verb) | to argue / to bet | still current |
| 35 | d87b9db | 2026-10-14 | TSV | стоить/— | cost / be worth (verb) | to cost / to be worth | still current |
| 36 | d87b9db | 2026-10-14 | TSV | улыбаться/улыбнуться | smile (verb) | to smile | still current |
| 37 | d87b9db | 2026-10-14 | TSV | чистить/почистить | clean / brush / peel (verb) | to clean / to brush / to peel | still current |
| 38 | a8ee0cb | 2026-10-17 | source-word-list.md | ни | neither / (emphasize extremeness)&nbsp; | not a single / not one | superseded: neither / not a single / not one |
| 39 | 7e584f7 | 2026-10-22 | source-word-list.md | привет | hi (informal) | hello / hi (informal) | still current |
| 40 | ce413d3 | 2026-10-26 | TSV | богато | richly | lavishly (looking expensive) | still current |
| 41 | ce413d3 | 2026-10-26 | TSV | больно | painfully | it hurts (I'm in pain)<br>painfully | still current |
| 42 | ce413d3 | 2026-10-26 | TSV | весело | cheerfully / merrily | fun (it's fun)<br>cheerfully | still current |
| 43 | ce413d3 | 2026-10-26 | TSV | глупо | stupidly | stupid (it's stupid to)<br>stupidly | still current |
| 44 | ce413d3 | 2026-10-26 | TSV | горячо | hotly / passionately | hot (to the touch)<br>passionately | still current |
| 45 | ce413d3 | 2026-10-26 | TSV | грустно | sadly | sad (I feel sad) | still current |
| 46 | ce413d3 | 2026-10-26 | TSV | грязно | dirtily | dirty (it's dirty here) | still current |
| 47 | ce413d3 | 2026-10-26 | TSV | дорого | expensively | expensive (it costs a lot) | still current |
| 48 | ce413d3 | 2026-10-26 | TSV | дёшево | cheaply | cheap (it costs little) | still current |
| 49 | ce413d3 | 2026-10-26 | TSV | здорово | healthily | great / awesome (colloquial) | still current |
| 50 | ce413d3 | 2026-10-26 | TSV | интересно | interestingly | interesting (I'm curious) | still current |
| 51 | ce413d3 | 2026-10-26 | TSV | прохладно | coolly | cool (it is cool out) | still current |
| 52 | ce413d3 | 2026-10-26 | TSV | скучно | boringly | boring (I'm bored) | still current |
| 53 | ce413d3 | 2026-10-26 | TSV | сложно | in a complicated way | complicated (it's hard to do) | still current |
| 54 | ce413d3 | 2026-10-26 | TSV | смешно | funnily | funny (it's funny) | still current |
| 55 | ce413d3 | 2026-10-26 | TSV | странно | strangely | strange (it's odd)<br>strangely | still current |
| 56 | ce413d3 | 2026-10-26 | TSV | тепло | warmly | warm (it is warm out) | still current |
| 57 | ce413d3 | 2026-10-26 | TSV | уродливо | in an ugly way | ugly (it looks ugly) | still current |
| 58 | ce413d3 | 2026-10-26 | TSV | холодно | coldly | cold (it is cold out) | still current |
| 59 | ce413d3 | 2026-10-26 | TSV | который | which / that (relative) | which / who / that | superseded: which / who / that (relative) |

## 4. Agent reorder-only changes (borderline)

None found by the classifier outside the adoption commits. The plan's two borderline cases are `вид` in `a885261` (listed in section 3: `kind` moved to its own line with a new parenthetical) and `так (adverb)` in `1693389` (section 7).

## 5. Agent parenthetical text rewritten (listed separately)

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 4e0bcce | 2026-09-03 | source-word-list.md | через | through, across, in (time) | through, across (what/where)<br>in (when/time) | still current (separators later normalised by 808c0c4) |
| 2 | 706590b | 2026-09-17 | override dict | будто | as if, as though (often implies doubt — он будто не знал "as if he didn't know", implying he did) | as if, as though (often implies doubt) | override dict entry removed by 4794da4; text now lives in the document (section 8b) |
| 3 | a64f3bd | 2026-10-07 | source-word-list.md | -ка | go on, just (softens an imperative: скажи-ка "go on, tell me"; informal) | go on, just (informal) | still current (separators later normalised by 808c0c4) |
| 4 | a64f3bd | 2026-10-07 | source-word-list.md | -то | some- (indefinite: кто-то "someone", где-то "somewhere"; contrast -нибудь = any-) | some- (indefinite) | still current |
| 5 | a64f3bd | 2026-10-07 | source-word-list.md | дескать | allegedly, "so they claim" (marks someone else's words; more formal than мол) | allegedly, "so they claim" (marks someone else's words) | still current (separators later normalised by 808c0c4) |
| 6 | a64f3bd | 2026-10-07 | source-word-list.md | ну и | what a... (emphasis, e.g., ну и день = what a day) | what a... (emphasis) | still current |
| 7 | a64f3bd | 2026-10-07 | TSV | лучший | better, best (attributive comparative/superlative of хороший) | better, best (attributive comparative/superlative) | still current (separators later normalised by 808c0c4) |
| 8 | a64f3bd | 2026-10-07 | override dict | тоже / также | тоже = also, too (same action, different subject — "me too": Я тоже иду) \|\| также = also, in addition (same subject, an extra thing — Я также купил хлеб; more formal) | тоже = also, too (same action, different subject — "me too") \|\| также = also, in addition (same subject, an extra thing; more formal) | still current (separators later normalised by 808c0c4) |
| 9 | 7ceeac1 | 2026-10-11 | source-word-list.md | извините | excuse me / sorry (formal) | excuse me / sorry (formal — when you are at fault) | still current |
| 10 | 7ceeac1 | 2026-10-11 | source-word-list.md | простите | excuse me / forgive me (formal) | excuse me / forgive me (formal — to get attention) | still current |
| 11 | a885261 | 2026-10-12 | source-word-list.md | ещё | still / yet / more (ongoing, or asking for more) | still / yet (ongoing)<br>more (asking for more) | still current |
| 12 | a885261 | 2026-10-12 | source-word-list.md | назад | backwards / ago (direction, or time past) | backwards (direction)<br>ago (time past) | still current |
| 13 | a885261 | 2026-10-12 | TSV | тяжёлый | heavy / hard (weighty, or difficult) | heavy (weighty)<br>hard (difficult) | still current |
| 14 | a885261 | 2026-10-12 | TSV | тяжело | heavily / with difficulty (a heavy burden) | heavily (a heavy burden)<br>with difficulty (with effort) | still current |
| 15 | a885261 | 2026-10-12 | TSV | взгляд | look / glance / view (a gaze, or an opinion) | look / glance (a gaze)<br>view (an opinion) | still current |
| 16 | a885261 | 2026-10-12 | TSV | очередь | line / queue / turn (people waiting) | line / queue (people waiting)<br>turn | still current |
| 17 | a885261 | 2026-10-12 | TSV | число | number / date (a numeral, or a calendar day) | number (a numeral)<br>date (a calendar day) | still current |
| 18 | a885261 | 2026-10-12 | TSV | вызывать/вызвать | call out / summon / cause (summon, or bring about) | call out / summon<br>cause (bring about) | still current |
| 19 | a885261 | 2026-10-12 | TSV | обращаться/обратиться | turn to / address / treat (behave towards) | turn to / address (direct words to someone)<br>treat (behave towards) | still current |
| 20 | a885261 | 2026-10-12 | TSV | растить/вырастить | raise / grow (bring up, cultivate) | raise (bring up)<br>grow (cultivate) | still current |
| 21 | a885261 | 2026-10-12 | TSV | собираться/собраться | gather / intend to (assemble, or intend) | gather (assemble)<br>intend to | still current |
| 22 | d87b9db | 2026-10-14 | source-word-list.md | вроде | like / kind of / sort of (adverb) | like / kind of / sort of (hedging) | still current |
| 23 | d87b9db | 2026-10-14 | source-word-list.md | наверняка | for sure / certainly (adverb) | for sure / certainly (confident of it) | still current |
| 24 | d87b9db | 2026-10-14 | source-word-list.md | конечно | of course / certainly (particle) | of course / certainly (obviously so) | still current |
| 25 | d87b9db | 2026-10-14 | source-word-list.md | ну | well / come on (particle) | well / come on (urging) | still current |
| 26 | d87b9db | 2026-10-14 | source-word-list.md | пожалуй | perhaps / I suppose (particle) | perhaps / I suppose (leaning towards it) | still current |
| 27 | d87b9db | 2026-10-14 | TSV | лёгкий | light / easy (adjective) | light / easy (not heavy) | still current |
| 28 | d87b9db | 2026-10-14 | TSV | плачущий | crying (adjective) | crying (describing someone) | still current |
| 29 | d87b9db | 2026-10-14 | TSV | нормально | normally / fine (adverb) | normally / fine (going OK) | still current |
| 30 | d87b9db | 2026-10-14 | TSV | хорошо | well (adverb) | well (done well) | still current |
| 31 | d87b9db | 2026-10-14 | TSV | муха | fly (noun) | fly (the insect) | still current |
| 32 | d87b9db | 2026-10-14 | TSV | свет | light (noun) | light (illumination) | still current |
| 33 | d87b9db | 2026-10-14 | TSV | секунда | second (noun) | second (the unit of time) | still current |
| 34 | d87b9db | 2026-10-14 | TSV | сон | sleep / dream (noun) | sleep / dream (while asleep) | still current |
| 35 | d87b9db | 2026-10-14 | TSV | штраф | fine / penalty (noun) | fine / penalty (a money punishment) | still current |
| 36 | d87b9db | 2026-10-14 | TSV | второй | second (numeral) | second (2nd in order) | still current |
| 37 | d87b9db | 2026-10-14 | TSV | ничто | nothing (pronoun) | nothing (not a single thing) | still current |
| 38 | 57d7b4c | 2026-10-18 | TSV | друг | friend (m) | friend (male) | still current |
| 39 | 57d7b4c | 2026-10-18 | TSV | кот | cat (m) / tomcat | cat (male) / tomcat | still current |
| 40 | 57d7b4c | 2026-10-18 | TSV | кошка | cat (f) | cat (female) | still current |
| 41 | 57d7b4c | 2026-10-18 | TSV | подруга | friend (f) | friend (female) | still current |
| 42 | 57d7b4c | 2026-10-18 | TSV | продукт | product / (pl.) groceries | product / (plural) groceries | still current |
| 43 | 57d7b4c | 2026-10-18 | TSV | он | he / it (m.) | he / it (masculine) | still current |
| 44 | 57d7b4c | 2026-10-18 | TSV | она | she / it (f.) | she / it (feminine) | still current |
| 45 | 57d7b4c | 2026-10-18 | TSV | оно | it (n.) | it (neuter) | still current |

## 6. Agent parenthesis-only changes

299 rows. In `4e0bcce`, `7ceeac1`, `92f72f2`, `8cc9946`, `d87b9db`, `1693389`, `c9a2bd1`, `a64f3bd` a parenthetical was added or removed and nothing else changed (`92f72f2`/`8cc9946` add disambiguating cues; `d87b9db` deletes the part-of-speech word).

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 4e0bcce | 2026-09-03 | source-word-list.md | без | without | without (whom/what) | still current |
| 2 | 4e0bcce | 2026-09-03 | source-word-list.md | благодаря | thanks to | thanks to (whom/what) | still current |
| 3 | 4e0bcce | 2026-09-03 | source-word-list.md | в / во | in, at, into | in / at (where)<br>into (where/what) | still current |
| 4 | 4e0bcce | 2026-09-03 | source-word-list.md | ввиду | in view of | in view of (what) | still current |
| 5 | 4e0bcce | 2026-09-03 | source-word-list.md | вдоль | along | along (what/where) | still current |
| 6 | 4e0bcce | 2026-09-03 | source-word-list.md | вместо | instead of | instead of (whom/what) | still current |
| 7 | 4e0bcce | 2026-09-03 | source-word-list.md | внутри | inside | inside (what/where) | still current |
| 8 | 4e0bcce | 2026-09-03 | source-word-list.md | возле | by, near | by, near (whom/what/where) | still current (separators later normalised by 808c0c4) |
| 9 | 4e0bcce | 2026-09-03 | source-word-list.md | вокруг | around | around (whom/what/where) | still current |
| 10 | 4e0bcce | 2026-09-03 | source-word-list.md | вопреки | despite, contrary to | despite, contrary to (what/whom) | still current (separators later normalised by 808c0c4) |
| 11 | 4e0bcce | 2026-09-03 | source-word-list.md | до | up to, until, before | up to (where/what)<br>until / before (when) | still current |
| 12 | 4e0bcce | 2026-09-03 | source-word-list.md | за | behind, for | behind (where/whom/what)<br>for (whom/what) | still current |
| 13 | 4e0bcce | 2026-09-03 | source-word-list.md | из | from, out of | from (where)<br>out of (what/where) | still current |
| 14 | 4e0bcce | 2026-09-03 | source-word-list.md | из-за | because of, from behind | because of (whom/what)<br>from behind (what/where) | still current |
| 15 | 4e0bcce | 2026-09-03 | source-word-list.md | из-под | from under | from under (what/where) | still current |
| 16 | 4e0bcce | 2026-09-03 | source-word-list.md | к / ко | to, toward | to, toward (whom/what/where) | still current (separators later normalised by 808c0c4) |
| 17 | 4e0bcce | 2026-09-03 | source-word-list.md | кроме | except, besides | except, besides (whom/what) | still current (separators later normalised by 808c0c4) |
| 18 | 4e0bcce | 2026-09-03 | source-word-list.md | между | between, among | between, among (whom/what) | still current (separators later normalised by 808c0c4) |
| 19 | 4e0bcce | 2026-09-03 | source-word-list.md | мимо | past, by | past, by (whom/what/where) | still current (separators later normalised by 808c0c4) |
| 20 | 4e0bcce | 2026-09-03 | source-word-list.md | на | on, at, onto | on / at (where)<br>onto (where/what) | still current |
| 21 | 4e0bcce | 2026-09-03 | source-word-list.md | навстречу | towards | towards (whom/what) | still current |
| 22 | 4e0bcce | 2026-09-03 | source-word-list.md | над | above, over | above, over (where/what/whom) | still current (separators later normalised by 808c0c4) |
| 23 | 4e0bcce | 2026-09-03 | source-word-list.md | насчёт | about, regarding | about, regarding (whom/what) | still current (separators later normalised by 808c0c4) |
| 24 | 4e0bcce | 2026-09-03 | source-word-list.md | о / об | about | about (whom/what) | still current |
| 25 | 4e0bcce | 2026-09-03 | source-word-list.md | около | near, around | near, around (whom/what/where/when) | still current (separators later normalised by 808c0c4) |
| 26 | 4e0bcce | 2026-09-03 | source-word-list.md | от | from, away from | from, away from (whom/what/where) | still current (separators later normalised by 808c0c4) |
| 27 | 4e0bcce | 2026-09-03 | source-word-list.md | перед | in front of, before | in front of, before (where/whom/what/when) | still current (separators later normalised by 808c0c4) |
| 28 | 4e0bcce | 2026-09-03 | source-word-list.md | поверх | over, on top of | over, on top of (what/where) | still current (separators later normalised by 808c0c4) |
| 29 | 4e0bcce | 2026-09-03 | source-word-list.md | под | under, below | under, below (where/what/whom) | still current (separators later normalised by 808c0c4) |
| 30 | 4e0bcce | 2026-09-03 | source-word-list.md | позади | behind | behind (whom/what/where) | still current |
| 31 | 4e0bcce | 2026-09-03 | source-word-list.md | после | after | after (whom/what/when) | still current |
| 32 | 4e0bcce | 2026-09-03 | source-word-list.md | посреди | in the middle of | in the middle of (what/where) | still current |
| 33 | 4e0bcce | 2026-09-03 | source-word-list.md | при | in the presence of, attached to | in the presence of (whom)<br>attached to (what/where) | still current |
| 34 | 4e0bcce | 2026-09-03 | source-word-list.md | против | against, opposite | against, opposite (whom/what/where) | still current (separators later normalised by 808c0c4) |
| 35 | 4e0bcce | 2026-09-03 | source-word-list.md | ради | for the sake of | for the sake of (whom/what) | still current |
| 36 | 4e0bcce | 2026-09-03 | source-word-list.md | сквозь | through | through (what/where) | still current |
| 37 | 4e0bcce | 2026-09-03 | source-word-list.md | согласно | according to | according to (what/whom) | headword renamed/removed since |
| 38 | 4e0bcce | 2026-09-03 | source-word-list.md | среди | among | among (whom/what) | still current |
| 39 | a64f3bd | 2026-10-07 | source-word-list.md | как (conjunction) | like, as (белый как снег) | like, as | superseded: like / as (comparison) |
| 40 | a64f3bd | 2026-10-07 | source-word-list.md | когда (conjunction) | when, while, as (Когда я пришёл, он спал) | when, while, as | superseded: when / while / as (at the time that) |
| 41 | a64f3bd | 2026-10-07 | source-word-list.md | таки | after all, nevertheless (often hyphenated: всё-таки) | after all, nevertheless | still current (separators later normalised by 808c0c4) |
| 42 | a64f3bd | 2026-10-07 | TSV | иной | different, other (more literary than другой) | different, other | superseded: different / other (of another kind) |
| 43 | 7ceeac1 | 2026-10-11 | source-word-list.md | ещё | still / yet / more | still / yet / more (ongoing, or asking for more) | superseded: still / yet (ongoing)<br>more (asking for more) |
| 44 | 7ceeac1 | 2026-10-11 | source-word-list.md | здесь | here | here (static location) | still current |
| 45 | 7ceeac1 | 2026-10-11 | source-word-list.md | опять | again | again (the same action repeating) | still current |
| 46 | 7ceeac1 | 2026-10-11 | source-word-list.md | сейчас | now / right now | now / right now (this exact moment) | still current |
| 47 | 7ceeac1 | 2026-10-11 | source-word-list.md | снова | again / anew | again / anew (afresh, a new start) | still current |
| 48 | 7ceeac1 | 2026-10-11 | source-word-list.md | теперь | now / nowadays | now / nowadays (as opposed to before) | still current |
| 49 | 7ceeac1 | 2026-10-11 | source-word-list.md | как (conjunction) | like / as | like / as (comparison) | still current |
| 50 | 7ceeac1 | 2026-10-11 | source-word-list.md | как будто | as if / as though | as if / as though (neutral, unreal comparison) | still current |
| 51 | 7ceeac1 | 2026-10-11 | source-word-list.md | пианино | piano | piano (upright) | still current |
| 52 | 7ceeac1 | 2026-10-11 | source-word-list.md | фортепиано | piano | piano (the instrument in general) | still current |
| 53 | 7ceeac1 | 2026-10-11 | source-word-list.md | всё | still / constantly | still / constantly (keeps on) | superseded: still / all / constantly (keeps on) |
| 54 | 7ceeac1 | 2026-10-11 | source-word-list.md | всё-таки | still / nevertheless | still / nevertheless (all the same) | still current |
| 55 | 7ceeac1 | 2026-10-11 | source-word-list.md | лишь | only / merely | only / merely (bookish) | still current |
| 56 | 7ceeac1 | 2026-10-11 | source-word-list.md | только | only | only (restrictive) | still current |
| 57 | 7ceeac1 | 2026-10-11 | TSV | врач | doctor | doctor (the medical profession) | still current |
| 58 | 7ceeac1 | 2026-10-11 | TSV | гостиница | hotel | hotel (the ordinary Russian word) | still current |
| 59 | 7ceeac1 | 2026-10-11 | TSV | доктор | doctor | doctor (as a title or form of address) | still current |
| 60 | 7ceeac1 | 2026-10-11 | TSV | отель | hotel | hotel (borrowed term, usually upscale/international) | still current |
| 61 | 92f72f2 | 2026-10-11 | source-word-list.md | вовсе | at all | at all (only with a negative: not at all) | still current |
| 62 | 92f72f2 | 2026-10-11 | source-word-list.md | вообще | in general / at all | in general / at all (generally speaking) | still current |
| 63 | 92f72f2 | 2026-10-11 | source-word-list.md | затем | then / after that | then / after that (next in sequence) | still current |
| 64 | 92f72f2 | 2026-10-11 | source-word-list.md | иначе | otherwise / differently | otherwise / differently (or else) | still current |
| 65 | 92f72f2 | 2026-10-11 | source-word-list.md | много | many / much / a lot | many / much / a lot (quantity) | still current |
| 66 | 92f72f2 | 2026-10-11 | source-word-list.md | назад | backwards / ago | backwards / ago (direction, or time past) | superseded: backwards (direction)<br>ago (time past) |
| 67 | 92f72f2 | 2026-10-11 | source-word-list.md | наоборот | vice versa / backwards | vice versa / backwards (the other way round) | still current |
| 68 | 92f72f2 | 2026-10-11 | source-word-list.md | потом | then / later | then / later (afterwards) | still current |
| 69 | 92f72f2 | 2026-10-11 | source-word-list.md | совсем | completely / entirely | completely / entirely (utterly) | still current |
| 70 | 92f72f2 | 2026-10-11 | source-word-list.md | тогда | then / in that case | then / in that case (at that time) | still current |
| 71 | 92f72f2 | 2026-10-11 | source-word-list.md | для того, чтобы | in order to | in order to (the emphatic, two-part form) | still current |
| 72 | 92f72f2 | 2026-10-11 | source-word-list.md | когда (conjunction) | when / while / as | when / while / as (at the time that) | still current |
| 73 | 92f72f2 | 2026-10-11 | source-word-list.md | либо | either / or | either / or (one or the other) | still current |
| 74 | 92f72f2 | 2026-10-11 | source-word-list.md | пока (conjunction) | while / until | while / until (for as long as) | still current |
| 75 | 92f72f2 | 2026-10-11 | source-word-list.md | так как | since / as | since / as (because) | still current |
| 76 | 92f72f2 | 2026-10-11 | source-word-list.md | бра | wall sconce / lamp | wall sconce / lamp (wall-mounted) | still current |
| 77 | 92f72f2 | 2026-10-11 | source-word-list.md | бюро | bureau / office | bureau / office (a bureau) | still current |
| 78 | 92f72f2 | 2026-10-11 | TSV | другой | other / different | other / different (another one) | still current |
| 79 | 92f72f2 | 2026-10-11 | TSV | замечательный | wonderful | wonderful (remarkable) | still current |
| 80 | 92f72f2 | 2026-10-11 | TSV | знаменитый | famous | famous (celebrated) | still current |
| 81 | 92f72f2 | 2026-10-11 | TSV | иной | different / other | different / other (of another kind) | still current |
| 82 | 92f72f2 | 2026-10-11 | TSV | короткий | short | short (not long) | still current |
| 83 | 92f72f2 | 2026-10-11 | TSV | красивый | beautiful / handsome | beautiful / handsome (good-looking) | still current |
| 84 | 92f72f2 | 2026-10-11 | TSV | маленький | small / little | small / little (not big) | still current |
| 85 | 92f72f2 | 2026-10-11 | TSV | мелкий | shallow / small | shallow / small (petty, fine-grained) | still current (separators later normalised by 808c0c4) |
| 86 | 92f72f2 | 2026-10-11 | TSV | низкий | low / short | low / short (not tall) | still current |
| 87 | 92f72f2 | 2026-10-11 | TSV | прекрасный | wonderful / beautiful | wonderful / beautiful (splendid) | still current |
| 88 | 92f72f2 | 2026-10-11 | TSV | разный | different / various | different / various (various, assorted) | still current |
| 89 | 92f72f2 | 2026-10-11 | TSV | страшный | terrible / frightful / scary | terrible / frightful / scary (frightening) | still current |
| 90 | 92f72f2 | 2026-10-11 | TSV | твёрдый | hard / firm | hard / firm (solid, not soft) | still current |
| 91 | 92f72f2 | 2026-10-11 | TSV | тяжёлый | heavy / hard | heavy / hard (weighty, or difficult) | superseded: heavy (weighty)<br>hard (difficult) |
| 92 | 92f72f2 | 2026-10-11 | TSV | ужасный | terrible / awful | terrible / awful (dreadful) | still current |
| 93 | 92f72f2 | 2026-10-11 | TSV | мягко | softly / gently | softly / gently (with softness) | still current |
| 94 | 92f72f2 | 2026-10-11 | TSV | нежно | tenderly / gently | tenderly / gently (with tenderness) | still current |
| 95 | 92f72f2 | 2026-10-11 | TSV | по-настоящему | really / for real | really / for real (genuinely) | still current |
| 96 | 92f72f2 | 2026-10-11 | TSV | по-разному | differently | differently (in various ways) | still current |
| 97 | 92f72f2 | 2026-10-11 | TSV | полностью | completely / fully | completely / fully (in full) | still current |
| 98 | 92f72f2 | 2026-10-11 | TSV | сильно | strongly / a lot | strongly / a lot (intensity) | still current |
| 99 | 92f72f2 | 2026-10-11 | TSV | трудно | with difficulty | with difficulty (it is hard to do) | still current |
| 100 | 92f72f2 | 2026-10-11 | TSV | тяжело | heavily / with difficulty | heavily / with difficulty (a heavy burden) | superseded: heavily (a heavy burden)<br>with difficulty (with effort) |
| 101 | 92f72f2 | 2026-10-11 | TSV | целиком | entirely / whole | entirely / whole (as a single whole) | still current |
| 102 | 92f72f2 | 2026-10-11 | TSV | банк | bank | bank (the financial one) | still current |
| 103 | 92f72f2 | 2026-10-11 | TSV | берег | shore / bank | shore / bank (of a river) | still current |
| 104 | 92f72f2 | 2026-10-11 | TSV | бизнес | business | business (commerce) | still current |
| 105 | 92f72f2 | 2026-10-11 | TSV | век | century / age | century / age (an era) | still current (separators later normalised by 808c0c4) |
| 106 | 92f72f2 | 2026-10-11 | TSV | взгляд | look / glance / view | look / glance / view (a gaze, or an opinion) | superseded: look / glance (a gaze)<br>view (an opinion) |
| 107 | 92f72f2 | 2026-10-11 | TSV | вид | view / kind / appearance | view / kind / appearance (what something looks like) | superseded: view / appearance (what something looks like)<br>kind (a type or species) |
| 108 | 92f72f2 | 2026-10-11 | TSV | водитель | driver | driver (the one driving) | still current |
| 109 | 92f72f2 | 2026-10-11 | TSV | возраст | age | age (how old someone is) | still current |
| 110 | 92f72f2 | 2026-10-11 | TSV | гнев | anger / wrath | anger / wrath (fury) | still current |
| 111 | 92f72f2 | 2026-10-11 | TSV | дело | matter / affair / business | matter / affair / business (an affair) | still current |
| 112 | 92f72f2 | 2026-10-11 | TSV | договор | agreement / contract | agreement / contract (a treaty or accord) | still current |
| 113 | 92f72f2 | 2026-10-11 | TSV | злость | anger / spite | anger / spite (malice) | still current |
| 114 | 92f72f2 | 2026-10-11 | TSV | значение | meaning / significance | meaning / significance (what it signifies) | still current |
| 115 | 92f72f2 | 2026-10-11 | TSV | контракт | contract | contract (the formal document) | still current |
| 116 | 92f72f2 | 2026-10-11 | TSV | лампа | lamp | lamp (a free-standing lamp) | still current |
| 117 | 92f72f2 | 2026-10-11 | TSV | линия | line | line (a geometric line) | still current |
| 118 | 92f72f2 | 2026-10-11 | TSV | люди | people | people (persons, individuals) | still current |
| 119 | 92f72f2 | 2026-10-11 | TSV | менеджер | manager | manager (a business manager) | still current |
| 120 | 92f72f2 | 2026-10-11 | TSV | метод | method | method (a formal method) | still current |
| 121 | 92f72f2 | 2026-10-11 | TSV | народ | people / nation | people / nation (a people) | still current |
| 122 | 92f72f2 | 2026-10-11 | TSV | нация | nation | nation (a nation state) | still current |
| 123 | 92f72f2 | 2026-10-11 | TSV | номер | number / hotel room | number / hotel room (an assigned number) | still current |
| 124 | 92f72f2 | 2026-10-11 | TSV | офис | office | office (a workplace) | still current |
| 125 | 92f72f2 | 2026-10-11 | TSV | очередь | line / queue / turn | line / queue / turn (people waiting) | superseded: line / queue (people waiting)<br>turn |
| 126 | 92f72f2 | 2026-10-11 | TSV | причина | cause / reason | cause / reason (the why) | still current |
| 127 | 92f72f2 | 2026-10-11 | TSV | разум | reason | reason (the faculty of reason) | still current |
| 128 | 92f72f2 | 2026-10-11 | TSV | ряд | row / line | row / line (a row of things) | still current |
| 129 | 92f72f2 | 2026-10-11 | TSV | секрет | secret | secret (a kept secret) | still current |
| 130 | 92f72f2 | 2026-10-11 | TSV | случайность | chance / accident | chance / accident (a coincidence) | still current |
| 131 | 92f72f2 | 2026-10-11 | TSV | смысл | meaning / sense | meaning / sense (the point of it) | still current |
| 132 | 92f72f2 | 2026-10-11 | TSV | способ | way / method | way / method (a way of doing something) | still current |
| 133 | 92f72f2 | 2026-10-11 | TSV | тайна | mystery / secret | mystery / secret (a mystery) | still current |
| 134 | 92f72f2 | 2026-10-11 | TSV | управляющий | manager | manager (the one in charge, an administrator) | still current |
| 135 | 92f72f2 | 2026-10-11 | TSV | фильм | film / movie | film / movie (a particular film) | still current |
| 136 | 92f72f2 | 2026-10-11 | TSV | число | number / date | number / date (a numeral, or a calendar day) | superseded: number (a numeral)<br>date (a calendar day) |
| 137 | 92f72f2 | 2026-10-11 | TSV | шанс | chance | chance (an opportunity) | still current |
| 138 | 92f72f2 | 2026-10-11 | TSV | шофёр | chauffeur / driver | chauffeur / driver (a hired driver) | still current |
| 139 | 92f72f2 | 2026-10-11 | TSV | варить/сварить | boil / cook | boil / cook (by boiling) | still current |
| 140 | 92f72f2 | 2026-10-11 | TSV | встречать/встретить | meet | meet (encounter someone) | still current |
| 141 | 92f72f2 | 2026-10-11 | TSV | вызывать/вызвать | call out / summon / cause | call out / summon / cause (summon, or bring about) | superseded: call out / summon<br>cause (bring about) |
| 142 | 92f72f2 | 2026-10-11 | TSV | готовить/приготовить | prepare / cook | prepare / cook (prepare food) | superseded: prepare / cook&nbsp; |
| 143 | 92f72f2 | 2026-10-11 | TSV | звать/позвать | call / summon / be named | call / summon / be named (summon someone) | still current |
| 144 | 92f72f2 | 2026-10-11 | TSV | знакомиться/познакомиться | get acquainted / meet | get acquainted / meet (for the first time) | still current |
| 145 | 92f72f2 | 2026-10-11 | TSV | лечить/вылечить | treat / cure | treat / cure (medically) | still current |
| 146 | 92f72f2 | 2026-10-11 | TSV | мочь/смочь | be able to / can | be able to / can (it is possible) | still current |
| 147 | 92f72f2 | 2026-10-11 | TSV | наблюдать/понаблюдать | observe / watch | observe / watch (study attentively) | still current |
| 148 | 92f72f2 | 2026-10-11 | TSV | называть/назвать | name / call | name / call (give a name to) | still current |
| 149 | 92f72f2 | 2026-10-11 | TSV | обращаться/обратиться | turn to / address / treat | turn to / address / treat (behave towards) | superseded: turn to / address (direct words to someone)<br>treat (behave towards) |
| 150 | 92f72f2 | 2026-10-11 | TSV | оказываться/оказаться | turn out / end up | turn out / end up (prove to be) | still current |
| 151 | 92f72f2 | 2026-10-11 | TSV | передавать/передать | pass / hand over / convey | pass / hand over / convey (hand something on) | still current |
| 152 | 92f72f2 | 2026-10-11 | TSV | поднимать/поднять | lift / raise / pick up | lift / raise / pick up (lift up) | still current |
| 153 | 92f72f2 | 2026-10-11 | TSV | получаться/получиться | turn out / work out | turn out / work out (come out well) | still current |
| 154 | 92f72f2 | 2026-10-11 | TSV | происходить/произойти | happen / occur | happen / occur (take place) | still current |
| 155 | 92f72f2 | 2026-10-11 | TSV | проходить/пройти | pass / go through | pass / go through (move past or through) | still current |
| 156 | 92f72f2 | 2026-10-11 | TSV | разговаривать/поговорить | talk / have a conversation | talk / have a conversation (converse) | still current |
| 157 | 92f72f2 | 2026-10-11 | TSV | рассказывать/рассказать | tell / narrate | tell / narrate (recount) | still current |
| 158 | 92f72f2 | 2026-10-11 | TSV | растить/вырастить | raise / grow | raise / grow (bring up, cultivate) | superseded: raise (bring up)<br>grow (cultivate) |
| 159 | 92f72f2 | 2026-10-11 | TSV | случаться/случиться | happen | happen (come to pass) | still current |
| 160 | 92f72f2 | 2026-10-11 | TSV | смотреть/посмотреть | look / watch | look / watch (direct your eyes at) | still current |
| 161 | 92f72f2 | 2026-10-11 | TSV | собирать/собрать | collect / gather | collect / gather (gather things up) | still current |
| 162 | 92f72f2 | 2026-10-11 | TSV | собираться/собраться | gather / intend to | gather / intend to (assemble, or intend) | superseded: gather (assemble)<br>intend to |
| 163 | 92f72f2 | 2026-10-11 | TSV | уметь/суметь | be able to / know how to | be able to / know how to (a learned skill) | superseded: can / be able to / know how to (a learned skill) |
| 164 | 8cc9946 | 2026-10-11 | source-word-list.md | вроде | like / kind of / sort of | like / kind of / sort of (adverb) | superseded: like / kind of / sort of (hedging) |
| 165 | 8cc9946 | 2026-10-11 | source-word-list.md | наверняка | for sure / certainly | for sure / certainly (adverb) | superseded: for sure / certainly (confident of it) |
| 166 | 8cc9946 | 2026-10-11 | source-word-list.md | так | like this / so | like this / so (adverb) | headword renamed/removed since |
| 167 | 8cc9946 | 2026-10-11 | source-word-list.md | пари | bet / wager | bet / wager (noun) | superseded: bet / wager |
| 168 | 8cc9946 | 2026-10-11 | source-word-list.md | шоу | show | show (noun) | superseded: show |
| 169 | 8cc9946 | 2026-10-11 | source-word-list.md | конечно | of course / certainly | of course / certainly (particle) | superseded: of course / certainly (obviously so) |
| 170 | 8cc9946 | 2026-10-11 | source-word-list.md | ладно | OK / all right / fine | OK / all right / fine (particle) | superseded: OK / all right (agreeing) |
| 171 | 8cc9946 | 2026-10-11 | source-word-list.md | ничего | nothing / it's OK / no problem | nothing / it's OK / no problem (particle) | superseded: nothing / it's OK / no problem |
| 172 | 8cc9946 | 2026-10-11 | source-word-list.md | ну | well / come on | well / come on (particle) | superseded: well / come on (urging) |
| 173 | 8cc9946 | 2026-10-11 | source-word-list.md | пожалуй | perhaps / I suppose | perhaps / I suppose (particle) | superseded: perhaps / I suppose (leaning towards it) |
| 174 | 8cc9946 | 2026-10-11 | source-word-list.md | просто (particle) | simply / just | simply / just (particle) | superseded: simply / just |
| 175 | 8cc9946 | 2026-10-11 | TSV | влажный | damp / humid | damp / humid (adjective) | superseded: damp / humid |
| 176 | 8cc9946 | 2026-10-11 | TSV | живой | alive / lively | alive / lively (adjective) | superseded: alive / lively |
| 177 | 8cc9946 | 2026-10-11 | TSV | закрытый | closed | closed (adjective) | superseded: closed |
| 178 | 8cc9946 | 2026-10-11 | TSV | знакомый | familiar | familiar (adjective) | superseded: familiar |
| 179 | 8cc9946 | 2026-10-11 | TSV | лёгкий | light / easy | light / easy (adjective) | superseded: light / easy (not heavy) |
| 180 | 8cc9946 | 2026-10-11 | TSV | мокрый | wet | wet (adjective) | superseded: wet |
| 181 | 8cc9946 | 2026-10-11 | TSV | нужный | needed / necessary | needed / necessary (adjective) | superseded: needed / necessary |
| 182 | 8cc9946 | 2026-10-11 | TSV | открытый | open | open (adjective) | superseded: open |
| 183 | 8cc9946 | 2026-10-11 | TSV | первый (adjective) | first | first (adjective) | superseded: first |
| 184 | 8cc9946 | 2026-10-11 | TSV | плачущий | crying | crying (adjective) | superseded: crying (describing someone) |
| 185 | 8cc9946 | 2026-10-11 | TSV | поздний | late | late (adjective) | superseded: late |
| 186 | 8cc9946 | 2026-10-11 | TSV | прямой | straight / direct | straight / direct (adjective) | superseded: straight / direct |
| 187 | 8cc9946 | 2026-10-11 | TSV | пустой | empty | empty (adjective) | superseded: empty |
| 188 | 8cc9946 | 2026-10-11 | TSV | ранний | early | early (adjective) | superseded: early |
| 189 | 8cc9946 | 2026-10-11 | TSV | чистый | clean / pure | clean / pure (adjective) | superseded: clean / pure |
| 190 | 8cc9946 | 2026-10-11 | TSV | влажно | humid | humid (adverb) | superseded: humid |
| 191 | 8cc9946 | 2026-10-11 | TSV | возможно | possibly / perhaps | possibly / perhaps (adverb) | superseded: possibly / perhaps |
| 192 | 8cc9946 | 2026-10-11 | TSV | живо | vividly / lively | vividly / lively (adverb) | superseded: vividly / lively |
| 193 | 8cc9946 | 2026-10-11 | TSV | закрыто | closed | closed (adverb) | superseded: closed |
| 194 | 8cc9946 | 2026-10-11 | TSV | знакомо | familiar | familiar (adverb) | superseded: familiar |
| 195 | 8cc9946 | 2026-10-11 | TSV | мокро | wet | wet (adverb) | superseded: wet |
| 196 | 8cc9946 | 2026-10-11 | TSV | нормально | normally / fine | normally / fine (adverb) | superseded: normally / fine (going OK) |
| 197 | 8cc9946 | 2026-10-11 | TSV | нужно | necessary | necessary (adverb) | superseded: necessary |
| 198 | 8cc9946 | 2026-10-11 | TSV | поздно | late | late (adverb) | superseded: late |
| 199 | 8cc9946 | 2026-10-11 | TSV | просто (adverb) | simply / just | simply / just (adverb) | superseded: simply / just |
| 200 | 8cc9946 | 2026-10-11 | TSV | прямо | straight / directly | straight / directly (adverb) | superseded: straight / directly |
| 201 | 8cc9946 | 2026-10-11 | TSV | пусто | empty | empty (adverb) | superseded: empty |
| 202 | 8cc9946 | 2026-10-11 | TSV | рано | early | early (adverb) | superseded: early |
| 203 | 8cc9946 | 2026-10-11 | TSV | хорошо | well | well (adverb) | superseded: well (done well) |
| 204 | 8cc9946 | 2026-10-11 | TSV | атака | attack | attack (noun) | superseded: attack |
| 205 | 8cc9946 | 2026-10-11 | TSV | желание | wish / desire | wish / desire (noun) | superseded: wish / desire |
| 206 | 8cc9946 | 2026-10-11 | TSV | конец | end | end (noun) | superseded: end |
| 207 | 8cc9946 | 2026-10-11 | TSV | любовь | love | love (noun) | superseded: love |
| 208 | 8cc9946 | 2026-10-11 | TSV | муха | fly | fly (noun) | superseded: fly (the insect) |
| 209 | 8cc9946 | 2026-10-11 | TSV | надежда | hope | hope (noun) | superseded: hope |
| 210 | 8cc9946 | 2026-10-11 | TSV | ответ | answer | answer (noun) | superseded: answer |
| 211 | 8cc9946 | 2026-10-11 | TSV | отдых | rest / vacation | rest / vacation (noun) | superseded: rest / vacation |
| 212 | 8cc9946 | 2026-10-11 | TSV | плач | crying | crying (noun) | superseded: weeping / crying (the sound) |
| 213 | 8cc9946 | 2026-10-11 | TSV | подозреваемый | suspect | suspect (noun) | superseded: suspect |
| 214 | 8cc9946 | 2026-10-11 | TSV | помощь | help | help (noun) | superseded: help |
| 215 | 8cc9946 | 2026-10-11 | TSV | приказ | order / command | order / command (noun) | superseded: order / command |
| 216 | 8cc9946 | 2026-10-11 | TSV | работа | work / job | work / job (noun) | superseded: work / job |
| 217 | 8cc9946 | 2026-10-11 | TSV | свет | light | light (noun) | superseded: light (illumination) |
| 218 | 8cc9946 | 2026-10-11 | TSV | секунда | second | second (noun) | superseded: second (the unit of time) |
| 219 | 8cc9946 | 2026-10-11 | TSV | сон | sleep / dream | sleep / dream (noun) | superseded: sleep / dream (while asleep) |
| 220 | 8cc9946 | 2026-10-11 | TSV | спасение | rescue / salvation | rescue / salvation (noun) | superseded: rescue / salvation |
| 221 | 8cc9946 | 2026-10-11 | TSV | старт | start | start (noun) | superseded: start |
| 222 | 8cc9946 | 2026-10-11 | TSV | стоимость | cost | cost (noun) | superseded: cost |
| 223 | 8cc9946 | 2026-10-11 | TSV | улыбка | smile | smile (noun) | superseded: smile |
| 224 | 8cc9946 | 2026-10-11 | TSV | ход | move / course | move / course (noun) | superseded: move / course |
| 225 | 8cc9946 | 2026-10-11 | TSV | штраф | fine / penalty | fine / penalty (noun) | superseded: fine / penalty (a money punishment) |
| 226 | 8cc9946 | 2026-10-11 | TSV | второй | second | second (numeral) | superseded: second (2nd in order) |
| 227 | 8cc9946 | 2026-10-11 | TSV | первый (numeral) | first | first (numeral) | superseded: first |
| 228 | 8cc9946 | 2026-10-11 | TSV | ничто | nothing | nothing (pronoun) | superseded: nothing (not a single thing) |
| 229 | 8cc9946 | 2026-10-11 | TSV | такой | such / this/that kind of / so | such / this/that kind of / so (pronoun) | superseded: such / that kind of / so (so + adjective) |
| 230 | 8cc9946 | 2026-10-11 | TSV | двигаться/двинуться | move | move (verb) | superseded: to move |
| 231 | 8cc9946 | 2026-10-11 | TSV | желать/пожелать | wish | wish (verb) | superseded: to wish |
| 232 | 8cc9946 | 2026-10-11 | TSV | заканчивать/закончить | finish / end | finish / end (verb) | superseded: to finish / to end |
| 233 | 8cc9946 | 2026-10-11 | TSV | летать/полететь | fly | fly (verb) | superseded: to fly |
| 234 | 8cc9946 | 2026-10-11 | TSV | любить/полюбить | love / like | love / like (verb) | superseded: to love / to like |
| 235 | 8cc9946 | 2026-10-11 | TSV | мечтать/помечтать | dream | dream (verb) | superseded: to dream (to aspire) |
| 236 | 8cc9946 | 2026-10-11 | TSV | надеяться/понадеяться | hope / rely on | hope / rely on (verb) | superseded: to hope / to rely on |
| 237 | 8cc9946 | 2026-10-11 | TSV | нападать/напасть | attack | attack (verb) | superseded: to attack |
| 238 | 8cc9946 | 2026-10-11 | TSV | начинать/начать | begin / start | begin / start (verb) | superseded: to begin / to start |
| 239 | 8cc9946 | 2026-10-11 | TSV | отвечать/ответить | answer | answer (verb) | superseded: to answer |
| 240 | 8cc9946 | 2026-10-11 | TSV | отдыхать/отдохнуть | rest / relax | rest / relax (verb) | superseded: to rest / to relax |
| 241 | 8cc9946 | 2026-10-11 | TSV | открывать/открыть | open | open (verb) | superseded: to open |
| 242 | 8cc9946 | 2026-10-11 | TSV | подозревать/заподозрить | suspect | suspect (verb) | superseded: to suspect |
| 243 | 8cc9946 | 2026-10-11 | TSV | показывать/показать | show | show (verb) | superseded: to show |
| 244 | 8cc9946 | 2026-10-11 | TSV | помогать/помочь | help | help (verb) | superseded: to help |
| 245 | 8cc9946 | 2026-10-11 | TSV | приказывать/приказать | order / command | order / command (verb) | superseded: to order / to command |
| 246 | 8cc9946 | 2026-10-11 | TSV | работать/поработать | work | work (verb) | superseded: to work |
| 247 | 8cc9946 | 2026-10-11 | TSV | спасать/спасти | save / rescue | save / rescue (verb) | superseded: to save / to rescue |
| 248 | 8cc9946 | 2026-10-11 | TSV | спать/поспать | sleep | sleep (verb) | superseded: to sleep |
| 249 | 8cc9946 | 2026-10-11 | TSV | спорить/поспорить | argue / bet | argue / bet (verb) | superseded: to argue / to bet |
| 250 | 8cc9946 | 2026-10-11 | TSV | стоить/— | cost / be worth | cost / be worth (verb) | superseded: to cost / to be worth |
| 251 | 8cc9946 | 2026-10-11 | TSV | улыбаться/улыбнуться | smile | smile (verb) | superseded: to smile |
| 252 | 8cc9946 | 2026-10-11 | TSV | чистить/почистить | clean / brush / peel | clean / brush / peel (verb) | superseded: to clean / to brush / to peel |
| 253 | c9a2bd1 | 2026-10-13 | source-word-list.md | если | if | if (conditional) | still current |
| 254 | 1693389 | 2026-10-13 | source-word-list.md | просто (particle) | simply / just (particle) | simply / just | still current |
| 255 | 1693389 | 2026-10-13 | TSV | первый (adjective) | first (adjective) | first | still current |
| 256 | 1693389 | 2026-10-13 | TSV | просто (adverb) | simply / just (adverb) | simply / just | still current |
| 257 | 1693389 | 2026-10-13 | TSV | первый (numeral) | first (numeral) | first | still current |
| 258 | d87b9db | 2026-10-14 | source-word-list.md | пари | bet / wager (noun) | bet / wager | still current |
| 259 | d87b9db | 2026-10-14 | source-word-list.md | шоу | show (noun) | show | still current |
| 260 | d87b9db | 2026-10-14 | source-word-list.md | ничего | nothing / it's OK / no problem (particle) | nothing / it's OK / no problem | still current |
| 261 | d87b9db | 2026-10-14 | TSV | влажный | damp / humid (adjective) | damp / humid | still current |
| 262 | d87b9db | 2026-10-14 | TSV | живой | alive / lively (adjective) | alive / lively | still current |
| 263 | d87b9db | 2026-10-14 | TSV | закрытый | closed (adjective) | closed | still current |
| 264 | d87b9db | 2026-10-14 | TSV | знакомый | familiar (adjective) | familiar | still current |
| 265 | d87b9db | 2026-10-14 | TSV | мокрый | wet (adjective) | wet | still current |
| 266 | d87b9db | 2026-10-14 | TSV | нужный | needed / necessary (adjective) | needed / necessary | still current |
| 267 | d87b9db | 2026-10-14 | TSV | открытый | open (adjective) | open | still current |
| 268 | d87b9db | 2026-10-14 | TSV | поздний | late (adjective) | late | still current |
| 269 | d87b9db | 2026-10-14 | TSV | прямой | straight / direct (adjective) | straight / direct | still current |
| 270 | d87b9db | 2026-10-14 | TSV | пустой | empty (adjective) | empty | still current |
| 271 | d87b9db | 2026-10-14 | TSV | ранний | early (adjective) | early | still current |
| 272 | d87b9db | 2026-10-14 | TSV | чистый | clean / pure (adjective) | clean / pure | still current |
| 273 | d87b9db | 2026-10-14 | TSV | влажно | humid (adverb) | humid | still current |
| 274 | d87b9db | 2026-10-14 | TSV | возможно | possibly / perhaps (adverb) | possibly / perhaps | still current |
| 275 | d87b9db | 2026-10-14 | TSV | живо | vividly / lively (adverb) | vividly / lively | still current |
| 276 | d87b9db | 2026-10-14 | TSV | закрыто | closed (adverb) | closed | still current |
| 277 | d87b9db | 2026-10-14 | TSV | знакомо | familiar (adverb) | familiar | still current |
| 278 | d87b9db | 2026-10-14 | TSV | мокро | wet (adverb) | wet | still current |
| 279 | d87b9db | 2026-10-14 | TSV | нужно | necessary (adverb) | necessary | still current |
| 280 | d87b9db | 2026-10-14 | TSV | поздно | late (adverb) | late | still current |
| 281 | d87b9db | 2026-10-14 | TSV | прямо | straight / directly (adverb) | straight / directly | still current |
| 282 | d87b9db | 2026-10-14 | TSV | пусто | empty (adverb) | empty | still current |
| 283 | d87b9db | 2026-10-14 | TSV | рано | early (adverb) | early | still current |
| 284 | d87b9db | 2026-10-14 | TSV | атака | attack (noun) | attack | still current |
| 285 | d87b9db | 2026-10-14 | TSV | желание | wish / desire (noun) | wish / desire | still current |
| 286 | d87b9db | 2026-10-14 | TSV | конец | end (noun) | end | still current |
| 287 | d87b9db | 2026-10-14 | TSV | любовь | love (noun) | love | still current |
| 288 | d87b9db | 2026-10-14 | TSV | надежда | hope (noun) | hope | still current |
| 289 | d87b9db | 2026-10-14 | TSV | ответ | answer (noun) | answer | still current |
| 290 | d87b9db | 2026-10-14 | TSV | отдых | rest / vacation (noun) | rest / vacation | still current |
| 291 | d87b9db | 2026-10-14 | TSV | подозреваемый | suspect (noun) | suspect | still current |
| 292 | d87b9db | 2026-10-14 | TSV | помощь | help (noun) | help | still current |
| 293 | d87b9db | 2026-10-14 | TSV | приказ | order / command (noun) | order / command | still current |
| 294 | d87b9db | 2026-10-14 | TSV | работа | work / job (noun) | work / job | still current |
| 295 | d87b9db | 2026-10-14 | TSV | спасение | rescue / salvation (noun) | rescue / salvation | still current |
| 296 | d87b9db | 2026-10-14 | TSV | старт | start (noun) | start | still current |
| 297 | d87b9db | 2026-10-14 | TSV | стоимость | cost (noun) | cost | still current |
| 298 | d87b9db | 2026-10-14 | TSV | улыбка | smile (noun) | smile | still current |
| 299 | d87b9db | 2026-10-14 | TSV | ход | move / course (noun) | move / course | still current |

### 6b. Separator-only normalisation (373 rows)

`808c0c4` collapses `,` and `;` into ` / ` in every English gloss (371 rows by this classifier; plus 2 in `a885261`). No word changed. `vocabulary_source.normalize_gloss` now applies this at TSV regeneration.

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 808c0c4 | 2026-10-08 | source-word-list.md | вроде | like, kind of, sort of | like / kind of / sort of | superseded: like / kind of / sort of (hedging) |
| 2 | 808c0c4 | 2026-10-08 | source-word-list.md | затем | then, after that | then / after that | superseded: then / after that (next in sequence) |
| 3 | 808c0c4 | 2026-10-08 | source-word-list.md | иначе | otherwise, differently | otherwise / differently | superseded: otherwise / differently (or else) |
| 4 | 808c0c4 | 2026-10-08 | source-word-list.md | мало | little, few | little / few | still current |
| 5 | 808c0c4 | 2026-10-08 | source-word-list.md | много | many, much, a lot | many / much / a lot | superseded: many / much / a lot (quantity) |
| 6 | 808c0c4 | 2026-10-08 | source-word-list.md | можно | one may, it is possible/allowed to | one may / it is possible/allowed to | still current |
| 7 | 808c0c4 | 2026-10-08 | source-word-list.md | надо | it is necessary, one must/needs to | it is necessary / one must/needs to | still current |
| 8 | 808c0c4 | 2026-10-08 | source-word-list.md | однажды | once, one day | once / one day | still current |
| 9 | 808c0c4 | 2026-10-08 | source-word-list.md | пока (adverb) | for now, so far | for now / so far | still current |
| 10 | 808c0c4 | 2026-10-08 | source-word-list.md | сколько | how much, how many | how much / how many | still current |
| 11 | 808c0c4 | 2026-10-08 | source-word-list.md | сначала | at first, at the beginning | at first / at the beginning | still current |
| 12 | 808c0c4 | 2026-10-08 | source-word-list.md | а | but, and (when contrasting) | but / and (when contrasting) | still current |
| 13 | 808c0c4 | 2026-10-08 | source-word-list.md | как (conjunction) | like, as | like / as | superseded: like / as (comparison) |
| 14 | 808c0c4 | 2026-10-08 | source-word-list.md | как будто | as if, as though | as if / as though | superseded: as if / as though (neutral, unreal comparison) |
| 15 | 808c0c4 | 2026-10-08 | source-word-list.md | когда (conjunction) | when, while, as | when / while / as | superseded: when / while / as (at the time that) |
| 16 | 808c0c4 | 2026-10-08 | source-word-list.md | пока (conjunction) | while, until | while / until | superseded: while / until (for as long as) |
| 17 | 808c0c4 | 2026-10-08 | source-word-list.md | причём | moreover, and what's more | moreover / and what's more | still current |
| 18 | 808c0c4 | 2026-10-08 | source-word-list.md | пускай | even though, let | even though / let | still current |
| 19 | 808c0c4 | 2026-10-08 | source-word-list.md | словно / будто | as if, like | as if / like | still current |
| 20 | 808c0c4 | 2026-10-08 | source-word-list.md | так как | since, as | since / as | superseded: since / as (because) |
| 21 | 808c0c4 | 2026-10-08 | source-word-list.md | тоже / также | also, too | also / too | still current |
| 22 | 808c0c4 | 2026-10-08 | source-word-list.md | что | what, that | what / that | still current |
| 23 | 808c0c4 | 2026-10-08 | source-word-list.md | чтобы / чтоб | so that, in order to | so that / in order to | still current |
| 24 | 808c0c4 | 2026-10-08 | source-word-list.md | бюро | bureau, office | bureau / office | superseded: bureau / office (a bureau) |
| 25 | 808c0c4 | 2026-10-08 | source-word-list.md | жалюзи | blinds, shutters (always plural in concept) | blinds / shutters (always plural in concept) | still current |
| 26 | 808c0c4 | 2026-10-08 | source-word-list.md | кино | cinema, movie | cinema / movie | still current |
| 27 | 808c0c4 | 2026-10-08 | source-word-list.md | метро | subway, metro | subway / metro | still current |
| 28 | 808c0c4 | 2026-10-08 | source-word-list.md | пари | bet, wager | bet / wager | still current |
| 29 | 808c0c4 | 2026-10-08 | source-word-list.md | резюме | resume, summary | resume / summary | still current |
| 30 | 808c0c4 | 2026-10-08 | source-word-list.md | табло | scoreboard, display board | scoreboard / display board | still current |
| 31 | 808c0c4 | 2026-10-08 | source-word-list.md | фойе | foyer, lobby | foyer / lobby | still current |
| 32 | 808c0c4 | 2026-10-08 | source-word-list.md | -ка | go on, just (informal) | go on / just (informal) | still current |
| 33 | 808c0c4 | 2026-10-08 | source-word-list.md | будто | as if, as though (often implies doubt) | as if / as though (often implies doubt) | still current |
| 34 | 808c0c4 | 2026-10-08 | source-word-list.md | ведь | you see, after all (asserting a known fact) | you see / after all (asserting a known fact) | still current |
| 35 | 808c0c4 | 2026-10-08 | source-word-list.md | во | wow, look at that | wow / look at that | still current |
| 36 | 808c0c4 | 2026-10-08 | source-word-list.md | всё | still, constantly | still / constantly | superseded: still / all / constantly (keeps on) |
| 37 | 808c0c4 | 2026-10-08 | source-word-list.md | всё-таки | still, nevertheless | still / nevertheless | superseded: still / nevertheless (all the same) |
| 38 | 808c0c4 | 2026-10-08 | source-word-list.md | дескать | allegedly, "so they claim" (marks someone else's words) | allegedly / "so they claim" (marks someone else's words) | still current |
| 39 | 808c0c4 | 2026-10-08 | source-word-list.md | же | but, then, after all (adds emphasis) | but / then / after all (adds emphasis) | still current |
| 40 | 808c0c4 | 2026-10-08 | source-word-list.md | извините | excuse me, sorry (formal) | excuse me / sorry (formal) | superseded: excuse me / sorry (formal — when you are at fault) |
| 41 | 808c0c4 | 2026-10-08 | source-word-list.md | именно | exactly, precisely | exactly / precisely | still current |
| 42 | 808c0c4 | 2026-10-08 | source-word-list.md | конечно | of course, certainly | of course / certainly | superseded: of course / certainly (obviously so) |
| 43 | 808c0c4 | 2026-10-08 | source-word-list.md | ладно | OK, all right, fine | OK / all right / fine | superseded: OK / all right (agreeing) |
| 44 | 808c0c4 | 2026-10-08 | source-word-list.md | ли | whether, if (turns a statement into a question) | whether / if (turns a statement into a question) | still current |
| 45 | 808c0c4 | 2026-10-08 | source-word-list.md | лишь | only, merely | only / merely | superseded: only / merely (bookish) |
| 46 | 808c0c4 | 2026-10-08 | source-word-list.md | мол | supposedly, "he said" (marks reported speech; colloquial) | supposedly / "he said" (marks reported speech; colloquial) | still current |
| 47 | 808c0c4 | 2026-10-08 | source-word-list.md | не | not, don’t | not / don’t | still current |
| 48 | 808c0c4 | 2026-10-08 | source-word-list.md | ни | neither, (emphasize extremeness)&nbsp; | neither / (emphasize extremeness)&nbsp; | superseded: neither / not a single / not one |
| 49 | 808c0c4 | 2026-10-08 | source-word-list.md | ничего | nothing; it's OK, no problem | nothing / it's OK / no problem | still current |
| 50 | 808c0c4 | 2026-10-08 | source-word-list.md | ну | well, come on | well / come on | superseded: well / come on (urging) |
| 51 | 808c0c4 | 2026-10-08 | source-word-list.md | пожалуй | perhaps, I suppose | perhaps / I suppose | superseded: perhaps / I suppose (leaning towards it) |
| 52 | 808c0c4 | 2026-10-08 | source-word-list.md | простите | excuse me, forgive me (formal) | excuse me / forgive me (formal) | superseded: excuse me / forgive me (formal — to get attention) |
| 53 | 808c0c4 | 2026-10-08 | source-word-list.md | просто | simply, just | simply / just | headword renamed/removed since |
| 54 | 808c0c4 | 2026-10-08 | source-word-list.md | таки | after all, nevertheless | after all / nevertheless | still current |
| 55 | 808c0c4 | 2026-10-08 | source-word-list.md | уж | really, indeed (emphatic) | really / indeed (emphatic) | still current |
| 56 | 808c0c4 | 2026-10-08 | source-word-list.md | возле | by, near (whom/what/where) | by / near (whom/what/where) | still current |
| 57 | 808c0c4 | 2026-10-08 | source-word-list.md | вопреки | despite, contrary to (what/whom) | despite / contrary to (what/whom) | still current |
| 58 | 808c0c4 | 2026-10-08 | source-word-list.md | для | for; for the sake of (whom/what) | for / for the sake of (whom/what) | still current |
| 59 | 808c0c4 | 2026-10-08 | source-word-list.md | к / ко | to, toward (whom/what/where) | to / toward (whom/what/where) | still current |
| 60 | 808c0c4 | 2026-10-08 | source-word-list.md | кроме | except, besides (whom/what) | except / besides (whom/what) | still current |
| 61 | 808c0c4 | 2026-10-08 | source-word-list.md | между | between, among (whom/what) | between / among (whom/what) | still current |
| 62 | 808c0c4 | 2026-10-08 | source-word-list.md | мимо | past, by (whom/what/where) | past / by (whom/what/where) | still current |
| 63 | 808c0c4 | 2026-10-08 | source-word-list.md | над | above, over (where/what/whom) | above / over (where/what/whom) | still current |
| 64 | 808c0c4 | 2026-10-08 | source-word-list.md | насчёт | about, regarding (whom/what) | about / regarding (whom/what) | still current |
| 65 | 808c0c4 | 2026-10-08 | source-word-list.md | около | near, around (whom/what/where/when) | near / around (whom/what/where/when) | still current |
| 66 | 808c0c4 | 2026-10-08 | source-word-list.md | от | from, away from (whom/what/where) | from / away from (whom/what/where) | still current |
| 67 | 808c0c4 | 2026-10-08 | source-word-list.md | перед | in front of, before (where/whom/what/when) | in front of / before (where/whom/what/when) | still current |
| 68 | 808c0c4 | 2026-10-08 | source-word-list.md | поверх | over, on top of (what/where) | over / on top of (what/where) | still current |
| 69 | 808c0c4 | 2026-10-08 | source-word-list.md | под | under, below (where/what/whom) | under / below (where/what/whom) | still current |
| 70 | 808c0c4 | 2026-10-08 | source-word-list.md | против | against, opposite (whom/what/where) | against / opposite (whom/what/where) | still current |
| 71 | 808c0c4 | 2026-10-08 | source-word-list.md | через | through, across (what/where)<br>in (when/time) | through / across (what/where)<br>in (when/time) | still current |
| 72 | 808c0c4 | 2026-10-08 | TSV | больной | sick; ill | sick / ill | still current |
| 73 | 808c0c4 | 2026-10-08 | TSV | большой | big; large | big / large | still current |
| 74 | 808c0c4 | 2026-10-08 | TSV | быстрый | fast; quick | fast / quick | still current |
| 75 | 808c0c4 | 2026-10-08 | TSV | весёлый | cheerful; fun | cheerful / fun | still current |
| 76 | 808c0c4 | 2026-10-08 | TSV | вкусный | tasty; delicious | tasty / delicious | still current |
| 77 | 808c0c4 | 2026-10-08 | TSV | влажный | damp; humid | damp / humid | still current |
| 78 | 808c0c4 | 2026-10-08 | TSV | внимательный | attentive; careful | attentive / careful | still current |
| 79 | 808c0c4 | 2026-10-08 | TSV | высокий | tall; high | tall / high | still current |
| 80 | 808c0c4 | 2026-10-08 | TSV | главный | main; chief | main / chief | still current |
| 81 | 808c0c4 | 2026-10-08 | TSV | глупый | stupid; silly | stupid / silly | still current |
| 82 | 808c0c4 | 2026-10-08 | TSV | дневной | day; daytime (adj.) | day / daytime (adj.) | still current |
| 83 | 808c0c4 | 2026-10-08 | TSV | дорогой | expensive; dear | expensive / dear | still current |
| 84 | 808c0c4 | 2026-10-08 | TSV | другой | other, different | other / different | superseded: other / different (another one) |
| 85 | 808c0c4 | 2026-10-08 | TSV | единственный | only, sole | only / sole | still current |
| 86 | 808c0c4 | 2026-10-08 | TSV | живой | alive; lively | alive / lively | still current |
| 87 | 808c0c4 | 2026-10-08 | TSV | злой | mean; evil; angry | mean / evil / angry | still current |
| 88 | 808c0c4 | 2026-10-08 | TSV | известный | famous; well-known | famous / well-known | still current |
| 89 | 808c0c4 | 2026-10-08 | TSV | иной | different, other | different / other | superseded: different / other (of another kind) |
| 90 | 808c0c4 | 2026-10-08 | TSV | каждый | each, every | each / every | still current |
| 91 | 808c0c4 | 2026-10-08 | TSV | красивый | beautiful; handsome | beautiful / handsome | superseded: beautiful / handsome (good-looking) |
| 92 | 808c0c4 | 2026-10-08 | TSV | личный | personal, private | personal / private | still current |
| 93 | 808c0c4 | 2026-10-08 | TSV | лишний | extra; unnecessary | extra / unnecessary | still current |
| 94 | 808c0c4 | 2026-10-08 | TSV | лучший | better, best (attributive comparative/superlative) | better / best (attributive comparative/superlative) | still current |
| 95 | 808c0c4 | 2026-10-08 | TSV | любимый | favorite; beloved | favorite / beloved | still current |
| 96 | 808c0c4 | 2026-10-08 | TSV | лёгкий | light; easy | light / easy | superseded: light / easy (not heavy) |
| 97 | 808c0c4 | 2026-10-08 | TSV | маленький | small; little | small / little | superseded: small / little (not big) |
| 98 | 808c0c4 | 2026-10-08 | TSV | мелкий | shallow; small | shallow / small | superseded: shallow<br>small (petty, fine-grained) |
| 99 | 808c0c4 | 2026-10-08 | TSV | настоящий | real; genuine; present | real / genuine / present | still current |
| 100 | 808c0c4 | 2026-10-08 | TSV | нежный | tender; gentle | tender / gentle | still current |
| 101 | 808c0c4 | 2026-10-08 | TSV | неправильный | incorrect; wrong | incorrect / wrong | still current |
| 102 | 808c0c4 | 2026-10-08 | TSV | низкий | low; short | low / short | superseded: low / short (not tall) |
| 103 | 808c0c4 | 2026-10-08 | TSV | нужный | needed; necessary | needed / necessary | still current |
| 104 | 808c0c4 | 2026-10-08 | TSV | общий | general, common, shared | general / common / shared | still current |
| 105 | 808c0c4 | 2026-10-08 | TSV | обычный | usual; ordinary | usual / ordinary | still current |
| 106 | 808c0c4 | 2026-10-08 | TSV | огромный | huge, enormous | huge / enormous | still current |
| 107 | 808c0c4 | 2026-10-08 | TSV | одинаковый | identical; the same | identical / the same | still current |
| 108 | 808c0c4 | 2026-10-08 | TSV | остальной | remaining, the rest of | remaining / the rest of | still current |
| 109 | 808c0c4 | 2026-10-08 | TSV | острый | sharp; spicy | sharp / spicy | still current |
| 110 | 808c0c4 | 2026-10-08 | TSV | понятный | clear; understandable | clear / understandable | still current |
| 111 | 808c0c4 | 2026-10-08 | TSV | правильный | correct; right | correct / right | still current |
| 112 | 808c0c4 | 2026-10-08 | TSV | прекрасный | wonderful; beautiful | wonderful / beautiful | superseded: wonderful / beautiful (splendid) |
| 113 | 808c0c4 | 2026-10-08 | TSV | прошлый | past; last (week, year) | past / last (week, year) | still current |
| 114 | 808c0c4 | 2026-10-08 | TSV | прямой | straight; direct | straight / direct | still current |
| 115 | 808c0c4 | 2026-10-08 | TSV | разный | different; various | different / various | superseded: different / various (various, assorted) |
| 116 | 808c0c4 | 2026-10-08 | TSV | следующий | next; following | next / following | still current |
| 117 | 808c0c4 | 2026-10-08 | TSV | сложный | complicated; complex | complicated / complex | still current |
| 118 | 808c0c4 | 2026-10-08 | TSV | согласный | agreeing; in agreement | agreeing / in agreement | still current |
| 119 | 808c0c4 | 2026-10-08 | TSV | страшный | terrible, frightful, scary | terrible / frightful / scary | superseded: terrible / frightful / scary (frightening) |
| 120 | 808c0c4 | 2026-10-08 | TSV | твёрдый | hard; firm | hard / firm | superseded: hard / firm (solid, not soft) |
| 121 | 808c0c4 | 2026-10-08 | TSV | толстый | thick; fat | thick / fat | still current |
| 122 | 808c0c4 | 2026-10-08 | TSV | тупой | blunt; dumb | blunt / dumb | still current |
| 123 | 808c0c4 | 2026-10-08 | TSV | тяжёлый | heavy; hard | heavy / hard | superseded: heavy (weighty)<br>hard (difficult) |
| 124 | 808c0c4 | 2026-10-08 | TSV | уверенный | confident; sure | confident / sure | still current |
| 125 | 808c0c4 | 2026-10-08 | TSV | удобный | comfortable; convenient | comfortable / convenient | still current |
| 126 | 808c0c4 | 2026-10-08 | TSV | ужасный | terrible; awful | terrible / awful | superseded: terrible / awful (dreadful) |
| 127 | 808c0c4 | 2026-10-08 | TSV | умный | smart; clever | smart / clever | still current |
| 128 | 808c0c4 | 2026-10-08 | TSV | хитрый | cunning; sly | cunning / sly | still current |
| 129 | 808c0c4 | 2026-10-08 | TSV | целый | whole; entire | whole / entire | still current |
| 130 | 808c0c4 | 2026-10-08 | TSV | чистый | clean; pure | clean / pure | still current |
| 131 | 808c0c4 | 2026-10-08 | TSV | весело | cheerfully; merrily | cheerfully / merrily | superseded: fun (it's fun)<br>cheerfully |
| 132 | 808c0c4 | 2026-10-08 | TSV | внимательно | attentively; carefully | attentively / carefully | still current |
| 133 | 808c0c4 | 2026-10-08 | TSV | возможно | possibly; perhaps | possibly / perhaps | still current |
| 134 | 808c0c4 | 2026-10-08 | TSV | горячо | hotly; passionately | hotly / passionately | superseded: hot (to the touch)<br>passionately |
| 135 | 808c0c4 | 2026-10-08 | TSV | днём | in the daytime; in the afternoon | in the daytime / in the afternoon | still current |
| 136 | 808c0c4 | 2026-10-08 | TSV | живо | vividly; lively | vividly / lively | still current |
| 137 | 808c0c4 | 2026-10-08 | TSV | зло | spitefully; angrily | spitefully / angrily | still current |
| 138 | 808c0c4 | 2026-10-08 | TSV | коротко | briefly; short | briefly / short | still current |
| 139 | 808c0c4 | 2026-10-08 | TSV | легко | easily; lightly | easily / lightly | still current |
| 140 | 808c0c4 | 2026-10-08 | TSV | мелко | finely (chopped); shallowly | finely (chopped) / shallowly | still current |
| 141 | 808c0c4 | 2026-10-08 | TSV | мягко | softly; gently | softly / gently | superseded: softly / gently (with softness) |
| 142 | 808c0c4 | 2026-10-08 | TSV | мёртво | deathly; lifelessly | deathly / lifelessly | still current |
| 143 | 808c0c4 | 2026-10-08 | TSV | нежно | tenderly; gently | tenderly / gently | superseded: tenderly / gently (with tenderness) |
| 144 | 808c0c4 | 2026-10-08 | TSV | нормально | normally; fine | normally / fine | superseded: normally / fine (going OK) |
| 145 | 808c0c4 | 2026-10-08 | TSV | одинаково | equally; the same way | equally / the same way | still current |
| 146 | 808c0c4 | 2026-10-08 | TSV | остро | sharply; acutely | sharply / acutely | still current |
| 147 | 808c0c4 | 2026-10-08 | TSV | по-доброму | kindly; in a good way | kindly / in a good way | still current |
| 148 | 808c0c4 | 2026-10-08 | TSV | по-настоящему | really; for real | really / for real | superseded: really / for real (genuinely) |
| 149 | 808c0c4 | 2026-10-08 | TSV | по-русски | in Russian; the Russian way | in Russian / the Russian way | still current |
| 150 | 808c0c4 | 2026-10-08 | TSV | по-старому | the old way; as before | the old way / as before | still current |
| 151 | 808c0c4 | 2026-10-08 | TSV | полностью | completely; fully | completely / fully | superseded: completely / fully (in full) |
| 152 | 808c0c4 | 2026-10-08 | TSV | популярно | accessibly; in plain terms | accessibly / in plain terms | still current |
| 153 | 808c0c4 | 2026-10-08 | TSV | просто | simply; just | simply / just | headword renamed/removed since |
| 154 | 808c0c4 | 2026-10-08 | TSV | прямо | straight; directly | straight / directly | still current |
| 155 | 808c0c4 | 2026-10-08 | TSV | свободно | freely; fluently | freely / fluently | still current |
| 156 | 808c0c4 | 2026-10-08 | TSV | сильно | strongly; a lot | strongly / a lot | superseded: strongly / a lot (intensity) |
| 157 | 808c0c4 | 2026-10-08 | TSV | смело | boldly; bravely | boldly / bravely | still current |
| 158 | 808c0c4 | 2026-10-08 | TSV | тонко | thinly; subtly | thinly / subtly | still current |
| 159 | 808c0c4 | 2026-10-08 | TSV | тупо | bluntly; dully | bluntly / dully | still current |
| 160 | 808c0c4 | 2026-10-08 | TSV | тяжело | heavily; with difficulty | heavily / with difficulty | superseded: heavily (a heavy burden)<br>with difficulty (with effort) |
| 161 | 808c0c4 | 2026-10-08 | TSV | удобно | conveniently; comfortably | conveniently / comfortably | still current |
| 162 | 808c0c4 | 2026-10-08 | TSV | ужасно | terribly; awfully | terribly / awfully | still current |
| 163 | 808c0c4 | 2026-10-08 | TSV | хитро | cunningly; slyly | cunningly / slyly | still current |
| 164 | 808c0c4 | 2026-10-08 | TSV | целиком | entirely; whole | entirely / whole | superseded: entirely / whole (as a single whole) |
| 165 | 808c0c4 | 2026-10-08 | TSV | чисто | cleanly; purely | cleanly / purely | still current |
| 166 | 808c0c4 | 2026-10-08 | TSV | беда | trouble; misfortune | trouble / misfortune | still current |
| 167 | 808c0c4 | 2026-10-08 | TSV | безопасность | safety; security | safety / security | still current |
| 168 | 808c0c4 | 2026-10-08 | TSV | берег | shore; bank | shore / bank | superseded: shore / bank (of a river) |
| 169 | 808c0c4 | 2026-10-08 | TSV | бой | battle; fight | battle / fight | still current |
| 170 | 808c0c4 | 2026-10-08 | TSV | ботинок | boot; shoe | boot / shoe | still current |
| 171 | 808c0c4 | 2026-10-08 | TSV | век | century; age | century / age | superseded: century<br>age (an era) |
| 172 | 808c0c4 | 2026-10-08 | TSV | взгляд | look; glance; view | look / glance / view | superseded: look / glance (a gaze)<br>view (an opinion) |
| 173 | 808c0c4 | 2026-10-08 | TSV | вид | view; kind; appearance | view / kind / appearance | superseded: view / appearance (what something looks like)<br>kind (a type or species) |
| 174 | 808c0c4 | 2026-10-08 | TSV | вина | guilt; fault | guilt / fault | still current |
| 175 | 808c0c4 | 2026-10-08 | TSV | власть | power; authority | power / authority | still current |
| 176 | 808c0c4 | 2026-10-08 | TSV | возможность | opportunity; possibility | opportunity / possibility | still current |
| 177 | 808c0c4 | 2026-10-08 | TSV | гнев | anger; wrath | anger / wrath | superseded: anger / wrath (fury) |
| 178 | 808c0c4 | 2026-10-08 | TSV | город | city; town | city / town | still current |
| 179 | 808c0c4 | 2026-10-08 | TSV | грудь | chest; breast | chest / breast | still current |
| 180 | 808c0c4 | 2026-10-08 | TSV | грязь | dirt; mud | dirt / mud | still current |
| 181 | 808c0c4 | 2026-10-08 | TSV | движение | movement; traffic | movement / traffic | still current |
| 182 | 808c0c4 | 2026-10-08 | TSV | двор | yard; courtyard | yard / courtyard | still current |
| 183 | 808c0c4 | 2026-10-08 | TSV | девушка | young woman; girlfriend | young woman / girlfriend | still current |
| 184 | 808c0c4 | 2026-10-08 | TSV | дело | matter; affair; business | matter / affair / business | superseded: matter / affair / business (an affair) |
| 185 | 808c0c4 | 2026-10-08 | TSV | дерево | tree; wood | tree / wood | still current |
| 186 | 808c0c4 | 2026-10-08 | TSV | диван | sofa; couch | sofa / couch | still current |
| 187 | 808c0c4 | 2026-10-08 | TSV | директор | director; principal | director / principal | still current |
| 188 | 808c0c4 | 2026-10-08 | TSV | договор | agreement; contract | agreement / contract | superseded: agreement / contract (a treaty or accord) |
| 189 | 808c0c4 | 2026-10-08 | TSV | долг | debt; duty | debt / duty | still current |
| 190 | 808c0c4 | 2026-10-08 | TSV | дом | house; home | house / home | still current |
| 191 | 808c0c4 | 2026-10-08 | TSV | желание | wish; desire | wish / desire | still current |
| 192 | 808c0c4 | 2026-10-08 | TSV | живот | belly; stomach | belly / stomach | still current |
| 193 | 808c0c4 | 2026-10-08 | TSV | закономерность | pattern; regularity | pattern / regularity | still current |
| 194 | 808c0c4 | 2026-10-08 | TSV | защита | defense; protection | defense / protection | still current |
| 195 | 808c0c4 | 2026-10-08 | TSV | земля | earth; land; ground | earth / land / ground | still current |
| 196 | 808c0c4 | 2026-10-08 | TSV | злость | anger; spite | anger / spite | superseded: anger / spite (malice) |
| 197 | 808c0c4 | 2026-10-08 | TSV | значение | meaning; significance | meaning / significance | superseded: meaning / significance (what it signifies) |
| 198 | 808c0c4 | 2026-10-08 | TSV | инструмент | tool; instrument | tool / instrument | still current |
| 199 | 808c0c4 | 2026-10-08 | TSV | история | history; story | history / story | still current |
| 200 | 808c0c4 | 2026-10-08 | TSV | картина | picture; painting | picture / painting | still current |
| 201 | 808c0c4 | 2026-10-08 | TSV | кастрюля | pot; saucepan | pot / saucepan | still current |
| 202 | 808c0c4 | 2026-10-08 | TSV | кино | cinema; movies | cinema / movies | headword renamed/removed since |
| 203 | 808c0c4 | 2026-10-08 | TSV | класс | class; grade; classroom | class / grade / classroom | still current |
| 204 | 808c0c4 | 2026-10-08 | TSV | кожа | skin; leather | skin / leather | still current |
| 205 | 808c0c4 | 2026-10-08 | TSV | кот | cat (m); tomcat | cat (m) / tomcat | superseded: cat (male) / tomcat |
| 206 | 808c0c4 | 2026-10-08 | TSV | край | edge; region | edge / region | still current |
| 207 | 808c0c4 | 2026-10-08 | TSV | лист | leaf; sheet (of paper) | leaf / sheet (of paper) | still current |
| 208 | 808c0c4 | 2026-10-08 | TSV | луч | ray; beam | ray / beam | still current |
| 209 | 808c0c4 | 2026-10-08 | TSV | магазин | store; shop | store / shop | still current |
| 210 | 808c0c4 | 2026-10-08 | TSV | масло | butter; oil | butter / oil | still current |
| 211 | 808c0c4 | 2026-10-08 | TSV | машина | car; machine | car / machine | superseded: machine / car |
| 212 | 808c0c4 | 2026-10-08 | TSV | место | place; seat | place / seat | still current |
| 213 | 808c0c4 | 2026-10-08 | TSV | метро | subway; metro | subway / metro | headword renamed/removed since |
| 214 | 808c0c4 | 2026-10-08 | TSV | мир | world; peace | world / peace | still current |
| 215 | 808c0c4 | 2026-10-08 | TSV | напряжение | tension; voltage | tension / voltage | still current |
| 216 | 808c0c4 | 2026-10-08 | TSV | народ | people; nation | people / nation | superseded: people / nation (a people) |
| 217 | 808c0c4 | 2026-10-08 | TSV | нога | leg; foot | leg / foot | still current |
| 218 | 808c0c4 | 2026-10-08 | TSV | образ | image; manner | image / manner | still current |
| 219 | 808c0c4 | 2026-10-08 | TSV | обувь | footwear; shoes | footwear / shoes | still current |
| 220 | 808c0c4 | 2026-10-08 | TSV | опыт | experience; experiment | experience / experiment | still current |
| 221 | 808c0c4 | 2026-10-08 | TSV | отдых | rest; vacation | rest / vacation | still current |
| 222 | 808c0c4 | 2026-10-08 | TSV | отношение | attitude; relation | attitude / relation | still current |
| 223 | 808c0c4 | 2026-10-08 | TSV | очередь | line; queue; turn | line / queue / turn | superseded: line / queue (people waiting)<br>turn |
| 224 | 808c0c4 | 2026-10-08 | TSV | палец | finger; toe | finger / toe | still current |
| 225 | 808c0c4 | 2026-10-08 | TSV | пара | pair; couple | pair / couple | still current |
| 226 | 808c0c4 | 2026-10-08 | TSV | парень | guy; boyfriend | guy / boyfriend | still current |
| 227 | 808c0c4 | 2026-10-08 | TSV | партия | party (political); batch | party (political) / batch | still current |
| 228 | 808c0c4 | 2026-10-08 | TSV | площадь | square; area | square / area | still current |
| 229 | 808c0c4 | 2026-10-08 | TSV | повар | cook; chef | cook / chef | still current |
| 230 | 808c0c4 | 2026-10-08 | TSV | политика | politics; policy | politics / policy | still current |
| 231 | 808c0c4 | 2026-10-08 | TSV | польза | benefit; use | benefit / use | still current |
| 232 | 808c0c4 | 2026-10-08 | TSV | почта | post office; mail | post office / mail | still current |
| 233 | 808c0c4 | 2026-10-08 | TSV | право | right; law (field) | right / law (field) | still current |
| 234 | 808c0c4 | 2026-10-08 | TSV | предмет | object; school subject | object / school subject | still current |
| 235 | 808c0c4 | 2026-10-08 | TSV | преподаватель | instructor; lecturer | instructor / lecturer | still current |
| 236 | 808c0c4 | 2026-10-08 | TSV | приказ | order; command | order / command | still current |
| 237 | 808c0c4 | 2026-10-08 | TSV | причина | cause; reason | cause / reason | superseded: cause / reason (the why) |
| 238 | 808c0c4 | 2026-10-08 | TSV | продукт | product; (pl.) groceries | product / (pl.) groceries | superseded: product / (plural) groceries |
| 239 | 808c0c4 | 2026-10-08 | TSV | путь | way; path | way / path | still current |
| 240 | 808c0c4 | 2026-10-08 | TSV | пятно | stain; spot | stain / spot | still current |
| 241 | 808c0c4 | 2026-10-08 | TSV | работа | work; job | work / job | still current |
| 242 | 808c0c4 | 2026-10-08 | TSV | раз | time, occasion (as in "once, twice...") | time / occasion (as in "once, twice...") | still current |
| 243 | 808c0c4 | 2026-10-08 | TSV | решение | decision; solution | decision / solution | still current |
| 244 | 808c0c4 | 2026-10-08 | TSV | рост | height; growth | height / growth | still current |
| 245 | 808c0c4 | 2026-10-08 | TSV | рука | hand; arm | hand / arm | still current |
| 246 | 808c0c4 | 2026-10-08 | TSV | ручка | pen; handle | pen / handle | still current |
| 247 | 808c0c4 | 2026-10-08 | TSV | ряд | row, line | row / line | superseded: row / line (a row of things) |
| 248 | 808c0c4 | 2026-10-08 | TSV | связь | connection; link | connection / link | still current |
| 249 | 808c0c4 | 2026-10-08 | TSV | сила | strength; force | strength / force | still current |
| 250 | 808c0c4 | 2026-10-08 | TSV | следствие | consequence; investigation | consequence / investigation | still current |
| 251 | 808c0c4 | 2026-10-08 | TSV | случай | case; occasion | case / occasion | still current |
| 252 | 808c0c4 | 2026-10-08 | TSV | случайность | chance; accident | chance / accident | superseded: chance / accident (a coincidence) |
| 253 | 808c0c4 | 2026-10-08 | TSV | смысл | meaning; sense | meaning / sense | superseded: meaning / sense (the point of it) |
| 254 | 808c0c4 | 2026-10-08 | TSV | сон | sleep; dream | sleep / dream | superseded: sleep / dream (while asleep) |
| 255 | 808c0c4 | 2026-10-08 | TSV | спасение | rescue; salvation | rescue / salvation | still current |
| 256 | 808c0c4 | 2026-10-08 | TSV | способ | way; method | way / method | superseded: way / method (a way of doing something) |
| 257 | 808c0c4 | 2026-10-08 | TSV | средство | means; remedy | means / remedy | still current |
| 258 | 808c0c4 | 2026-10-08 | TSV | срок | term; deadline | term / deadline | still current |
| 259 | 808c0c4 | 2026-10-08 | TSV | степень | degree; extent | degree / extent | still current |
| 260 | 808c0c4 | 2026-10-08 | TSV | тайна | mystery; secret | mystery / secret | superseded: mystery / secret (a mystery) |
| 261 | 808c0c4 | 2026-10-08 | TSV | тень | shadow; shade | shadow / shade | still current |
| 262 | 808c0c4 | 2026-10-08 | TSV | товар | goods; product | goods / product | still current |
| 263 | 808c0c4 | 2026-10-08 | TSV | товарищ | comrade; companion | comrade / companion | still current |
| 264 | 808c0c4 | 2026-10-08 | TSV | угол | corner; angle | corner / angle | still current |
| 265 | 808c0c4 | 2026-10-08 | TSV | удар | blow; strike | blow / strike | still current |
| 266 | 808c0c4 | 2026-10-08 | TSV | ум | mind; intellect | mind / intellect | still current |
| 267 | 808c0c4 | 2026-10-08 | TSV | услуга | service; favor | service / favor | still current |
| 268 | 808c0c4 | 2026-10-08 | TSV | форма | shape; form; uniform | shape / form / uniform | still current |
| 269 | 808c0c4 | 2026-10-08 | TSV | характер | character; personality | character / personality | still current |
| 270 | 808c0c4 | 2026-10-08 | TSV | ход | move; course | move / course | still current |
| 271 | 808c0c4 | 2026-10-08 | TSV | художник | artist; painter | artist / painter | still current |
| 272 | 808c0c4 | 2026-10-08 | TSV | цель | goal; target | goal / target | still current |
| 273 | 808c0c4 | 2026-10-08 | TSV | цифра | digit; figure | digit / figure | still current |
| 274 | 808c0c4 | 2026-10-08 | TSV | часы | clock; watch | clock / watch | still current |
| 275 | 808c0c4 | 2026-10-08 | TSV | число | number; date | number / date | superseded: number (a numeral)<br>date (a calendar day) |
| 276 | 808c0c4 | 2026-10-08 | TSV | шкаф | wardrobe; cupboard | wardrobe / cupboard | still current |
| 277 | 808c0c4 | 2026-10-08 | TSV | шофёр | chauffeur; driver | chauffeur / driver | superseded: chauffeur / driver (a hired driver) |
| 278 | 808c0c4 | 2026-10-08 | TSV | штраф | fine; penalty | fine / penalty | superseded: fine / penalty (a money punishment) |
| 279 | 808c0c4 | 2026-10-08 | TSV | язык | language; tongue | language / tongue | still current |
| 280 | 808c0c4 | 2026-10-08 | TSV | ваш | your, yours (formal / plural) | your / yours (formal / plural) | still current |
| 281 | 808c0c4 | 2026-10-08 | TSV | какой | which, what kind of, what a... | which / what kind of / what a... | superseded: which / what kind of / what a |
| 282 | 808c0c4 | 2026-10-08 | TSV | который | which, that (relative) | which / that (relative) | superseded: which / who / that (relative) |
| 283 | 808c0c4 | 2026-10-08 | TSV | мой | my, mine | my / mine | still current |
| 284 | 808c0c4 | 2026-10-08 | TSV | наш | our, ours | our / ours | still current |
| 285 | 808c0c4 | 2026-10-08 | TSV | никакой | no kind of, none at all | no kind of / none at all | still current |
| 286 | 808c0c4 | 2026-10-08 | TSV | самый | the most, the very | the most / the very | still current |
| 287 | 808c0c4 | 2026-10-08 | TSV | такой | such, this/that kind of, so | such / this/that kind of / so | superseded: such / that kind of / so (so + adjective) |
| 288 | 808c0c4 | 2026-10-08 | TSV | твой | your, yours (informal) | your / yours (informal) | still current |
| 289 | 808c0c4 | 2026-10-08 | TSV | тот | that (one), that ... over there | that (one) / that ... over there | superseded: that (one) / that (over there) |
| 290 | 808c0c4 | 2026-10-08 | TSV | бежать/побежать | to run (on foot, one direction); to set off running | to run (on foot, one direction) / to set off running | still current |
| 291 | 808c0c4 | 2026-10-08 | TSV | бросать/бросить | throw; quit | throw / quit | still current |
| 292 | 808c0c4 | 2026-10-08 | TSV | варить/сварить | boil; cook | boil / cook | superseded: boil / cook (by boiling) |
| 293 | 808c0c4 | 2026-10-08 | TSV | водить/повести | lead; drive (a car) | lead / drive (a car) | still current |
| 294 | 808c0c4 | 2026-10-08 | TSV | возвращаться/вернуться | return; come back | return / come back | still current |
| 295 | 808c0c4 | 2026-10-08 | TSV | возить/повезти | transport; drive (someone) | transport / drive (someone) | still current |
| 296 | 808c0c4 | 2026-10-08 | TSV | вставать/встать | get up; stand up | get up / stand up | still current |
| 297 | 808c0c4 | 2026-10-08 | TSV | выходить/выйти | go out; exit | go out / exit | still current |
| 298 | 808c0c4 | 2026-10-08 | TSV | говорить/сказать | speak, talk / say, tell | speak / talk / say / tell | still current |
| 299 | 808c0c4 | 2026-10-08 | TSV | готовить/приготовить | prepare; cook | prepare / cook | superseded: prepare / cook&nbsp; |
| 300 | 808c0c4 | 2026-10-08 | TSV | делать/сделать | do; make | do / make | still current |
| 301 | 808c0c4 | 2026-10-08 | TSV | держать/подержать | to hold, keep | to hold / keep | still current |
| 302 | 808c0c4 | 2026-10-08 | TSV | догадываться/догадаться | guess; figure out | guess / figure out | still current |
| 303 | 808c0c4 | 2026-10-08 | TSV | ездить/поехать | go (by vehicle); ride | go (by vehicle) / ride | still current |
| 304 | 808c0c4 | 2026-10-08 | TSV | ехать/поехать | to go, ride, drive, travel (by vehicle, one direction) | to go / ride / drive / travel (by vehicle, one direction) | still current |
| 305 | 808c0c4 | 2026-10-08 | TSV | жалеть/пожалеть | regret; feel sorry for | regret / feel sorry for | still current |
| 306 | 808c0c4 | 2026-10-08 | TSV | жарить/пожарить | fry; roast | fry / roast | still current |
| 307 | 808c0c4 | 2026-10-08 | TSV | заканчивать/закончить | finish; end | finish / end | superseded: to finish / to end |
| 308 | 808c0c4 | 2026-10-08 | TSV | защищать/защитить | defend; protect | defend / protect | still current |
| 309 | 808c0c4 | 2026-10-08 | TSV | звонить/позвонить | call (phone); ring | call (phone) / ring | still current |
| 310 | 808c0c4 | 2026-10-08 | TSV | значить/значить | to mean, signify | to mean / signify | still current |
| 311 | 808c0c4 | 2026-10-08 | TSV | иметь/иметь | to have, possess | to have / possess | still current |
| 312 | 808c0c4 | 2026-10-08 | TSV | искать/поискать | look for; search | look for / search | still current |
| 313 | 808c0c4 | 2026-10-08 | TSV | казаться/показаться | seem; appear | seem / appear | still current |
| 314 | 808c0c4 | 2026-10-08 | TSV | касаться/коснуться | touch; concern | touch / concern | still current |
| 315 | 808c0c4 | 2026-10-08 | TSV | любить/полюбить | love; like | love / like | superseded: to love / to like |
| 316 | 808c0c4 | 2026-10-08 | TSV | менять/поменять | change; exchange | change / exchange | still current |
| 317 | 808c0c4 | 2026-10-08 | TSV | мешать/помешать | bother; hinder | bother / hinder | still current |
| 318 | 808c0c4 | 2026-10-08 | TSV | мочь/смочь | be able to; can | be able to / can | superseded: be able to / can (it is possible) |
| 319 | 808c0c4 | 2026-10-08 | TSV | наблюдать/понаблюдать | observe; watch | observe / watch | superseded: observe / watch (study attentively) |
| 320 | 808c0c4 | 2026-10-08 | TSV | надеяться/понадеяться | hope; rely on | hope / rely on | superseded: to hope / to rely on |
| 321 | 808c0c4 | 2026-10-08 | TSV | надоедать/надоесть | bore; annoy | bore / annoy | still current |
| 322 | 808c0c4 | 2026-10-08 | TSV | называть/назвать | name; call | name / call | superseded: name / call (give a name to) |
| 323 | 808c0c4 | 2026-10-08 | TSV | начинать/начать | begin; start | begin / start | superseded: to begin / to start |
| 324 | 808c0c4 | 2026-10-08 | TSV | носить/понести | carry; wear | carry / wear | still current |
| 325 | 808c0c4 | 2026-10-08 | TSV | нравиться/понравиться | to be pleasing to; (impers.) to like | to be pleasing to / (impers.) to like | still current |
| 326 | 808c0c4 | 2026-10-08 | TSV | обманывать/обмануть | deceive; cheat | deceive / cheat | still current |
| 327 | 808c0c4 | 2026-10-08 | TSV | обращаться/обратиться | turn to; address; treat | turn to / address / treat | superseded: turn to / address (direct words to someone)<br>treat (behave towards) |
| 328 | 808c0c4 | 2026-10-08 | TSV | оказываться/оказаться | turn out; end up | turn out / end up | superseded: turn out / end up (prove to be) |
| 329 | 808c0c4 | 2026-10-08 | TSV | оставаться/остаться | stay; remain | stay / remain | still current |
| 330 | 808c0c4 | 2026-10-08 | TSV | оставлять/оставить | to leave (behind), abandon | to leave (behind) / abandon | still current |
| 331 | 808c0c4 | 2026-10-08 | TSV | останавливаться/остановиться | stop; stay (at a place) | stop / stay (at a place) | still current |
| 332 | 808c0c4 | 2026-10-08 | TSV | отдавать/отдать | give back; give away | give back / give away | still current |
| 333 | 808c0c4 | 2026-10-08 | TSV | отдыхать/отдохнуть | rest; relax | rest / relax | superseded: to rest / to relax |
| 334 | 808c0c4 | 2026-10-08 | TSV | отказываться/отказаться | refuse; decline | refuse / decline | still current |
| 335 | 808c0c4 | 2026-10-08 | TSV | ошибаться/ошибиться | make a mistake; be wrong | make a mistake / be wrong | still current |
| 336 | 808c0c4 | 2026-10-08 | TSV | передавать/передать | pass; hand over; convey | pass / hand over / convey | superseded: pass / hand over / convey (hand something on) |
| 337 | 808c0c4 | 2026-10-08 | TSV | плавать/поплыть | swim; sail | swim / sail | still current |
| 338 | 808c0c4 | 2026-10-08 | TSV | поднимать/поднять | lift; raise; pick up | lift / raise / pick up | superseded: lift / raise / pick up (lift up) |
| 339 | 808c0c4 | 2026-10-08 | TSV | подходить/подойти | to approach, come up to | to approach / come up to | still current |
| 340 | 808c0c4 | 2026-10-08 | TSV | получать/получить | receive; get | receive / get | still current |
| 341 | 808c0c4 | 2026-10-08 | TSV | получаться/получиться | turn out; work out | turn out / work out | superseded: turn out / work out (come out well) |
| 342 | 808c0c4 | 2026-10-08 | TSV | попадать/попасть | to hit; to end up, find oneself | to hit / to end up / find oneself | still current |
| 343 | 808c0c4 | 2026-10-08 | TSV | предлагать/предложить | offer; suggest | offer / suggest | still current |
| 344 | 808c0c4 | 2026-10-08 | TSV | признавать/признать | admit; recognize | admit / recognize | still current |
| 345 | 808c0c4 | 2026-10-08 | TSV | приказывать/приказать | order; command | order / command | superseded: to order / to command |
| 346 | 808c0c4 | 2026-10-08 | TSV | приходить/прийти | come; arrive (on foot) | come / arrive (on foot) | still current |
| 347 | 808c0c4 | 2026-10-08 | TSV | приходиться/прийтись | (impers.) to have to; to fit, fall to | (impers.) to have to / to fit / fall to | still current |
| 348 | 808c0c4 | 2026-10-08 | TSV | проверять/проверить | check; verify | check / verify | still current |
| 349 | 808c0c4 | 2026-10-08 | TSV | провожать/проводить | see off; accompany | see off / accompany | still current |
| 350 | 808c0c4 | 2026-10-08 | TSV | происходить/произойти | happen; occur | happen / occur | superseded: happen / occur (take place) |
| 351 | 808c0c4 | 2026-10-08 | TSV | просить/попросить | ask (for); request | ask (for) / request | still current |
| 352 | 808c0c4 | 2026-10-08 | TSV | проходить/пройти | pass; go through | pass / go through | superseded: pass / go through (move past or through) |
| 353 | 808c0c4 | 2026-10-08 | TSV | разрешать/разрешить | allow; permit | allow / permit | still current |
| 354 | 808c0c4 | 2026-10-08 | TSV | растить/вырастить | raise; grow | raise / grow | superseded: raise (bring up)<br>grow (cultivate) |
| 355 | 808c0c4 | 2026-10-08 | TSV | резать/порезать | cut; slice | cut / slice | still current |
| 356 | 808c0c4 | 2026-10-08 | TSV | решать/решить | decide; solve | decide / solve | still current |
| 357 | 808c0c4 | 2026-10-08 | TSV | сдавать/сдать | take (exam) / pass (exam); hand in | take (exam) / pass (exam) / hand in | still current |
| 358 | 808c0c4 | 2026-10-08 | TSV | смотреть/посмотреть | look; watch | look / watch | superseded: look / watch (direct your eyes at) |
| 359 | 808c0c4 | 2026-10-08 | TSV | собирать/собрать | collect; gather | collect / gather | superseded: collect / gather (gather things up) |
| 360 | 808c0c4 | 2026-10-08 | TSV | собираться/собраться | gather; intend to | gather / intend to | superseded: gather (assemble)<br>intend to |
| 361 | 808c0c4 | 2026-10-08 | TSV | спасать/спасти | save; rescue | save / rescue | superseded: to save / to rescue |
| 362 | 808c0c4 | 2026-10-08 | TSV | становиться/стать | to become; to start (doing) | to become / to start (doing) | still current |
| 363 | 808c0c4 | 2026-10-08 | TSV | стирать/постирать | do laundry; wash clothes | do laundry / wash clothes | still current |
| 364 | 808c0c4 | 2026-10-08 | TSV | считать/посчитать | count; consider | count / consider | still current |
| 365 | 808c0c4 | 2026-10-08 | TSV | убирать/убрать | clean up; tidy; put away | clean up / tidy / put away | still current |
| 366 | 808c0c4 | 2026-10-08 | TSV | удаваться/удаться | to succeed, turn out well, manage | to succeed / turn out well / manage | still current |
| 367 | 808c0c4 | 2026-10-08 | TSV | учить/выучить | learn (memorize); teach | learn (memorize) / teach | still current |
| 368 | 808c0c4 | 2026-10-08 | TSV | хватать/хватить | be enough; grab | be enough / grab | still current |
| 369 | 808c0c4 | 2026-10-08 | TSV | чистить/почистить | clean; brush; peel | clean / brush / peel | superseded: to clean / to brush / to peel |
| 370 | 808c0c4 | 2026-10-08 | override dict | словно / будто | словно = as if, like (literary — a poetic simile) | словно = as if / like (literary — a poetic simile) | still current |
| 371 | 808c0c4 | 2026-10-08 | override dict | тоже / также | тоже = also, too (same action, different subject — "me too") \|\| также = also, in addition (same subject, an extra thing; more formal) | тоже = also / too (same action, different subject — "me too") \|\| также = also / in addition (same subject, an extra thing; more formal) | still current |
| 372 | a885261 | 2026-10-12 | TSV | мелкий | shallow / small (petty, fine-grained) | shallow<br>small (petty, fine-grained) | still current |
| 373 | a885261 | 2026-10-12 | TSV | век | century / age (an era) | century<br>age (an era) | still current |

## 7. Rows added, split or removed; headword identity changes paired by hand

### 7a. Hand pairings

| commit | headword | what happened | effect on the English |
|---|---|---|---|
| 8fd2ab8 | как | как (conjunction) 'like, as (белый как снег)' + new как (adverb) 'how' | 'how' left the conjunction row for the new adverb row; the conjunction gloss lost 'how' |
| 8fd2ab8 | когда | когда (conjunction) 'when, while, as (...)' + new когда (adverb) 'when' | conjunction gloss unchanged in meaning; row split by part of speech |
| 8fd2ab8 | пока | пока (conjunction) 'while, until' + new пока (adverb) 'for now, so far' | row split by part of speech |
| 8fd2ab8 | почти | почти moved from Particles to Base Adverbs | row moved between sections |
| e0e53ba | правда | правда (noun) 'truth' + new правда (adverb) 'really / indeed / actually' | headword renamed; gloss text 'truth' unchanged here (edited in 7ceeac1) |
| 1693389 | так | так (adverb) 'so / like this' + new так (particle) 'well then / all right (...)' | headword renamed; senses reordered 'like this / so' -> 'so / like this'; '(adverb)' parenthetical dropped from gloss |

### 7b. Rows removed, with the surviving row where one exists

| commit | actor | file | headword | removed gloss | survivor(s) in the same tree |
|---|---|---|---|---|---|
| 8fd2ab8 | agent | md | как | how, like, as | md:как (conjunction) = like, as (белый как снег); md:как (adverb) = how |
| 8fd2ab8 | agent | md | когда | when, while, as | md:когда (conjunction) = when, while, as (Когда я пришёл, он спал); md:когда (adverb) = when |
| 8fd2ab8 | agent | md | пока | while, until | md:пока (conjunction) = while, until; md:пока (adverb) = for now, so far |
| e0e53ba | agent | tsv | правда | truth | md:правда (adverb) = really / indeed / actually; tsv:правда (noun) = truth |
| 92f72f2 | agent | md | просто | simply / just | md:просто (particle) = simply / just; tsv:просто (adverb) = simply / just |
| 92f72f2 | agent | md | согласно | according to (what/whom) | md:согласно (preposition) = according to (what/whom); tsv:согласно (adverb) = according to |
| 92f72f2 | agent | tsv | первый | first ## first | tsv:первый (adjective) = first; tsv:первый (numeral) = first |
| 92f72f2 | agent | tsv | просто | simply / just | md:просто (particle) = simply / just; tsv:просто (adverb) = simply / just |
| 92f72f2 | agent | tsv | согласно | according to | md:согласно (preposition) = according to (what/whom); tsv:согласно (adverb) = according to |
| 45f3612 | agent | tsv | кафе | café | md:кафе = cafe |
| 45f3612 | agent | tsv | кино | cinema / movies | md:кино = cinema / movie |
| 45f3612 | agent | tsv | кофе | coffee | md:кофе = coffee |
| 45f3612 | agent | tsv | метро | subway / metro | md:метро = subway / metro |
| 45f3612 | agent | tsv | пальто | coat | md:пальто = coat |
| 1693389 | agent | md | так | like this / so (adverb) | md:так (particle) = well then / all right (resuming or confirming a point); md:так (adverb) = so / like this |
| 4794da4 | user hand-edit adopted | md | да | and, but | - |
| 4794da4 | agent text relocated (706590b) | py | -ка | go on, just (softens an imperative: скажи-ка "go on, tell me"; informal) | - |
| 4794da4 | agent text relocated (706590b) | py | -то | some- (indefinite: кто-то "someone", где-то "somewhere"; contrast -нибудь = any-) | - |
| 4794da4 | agent text relocated (706590b) | py | будто | as if, as though (often implies doubt) | - |

### 7c. Rows added (counts; text not a change of an existing gloss)

| commit | date | rows added | note |
|---|---|---|---|
| 6fabf2a | 2026-09-01 | 156 | initial import of the source document |
| 8fd2ab8 | 2026-09-22 | 58 |  |
| 92baf55 | 2026-09-26 | 1003 | first tracked TSVs; generated from the untracked workbook |
| 13b2b41 | 2026-09-26 | 2 | headwords: налево / слева, направо / справа |
| 50a9de0 | 2026-09-30 | 138 |  |
| 572194a | 2026-10-05 | 2 | headwords: замечательный, знаменитый |
| e0e53ba | 2026-10-10 | 2 | headwords: правда (adverb), правда (noun) |
| 7ceeac1 | 2026-10-11 | 99 |  |
| 92f72f2 | 2026-10-11 | 6 | headwords: первый (adjective), первый (numeral), просто (adverb), просто (particle), согласно (adverb), согласно (preposition) |
| 1693389 | 2026-10-13 | 2 | headwords: так (adverb), так (particle) |
| ed85df8 | 2026-10-18 | 6 | headwords: его, её, их, она, они, оно |
| ce413d3 | 2026-10-26 | 15 | headwords: встреча, добро, доступ, заблудиться/—, заблуждаться/—, интернет, находиться/найтись, по-английски, поблизости, повторять/повторить, приятно, скидка, туалет, фотографировать/сфотографировать, чек |

## 8. User hand-edits adopted (reported separately)

The collection value was edited by hand in Anki; the commit wrote it into source so a rebuild stops reverting it. The commit author is the agent run, the text is the user's.

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 4794da4 | 2026-09-19 | source-word-list.md | да | and, but |  | - |
| 2 | 4794da4 | 2026-09-19 | source-word-list.md | и | and | and (standard) | still current |
| 3 | 4794da4 | 2026-09-19 | source-word-list.md | как | as, like, how | how, like, as | headword renamed/removed since |
| 4 | 4794da4 | 2026-09-19 | source-word-list.md | когда | when | when, while, as | headword renamed/removed since |
| 5 | 4794da4 | 2026-09-19 | source-word-list.md | что | that, what | what, that | still current (separators later normalised by 808c0c4) |
| 6 | 4794da4 | 2026-09-19 | source-word-list.md | бы | (forms the conditional/subjunctive mood) | would (forms the conditional) | still current |
| 7 | 4794da4 | 2026-09-19 | source-word-list.md | вот | here is, there is (pointing something out) | here/there is (pointing something out) | superseded: here (is) / there (is) (pointing something out) |
| 8 | 4794da4 | 2026-09-19 | source-word-list.md | дескать | (indicates reported speech/quote) | allegedly, "so they claim" (marks someone else's words; more formal than мол) | superseded: allegedly / "so they claim" (marks someone else's words) |
| 9 | 4794da4 | 2026-09-19 | source-word-list.md | же | (adds strong emphasis) | but, then, after all (emphasis — Что же делать? "But what to do?") | superseded: but / then / after all (adds emphasis) |
| 10 | 4794da4 | 2026-09-19 | source-word-list.md | мол | (indicates reported speech/quote) | supposedly, "he said" (marks reported speech; colloquial) | still current (separators later normalised by 808c0c4) |
| 11 | 4794da4 | 2026-09-19 | source-word-list.md | не | not | not, don’t | still current (separators later normalised by 808c0c4) |
| 12 | 4794da4 | 2026-09-19 | source-word-list.md | с / со | with (whom/what)<br>from / off of (where/what) | with (whom/what)<br>from / off of (where/what)<div>since (when)</div> | still current |
| 13 | 85e4a42 | 2026-09-24 | source-word-list.md | же | but, then, after all (emphasis — Что же делать? "But what to do?") | but, then, after all (adds emphasis) | still current (separators later normalised by 808c0c4) |
| 14 | 85e4a42 | 2026-09-24 | source-word-list.md | ни | not a, neither | neither, (emphasize extremeness)&nbsp; | superseded: neither / not a single / not one |
| 15 | 52478b6 | 2026-11-01 | source-word-list.md | немного | a little bit / some | a little bit / some / few | still current |
| 16 | 52478b6 | 2026-11-01 | source-word-list.md | вот | here/there is (pointing something out) | here (is) / there (is) (pointing something out) | still current |
| 17 | 52478b6 | 2026-11-01 | source-word-list.md | ни | not a single / not one | neither / not a single / not one | still current |
| 18 | 52478b6 | 2026-11-01 | source-word-list.md | так (particle) | well then / all right (resuming or confirming a point) | well then / alright (resuming or confirming a point) | still current |
| 19 | 52478b6 | 2026-11-01 | TSV | бронь | reservation (for a hotel or restaurant) | reservation (for a place or event) | still current |
| 20 | 52478b6 | 2026-11-01 | TSV | машина | car / machine | machine / car | still current |
| 21 | 52478b6 | 2026-11-01 | TSV | какой | which / what kind of / what a... | which / what kind of / what a | still current |
| 22 | 52478b6 | 2026-11-01 | TSV | который | which / who / that | which / who / that (relative) | still current |
| 23 | 52478b6 | 2026-11-01 | TSV | тот | that (one) / that ... over there | that (one) / that (over there) | still current |
| 24 | 52478b6 | 2026-11-01 | TSV | этот | this (one) | this (one) / this (right here) | still current |
| 25 | 52478b6 | 2026-11-01 | TSV | готовить/приготовить | prepare / cook (prepare food) | prepare / cook&nbsp; | still current |
| 26 | 52478b6 | 2026-11-01 | TSV | закрывать/закрыть | close | (to) close | still current |
| 27 | 52478b6 | 2026-11-01 | TSV | уметь/суметь | be able to / know how to (a learned skill) | can / be able to / know how to (a learned skill) | still current |
| 28 | 62b5157 | 2026-11-04 | source-word-list.md | это | this is / that is / it is | this (is) / that (is) / it (is) | still current |

### 8b. Agent text relocated (not a user edit)

`4794da4` deleted these three `TRANSLATION_OVERRIDES` entries and wrote the same text into the document. The text is the agent's `706590b` text; the commit message calls it relocation.

| # | commit | date | file | headword | old | new | HEAD source |
|---|---|---|---|---|---|---|---|
| 1 | 4794da4 | 2026-09-19 | source-word-list.md | -ка | (suffix to soften a command, e.g., скажи-ка = tell me) | go on, just (softens an imperative: скажи-ка "go on, tell me"; informal) | superseded: go on / just (informal) |
| 2 | 4794da4 | 2026-09-19 | source-word-list.md | -то | (suffix to add vagueness, e.g., кто-то = someone) | some- (indefinite: кто-то "someone", где-то "somewhere"; contrast -нибудь = any-) | superseded: some- (indefinite) |
| 3 | 4794da4 | 2026-09-19 | source-word-list.md | будто | as if | as if, as though (often implies doubt) | still current (separators later normalised by 808c0c4) |
| 4 | 4794da4 | 2026-09-19 | override dict | -ка | go on, just (softens an imperative: скажи-ка "go on, tell me"; informal) |  | - |
| 5 | 4794da4 | 2026-09-19 | override dict | -то | some- (indefinite: кто-то "someone", где-то "somewhere"; contrast -нибудь = any-) |  | - |
| 6 | 4794da4 | 2026-09-19 | override dict | будто | as if, as though (often implies doubt) |  | - |

### 8c. Rows touched by both a user adoption and an agent edit (timelines)

- **готовить/приготовить**
  - 92f72f2 (2026-10-11, agent): 'prepare / cook' -> 'prepare / cook (prepare food)'
  - 52478b6 (2026-11-01, user hand-edit adopted): 'prepare / cook (prepare food)' -> 'prepare / cook&nbsp;'
- **дескать**
  - 4794da4 (2026-09-19, user hand-edit adopted): '(indicates reported speech/quote)' -> 'allegedly, "so they claim" (marks someone else\'s words; more formal than мол)'
  - a64f3bd (2026-10-07, agent): 'allegedly, "so they claim" (marks someone else\'s words; more formal than мол)' -> 'allegedly, "so they claim" (marks someone else\'s words)'
- **который**
  - ce413d3 (2026-10-26, agent): 'which / that (relative)' -> 'which / who / that'
  - 52478b6 (2026-11-01, user hand-edit adopted): 'which / who / that' -> 'which / who / that (relative)'
- **ни**
  - 85e4a42 (2026-09-24, user hand-edit adopted): 'not a, neither' -> 'neither, (emphasize extremeness)&nbsp;'
  - a8ee0cb (2026-10-17, agent): 'neither / (emphasize extremeness)&nbsp;' -> 'not a single / not one'
  - 52478b6 (2026-11-01, user hand-edit adopted): 'not a single / not one' -> 'neither / not a single / not one'
- **с / со**
  - 4e0bcce (2026-09-03, agent): 'with, from' -> 'with (whom/what)<br>from / off of (where/what)'
  - 4794da4 (2026-09-19, user hand-edit adopted): 'with (whom/what)<br>from / off of (where/what)' -> 'with (whom/what)<br>from / off of (where/what)<div>since (when)</div>'
- **уметь/суметь**
  - 92f72f2 (2026-10-11, agent): 'be able to / know how to' -> 'be able to / know how to (a learned skill)'
  - 52478b6 (2026-11-01, user hand-edit adopted): 'be able to / know how to (a learned skill)' -> 'can / be able to / know how to (a learned skill)'

The `ни` row is the overwrite the plan names: the user's `85e4a42` edit (`neither, (emphasize extremeness)&nbsp;`) was replaced by the agent's `a8ee0cb` (`not a single / not one`), and the user's collection edit was adopted again by `52478b6` (`neither / not a single / not one`).

## 9. Cross-check against the collection (1.3 drift tool)

Run: `anki_tools/source_drift_cli.py --format tsv` (read-only; it copies the collection), against `~/.local/share/Anki2/User 1/collection.anki2`, with the source at this branch's HEAD (which includes `62b5157`). The collection file's sha256 was `8fd18eec577d7898baddef73f1c2ef3af80734f2e300eaf07ba6ad3850076e5c` before and after.

Observed: 44 drifted fields, **all in the `Case` field** (the collection has case text the source has no column for yet; 4.3 writes it); **0 `Translation` fields** drift; 6 orphans (`так (adverb)`, and Mutable Nouns `пальто`, `кино`, `кафе`, `метро`, `кофе`); 0 missing. So every English text this report calls current ('still current' in the tables) is also what the collection holds, and every user-adopted value in section 8 marked 'still current' is also what the collection holds. Rows marked 'superseded' in section 3 are agent edits the collection no longer shows either, because a user adoption replaced them.

## 10. Reconciliation with the planning-time count (61)

Planning-time list: **61** agent meaning edits (58 in data files, 3 in `TRANSLATION_OVERRIDES`), plus borderline `вид` and `так (adverb)`.

Re-derived from history:

| commit | planning-time | re-derived | rows |
|---|---|---|---|
| ce413d3 | 20 (19 adverbs + который) | 20 | the 19 adverbs and который; same rows |
| d87b9db | 27 (24 verbs + плач, такой, ладно) | **26** | **23 verbs** + плач, такой, ладно. The pre-commit verbs.tsv has exactly 23 `(verb)` glosses (counting `(verb)` in `git show d87b9db^:<verbs.tsv>` gives 23), so the planner's 24 is one too many |
| 4e0bcce | 4 (с / со, по, у, вне) | 4 | same rows |
| 706590b | 3 (-то, -ка, будто) | 2 + 1 | -то and -ка are `meaning`; будто keeps its sense and drops an example, so the classifier calls it a parenthetical rewrite (section 5); counted here to match the plan |
| e0e53ba | 2 (идти, прощать) | 2 | same rows |
| 7ceeac1 | 1 (правда) | 1 | правда (noun) 'truth' to 'truth / justice' |
| 8fd2ab8 | 1 (как) | 1 | found only by hand pairing (section 7a), not by the classifier |
| 1693389 | 1 (всё) | 1 | всё; plus the borderline так (adverb) reorder |
| a8ee0cb | 1 (ни) | 1 | ни |
| 7e584f7 | 1 (привет) | 1 | привет |
| a885261 | borderline (вид) | borderline | вид: `kind` moved to its own line |

Total: **60** agent meaning edits (ce413d3 20, d87b9db 26, 4e0bcce 4, 706590b 3, e0e53ba 2, 7ceeac1 1, 8fd2ab8 1, 1693389 1, a8ee0cb 1, 7e584f7 1), against the planner's 61; the whole difference is the one verb in `d87b9db`. The classifier's own `meaning` count is 59 (section 3: 60 minus будто and как, plus the borderline вид). Adopted user edits, reported separately in section 8, are not in this count.

Authorship: all of these are agent-made by commit message. The user-edit adoptions (`4794da4`, `85e4a42`, `52478b6`, `62b5157`) match the plan's list; `62b5157` (это) is the fourth adoption the plan names.

## 11. Positive controls and reproduction

- **Control 1.** `здорово` in `ce413d3`: `'healthily'` to `'great / awesome (colloquial)'`, classified `meaning` (section 3).
- **Control 2.** `лёгкий` in `d87b9db`: `'light / easy (adjective)'` to `'light / easy (not heavy)'`, classified parenthetical rewritten (section 5); `атака` in `d87b9db`: `'attack (noun)'` to `'attack'`, parenthesis-only (section 6).
- **Control 3 (negative).** A separator-only row (`808c0c4`) is not in section 3.
- **Reproduction.** Any row: `git -C <repo> show <commit>^:<path>` and `git -C <repo> show <commit>:<path>`, read the headword's English cell. The paths are the TSV, md and dict files named in section 1.
