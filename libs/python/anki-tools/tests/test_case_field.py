"""Contract tests for the `Case` field: the case a preposition governs,
rendered inline beside the Russian word.
"""

import re
from pathlib import Path

import pytest

from anki_tools import case_field
from anki_tools.immutable_words_plan import FIELD_NAMES, parse_word_list

REAL_SOURCE_PATH = Path(__file__).resolve().parent / "data" / "source-word-list.md"


@pytest.fixture(scope="module")
def real_rows():
    with open(REAL_SOURCE_PATH, encoding="utf-8") as fh:
        return parse_word_list(fh.read())


@pytest.mark.parametrize(
    "info,expected",
    [
        ("Genitive", "(+ genitive case)"),
        ("Dative", "(+ dative case)"),
        ("Prepositional", "(+ prepositional case)"),
        ("Instrumental", "(+ instrumental case)"),
        ("Accusative", "(+ accusative case)"),
        ("Accusative for motion in; Prepositional for location", "(+ accusative or prepositional case)"),
        ('Instrumental for "with"; Genitive for "from / since"', "(+ instrumental or genitive case)"),
        ("Genitive — always", "(+ genitive case)"),
        ("Static location", ""),
        ("", ""),
    ],
)
def test_case_tag_cases(info, expected):
    assert case_field.case_tag(info) == expected


def test_dash_commentary_is_not_read_as_a_second_case():
    info = "Dative — one of the few Genitive-looking ones that takes Dative"
    assert case_field.case_tag(info) == "(+ dative case)"


def test_tag_order_follows_the_cell_not_the_abbreviation_table():
    assert case_field.case_tag("Genitive; Accusative") == "(+ genitive or accusative case)"
    assert case_field.case_tag("Accusative; Genitive") == "(+ accusative or genitive case)"


def test_case_tag_for_row_only_fires_for_prepositions():
    assert case_field.case_tag_for_row("Prepositions", "Genitive") == "(+ genitive case)"
    for pos in ("Particles", "Base Adverbs", "Conjunctions", "Indeclinable Nouns"):
        assert case_field.case_tag_for_row(pos, "Genitive") == ""


def test_poznravlyayu_style_row_is_never_tagged():
    """`с` governs the instrumental there, not the word itself."""
    info = "1st-person present of поздравлять; often + с + instrumental"
    assert case_field.case_tag(info) == "(+ instrumental case)"
    assert case_field.case_tag_for_row("Particles", info) == ""


def test_every_real_preposition_gets_a_case_tag(real_rows):
    prepositions = [r for r in real_rows if r.pos == "Prepositions"]
    assert len(prepositions) == 44
    tagged = {
        r.russian: case_field.case_tag_for_row(r.pos, r.info) for r in prepositions
    }
    untagged = [w for w, tag in tagged.items() if not tag]
    assert untagged == []
    assert tagged["о / об"] == "(+ prepositional case)"
    assert tagged["насчёт"] == "(+ genitive case)"
    assert tagged["в / во"] == "(+ accusative or prepositional case)"
    assert tagged["вопреки"] == "(+ dative case)"


def test_no_non_preposition_row_is_tagged(real_rows):
    tagged = [
        (r.pos, r.russian)
        for r in real_rows
        if r.pos != "Prepositions" and case_field.case_tag_for_row(r.pos, r.info)
    ]
    assert tagged == []
    # positive control: those rows' raw info DOES name cases, so the
    # section guard is what suppresses them, not an empty input.
    assert [
        r.russian
        for r in real_rows
        if case_field.case_tag(r.info) and r.pos != "Prepositions"
    ] == ["нет", "поздравляю", "мало", "много"]


def test_case_is_a_field_of_the_note_type():
    assert case_field.CASE_FIELD in FIELD_NAMES


def test_every_row_supplies_a_value_for_every_field(real_rows):
    for row in real_rows:
        assert len(row.fields()) == len(FIELD_NAMES)


def test_preposition_rows_carry_the_tag_in_the_case_field(real_rows):
    index = FIELD_NAMES.index(case_field.CASE_FIELD)
    prepositions = [r for r in real_rows if r.pos == "Prepositions"]
    assert len(prepositions) == 44
    for row in prepositions:
        assert row.fields()[index] == case_field.case_tag(row.info)
    others = [r for r in real_rows if r.pos != "Prepositions"]
    assert len(others) == 187
    for row in others:
        assert row.fields()[index] == ""


def test_add_case_tag_wraps_the_translation_div():
    html = '\t<div id="translation">\n\t\t{{Translation}}\n\t</div>\n'
    out = case_field.add_case_tag(html)
    assert (
        '<div id="translation">{{Translation}}{{#Case}} '
        '<span class="case">{{Case}}</span>{{/Case}}</div>' in out
    )


def test_the_russian_is_never_tagged():
    """The case rides with the English; beside the word it is restatement."""
    for html in (
        '\t<div id="russian">{{Russian}}</div>',
        '{{FrontSide}}\n\t<div id="russian">{{Russian}}</div>',
    ):
        assert case_field.add_case_tag(html) == html


def test_add_case_tag_is_idempotent():
    html = '\t<div id="translation">\n\t\t{{Translation}}\n\t</div>\n'
    once = case_field.add_case_tag(html)
    assert case_field.add_case_tag(once) == once


def test_add_case_tag_leaves_a_template_without_a_translation_div_alone():
    html = '<div id="pronunciation">{{hint:Pronunciation}}</div>'
    assert case_field.add_case_tag(html) == html


def test_tag_is_conditional_so_an_untagged_row_renders_no_stray_space():
    out = case_field.add_case_tag('<div id="translation">{{Translation}}</div>')
    assert "{{#Case}}" in out and "{{/Case}}" in out
    assert re.search(r"\{\{Translation\}\}\{\{#Case\}\}", out)


def test_case_css_defines_the_class_the_template_uses():
    assert f".{case_field.CASE_CLASS} {{" in case_field.CASE_CSS


@pytest.mark.parametrize(
    "info,expected",
    [
        ("Prepositional", ""),
        ("Genitive", ""),
        ("Dative", ""),
        ("Genitive — always", "always"),
        ("Dative — always", "always"),
        (
            "Accusative for motion in; Prepositional for location",
            "Accusative for motion in; Prepositional for location",
        ),
        (
            'Instrumental for "with"; Genitive for "from / since"',
            'Instrumental for "with"; Genitive for "from / since"',
        ),
        (
            "Dative — one of the few Genitive-looking ones that takes Dative",
            "one of the few Genitive-looking ones that takes Dative",
        ),
        ("", ""),
    ],
)
def test_residual_info(info, expected):
    assert case_field.residual_info(info) == expected


def test_residual_info_only_applies_to_prepositions():
    assert case_field.residual_info_for_row("Prepositions", "Genitive") == ""
    for pos in ("Particles", "Base Adverbs", "Conjunctions", "Indeclinable Nouns"):
        assert case_field.residual_info_for_row(pos, "Genitive") == "Genitive"


def test_no_preposition_states_its_case_twice(real_rows):
    """The whole point: the tag renders the case, so the prose must not."""
    for row in (r for r in real_rows if r.pos == "Prepositions"):
        residual = case_field.residual_info(row.info)
        tag = case_field.case_tag(row.info)
        assert tag, row.russian
        if residual and "—" not in row.info:
            # kept only because it says WHEN each case applies
            assert "for" in residual, (row.russian, residual)


def test_bare_case_cells_collapse_and_informative_ones_survive(real_rows):
    preps = [r for r in real_rows if r.pos == "Prepositions"]
    residual = {r.russian: case_field.residual_info(r.info) for r in preps}
    assert residual["о / об"] == ""
    assert residual["из"] == ""
    assert residual["для"] == "always"
    assert residual["в / во"].startswith("Accusative for motion in")
    assert sum(1 for v in residual.values() if not v) == 36
    assert sum(1 for v in residual.values() if v) == 8


def test_additional_info_field_carries_the_residual(real_rows):
    index = FIELD_NAMES.index("Additional Info")
    for row in real_rows:
        expected = (
            case_field.residual_info(row.info)
            if row.pos == "Prepositions"
            else row.info
        )
        assert row.fields()[index] == expected


def test_no_two_rows_share_an_identical_english_gloss(real_rows):
    """An English prompt must name exactly one Russian word.

    `about` cannot ask for `о / об` rather than `насчёт`, and `now` cannot
    ask for `сейчас` rather than `теперь`. Prepositions are separated by the
    inline `Case` tag; everything else carries a parenthetical sense in its
    own English column, which is why this holds for the whole document.
    """
    seen: dict[str, str] = {}
    clashes = []
    for row in real_rows:
        key = re.sub(r"\s+", " ", row.english.strip().lower())
        if key in seen:
            clashes.append((key, seen[key], row.russian))
        seen[key] = row.russian
    assert clashes == []


def test_prepositions_sharing_a_gloss_are_separated_by_their_case(real_rows):
    """The `about` pair that prompted the tag: same gloss, different case."""
    by_word = {r.russian: r for r in real_rows if r.pos == "Prepositions"}
    o, naschet = by_word["о / об"], by_word["насчёт"]
    assert "about" in o.english and "about" in naschet.english
    assert case_field.case_tag(o.info) == "(+ prepositional case)"
    assert case_field.case_tag(naschet.info) == "(+ genitive case)"
    assert case_field.case_tag(o.info) != case_field.case_tag(naschet.info)


def test_case_tag_is_spelled_out_never_abbreviated(real_rows):
    """`prep.` reads as "preposition", the one thing it does not mean."""
    for row in (r for r in real_rows if r.pos == "Prepositions"):
        tag = case_field.case_tag(row.info)
        assert tag.endswith(" case)"), (row.russian, tag)
        assert "." not in tag, (row.russian, tag)
