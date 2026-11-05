"""The free-text case ban over every note type's prose fields."""

import csv
import re
from pathlib import Path

import pytest

from anki_tools import immutable_words_plan, mutable_words_plan
from anki_tools.case_ban import BAN, FREE_TEXT_FIELDS, ban_hits, visible_text

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA = PACKAGE_ROOT / "anki_tools" / "data"
VOCAB = DATA / "russian-vocabulary"
ROUTING = DATA / "case-text-routing.tsv"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"

MUTABLE_LOADERS = {
    "Nouns": mutable_words_plan.parse_nouns,
    "Verbs": mutable_words_plan.parse_verbs,
    "Adjectives": mutable_words_plan.parse_adjectives,
    "Adverbs": mutable_words_plan.parse_adverbs,
    "Pronouns": mutable_words_plan.parse_pronouns,
    "Numerals": mutable_words_plan.parse_numerals,
}
IMMUTABLE_NOTE_TYPE = "Russian - Immutable Words (Ellis Version)"

ADVISORY_NOTES = [
    "oblique cases add -ер-: матери, матерью",
    "no case; often + a что-clause (это значит, что...)",
    "fully suppletive oblique stem (мен-/мн-)",
    "opposed to этот; oblique cases are END-stressed (того́)",
    "oblique cases keep the STEM stress (э́того), unlike тот's end-stressed того́",
    "declines like an adjective; oblique forms are end-stressed (моего́)",
    "also declines for D/I/P: двум, двумя, о двух",
    "loses its vowel in the oblique cases: восьми́, восьмью́",
    "a fully-declining compound: all three parts change in the oblique cases",
]


def free_text_fields():
    """Yield (note type, headword, field, value) for every free-text field."""
    rows = immutable_words_plan.parse_word_list(SOURCE_LIST.read_text("utf-8"))
    for row in rows:
        for name, value in zip(immutable_words_plan.FIELD_NAMES, row.fields()):
            if name in FREE_TEXT_FIELDS:
                yield IMMUTABLE_NOTE_TYPE, row.russian, name, value
    for sheet, loader in MUTABLE_LOADERS.items():
        for row in loader(str(VOCAB / f"{sheet.lower()}.tsv")):
            fields = row.fields()
            for name, value in zip(mutable_words_plan.FIELD_NAMES[sheet], fields):
                if name in FREE_TEXT_FIELDS:
                    yield (
                        mutable_words_plan.NOTE_TYPE_NAMES[sheet],
                        fields[0],
                        name,
                        value,
                    )


def real_hits():
    return [
        (note_type, headword, name, value)
        for note_type, headword, name, value in free_text_fields()
        if ban_hits(value)
    ]


def test_scan_covers_all_seven_note_types():
    seen = {note_type for note_type, *_ in free_text_fields()}
    assert seen == {IMMUTABLE_NOTE_TYPE, *mutable_words_plan.NOTE_TYPE_NAMES.values()}
    assert len(seen) == 7


def test_scan_reaches_every_free_text_field_name():
    seen = {name for _, _, name, _ in free_text_fields()}
    assert seen == set(FREE_TEXT_FIELDS)


def test_no_free_text_field_names_a_case():
    hits = real_hits()
    assert hits == [], "\n".join(
        f"{note_type} | {headword} | {name} | {value!r}"
        for note_type, headword, name, value in hits
    )


@pytest.mark.parametrize(
    "text",
    [
        "Nominative",
        "takes Genitive",
        "the dative",
        "ACCUSATIVE object",
        "instrumental of ночь",
        "prepositional for location",
    ],
)
def test_case_name_arm_fires(text):
    assert ban_hits(text)


@pytest.mark.parametrize(
    "text",
    [
        "nom. pl.",
        "gen. sg.",
        "dat.",
        "acc.",
        "в/на + acc. (destination)",
        "instr.",
        "inst.",
        "на + prep. (means)",
        "prepl.",
        "(gen. pl. = nom. pl.)",
        "Nom.",
    ],
)
def test_abbreviation_arm_fires(text):
    assert ban_hits(text)


@pytest.mark.parametrize(
    "text",
    [
        "takes the direct object",
        "takes indirect object",
        "takes object",
        "direct object",
        "an Indirect Object",
        "governs the plural",
        "govern",
        "with the instrumental",
        "in the locative case",
        "takes the genitive",
        "Takes genitive",
    ],
)
def test_phrase_arm_fires(text):
    assert ban_hits(text)


def test_seeded_object_phrasing_fails_a_real_field():
    seeded = "to see (takes a direct object)"
    assert ban_hits(seeded) == ["direct object"]


def test_each_abbreviation_is_matched_whole():
    for abbr in ("nom", "gen", "dat", "acc", "instr", "inst", "prep", "prepl"):
        assert ban_hits(f"{abbr}. sg.")


@pytest.mark.parametrize(
    "text",
    [
        "похож на + what/whom",
        "рад + infinitive, or + to whom/what",
        "аллергия на + what/whom",
        "на + what",
        "to whom/what",
        "genital herpes",
        "generation",
        "accuse",
        "instrument",
        "preposition",
        "nominate",
    ],
)
def test_rephrasings_and_lookalikes_pass(text):
    assert ban_hits(text) == []


@pytest.mark.parametrize("text", ADVISORY_NOTES)
def test_kept_advisory_declension_notes_are_not_matched(text):
    assert ban_hits(text) == []


def test_tint_markup_is_not_prose():
    tinted = '<span class="case-text case-prepositional">in / at (where)</span>'
    assert BAN.search(tinted)
    assert ban_hits(tinted) == []
    assert visible_text(tinted) == "in / at (where)"


def test_tint_markup_does_not_hide_prose():
    assert ban_hits('<span class="case-text">takes genitive</span>')


def routing_rows():
    with ROUTING.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


def test_pre_change_texts_all_trip_the_ban():
    rows = routing_rows()
    assert len(rows) >= 100
    assert all(ban_hits(row["current text"]) for row in rows)


def test_post_change_texts_none_trip_the_ban():
    assert not [r for r in routing_rows() if ban_hits(r["resulting text"])]


def pre_change(headword, field=None):
    return [
        row["current text"]
        for row in routing_rows()
        if row["headword"] == headword and (field is None or row["field"] == field)
    ]


def test_abbreviation_arm_reproduces_the_planning_probe():
    abbreviations = re.compile(
        r"(?<![\w])(?:nom|gen|dat|acc|instr|inst|prepl|prep)\.", re.I
    )
    assert abbreviations.search(pre_change("бежать", "Case / Preposition")[0])
    nouns = [
        row
        for row in routing_rows()
        if row["note type"].endswith("Nouns (Ellis Version)")
        and re.search(r"\bprep\.", row["current text"])
    ]
    assert len(nouns) == 9
    for headword in ("рубль", "сторона", "раз"):
        assert re.search(r"gen\.\s*(sg|pl)\.", pre_change(headword)[0])
    for headword in ("сорок", "девяносто", "сто"):
        assert "nom./acc." in pre_change(headword)[0]


def test_phrase_arm_reproduces_governs_and_takes():
    assert "governs the genitive plural" in pre_change("пять")[0].lower()
    for headword in ("мало", "много"):
        assert re.search(r"takes genitive", pre_change(headword)[0], re.I)
    assert ban_hits("governs the genitive plural")
