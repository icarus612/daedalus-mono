#!/usr/bin/env python3
"""Every word the Russian phrase deck teaches, resolved against the words
the mutable and immutable decks already teach.

The phrase deck (`Russian - Common Words (Ellis Version)`) holds whole
utterances, so its vocabulary is invisible to any report that looks at
headwords: `Можно сфотографировать?` is one note, two words, and neither
of them is a card. This module takes the deck apart word by word -- single
word entries and multi-word phrases down the same path -- and says of each
word whether it is taught, and if so what state its cards are in.

Resolution runs in two tiers, and the order is the whole point:

1. **Surface** -- the normalized token is a form some taught note already
   spells out, either as its headword or in one of its inflection fields
   (`Plural`, `Oblique Forms`, `я (1sg)`, ...). No guessing.
2. **Lemma** -- an explicit ending table rewrites the token into candidate
   dictionary forms, and a candidate counts only if it is itself in the
   surface index. Nothing is invented: an untaught word produces candidates
   that miss, and is reported missing.

Tier 1 before tier 2 matters: `встречи` is the stored plural of the noun
`встреча`, and a lemma guess alone would reach the verb `встречать`.

Normalization is NFC, lowercase, stress marks stripped, `ё` folded to `е`,
then NFC AGAIN. The second pass is load-bearing: a decomposed `ё` is
`е` + U+0308, which only becomes foldable after the first composition.

Pure module: standard library only, no `anki` import. `phrase_words_cli`
is the command.
"""

import re
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from typing import NamedTuple

PHRASE_NOTE_TYPE = "Russian - Common Words (Ellis Version)"
PHRASE_DECK = "Languages::Russian::6. Russian Phrases"

NEW_TYPE = 0
SUSPENDED_QUEUE = -1

STUDIED = "studied"
ALL_NEW = "all-new"
PART_NEW = "part-new"
SUSPENDED = "suspended"
NO_CARDS = "no-cards"
MISSING = "missing"
STATES = (STUDIED, ALL_NEW, PART_NEW, SUSPENDED, NO_CARDS, MISSING)

VIA_SURFACE = "surface"
VIA_LEMMA = "lemma"

HEADWORD_FIELDS = ("Russian", "Russian (m)", "Adverb", "Imperfective", "Perfective")
INFLECTION_FIELDS = (
    "Feminine",
    "Neuter",
    "Plural",
    "Short Form",
    "Comparative",
    "Genitive Sg",
    "Genitive Pl",
    "Genitive",
    "Gender Forms",
    "Oblique Forms",
    "я (1sg)",
    "ты (2sg)",
    "они (3pl)",
    "Past (m / f)",
)

STRESS_MARKS = ("́", "̀")
YO = "ё"
YE = "е"

_MARKUP = re.compile(r"<[^>]*>")
_PARENTHETICAL = re.compile(r"\([^)]*\)")
_TOKEN = re.compile(r"[Ѐ-ӿ]+(?:-[Ѐ-ӿ]+)*")

_PRESENT_ENDINGS = (
    "ете",
    "ите",
    "ешь",
    "ишь",
    "ем",
    "им",
    "ют",
    "ут",
    "ят",
    "ат",
    "ет",
    "ит",
    "ю",
    "у",
    "й",
    "и",
    "ь",
)
_INFINITIVE_ENDINGS = (
    "ть",
    "ить",
    "ать",
    "ять",
    "еть",
    "уть",
    "ыть",
    "нуть",
    "овать",
    "евать",
    "ывать",
    "ивать",
)
_EPENTHETIC = (("бл", "б"), ("вл", "в"), ("пл", "п"), ("мл", "м"), ("фл", "ф"))
_NOMINAL_ENDINGS = (
    "ыми",
    "ими",
    "ого",
    "его",
    "ому",
    "ему",
    "ую",
    "юю",
    "ая",
    "яя",
    "ое",
    "ее",
    "ые",
    "ие",
    "ой",
    "ей",
    "ом",
    "ем",
    "ым",
    "им",
    "ах",
    "ях",
    "ам",
    "ям",
    "ов",
    "ев",
    "ы",
    "и",
    "а",
    "я",
    "о",
    "е",
    "у",
    "ю",
    "ь",
    "й",
)
_NOMINAL_SUFFIXES = (
    "",
    "а",
    "я",
    "о",
    "е",
    "ь",
    "ы",
    "и",
    "й",
    "ый",
    "ий",
    "ой",
    "ая",
    "ое",
    "ые",
)
_REFLEXIVE = ("ся", "сь")
_VOWELS = "аеиоуыэюя"
_MIN_VERB_STEM = 2
_MIN_NOMINAL_STEM = 3


class TaughtWord(NamedTuple):
    """One taught note: its headword as written, and every surface form of
    it the note spells out, normalized."""

    headword: str
    note_id: int
    forms: tuple[str, ...]


class Resolution(NamedTuple):
    token: str
    word: TaughtWord
    matched: str
    via: str


class WordRecord(NamedTuple):
    token: str
    phrases: tuple[str, ...]
    headword: str | None
    matched: str | None
    via: str
    state: str


def normalize(text: str) -> str:
    composed = unicodedata.normalize("NFC", text).lower()
    for mark in STRESS_MARKS:
        composed = composed.replace(mark, "")
    composed = composed.replace(YO, YE)
    return unicodedata.normalize("NFC", composed)


def strip_markup(text: str) -> str:
    return _MARKUP.sub(" ", text)


def tokenize(text: str) -> list[str]:
    """Word tokens of a Russian field, hyphenated adverbs kept whole."""
    return _TOKEN.findall(normalize(strip_markup(text)))


def is_taught_note_type(name: str) -> bool:
    """Whether a note type is part of the taught-word index.

    The phrase deck's own type is deliberately excluded -- it is the thing
    being audited, not evidence that anything is taught.
    """
    stripped = name.strip()
    if not stripped.startswith("Russian - ") or "Common Words" in stripped:
        return False
    return "Immutable Words" in stripped or "Mutable " in stripped


def taught_word(
    note_id: int, field_names: Sequence[str], fields: Sequence[str]
) -> TaughtWord | None:
    """Build a `TaughtWord` from one note's field names and values.

    Returns `None` when the note type carries no headword field, which is
    how a non-vocabulary type drops out without a name check.
    """
    values = dict(zip(field_names, fields))
    headwords = [
        values[name].strip()
        for name in HEADWORD_FIELDS
        if tokenize(values.get(name, ""))
    ]
    if not headwords:
        return None

    forms: list[str] = []
    for raw in headwords:
        forms.extend(tokenize(_PARENTHETICAL.sub(" ", raw)))
    for name in INFLECTION_FIELDS:
        forms.extend(tokenize(values.get(name, "")))

    seen: dict[str, None] = {}
    for form in forms:
        seen.setdefault(form, None)
    return TaughtWord(
        headword=" / ".join(headwords), note_id=note_id, forms=tuple(seen)
    )


def build_index(words: Iterable[TaughtWord]) -> dict[str, TaughtWord]:
    """Map every surface form to its word. First claim on a form wins, so a
    headword never loses its own spelling to another note's inflection."""
    index: dict[str, TaughtWord] = {}
    for word in words:
        for form in word.forms:
            index.setdefault(normalize(form), word)
    return index


def lemma_candidates(token: str) -> list[str]:
    """Dictionary forms `token` could be an inflection of.

    Generated from explicit ending tables, deduplicated, longest first so a
    caller that takes the first hit prefers `какой` over `как`. These are
    candidates only -- a caller must confirm each against the index.
    """
    out: list[str] = []
    bases = [(token, "")]
    for particle in _REFLEXIVE:
        if token.endswith(particle) and len(token) - len(particle) > _MIN_VERB_STEM:
            bases.append((token[: -len(particle)], particle))

    for base, particle in bases:
        for ending in _PRESENT_ENDINGS:
            if not base.endswith(ending):
                continue
            stem = base[: -len(ending)]
            if len(stem) < _MIN_VERB_STEM:
                continue
            stems = [stem]
            for cluster, plain in _EPENTHETIC:
                if stem.endswith(cluster):
                    stems.append(stem[: -len(cluster)] + plain)
            for candidate_stem in stems:
                for suffix in _INFINITIVE_ENDINGS + _PRESENT_ENDINGS:
                    out.append(candidate_stem + suffix + particle)
                    if candidate_stem[-1] in _VOWELS:
                        out.append(candidate_stem[:-1] + suffix + particle)
        for ending in _NOMINAL_ENDINGS:
            if not base.endswith(ending):
                continue
            stem = base[: -len(ending)]
            if len(stem) < _MIN_NOMINAL_STEM:
                continue
            for suffix in _NOMINAL_SUFFIXES:
                out.append(stem + suffix + particle)
        for suffix in _NOMINAL_SUFFIXES:
            out.append(base + suffix + particle)

    return sorted(set(out), key=lambda form: (-len(form), form))


def resolve(
    token: str, index: Mapping[str, TaughtWord], use_lemma: bool = True
) -> Resolution | None:
    """The taught word `token` is a form of, or `None` if nothing teaches it.

    `use_lemma=False` restricts the answer to forms the notes spell out,
    which is what reproduces an earlier surface-only count.
    """
    key = normalize(token)
    if key in index:
        return Resolution(token=key, word=index[key], matched=key, via=VIA_SURFACE)
    if not use_lemma:
        return None
    for candidate in lemma_candidates(key):
        if candidate in index:
            return Resolution(
                token=key, word=index[candidate], matched=candidate, via=VIA_LEMMA
            )
    return None


def card_state(rows: Iterable[tuple[int, int]]) -> str:
    """Bucket a note's cards from their `(type, queue)` rows.

    A suspended card is out of circulation, so it does not make the word
    part-new; a note whose cards are ALL suspended is reported as such.
    """
    cards = list(rows)
    if not cards:
        return NO_CARDS
    live = [
        (card_type, queue) for card_type, queue in cards if queue != SUSPENDED_QUEUE
    ]
    if not live:
        return SUSPENDED
    new_count = sum(1 for card_type, _ in live if card_type == NEW_TYPE)
    if new_count == len(live):
        return ALL_NEW
    if new_count:
        return PART_NEW
    return STUDIED


def audit(
    phrases: Sequence[str],
    index: Mapping[str, TaughtWord],
    card_rows: Mapping[int, Sequence[tuple[int, int]]],
    use_lemma: bool = True,
) -> list[WordRecord]:
    """One record per distinct token across `phrases`, ordered by token.

    `card_rows` maps a taught note id to its cards' `(type, queue)` rows.
    """
    sources: dict[str, list[str]] = {}
    for phrase in phrases:
        for token in tokenize(phrase):
            seen = sources.setdefault(token, [])
            if phrase not in seen:
                seen.append(phrase)

    records = []
    for token in sorted(sources):
        found = resolve(token, index, use_lemma=use_lemma)
        if found is None:
            records.append(
                WordRecord(
                    token=token,
                    phrases=tuple(sources[token]),
                    headword=None,
                    matched=None,
                    via="",
                    state=MISSING,
                )
            )
            continue
        records.append(
            WordRecord(
                token=token,
                phrases=tuple(sources[token]),
                headword=found.word.headword,
                matched=found.matched,
                via=found.via,
                state=card_state(card_rows.get(found.word.note_id, ())),
            )
        )
    return records


def group_by_state(records: Iterable[WordRecord]) -> dict[str, list[WordRecord]]:
    grouped: dict[str, list[WordRecord]] = {state: [] for state in STATES}
    for record in records:
        grouped[record.state].append(record)
    return grouped
