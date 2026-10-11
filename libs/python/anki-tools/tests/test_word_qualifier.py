"""Contract tests for the headword qualifier's display styling."""

import re

from anki_tools import word_qualifier

RUSSIAN_DIV = '<div id="russian">{{Russian}}</div>'


def test_script_is_appended_to_a_side_that_shows_the_word():
    out = word_qualifier.add_qualifier_script(RUSSIAN_DIV)
    assert out.startswith(RUSSIAN_DIV)
    assert word_qualifier.QUALIFIER_SCRIPT in out


def test_is_idempotent():
    once = word_qualifier.add_qualifier_script(RUSSIAN_DIV)
    assert word_qualifier.add_qualifier_script(once) == once


def test_a_side_without_the_word_is_left_alone():
    html = '<div id="translation">{{Translation}}</div>'
    assert word_qualifier.add_qualifier_script(html) == html


def test_matches_the_russian_div_whatever_its_attribute_spelling():
    for div in (
        '<div id="russian">{{Russian}}</div>',
        "<div id='russian' class='x'>{{Russian}}</div>",
        '<div class="x" id="russian">{{Russian}}</div>',
    ):
        assert word_qualifier.QUALIFIER_SCRIPT in word_qualifier.add_qualifier_script(
            div
        )


def test_css_defines_the_class_the_script_applies():
    assert f".{word_qualifier.QUALIFIER_CLASS} {{" in word_qualifier.QUALIFIER_CSS


def test_qualifier_matches_the_english_field_size():
    """`.card` sets 20px and `#translation` adds none, so 20px IS the English
    field's size. The qualifier reads as a sibling of the gloss, not as fine
    print under a 2.2rem headword."""
    assert "font-size: 20px;" in word_qualifier.QUALIFIER_CSS
    assert "em;" not in word_qualifier.QUALIFIER_CSS
