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


def test_qualifier_is_decisively_smaller_than_the_headword():
    """`#russian` is 2.2rem, so anything near 1em competes with the word."""
    size = float(re.search(r"font-size: ([\d.]+)em", word_qualifier.QUALIFIER_CSS)[1])
    assert size <= 0.55
    assert 2.2 * size <= 1.25


_PATTERN = re.compile(r"^([\s\S]*\S)(\s*\([^()]*\))\s*$")


def _applied(inner):
    """The regex the script runs, mirrored here so its behaviour is pinned."""
    m = _PATTERN.match(inner)
    if not m:
        return inner
    return f'{m[1]} <span class="qualifier">{m[2].strip()}</span>'


def test_wraps_a_trailing_qualifier():
    assert _applied("когда (conjunction)") == (
        'когда <span class="qualifier">(conjunction)</span>'
    )
    assert _applied("правда (noun)") == ('правда <span class="qualifier">(noun)</span>')


def test_leaves_a_word_without_a_qualifier_alone():
    for word in ("насчёт", "в / во", "ни... ни..."):
        assert _applied(word) == word


def test_does_not_touch_a_word_already_followed_by_the_case_span():
    inner = 'насчёт <span class="case">(+ gen.)</span>'
    assert _applied(inner) == inner


def test_script_guards_against_double_wrapping():
    assert '.querySelector(".qualifier")' in word_qualifier.QUALIFIER_SCRIPT
