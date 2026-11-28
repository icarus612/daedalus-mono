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

Pure module: standard library and `audio_naming` only, no `anki` import.
`flagged_audio_cli` is the command.
"""

from collections.abc import Iterable, Sequence

from anki_tools.audio_naming import STRESSED_AUDIO_WORDS, strip_stress

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
    second request. Displayed headwords carry stress marks; audio is named
    after the plain word, so the marks are dropped.
    """
    seen: list[str] = []
    for raw in headwords:
        raw = (raw or "").strip()
        word = STRESSED_AUDIO_WORDS.get(raw) or strip_stress(raw).strip()
        variants = {part.strip() for part in word.split(" / ")}
        if len(variants) == 1:
            word = variants.pop()
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


PINK = 5
BLUE = 4
GENDER_BOTH = "both"
_FLAG_GENDER = {PINK: "female", BLUE: "male"}


def words_by_gender(
    rows: Iterable[tuple[int, str, Sequence[str]]],
    flags_wanted: Iterable[int] | None = None,
) -> dict[tuple[str, str], list[str]]:
    """Like `words_to_regenerate`, keyed by (mode, gender) instead of mode.

    Pink reports a female voice and blue a male one, so only that gender is
    redone; any other colour, or a word flagged both pink and blue, redoes both.
    """
    wanted = set(flags_wanted) if flags_wanted is not None else None
    genders: dict[tuple[str, str], set[str]] = {}
    for flags, note_type, headwords in rows:
        flag = flag_of(flags)
        if flag == UNFLAGGED or (wanted is not None and flag not in wanted):
            continue
        gender = _FLAG_GENDER.get(flag, GENDER_BOTH)
        for word in clean_headwords(headwords):
            genders.setdefault((mode_for_note_type(note_type), word), set()).add(gender)
    grouped: dict[tuple[str, str], list[str]] = {}
    for (mode, word), found in genders.items():
        gender = found.pop() if len(found) == 1 else GENDER_BOTH
        grouped.setdefault((mode, gender), []).append(word)
    return {key: sorted(words) for key, words in sorted(grouped.items())}


def slots_for_gender(slots: Sequence[str], gender: str) -> list[str]:
    if gender == GENDER_BOTH:
        return list(slots)
    return [slot for slot in slots if slot.startswith(gender[0])]


def count_by_flag(rows: Iterable[tuple[int, str, Sequence[str]]]) -> dict[int, int]:
    """Flagged cards per colour, so a report shows what was picked up."""
    counts: dict[int, int] = {}
    for flags, _, _ in rows:
        flag = flag_of(flags)
        if flag != UNFLAGGED:
            counts[flag] = counts.get(flag, 0) + 1
    return dict(sorted(counts.items()))
