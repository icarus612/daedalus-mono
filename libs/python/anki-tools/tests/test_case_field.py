"""Contract tests for the `Case` field: the case a preposition governs,
rendered as its own labelled row on the answer side.
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
        ("Genitive", "Genitive"),
        ("Dative", "Dative"),
        ("Prepositional", "Prepositional"),
        ("Instrumental", "Instrumental"),
        ("Accusative", "Accusative"),
        (
            "Accusative for motion in; Prepositional for location",
            "Accusative or Prepositional",
        ),
        (
            'Instrumental for "with"; Genitive for "from / since"',
            "Instrumental or Genitive",
        ),
        ("Genitive — always", "Genitive"),
        ("Static location", ""),
        ("", ""),
    ],
)
def test_case_name_cases(info, expected):
    assert case_field.case_name(info) == expected


def test_dash_commentary_is_not_read_as_a_second_case():
    info = "Dative — one of the few Genitive-looking ones that takes Dative"
    assert case_field.case_name(info) == "Dative"


def test_case_order_follows_the_cell_not_the_table():
    assert case_field.case_name("Genitive; Accusative") == "Genitive or Accusative"
    assert case_field.case_name("Accusative; Genitive") == "Accusative or Genitive"


def test_case_name_for_row_only_fires_for_prepositions():
    assert case_field.case_name_for_row("Prepositions", "Genitive") == "Genitive"
    for pos in ("Particles", "Base Adverbs", "Conjunctions", "Indeclinable Nouns"):
        assert case_field.case_name_for_row(pos, "Genitive") == ""


def test_poznravlyayu_style_row_is_never_tagged():
    """`с` governs the instrumental there, not the word itself."""
    info = "1st-person present of поздравлять; often + с + instrumental"
    assert case_field.case_name(info) == "Instrumental"
    assert case_field.case_name_for_row("Particles", info) == ""


def test_every_real_preposition_gets_a_case(real_rows):
    prepositions = [r for r in real_rows if r.pos == "Prepositions"]
    assert len(prepositions) == 44
    tagged = {
        r.russian: case_field.case_name_for_row(r.pos, r.info) for r in prepositions
    }
    untagged = [w for w, tag in tagged.items() if not tag]
    assert untagged == []
    assert tagged["о / об"] == "Prepositional"
    assert tagged["насчёт"] == "Genitive"
    assert tagged["в / во"] == "Accusative or Prepositional"
    assert tagged["вопреки"] == "Dative"


def test_no_non_preposition_row_is_tagged(real_rows):
    tagged = [
        (r.pos, r.russian)
        for r in real_rows
        if r.pos != "Prepositions" and case_field.case_name_for_row(r.pos, r.info)
    ]
    assert tagged == []
    # positive control: those rows' raw info DOES name cases, so the
    # section guard is what suppresses them, not an empty input.
    assert [
        r.russian
        for r in real_rows
        if case_field.case_name(r.info) and r.pos != "Prepositions"
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
        assert row.fields()[index] == case_field.case_name(row.info)
    others = [r for r in real_rows if r.pos != "Prepositions"]
    assert len(others) == 188
    for row in others:
        assert row.fields()[index] == ""


DETAIL_SIDE = (
    '\t<div id="additional-info">{{Additional Info}}</div>\n'
    "<script>\n"
    '\taddTitle("additional-info", "&#9432;");\n'
    "</script>\n"
)


def test_add_case_row_adds_a_div_and_its_title_above_additional_info():
    out = case_field.add_case_row(DETAIL_SIDE)
    assert '<div id="case">{{Case}}</div>' in out
    assert 'addTitle("case", "Case");' in out
    assert out.index('id="case"') < out.index('id="additional-info"')
    assert out.index('addTitle("case"') < out.index('addTitle("additional-info"')


def test_the_case_is_never_spliced_into_another_field():
    """It is its own row, like Case / Preposition on Verbs -- never text
    appended to the Russian or the English."""
    out = case_field.add_case_row(DETAIL_SIDE)
    assert "{{Translation}}{{#Case}}" not in out
    assert 'class="case"' not in out
    assert "(+ " not in out


def test_add_case_row_is_idempotent():
    once = case_field.add_case_row(DETAIL_SIDE)
    assert case_field.add_case_row(once) == once


def test_add_case_row_leaves_a_side_without_the_detail_block_alone():
    """The question sides render no detail block, so they get no case row."""
    for html in (
        '<div id="pronunciation">{{hint:Pronunciation}}</div>',
        '\t<div id="russian">{{Russian}}</div>',
        '\t<div id="translation">{{Translation}}</div>',
    ):
        assert case_field.add_case_row(html) == html


def test_case_css_styles_the_row_the_template_emits():
    assert f"#{case_field.CASE_ID} {{" in case_field.CASE_CSS
    assert f"#{case_field.CASE_ID} .title {{" in case_field.CASE_CSS
    assert f"#{case_field.CASE_ID} .body {{" in case_field.CASE_CSS


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
        tag = case_field.case_name(row.info)
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
    ask for `сейчас` rather than `теперь`. Every row carries a parenthetical
    sense in its own English column, prepositions included, which is why
    this holds for the whole document without the `Case` row being involved.
    """
    seen: dict[str, str] = {}
    clashes = []
    for row in real_rows:
        key = re.sub(r"\s+", " ", row.english.strip().lower())
        if key in seen:
            clashes.append((key, seen[key], row.russian))
        seen[key] = row.russian
    assert clashes == []


def test_the_about_pair_is_told_apart_by_its_english_not_by_its_case(real_rows):
    """Both say "about" and each governs a different case, but the English
    columns already differ -- so the prompt is answerable on its own and the
    `Case` row never has to carry that weight."""
    by_word = {r.russian: r for r in real_rows if r.pos == "Prepositions"}
    o, naschet = by_word["о / об"], by_word["насчёт"]
    assert "about" in o.english and "about" in naschet.english
    assert o.english != naschet.english
    assert case_field.case_name(o.info) == "Prepositional"
    assert case_field.case_name(naschet.info) == "Genitive"


def test_case_is_spelled_out_never_abbreviated(real_rows):
    """`prep.` reads as "preposition", the one thing it does not mean."""
    for row in (r for r in real_rows if r.pos == "Prepositions"):
        name = case_field.case_name(row.info)
        assert name, row.russian
        assert "." not in name, (row.russian, name)
        for word in name.split(" or "):
            assert word in [full for full, _ in case_field.CASE_NAMES], (
                row.russian,
                word,
            )
