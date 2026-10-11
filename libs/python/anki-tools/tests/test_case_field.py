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
        ("Genitive", "(+ gen.)"),
        ("Dative", "(+ dat.)"),
        ("Prepositional", "(+ prep.)"),
        ("Instrumental", "(+ instr.)"),
        ("Accusative", "(+ acc.)"),
        ("Accusative for motion in; Prepositional for location", "(+ acc./prep.)"),
        ('Instrumental for "with"; Genitive for "from / since"', "(+ instr./gen.)"),
        ("Genitive — always", "(+ gen.)"),
        ("Static location", ""),
        ("", ""),
    ],
)
def test_case_tag_cases(info, expected):
    assert case_field.case_tag(info) == expected


def test_dash_commentary_is_not_read_as_a_second_case():
    info = "Dative — one of the few Genitive-looking ones that takes Dative"
    assert case_field.case_tag(info) == "(+ dat.)"


def test_tag_order_follows_the_cell_not_the_abbreviation_table():
    assert case_field.case_tag("Genitive; Accusative") == "(+ gen./acc.)"
    assert case_field.case_tag("Accusative; Genitive") == "(+ acc./gen.)"


def test_case_tag_for_row_only_fires_for_prepositions():
    assert case_field.case_tag_for_row("Prepositions", "Genitive") == "(+ gen.)"
    for pos in ("Particles", "Base Adverbs", "Conjunctions", "Indeclinable Nouns"):
        assert case_field.case_tag_for_row(pos, "Genitive") == ""


def test_poznravlyayu_style_row_is_never_tagged():
    """`с` governs the instrumental there, not the word itself."""
    info = "1st-person present of поздравлять; often + с + instrumental"
    assert case_field.case_tag(info) == "(+ instr.)"
    assert case_field.case_tag_for_row("Particles", info) == ""


def test_every_real_preposition_gets_a_case_tag(real_rows):
    prepositions = [r for r in real_rows if r.pos == "Prepositions"]
    assert len(prepositions) == 44
    tagged = {
        r.russian: case_field.case_tag_for_row(r.pos, r.info) for r in prepositions
    }
    untagged = [w for w, tag in tagged.items() if not tag]
    assert untagged == []
    assert tagged["о / об"] == "(+ prep.)"
    assert tagged["насчёт"] == "(+ gen.)"
    assert tagged["в / во"] == "(+ acc./prep.)"
    assert tagged["вопреки"] == "(+ dat.)"


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
    assert len(others) == 186
    for row in others:
        assert row.fields()[index] == ""


def test_add_case_tag_wraps_the_russian_div():
    html = '\t<div id="russian">{{Russian}}</div>\n'
    out = case_field.add_case_tag(html)
    assert (
        '<div id="russian">{{Russian}}{{#Case}} '
        '<span class="case">{{Case}}</span>{{/Case}}</div>' in out
    )


def test_add_case_tag_is_idempotent():
    html = '\t<div id="russian">{{Russian}}</div>\n'
    once = case_field.add_case_tag(html)
    assert case_field.add_case_tag(once) == once


def test_add_case_tag_leaves_a_template_without_a_russian_div_alone():
    html = '<div id="translation">{{Translation}}</div>'
    assert case_field.add_case_tag(html) == html


def test_tag_is_conditional_so_an_untagged_row_renders_no_stray_space():
    out = case_field.add_case_tag('<div id="russian">{{Russian}}</div>')
    assert "{{#Case}}" in out and "{{/Case}}" in out
    assert re.search(r"\{\{Russian\}\}\{\{#Case\}\}", out)


def test_case_css_defines_the_class_the_template_uses():
    assert f".{case_field.CASE_CLASS} {{" in case_field.CASE_CSS
