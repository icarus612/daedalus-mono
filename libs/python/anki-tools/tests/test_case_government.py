"""Contract tests for the case-government table and the case-text routing list."""

import csv
import json
import re
from pathlib import Path

import pytest

from anki_tools import case_field, immutable_words_plan, mutable_words_plan

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA = PACKAGE_ROOT / "anki_tools" / "data"
VOCAB = DATA / "russian-vocabulary"
GOVERNMENT = DATA / "case-government.tsv"
ROUTING = DATA / "case-text-routing.tsv"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"
GUID_FIXTURE = PACKAGE_ROOT / "tests" / "data" / "immutable_guids.json"

CANONICAL = {name for name, _ in case_field.CASE_NAMES}
STATUSES = {"ok", "empty", "wrong", "none"}
LINE_SEPARATOR = re.compile(r"<br\s*/?>|</?div\b[^>]*>", re.I)

_NAMES = r"\b(?:nominative|genitive|dative|accusative|instrumental|prepositional)\b"
_ABBR = r"(?<![\w])(?:nom|gen|dat|acc|instr|inst|prepl|prep)\.(?:\s*(?:sg|pl)\.)?"
_PHRASES = (
    r"\b(?:takes\s+(?:the\s+)?(?:(?:direct|indirect)\s+)?object"
    r"|(?:direct|indirect)\s+object|in\s+the\s+\w+\s+case|governs?)\b"
)
BAN = re.compile("|".join([_NAMES, _ABBR, _PHRASES]), re.I)


def read_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


@pytest.fixture(scope="module")
def table():
    return read_table(GOVERNMENT)


@pytest.fixture(scope="module")
def immutable_rows():
    return immutable_words_plan.parse_word_list(SOURCE_LIST.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def verb_rows():
    return mutable_words_plan.parse_verbs(str(VOCAB / "verbs.tsv"))


@pytest.fixture(scope="module")
def adverb_rows():
    return mutable_words_plan.parse_adverbs(str(VOCAB / "adverbs.tsv"))


@pytest.fixture(scope="module")
def universe(immutable_rows, verb_rows, adverb_rows):
    return {row.guid for row in [*immutable_rows, *verb_rows, *adverb_rows]}


def missing_from(table_rows, universe_guids):
    return universe_guids - {row["guid"] for row in table_rows}


def test_header_carries_the_reader_columns(table):
    assert {"guid", "cases", "meaning->case"} <= set(table[0])


def test_every_note_has_exactly_one_row_and_no_orphans(table, universe):
    guids = [row["guid"] for row in table]
    assert len(guids) == len(set(guids))
    assert missing_from(table, universe) == set()
    assert set(guids) - universe == set()


def test_deleting_one_preposition_row_fails_coverage(table, universe):
    victim = next(row for row in table if row["headword"] == "для")
    shrunk = [row for row in table if row is not victim]
    assert missing_from(shrunk, universe) == {victim["guid"]}


def test_fixture_guids_still_present_are_covered(table, universe):
    fixture = {entry["guid"] for entry in json.loads(GUID_FIXTURE.read_text())}
    assert fixture & universe
    assert (fixture & universe) <= {row["guid"] for row in table}


def test_every_row_has_a_reference_and_a_known_status(table):
    for row in table:
        assert row["reference"].strip(), row["headword"]
        assert row["status"] in STATUSES, row["headword"]


def test_only_canonical_case_names_appear(table):
    for row in table:
        cases = [name.strip() for name in row["cases"].split(",") if name.strip()]
        assert set(cases) <= CANONICAL, row["headword"]
        assert len(cases) == len(set(cases)), row["headword"]


def test_status_none_means_blank_cases_and_vice_versa(table):
    for row in table:
        assert (row["status"] == "none") == (not row["cases"].strip()), row["headword"]


def test_reader_loads_every_governor(table):
    government = case_field.load_case_government(GOVERNMENT)
    governors = {row["guid"] for row in table if row["cases"].strip()}
    assert set(government) == governors
    assert all(len(entry.cases) >= 1 for entry in government.values())


def gloss_lines(english: str) -> set[str]:
    return {line.strip() for line in LINE_SEPARATOR.split(english)}


def test_every_meaning_key_matches_an_actual_gloss_line(
    table, immutable_rows, verb_rows
):
    english = {row.guid: row.english for row in immutable_rows}
    english.update({row.guid: row.translation for row in verb_rows})
    mapped = [row for row in table if row["meaning->case"].strip()]
    assert mapped
    for row in mapped:
        entries = row["meaning->case"].split(case_field.LINE_CASE_SEPARATOR)
        for entry in entries:
            line, _, case = entry.partition(case_field.LINE_CASE_ARROW)
            assert line in gloss_lines(english[row["guid"]]), (row["headword"], line)
            assert case in row["cases"].split(", "), (row["headword"], case)


def test_a_key_that_is_not_a_gloss_line_is_caught():
    assert "not a line of this gloss" not in gloss_lines(
        "in / at (where)<br>into (where)"
    )


@pytest.mark.parametrize(
    "headword,cases",
    [
        ("в / во", {"Accusative", "Prepositional"}),
        ("на", {"Accusative", "Prepositional"}),
        ("с / со", {"Instrumental", "Genitive"}),
        ("за", {"Accusative", "Instrumental"}),
        ("под", {"Accusative", "Instrumental"}),
        ("для", {"Genitive"}),
        ("вопреки", {"Dative"}),
        ("нет", {"Genitive"}),
        ("мало", {"Genitive"}),
        ("согласно (adverb)", {"Dative"}),
        ("помогать", {"Dative"}),
        ("бояться", {"Genitive"}),
    ],
)
def test_known_governors(table, headword, cases):
    row = next(row for row in table if row["headword"] == headword)
    assert set(row["cases"].split(", ")) == cases


def test_every_preposition_governs_a_case(table, immutable_rows):
    preposition_guids = {
        row.guid for row in immutable_rows if row.pos == "Prepositions"
    }
    by_guid = {row["guid"]: row for row in table}
    assert preposition_guids
    for guid in preposition_guids:
        assert by_guid[guid]["cases"].strip(), by_guid[guid]["headword"]


def test_two_case_prepositions_tint_each_case_line(table):
    by_head = {row["headword"]: row for row in table}
    for head in ("в / во", "на", "с / со", "за"):
        tinted = by_head[head]["meaning->case"].split(case_field.LINE_CASE_SEPARATOR)
        assert len(tinted) >= 2, head


@pytest.fixture(scope="module")
def routing():
    return read_table(ROUTING)


def test_routing_header(routing):
    assert list(routing[0]) == [
        "note type",
        "headword",
        "field",
        "current text",
        "destination field",
        "resulting text",
        "moved text",
        "reason",
    ]


def test_routing_keys_are_unique(routing):
    keys = [(r["note type"], r["headword"], r["field"]) for r in routing]
    assert len(keys) == len(set(keys))


def test_every_routed_current_text_is_a_real_ban_hit(routing):
    for row in routing:
        assert BAN.search(row["current text"]), row["headword"]


def test_no_resulting_text_matches_the_ban(routing):
    for row in routing:
        assert not BAN.search(row["resulting text"]), row["headword"]


def test_ban_check_fails_on_a_seeded_case_name():
    assert BAN.search("takes Dative")
    assert BAN.search("gen. pl.")
    assert BAN.search("governs the thing")
    assert not BAN.search("похож на + what/whom")


def test_hit_counts_match_the_planning_probe(routing):
    def count(field, immutable):
        return sum(
            1
            for r in routing
            if r["field"] == field and (("Immutable" in r["note type"]) == immutable)
        )

    english = sum(1 for r in routing if r["field"] == "English Distinction")
    assert english == 28
    assert count("Additional Info", True) == 10
    assert count("Additional Info", False) == 33
    assert sum(1 for r in routing if r["field"] == "Case / Preposition") == 43


def test_every_verb_case_residue_moves_cases_into_the_case_field(routing, table):
    audited = {row["headword"]: row["cases"] for row in table}
    for row in routing:
        if row["field"] != "Case / Preposition":
            continue
        assert row["destination field"] == "Case"
        assert row["moved text"] == audited[row["headword"]], row["headword"]


def test_every_routed_note_exists(routing, immutable_rows, verb_rows):
    headwords = {r.russian for r in immutable_rows} | {
        v.base_words[0] for v in verb_rows
    }
    mutable = set()
    for loader, name in (
        (mutable_words_plan.parse_nouns, "nouns"),
        (mutable_words_plan.parse_adjectives, "adjectives"),
        (mutable_words_plan.parse_adverbs, "adverbs"),
        (mutable_words_plan.parse_pronouns, "pronouns"),
        (mutable_words_plan.parse_numerals, "numerals"),
    ):
        mutable |= {r.base_words[0] for r in loader(str(VOCAB / f"{name}.tsv"))}
    for row in routing:
        assert row["headword"] in headwords | mutable, row["headword"]


FREE_FIELDS = (
    "Translation",
    "English Distinction",
    "Russian Distinction",
    "Additional Info",
    "Case / Preposition",
)


def source_hits(immutable_rows):
    for row in immutable_rows:
        names = immutable_words_plan.FIELD_NAMES
        for name, value in zip(names, row.fields({})):
            if name in FREE_FIELDS and BAN.search(value):
                yield (immutable_words_plan_note_type(), row.russian, name)
    for sheet, loader in (
        ("Nouns", mutable_words_plan.parse_nouns),
        ("Verbs", mutable_words_plan.parse_verbs),
        ("Adjectives", mutable_words_plan.parse_adjectives),
        ("Adverbs", mutable_words_plan.parse_adverbs),
        ("Pronouns", mutable_words_plan.parse_pronouns),
        ("Numerals", mutable_words_plan.parse_numerals),
    ):
        for row in loader(str(VOCAB / f"{sheet.lower()}.tsv")):
            names = mutable_words_plan.FIELD_NAMES[sheet]
            for name, value in zip(names, row.fields()):
                if name in FREE_FIELDS and BAN.search(value):
                    yield (
                        mutable_words_plan.NOTE_TYPE_NAMES[sheet],
                        row.base_words[0],
                        name,
                    )


def immutable_words_plan_note_type():
    return "Russian - Immutable Words (Ellis Version)"


def test_every_source_hit_has_a_routing_row(routing, immutable_rows):
    keys = {(r["note type"], r["headword"], r["field"]) for r in routing}
    hits = set(source_hits(immutable_rows))
    assert hits <= keys


def test_source_hits_are_all_routed_away(immutable_rows):
    assert set(source_hits(immutable_rows)) == set()


def test_a_hit_without_a_row_is_caught(routing):
    keys = {(r["note type"], r["headword"], r["field"]) for r in routing}
    unrouted = {
        ("Russian - Immutable Words (Ellis Version)", "нет-такого", "Additional Info")
    }
    assert not unrouted <= keys
