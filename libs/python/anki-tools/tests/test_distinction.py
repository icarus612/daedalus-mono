"""Contract tests for the two distinction fields: one marker per side."""

import dataclasses
from pathlib import Path

import pytest

from anki_tools import case_field, collisions, distinction
from anki_tools.audio_naming import strip_qualifier

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"


@pytest.mark.parametrize(
    "text,expected",
    [
        ("как (conjunction)", "conjunction"),
        ("как (adverb)", "adverb"),
        ("согласно (preposition)", "preposition"),
        ("дом", ""),
        ("в / во", ""),
        ("о / об", ""),
        ("ни... ни...", ""),
        ("", ""),
    ],
)
def test_qualifier_of_reads_only_a_trailing_parenthetical(text, expected):
    assert distinction.qualifier_of(text) == expected


@pytest.mark.parametrize(
    "headword,word,qualifier",
    [
        ("как (conjunction)", "как", "conjunction"),
        ("когда (adverb)", "когда", "adverb"),
        ("первый (numeral)", "первый", "numeral"),
        ("дом", "дом", ""),
        ("в / во", "в / во", ""),
    ],
)
def test_qualifier_of_is_the_inverse_of_strip_qualifier(headword, word, qualifier):
    assert strip_qualifier(headword) == word
    assert distinction.qualifier_of(headword) == qualifier
    rebuilt = f"{word} ({qualifier})" if qualifier else word
    assert rebuilt == headword


def test_the_two_sides_get_two_separate_fields():
    assert distinction.RUSSIAN_FIELD != distinction.ENGLISH_FIELD
    assert distinction.RUSSIAN_FIELD in distinction.FIELDS
    assert distinction.ENGLISH_FIELD in distinction.FIELDS


@pytest.mark.parametrize(
    "russian,expected",
    [
        ("о / об", ""),
        ("насчёт", ""),
        ("какой", "interrogative / exclamative"),
        ("который", "relative / interrogative"),
        ("согласно (preposition)", "formal"),
        ("дом", ""),
        ("как (conjunction)", ""),
        ("как (adverb)", ""),
        ("", ""),
    ],
)
def test_english_distinction_returns_the_stored_hint_or_nothing(russian, expected):
    assert distinction.english_distinction(russian) == expected


def test_every_stored_hint_is_short_and_non_empty():
    assert distinction.ENGLISH_DISTINCTIONS
    for russian, hint in distinction.ENGLISH_DISTINCTIONS.items():
        assert hint.strip() == hint, russian
        assert hint, russian
        assert len(hint) <= 60, (russian, hint)


def test_colliding_words_never_share_gloss_and_cue():
    """Words held together by one English sense and not told apart by deck
    header or case pill must differ in their gloss or their cue."""
    notes = collisions.load_notes(
        SOURCE_LIST, DATA_DIR, case_field.default_government()
    )
    by_guid = {note.guid: note for note in notes}
    pairs = [
        pair
        for group in collisions.find_collisions(notes)
        for pair in group.unseparated
    ]
    assert pairs
    for first, second in pairs:
        a, b = by_guid[first], by_guid[second]
        assert (a.translation.casefold(), a.english_distinction.casefold()) != (
            b.translation.casefold(),
            b.english_distinction.casefold(),
        ), (a.headword, b.headword)
    for use in collisions.map_cues(notes, collisions.find_collisions(notes)):
        if use.role == "needed":
            assert use.separates, use.headword


def test_a_shared_gloss_and_cue_is_caught():
    first = collisions.Note(
        family="mutable",
        note_type="t",
        section="Nouns",
        deck="Languages::Russian::1. Mutable Words::a. Nouns",
        headword="а",
        guid="g1",
        translation="shore",
        russian_distinction="",
        english_distinction="river",
        additional_info="",
        cases=frozenset(),
    )
    second = dataclasses.replace(first, headword="б", guid="g2")
    [group] = collisions.find_collisions([first, second])
    assert group.unseparated
    uses = collisions.map_cues([first, second], [group])
    assert not any(use.separates for use in uses)
