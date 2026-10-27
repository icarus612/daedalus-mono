#!/usr/bin/env python3
"""Which words a flag is pointing at, and how many voices each one needs.

Flagging a card is how a mispronunciation gets reported: the flag marks the
card, but audio is named after the WORD, so the flag has to be resolved back
to headwords before anything can be regenerated. A verb note carries two of
them -- the aspects have separate audio fields -- so one flagged verb can
mean two words.

The two deck families use different voice counts (Mutable f1/m2, Immutable
f1/f2/m1/m2), which is why the result is grouped by mode rather than being
one flat list: `word_audio --mode` takes one value per run.

Pure module: standard library only, no `anki` import. `flagged_audio_cli` is
the command.
"""

from collections.abc import Iterable, Sequence

FLAG_MASK = 7
UNFLAGGED = 0

MODE_SINGLE = "single"
MODE_DOUBLE = "double"

IMMUTABLE_NOTE_TYPE = "Russian - Immutable Words (Ellis Version)"

FLAG_NAMES = {
    1: "Red",
    2: "Orange",
    3: "Green",
    4: "Blue",
    5: "Pink",
    6: "Turquoise",
    7: "Purple",
}

_PLACEHOLDERS = {"", "-", "—", "–"}


def flag_of(flags: int) -> int:
    """The flag colour in a card's `flags` column, which packs other bits."""
    return flags & FLAG_MASK


def mode_for_note_type(name: str) -> str:
    return MODE_DOUBLE if name == IMMUTABLE_NOTE_TYPE else MODE_SINGLE


def clean_headwords(headwords: Sequence[str]) -> list[str]:
    """Headwords worth voicing, in field order, de-duplicated.

    A verb with no distinct perfective stores a dash rather than an empty
    cell, and a suppletive pair can repeat a form; neither should become a
    second request.
    """
    seen: list[str] = []
    for raw in headwords:
        word = (raw or "").strip()
        if word in _PLACEHOLDERS or word in seen:
            continue
        seen.append(word)
    return seen


def words_to_regenerate(
    rows: Iterable[tuple[int, str, Sequence[str]]],
    flags_wanted: Iterable[int] | None = None,
) -> dict[str, list[str]]:
    """Words behind the flagged cards in `rows`, grouped by voice mode.

    `rows` is `(flags, notetype_name, headwords)` per CARD. Two cards of one
    note resolve to the same words, so the result is de-duplicated and
    sorted -- a run is reproducible and never voices a word twice.

    `flags_wanted` restricts to those flag colours; None takes every colour.
    An unflagged card is never a hit.
    """
    wanted = set(flags_wanted) if flags_wanted is not None else None
    grouped: dict[str, set[str]] = {MODE_SINGLE: set(), MODE_DOUBLE: set()}
    for flags, note_type, headwords in rows:
        flag = flag_of(flags)
        if flag == UNFLAGGED or (wanted is not None and flag not in wanted):
            continue
        grouped[mode_for_note_type(note_type)].update(clean_headwords(headwords))
    return {mode: sorted(words) for mode, words in grouped.items() if words}


def count_by_flag(rows: Iterable[tuple[int, str, Sequence[str]]]) -> dict[int, int]:
    """Flagged cards per colour, so a report shows what was picked up."""
    counts: dict[int, int] = {}
    for flags, _, _ in rows:
        flag = flag_of(flags)
        if flag != UNFLAGGED:
            counts[flag] = counts.get(flag, 0) + 1
    return dict(sorted(counts.items()))
