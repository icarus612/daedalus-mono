"""Case coverage and exclusion: governors build a Case, inflected types get none."""

import csv
from pathlib import Path

import pytest

from anki_tools import (
    case_field,
    case_pill,
    immutable_words_plan,
    mutable_words_plan,
)

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA = PACKAGE_ROOT / "anki_tools" / "data"
VOCAB = DATA / "russian-vocabulary"
GOVERNMENT = DATA / "case-government.tsv"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"

EXCLUDED_SHEETS = ("Nouns", "Adjectives", "Pronouns", "Numerals")
QUANTITY_WORDS = ("нет", "немного", "чуть-чуть", "вроде", "мало", "много", "сколько")


def read_table(path: Path = GOVERNMENT) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


def built_case(field_names, values) -> str:
    return values[field_names.index(case_field.CASE_FIELD)]


@pytest.fixture(scope="module")
def table():
    return read_table()


@pytest.fixture(scope="module")
def governors(table):
    return [row for row in table if row["cases"].strip()]


@pytest.fixture(scope="module")
def immutable_rows():
    return immutable_words_plan.parse_word_list(SOURCE_LIST.read_text("utf-8"))


@pytest.fixture(scope="module")
def verb_rows():
    return mutable_words_plan.parse_verbs(str(VOCAB / "verbs.tsv"))


@pytest.fixture(scope="module")
def adverb_rows():
    return mutable_words_plan.parse_adverbs(str(VOCAB / "adverbs.tsv"))


def built_cases(immutable_rows, verb_rows, adverb_rows, government=None):
    """{guid: built Case value} for every note that has a Case field."""
    cases = {}
    for row in immutable_rows:
        cases[row.guid] = built_case(
            immutable_words_plan.FIELD_NAMES, row.fields(government)
        )
    for row in verb_rows:
        cases[row.guid] = built_case(
            mutable_words_plan.FIELD_NAMES["Verbs"], row.fields()
        )
    for row in adverb_rows:
        cases[row.guid] = built_case(
            mutable_words_plan.FIELD_NAMES["Adverbs"], row.fields()
        )
    return cases


def empty_governors(table, cases):
    return [
        row["headword"]
        for row in table
        if row["cases"].strip() and not cases.get(row["guid"], "").strip()
    ]


@pytest.fixture(scope="module")
def cases(immutable_rows, verb_rows, adverb_rows):
    return built_cases(immutable_rows, verb_rows, adverb_rows)


def test_every_table_governor_builds_with_a_nonempty_case(table, cases):
    assert empty_governors(table, cases) == []


def test_built_case_equals_the_audited_cases(governors, cases):
    for row in governors:
        assert cases[row["guid"]] == row["cases"], row["headword"]


def test_every_table_guid_resolves_to_a_built_note(table, cases):
    assert [row["headword"] for row in table if row["guid"] not in cases] == []


def test_non_governors_build_with_an_empty_case(table, cases):
    stray = [
        row["headword"]
        for row in table
        if not row["cases"].strip() and cases[row["guid"]].strip()
    ]
    assert stray == []


def test_an_emptied_preposition_case_fails(
    table, immutable_rows, verb_rows, adverb_rows
):
    government = {
        guid: entry
        for guid, entry in case_field.default_government().items()
        if guid != next(r.guid for r in immutable_rows if r.russian == "для")
    }
    emptied = built_cases(immutable_rows, verb_rows, adverb_rows, government)
    assert empty_governors(table, emptied) == ["для"]


def test_every_preposition_builds_a_case(immutable_rows, cases):
    prepositions = [r for r in immutable_rows if r.pos == "Prepositions"]
    assert prepositions
    assert [r.russian for r in prepositions if not cases[r.guid].strip()] == []


@pytest.mark.parametrize("word", QUANTITY_WORDS)
def test_each_quantity_word_governs_and_builds_genitive(word, immutable_rows, cases):
    row = next(r for r in immutable_rows if r.russian == word)
    assert cases[row.guid] == "Genitive"


def test_the_seven_quantity_words_are_all_the_non_preposition_immutable_governors(
    table, immutable_rows
):
    by_guid = {r.guid: r for r in immutable_rows}
    others = {
        by_guid[row["guid"]].russian
        for row in table
        if row["family"] == "immutable"
        and row["cases"].strip()
        and by_guid[row["guid"]].pos != "Prepositions"
    }
    assert others == set(QUANTITY_WORDS)


def test_every_verb_governor_builds_a_case(governors, verb_rows, cases):
    verb_guids = {v.guid for v in verb_rows}
    verb_governors = [row for row in governors if row["guid"] in verb_guids]
    assert len(verb_governors) > 100
    assert [r["headword"] for r in verb_governors if not cases[r["guid"]]] == []


def test_every_source_stated_government_is_in_the_table(immutable_rows, governors):
    listed = {row["guid"] for row in governors}
    stated = [r for r in immutable_rows if case_field.case_name(r.info)]
    assert stated
    assert [r.russian for r in stated if r.guid not in listed] == []


def test_a_dropped_governor_is_caught_by_the_source_check(immutable_rows, governors):
    victim = next(r for r in immutable_rows if r.russian == "для")
    listed = {row["guid"] for row in governors} - {victim.guid}
    stated = [r for r in immutable_rows if case_field.case_name(r.info)]
    assert victim.guid not in listed
    assert victim in stated


@pytest.mark.parametrize("sheet", EXCLUDED_SHEETS)
def test_excluded_note_types_have_no_case_field(sheet):
    assert case_field.CASE_FIELD not in mutable_words_plan.FIELD_NAMES[sheet]


@pytest.mark.parametrize("sheet", EXCLUDED_SHEETS)
@pytest.mark.parametrize("card_index", [0, 1])
def test_excluded_templates_have_no_pill_markup(sheet, card_index):
    for side in mutable_words_plan.build_template(sheet, card_index):
        assert case_pill.PILL_WRAPPER_CLASS not in side


@pytest.mark.parametrize("sheet", ["Verbs", "Adverbs"])
def test_governing_note_types_do_carry_pill_markup(sheet):
    sides = mutable_words_plan.build_template(
        sheet, 0
    ) + mutable_words_plan.build_template(sheet, 1)
    assert any(case_pill.PILL_WRAPPER_CLASS in side for side in sides)


def test_a_seeded_noun_with_pill_markup_fails():
    qfmt, afmt = mutable_words_plan.build_template("Nouns", 1)
    seeded = case_pill.add_pill_block(qfmt)
    assert case_pill.PILL_WRAPPER_CLASS not in qfmt
    assert case_pill.PILL_WRAPPER_CLASS in seeded
