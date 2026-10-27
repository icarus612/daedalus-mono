"""Contract tests for the two distinction fields: one marker per side."""

import pytest

from anki_tools import distinction
from anki_tools.audio_naming import strip_qualifier


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
        ("о / об", "Prepositional"),
        ("насчёт", "Genitive"),
        ("какой", "interrogative / exclamative"),
        ("который", "relative / interrogative"),
        ("согласно (preposition)", "Dative; formal"),
        ("дом", ""),
        ("как (conjunction)", "comparison"),
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
        assert len(hint) <= 48, (russian, hint)


def test_colliding_glosses_get_different_hints():
    """The bug this field exists for: with the gloss alone, "about" and
    "which" each name two words and nothing chooses between them."""
    for pair in (("о / об", "насчёт"), ("какой", "который")):
        first, second = (distinction.english_distinction(word) for word in pair)
        assert first and second, pair
        assert first != second, pair
