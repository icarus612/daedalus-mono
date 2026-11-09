"""The built rows equal the approved qualifier-classification and routing artifacts."""

import csv
import re
from pathlib import Path

import pytest

from anki_tools import case_field, immutable_words_plan, mutable_words_plan

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
DATA = PACKAGE_ROOT / "anki_tools" / "data"
VOCAB = DATA / "russian-vocabulary"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"
BASELINE = PACKAGE_ROOT / "tests" / "data" / "meaning-freeze-baseline.tsv"
IMMUTABLE_TYPE = "Russian - Immutable Words (Ellis Version)"

PINNED_SO_GUID = "p[f.<aMxja"
UNBUILT_BASELINE_GUIDS = {
    "f)^X@TkXxV",
    "AWzYhLC}0g",
    "Ma-xRJ&XfP",
    "Kfyy3[<gHw",
    "B9<ldHd%Q|",
    "uGCt-H97.M",
}
NEW_VERB_HEADWORDS = {
    "лично",
    "страшно",
    "по-другому",
    "замечательно",
    "наивно",
    "активно",
    "приятный",
    "английский",
    "позже",
    "жаловать",
    "узнавать",
    "вспоминать",
    "пугаться",
    "лететь",
    "плыть",
    "вести",
    "нести",
    "везти",
}
CUE_SUPERSEDED_BY_CLASSIFICATION = {
    "по",
    "из",
    "от",
    "ради",
    "бежать",
    "нравиться",
    "вдоль",
    "до",
    "за",
    "кроме",
    "между",
    "над",
    "насчёт",
    "о / об",
    "перед",
    "поверх",
    "позади",
    "с / со",
    "согласно (preposition)",
    "среди",
}

TINT = re.compile(r"</?span\b[^>]*>")
TAG = re.compile(r"<[^>]+>")
PARENTHETICAL = re.compile(r"\([^()]*\)")


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


def meaning(text: str) -> str:
    bare = PARENTHETICAL.sub(" ", TAG.sub(" ", text))
    return re.sub(r"\s+", " ", bare).strip()


def build_notes() -> dict[str, dict]:
    notes: dict[str, dict] = {}
    for row in immutable_words_plan.parse_word_list(
        SOURCE_LIST.read_text(encoding="utf-8")
    ):
        notes[row.guid] = {
            "note type": IMMUTABLE_TYPE,
            "headword": row.russian,
            "pos": row.pos,
            "fields": dict(zip(immutable_words_plan.FIELD_NAMES, row.fields())),
        }
    loaders = {
        "Nouns": mutable_words_plan.parse_nouns,
        "Verbs": mutable_words_plan.parse_verbs,
        "Adjectives": mutable_words_plan.parse_adjectives,
        "Adverbs": mutable_words_plan.parse_adverbs,
        "Pronouns": mutable_words_plan.parse_pronouns,
        "Numerals": mutable_words_plan.parse_numerals,
    }
    for sheet, loader in loaders.items():
        for row in loader(str(VOCAB / f"{sheet.lower()}.tsv")):
            notes[row.guid] = {
                "note type": mutable_words_plan.NOTE_TYPE_NAMES[sheet],
                "headword": row.base_words[0],
                "sheet": sheet,
                "fields": dict(
                    zip(mutable_words_plan.FIELD_NAMES[sheet], row.fields())
                ),
            }
    return notes


@pytest.fixture(scope="module")
def notes():
    return build_notes()


@pytest.fixture(scope="module")
def classification():
    rows = read_tsv(VOCAB / "qualifier-classification.tsv")
    by_guid: dict[str, dict[str, str]] = {}
    for row in rows:
        by_guid.setdefault(row["guid"], row)
    return rows, by_guid


@pytest.fixture(scope="module")
def routing():
    return {
        (r["note type"], r["headword"], r["field"]): r
        for r in read_tsv(DATA / "case-text-routing.tsv")
    }


def test_artifact_sizes():
    assert len(read_tsv(VOCAB / "qualifier-classification.tsv")) == 898
    assert len(read_tsv(DATA / "case-text-routing.tsv")) == 114


def test_every_classified_note_is_built_under_its_key(notes, classification):
    _, by_guid = classification
    assert by_guid
    for guid, row in by_guid.items():
        assert guid in notes, row["headword (keyed)"]
        assert notes[guid]["headword"] == row["headword (keyed)"]
        assert notes[guid]["note type"] == row["note type"]


def test_classification_rows_of_one_note_agree(classification):
    rows, by_guid = classification
    for row in rows:
        first = by_guid[row["guid"]]
        for column in (
            "resulting Translation",
            "resulting English Distinction",
            "resulting Additional Info",
        ):
            assert row[column] == first[column], row["headword (keyed)"]


def test_built_translation_equals_the_resulting_translation(notes, classification):
    _, by_guid = classification
    for guid, row in by_guid.items():
        built = TINT.sub("", notes[guid]["fields"]["Translation"])
        assert built == row["resulting Translation"], row["headword (keyed)"]


def test_built_english_distinction_equals_the_resulting_cue(notes, classification):
    _, by_guid = classification
    for guid, row in by_guid.items():
        built = notes[guid]["fields"]["English Distinction"]
        assert built == row["resulting English Distinction"], row["headword (keyed)"]


def test_unclassified_notes_carry_no_cue(notes, classification):
    _, by_guid = classification
    for guid, note in notes.items():
        if guid not in by_guid:
            assert note["fields"]["English Distinction"] == "", note["headword"]


def expected_info(note, classified, routed):
    if routed is not None:
        keeps = routed["destination field"] == "Additional Info"
        return routed["resulting text"] if keeps else ""
    if note.get("pos") == case_field.GOVERNING_SECTION:
        return None
    return classified["resulting Additional Info"] if classified else None


def test_built_additional_info_equals_the_approved_result(
    notes, classification, routing
):
    _, by_guid = classification
    checked = 0
    for guid, note in notes.items():
        routed = routing.get((note["note type"], note["headword"], "Additional Info"))
        want = expected_info(note, by_guid.get(guid), routed)
        if want is None:
            continue
        checked += 1
        assert note["fields"]["Additional Info"] == want, note["headword"]
    assert checked > 400


def test_routing_rows_are_all_applied(notes, routing):
    by_head = {(n["note type"], n["headword"]): n for n in notes.values()}
    for (note_type, headword, field), row in routing.items():
        fields = by_head[(note_type, headword)]["fields"]
        if field == "Case / Preposition":
            assert fields["Case / Preposition"] == row["resulting text"], headword
            assert fields["Case"] == row["moved text"], headword
        elif field == "Additional Info" and row["destination field"] == "Formation":
            assert fields["Formation"] == row["moved text"], headword
        elif field == "English Distinction":
            if headword in CUE_SUPERSEDED_BY_CLASSIFICATION:
                assert fields["English Distinction"] != row["resulting text"]
            elif row["destination field"] == "delete":
                assert fields["English Distinction"] == "", headword
            else:
                assert fields["English Distinction"] == row["resulting text"], headword


def test_the_routing_disagreements_are_exactly_the_known_set(
    notes, classification, routing
):
    differing = set()
    by_head = {(n["note type"], n["headword"]): n for n in notes.values()}
    for (note_type, headword, field), row in routing.items():
        if field != "English Distinction":
            continue
        want = "" if row["destination field"] == "delete" else row["resulting text"]
        if by_head[(note_type, headword)]["fields"]["English Distinction"] != want:
            differing.add(headword)
    assert differing == CUE_SUPERSEDED_BY_CLASSIFICATION


def test_case_column_agrees_with_the_case_government(notes):
    government = case_field.default_government()
    checked = 0
    for guid, note in notes.items():
        fields = note["fields"]
        if note["note type"] == IMMUTABLE_TYPE or note.get("sheet") in (
            "Verbs",
            "Adverbs",
        ):
            assert fields["Case"] == case_field.case_value(government, guid), note[
                "headword"
            ]
            checked += 1
        else:
            assert "Case" not in fields
    assert checked > 400


def test_a_drifted_case_column_is_caught(notes):
    government = case_field.default_government()
    guid = next(
        g for g, n in notes.items() if n.get("sheet") == "Verbs" and n["fields"]["Case"]
    )
    drifted = {**notes[guid]["fields"], "Case": "Nominative"}
    assert drifted["Case"] != case_field.case_value(government, guid)


def test_governing_verbs_and_adverbs_have_a_case_value(notes):
    government = case_field.default_government()
    governed = {
        g
        for g, n in notes.items()
        if n.get("sheet") in ("Verbs", "Adverbs") and g in government
    }
    assert governed
    assert all(notes[g]["fields"]["Case"] for g in governed)


def test_so_adverb_keeps_the_reviewed_notes_guid(notes):
    [so] = [n for n in notes.values() if n["headword"] == "так (adverb)"]
    assert PINNED_SO_GUID in notes
    assert notes[PINNED_SO_GUID] is so


def read_baseline() -> dict[str, str]:
    return {r["guid"]: r["Translation"] for r in read_tsv(BASELINE)}


def test_guid_set_changes_only_by_the_pin_and_the_new_verbs(notes):
    baseline = read_baseline()
    assert len(baseline) == 1474
    assert set(baseline) - set(notes) == UNBUILT_BASELINE_GUIDS
    added = set(notes) - set(baseline)
    assert {notes[g]["headword"] for g in added} == NEW_VERB_HEADWORDS


def test_meaning_freeze_against_the_captured_baseline(notes):
    baseline = read_baseline()
    changed = [
        notes[guid]["headword"]
        for guid, translation in baseline.items()
        if guid in notes
        and meaning(notes[guid]["fields"]["Translation"]) != meaning(translation)
    ]
    assert changed == []


def test_meaning_freeze_fails_on_a_seeded_meaning_edit(notes):
    baseline = read_baseline()
    guid = next(g for g in baseline if g in notes)
    seeded = notes[guid]["fields"]["Translation"] + " extra"
    assert meaning(seeded) != meaning(baseline[guid])


def test_meaning_normaliser_ignores_markup_and_parentheticals_only():
    assert meaning('<span class="case-text">in</span> (where)<br>into') == "in into"
    assert meaning("in") != meaning("on")
