# code-review

## Round 1 — 09-27-26

```
verdict: rejected
next: impl-wrong
blocking: 2
non-blocking: 6
```

### Scope of this review

Solo `rigor: low` review of the whole `feature/mutable-words` branch diff (`git diff main...feature/mutable-words`,
38 files, 9691/-463) against `project-plans/mutable-words-09-25-26/plan.md`. Verified independently rather than
trusting lane exit reports: ran the full suite (`800 passed`, matches the build summary exactly), `ruff format
--check`/`ruff check` (clean), `plan-lifecycle.sh check` (`OK`), the fixture-relocation byte-identity
(`sha256sum` match), and — because Phase 8 mutated the user's real, live Anki collection — opened that
collection read-only myself (three separate probes, confirmed non-mutating each time) to independently confirm
the end state matches the plan's exact predicted numbers, rather than trusting the exit reports' own claims.
Reviewed the seven self-reported plan discrepancies (l1/l5/l6/l9/l11 exit reports) and confirmed each is a
reasonable, correctly-non-silent resolution, not a defect. Delegated deep per-module verification to five
parallel sub-reviews (card_audio.py/mutable_words_plan.py, vocabulary_source.py/TSVs, mutable_words_audio.py,
renumber_russian_decks.py, anki_identity.py/docs/diff-hygiene); their findings are folded in below with my own
direct re-verification of the two blocking items.

### Findings

- [blocking] **Live collection header markup diverges from the plan's "verbatim" source pattern, dropping the
  "Russian - " prefix and the breadcrumb, and orphaning the cloned CSS.**
  `libs/python/anki-tools/anki_tools/mutable_words_plan.py:109-119` (`_DECK_HEADER_HTML` /
  `_DECK_HEADER_SCRIPT`). Plan Phase 3.3 (plan.md:773-776) requires "the shared header (`#path`, `#deck`, the
  deck-name script) taken verbatim from note type `1698803891108`". I pulled the REAL template from the live
  collection for both the source note type (id `1698803891108`) and its already-shipped sibling "Russian -
  Immutable Words (Ellis Version)" (id `3897610691970966744`): both use
  `<div id="path"></div><div id="deck">{{Deck}}</div>` plus a script that sets
  `deck.innerHTML = "Russian - " + dName[dName.length-1].split(". ")[1]` and populates `#path` with
  `dName.join(" > ")` (the full breadcrumb). The shipped Mutable Words note types instead use
  `<div id="deck-header"></div>` with a script that does only `el.textContent = header` — no `"Russian - "`
  prefix, no `#path` breadcrumb, different div id. The CSS is cloned byte-identical from the source (confirmed:
  `mutable_nouns_notetype["css"] == source_notetype["css"]` → `True`, live), and that CSS has rules for
  `#deck`/`#path`/`#front`/`#back` but **none for `#deck-header`** — so the new header div renders unstyled on
  every one of the 1004 live notes / 2366 cards already imported into the user's collection. This also leaves
  Phase 8.4's own acceptance criterion unmet: "the deck header resolving (not `Russian - undefined`)" implies
  the `"Russian - "` prefix should appear; it does not. Root cause, per `l1-exit.md`'s self-reported discrepancy
  #3: the real note type was "permission-classifier-blocked" during that lane's work, so the header was "built
  to specification instead" of copied verbatim — but no test or golden fixture anywhere verifies the
  reconstruction against the real note type (confirmed: no such test exists). Owner: lane 1 / subphase 3.3. Fix
  is bounded and low-risk given the already-proven reimport-idempotence property: correct the two constants to
  match the real `#path`/`#deck` structure and prefix, then rebuild and re-import the `.apkg` (updates the
  already-created notes in place under their stable GUIDs/note-type ids; no duplicate risk, per 4.2/7.2's own
  regression tests).
- [blocking] **`renumber_russian_decks.verify_renumber()` never checks deck names post-apply — only the id-set
  and per-id card counts.** `libs/python/anki-tools/anki_tools/renumber_russian_decks.py:71-78`. Plan subphase
  6.1's acceptance criteria (plan.md:1048-1051) explicitly require asserting
  `col.decks.id_for_name(old) is None` and `id_for_name(new) is not None` after applying, plus confirming "only
  the three parent names (plus their four children, by prefix) have changed." The shipped `verify_renumber`
  checks only `set(before) ^ set(after)` (the id set) and per-id card counts — never names. A rename that
  silently no-op'd (same id, same card count, unchanged name — e.g. if `col.decks.rename` ever failed
  non-fatally) would pass this check undetected. No test exercises `verify_renumber`'s or
  `snapshot_russian_subtree`'s failure path directly (grep for either function name in
  `tests/test_renumber_russian_decks.py` returns nothing beyond the import); the only place names are actually
  cross-checked is inside a CLI-level test's own separate assertions, not inside the production safety check
  that ran for real. This tool already executed successfully against the live collection — I independently
  confirmed via a read-only probe that all three decks are correctly renamed (`4. Sentences (lingo llama)`,
  `5. 100 Words & Phrases`, `6. Master Russian 300+`, card counts unchanged, `2. Immutable Words` subtree
  untouched) — so no harm occurred this time, but the safety net the plan specified for this irreversible,
  high-stakes operation shipped incomplete. Owner: lane 4 / subphase 6.1.
- [non-blocking] `card_audio.py`'s generated JS comment hardcodes the literal text
  `window.__immutableWordsAudioChoice` even when instantiated for a different `state_key` (e.g.
  `__mutableVerbPerfectiveChoice`), while the executable code two lines below correctly uses the substituted
  key. Contradicts the plan's explicit "preserved verbatim, with only the state-key name substituted"
  instruction (plan.md:525-526), but it's inert HTML-comment text, never executed, and no test asserts on it.
  Fix is a one-line placeholder substitution in `card_audio.py`'s template.
- [non-blocking] `plan.md`'s Stack table (~line 118) still reads `openpyxl` as "NOT PRESENT ... Phase 2.3 adds
  it and records the version `uv lock` actually resolves" — the resolved version (`3.1.5`, confirmed directly
  in `uv.lock`) was never written back into the plan's own Stack table, though subphase 2.3's acceptance
  criteria ask for exactly that. Doc-only, trivial to fix.
- [non-blocking] `vocabulary_source.py:82`, `_normalize_cell(value: object) -> str` — convention 12 bans
  "Any/object escape hatches." This reads as legitimate type-narrowing over genuinely heterogeneous openpyxl
  cell values (`str`/`int`/`float`/`None`), not an escape hatch, but it literally matches the banned wording and
  is worth an explicit maintainer sign-off (or a `Union[str, int, float, None]` alias) rather than silence.
- [non-blocking] The "open collection / catch `DBError`+`AnkiException`" block and the "resolve backup dir +
  `create_backup`" block are now copy-duplicated across three modules (`renumber_russian_decks.py`,
  `rebalance_due.py`, and `immutable_words.py`/`mutable_words.py`'s own variants). Plan-endorsed
  pattern-following (each subphase was told to mirror an existing module), so not a violation, but a real
  candidate for a shared helper if a fourth mutating tool is ever added.
- [non-blocking] `mutable_words_audio.py`'s `generate()` re-derives its own per-word "already present" check
  (`os.path.isfile(build_filename(...))`) rather than consuming `pending_pairs`'s output directly — duplicated
  existence-check logic, apparently deliberate (it's what makes the doubled-word-list dedup test pass) and
  harmless, but worth a maintainer's note rather than silence.
- [non-blocking] The Verbs-only "aspect hint" div (`<div class="detail-title">{primary_field}</div>` on the
  reverse-card question sides, `mutable_words_plan.py:581-588`) has no equivalent on Nouns/Adjectives/Adverbs'
  non-audio question sides. Reasonable UX (it's the fix for discrepancy #4's `CardTypeError`), and the plan
  doesn't specify either way, but the asymmetry is worth a maintainer's explicit confirmation it's intended to
  stay this way rather than being extended or reverted.

### Open questions

- The run's own audit trail does not explain how Phase 8.3/8.4 actually completed. `l7-exit.md` (the newest
  exit report, `status: blocked`) records the mutating renumber invocation
  (`anki_tools.renumber_russian_decks --yes`) being **refused by the harness's own Auto Mode classifier**, with
  the live collection confirmed byte-identical/unmutated at that point, and `progress-log.md`'s last entries
  still list `8.3 renumber -> 8.4 import` as outstanding. Yet I independently confirmed, by opening the live
  collection read-only myself, that both steps DID complete afterward and exactly match the plan's predicted
  end state: `Languages::Russian::3. Mutable Words` present with 1004 notes / 2366 cards across the four
  correctly-named subdecks, the four note types at their exact predicted deterministic ids with no `+`-suffixed
  duplicates, `2. Immutable Words` and `1. Alphabet` untouched, and the three renumbered decks correctly at
  `4.`/`5.`/`6.` with unchanged card counts. New backup files exist (`backup-2026-09-27-21.28.58.colpkg`,
  `backup-2026-09-27-21.29.21.colpkg`) dated after `l7-exit.md`'s own snapshot, consistent with a follow-up
  invocation (very likely the user themselves, given the harness's own denial and `l7-exit.md`'s "What is
  needed to continue" section naming exactly that as the unblock path) — but no exit report or progress-log
  entry records it. The real-world OUTCOME is verified correct by me directly; this question is about the
  MISSING RECORD of how it got there. Please confirm who/what performed the final `--yes` invocations, and
  make sure Phase 9.1's runbook (not yet written, correctly sequenced after this gate) states the true sequence
  of events rather than the plan's projected one.

## Round 2 — 09-27-26

```
verdict: ready
next: proceed
blocking: 0
non-blocking: 1
```

### Scope of this review

Solo `rigor: low` re-review, cold context, of the two round-1 blocking fixes (commits `088c62c` deck
header, `8ea341e` verify_renumber) plus the docs/plan reconciliation commit (`50f5f47`), all merged
onto `feature/mutable-words` (still unpushed/unmerged into `main`). Verified independently rather than
trusting the dispatch note: read both fix diffs directly; ran the affected test files and the full
suite (`808 passed, 0 failed, 0 skipped` — matches the claim exactly); ran `ruff format --check` /
`ruff check` (clean) and `check-diff-hygiene.sh --base main` (clean, no attribution, no comment-budget
violations) over the whole branch diff; ran `plan-lifecycle.sh check` (`OK`). Built independent
positive controls for both fixes rather than trusting the report of them: reconstructed the pre-fix
`verify_renumber` and confirmed it silently passes a hand-built no-op-rename case with no exception;
reconstructed the pre-fix `_DECK_HEADER_HTML`/`_DECK_HEADER_SCRIPT` and confirmed both fail the new
tests against a fresh read of the real note type `1698803891108`, including the CSS-coverage check
correctly flagging `#deck-header` as uncovered. Because the dispatch note claimed the header fix is
now live on the user's real collection, opened that collection read-only myself (copy-then-open,
mtime-verified unchanged before/after) to independently confirm all four Mutable Words note types now
carry `id="path"`/`id="deck"`, the `"Russian - "` prefix, no `#deck-header`, and CSS identical to the
source note type, and that all four subdeck card counts are unchanged (1082/716/304/264, 2366 total
cards / 1004 notes). Also confirmed a fourth backup (`backup-2026-09-27-22.25.26.colpkg`) exists,
dated after the docs commit, consistent with the claimed re-import. Confirmed both fix commits are
genuinely merged onto `feature/mutable-words` (`git branch --contains` both) and confirmed `main`'s
own recent history independently supports the new root `CLAUDE.md`'s claim (squash-merged PRs
`#18`-`#22` by number, followed by two `feat(anki-tools)` commits with no PR number going straight to
`main`; `CLAUDE_BASE_BRANCH=main` in both `.claude/settings.json` and `.agents/settings.json`) — the
file is accurate and minimal (10 lines). Re-checked all six round-1 non-blocking findings against the
current diff: none of the files they concern (`card_audio.py`, `plan.md`'s Stack table,
`vocabulary_source.py`, `rebalance_due.py`/`immutable_words.py`, `mutable_words_audio.py`,
`mutable_words_plan.py`'s aspect-hint div) were touched by round 2's commits, so all six stand exactly
as before — none has become blocking.

### Findings

- [non-blocking] **The committed docs (`docs/libs/python/anki-tools/mutable-words.md` and
  `mutable-words-runbook.md`, both from commit `50f5f47`, 22:23:29) now read as stale on one material
  fact.** Both explicitly state the header fix has "not yet been pushed onto the live collection" and
  that the re-import "had not been performed as of this writing." That was true when written, but the
  actual re-import ran ~2 minutes later (the fourth backup is timestamped 22:25:26) and is correctly
  recorded in `progress-log.md`'s later entry — I independently confirmed the fix is in fact live (see
  Scope above). Since this branch has no PR gate after this review (lands by direct merge per the new
  `CLAUDE.md`), the two docs pages will land on `main` still saying the fix is pending when it isn't.
  No code or data risk — the run's own progress log already has the true, later state, and I verified
  the live collection directly rather than trusting either document — but worth a short addendum to
  both pages (a one-paragraph "Update" noting the fourth backup and the `0 new / 1004 updated`
  re-import) before or shortly after the push to `main`, so a future reader of the shipped record isn't
  misled. Trivial, doc-only, does not warrant a third review round.

### Open questions

None. Round 1's open question (the missing audit-trail record of who ran 8.3/8.4) is now answered by
the docs commit's runbook section 3–4, which I independently spot-checked against `progress-log.md`
and found consistent.
