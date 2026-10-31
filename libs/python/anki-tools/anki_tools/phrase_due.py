#!/usr/bin/env python3
"""Find phrase-sourced words whose every card is still new.

The phrase deck teaches whole utterances; the words inside them are taught
separately in the Mutable and Immutable decks. A word that has only ever
been met inside a phrase routinely sits with EVERY card still new, so it
never comes up -- it waits behind hundreds of genuinely unseen words even
though the phrase already taught it.

This is the companion to `counterpart_due`, not a copy of it. That module
selects a NEW card whose SIBLING has been studied, and deliberately skips a
note whose cards are all new as "a word simply not started yet". Here the
all-new note is exactly the target: membership in a phrase is the evidence
that the word is not really new, and that evidence lives in the phrase deck
rather than in the note's own card states. The two predicates are therefore
complements -- a note is a hit for at most one of them, never both.

The condition recurs. Every phrase entry added later brings its own words,
so a single sweep never settles it and the result is sorted and stable so
re-running is safe.

SUSPENDED cards are never selected. A suspended card was deliberately taken
out of circulation, and Anki's `set_due_date` silently unsuspends whatever
it touches, so including one here would quietly undo that decision. The
count skipped for that reason is reported rather than swallowed.

Pure module: standard library only, no `anki` import. `phrase_due_cli` is
the command.
"""

import re
import unicodedata
from collections.abc import Iterable, Sequence

NEW_TYPE = 0
SUSPENDED_QUEUE = -1

STRESS_MARKS = frozenset("́̀")

_TAGS = re.compile(r"<[^>]+>")
_TRAILING_QUALIFIER = re.compile(r"\s*\([^()]*\)\s*$")
_WORD = re.compile(r"[^\W\d_]+(?:-[^\W\d_]+)*", re.UNICODE)


def normalize_form(text: str) -> str:
    """One comparable surface form: NFC, lowercase, unstressed, `ё`->`е`.

    The final re-normalization is load-bearing: folding `ё` after
    decomposition leaves combining sequences behind, and a prior run
    reported 32 false misses by comparing those against composed forms.
    """
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    stripped = "".join(ch for ch in decomposed if ch not in STRESS_MARKS)
    folded = unicodedata.normalize("NFC", stripped).replace("ё", "е")
    return unicodedata.normalize("NFC", folded)


def headword_variants(headword: str) -> list[str]:
    """The spellings one headword field stands for.

    `в / во` is one note covering two spellings, and `как (conjunction)` is
    one spelling carrying an editorial qualifier that is not part of the
    word. Both shapes have to resolve or a phrase token matches nothing.
    """
    bare = _TRAILING_QUALIFIER.sub("", _TAGS.sub("", headword)).strip()
    return [part.strip() for part in bare.split("/") if part.strip()]


def tokenize(text: str) -> list[str]:
    """Normalized word tokens of a phrase, hyphenated words kept whole."""
    return [normalize_form(m) for m in _WORD.findall(_TAGS.sub(" ", text))]


def build_taught_index(
    notes: Iterable[tuple[int, Sequence[str]]],
) -> dict[str, set[int]]:
    """Surface form -> the taught note ids carrying it.

    `notes` is `(note_id, headwords)`; a verb contributes both aspects. The
    value is a SET because one spelling can be two notes on purpose -- the
    homonym pairs (`правда` noun and adverb) are separate words.
    """
    index: dict[str, set[int]] = {}
    for note_id, headwords in notes:
        for headword in headwords:
            for variant in headword_variants(headword):
                index.setdefault(normalize_form(variant), set()).add(note_id)
    return index


def resolve_phrase_note_ids(
    phrase_texts: Iterable[str],
    taught_index: dict[str, set[int]],
) -> set[int]:
    """Taught note ids reached by any word of any phrase.

    Single-word entries and multi-word phrases go through the same path,
    which is what "every word that's by itself and every word from a
    phrase" requires. Matching is by exact normalized form; an inflection
    whose lemma is taught does not resolve here.
    """
    resolved: set[int] = set()
    for text in phrase_texts:
        for token in tokenize(text):
            resolved |= taught_index.get(token, set())
    return resolved


def _group_by_note(
    rows: Iterable[tuple[int, int, int, int]],
    phrase_note_ids: set[int] | frozenset[int],
) -> dict[int, list[tuple[int, int, int]]]:
    by_note: dict[int, list[tuple[int, int, int]]] = {}
    for card_id, note_id, card_type, queue in rows:
        if note_id in phrase_note_ids:
            by_note.setdefault(note_id, []).append((card_id, card_type, queue))
    return by_note


def _all_new(cards: Sequence[tuple[int, int, int]]) -> bool:
    return all(card_type == NEW_TYPE for _, card_type, _ in cards)


def find_all_new_cards(
    rows: Iterable[tuple[int, int, int, int]],
    phrase_note_ids: set[int] | frozenset[int],
) -> list[int]:
    """Card ids of phrase-sourced notes whose EVERY card is still new.

    `rows` is `(card_id, note_id, type, queue)` straight out of the `cards`
    table. Returns ids in ascending order so a run is reproducible.
    Suspended cards are excluded; a note with even one studied card is left
    to `counterpart_due`.
    """
    due = []
    for cards in _group_by_note(rows, phrase_note_ids).values():
        if not _all_new(cards):
            continue
        due.extend(card_id for card_id, _, queue in cards if queue != SUSPENDED_QUEUE)
    return sorted(due)


def count_suspended_skipped(
    rows: Iterable[tuple[int, int, int, int]],
    phrase_note_ids: set[int] | frozenset[int],
) -> int:
    """How many all-new phrase-sourced cards were left alone for being
    suspended -- reported so the skip is visible rather than silent."""
    skipped = 0
    for cards in _group_by_note(rows, phrase_note_ids).values():
        if not _all_new(cards):
            continue
        skipped += sum(1 for _, _, queue in cards if queue == SUSPENDED_QUEUE)
    return skipped
