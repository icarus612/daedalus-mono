import dataclasses
import json
import os
import re
import shutil
from pathlib import Path

import pytest
from anki.collection import Collection
from test_immutable_words import _build_synthetic_source_collection

from anki_tools import (
    examples_field,
    immutable_words,
    mutable_words,
    mutable_words_plan,
)
from anki_tools.immutable_words_plan import parse_word_list

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"
BEFORE_SNAPSHOT = PACKAGE_ROOT / "tests" / "data" / "russian-runs-before-examples.json"

CYRILLIC = re.compile(r"[Ѐ-ӿ]")
RUSSIAN_RUN = re.compile(r"[Ѐ-ӿ́]+(?:-[Ѐ-ӿ́]+)*")

PARSERS = {
    "Nouns": mutable_words_plan.parse_nouns,
    "Verbs": mutable_words_plan.parse_verbs,
    "Adjectives": mutable_words_plan.parse_adjectives,
    "Adverbs": mutable_words_plan.parse_adverbs,
    "Pronouns": mutable_words_plan.parse_pronouns,
    "Numerals": mutable_words_plan.parse_numerals,
}


def _mutable_rows():
    return {
        sheet: parser(str(DATA_DIR / f"{sheet.lower()}.tsv"))
        for sheet, parser in PARSERS.items()
    }


def _immutable_rows():
    return parse_word_list(SOURCE_LIST.read_text(encoding="utf-8"))


def _all_notes():
    """(guid, translation, additional_info, examples) for every real note."""
    notes = []
    for rows in _mutable_rows().values():
        notes.extend(
            (r.guid, r.translation, r.additional_info, r.examples) for r in rows
        )
    notes.extend((r.guid, r.english, r.info, r.examples) for r in _immutable_rows())
    return notes


def _translations_with_cyrillic(translations):
    return [text for text in translations if CYRILLIC.search(text)]


def _runs(*texts):
    return {run for text in texts for run in RUSSIAN_RUN.findall(text)}


def test_no_translation_contains_cyrillic():
    translations = [translation for _, translation, _, _ in _all_notes()]
    assert len(translations) == 1351
    assert _translations_with_cyrillic(translations) == []


def test_cyrillic_guard_flags_a_translation_with_russian_in_it():
    rows = _mutable_rows()["Adjectives"]
    tainted = dataclasses.replace(rows[0], translation="new (как белый снег)")
    translations = [row.translation for row in [tainted, *rows[1:]]]
    assert _translations_with_cyrillic(translations) == ["new (как белый снег)"]


def test_cyrillic_guard_flags_a_tsv_translation_end_to_end(tmp_path):
    source = (DATA_DIR / "nouns.tsv").read_text(encoding="utf-8").split("\n")
    header = source[0].split("\t")
    cells = source[1].split("\t")
    cells[header.index("English")] = "year (в прошлом году)"
    path = tmp_path / "nouns.tsv"
    path.write_text("\n".join([source[0], "\t".join(cells)]) + "\n", encoding="utf-8")
    parsed = mutable_words_plan.parse_nouns(str(path))
    assert _translations_with_cyrillic([r.translation for r in parsed]) == [
        "year (в прошлом году)"
    ]


def _lost_runs(before, after):
    return {
        guid: sorted(set(runs) - after.get(guid, set()))
        for guid, runs in before.items()
        if set(runs) - after.get(guid, set())
    }


def _runs_by_guid():
    return {
        guid: _runs(translation, info, examples)
        for guid, translation, info, examples in _all_notes()
    }


def test_no_russian_run_dropped_by_the_examples_migration():
    before = json.loads(BEFORE_SNAPSHOT.read_text(encoding="utf-8"))
    assert _lost_runs(before, _runs_by_guid()) == {}


def test_round_trip_check_reports_a_dropped_run():
    before = json.loads(BEFORE_SNAPSHOT.read_text(encoding="utf-8"))
    after = _runs_by_guid()
    victim = next(guid for guid, runs in before.items() if len(runs) > 1)
    dropped = sorted(before[victim])[0]
    after[victim] = after[victim] - {dropped}
    assert _lost_runs(before, after) == {victim: [dropped]}


@pytest.mark.parametrize(
    ("sheet", "word", "field", "text"),
    [
        ("Indeclinable Nouns", "кофе", "examples", "чёрный кофе"),
        ("Indeclinable Nouns", "кино", "examples", "новое кино"),
        ("Conjunctions", "как (conjunction)", "examples", "белый как снег"),
        ("Conjunctions", "тоже", "examples", "Я тоже иду"),
        ("Base Adverbs", "много", "examples", "много людей"),
    ],
)
def test_immutable_standalone_examples_moved(sheet, word, field, text):
    row = next(r for r in _immutable_rows() if r.pos == sheet and r.russian == word)
    assert row.examples == text
    assert text not in row.info
    assert text not in row.english


def test_immutable_lexeme_references_stay_inline():
    rows = {(r.pos, r.russian): r for r in _immutable_rows()}
    assert "потому что" in rows[("Conjunctions", "так как")].info
    assert rows[("Conjunctions", "так как")].examples == ""
    assert "пока не" in rows[("Conjunctions", "пока (conjunction)")].info


def test_mutable_standalone_examples_moved_and_glossed_russian_kept():
    verbs = {r.imperfective: r for r in _mutable_rows()["Verbs"]}
    assert verbs["касаться"].examples == "это тебя не каса́ется"
    assert "каса́ется" not in verbs["касаться"].additional_info
    assert "звонить кому" in verbs["звонить"].additional_info
    assert verbs["звонить"].examples == ""
    adverbs = {r.adverb: r for r in _mutable_rows()["Adverbs"]}
    assert adverbs["ужасно"].examples == "ужа́сно рад"
    assert adverbs["хорошо"].examples == ""
    assert "Всё хорошо́ = everything's fine" in adverbs["хорошо"].additional_info
    adjectives = {r.russian_m: r for r in _mutable_rows()["Adjectives"]}
    assert adjectives["иной"].additional_info == "more literary than другой"
    assert adjectives["иной"].translation == "different / other"


@pytest.mark.parametrize("sheet", list(mutable_words_plan.FIELD_NAMES))
def test_examples_field_follows_additional_info(sheet):
    names = mutable_words_plan.FIELD_NAMES[sheet]
    assert names.index("Examples") == names.index("Additional Info") + 1


@pytest.mark.parametrize("sheet", list(mutable_words_plan.FIELD_NAMES))
def test_mutable_rows_carry_examples_in_field_order(sheet):
    names = mutable_words_plan.FIELD_NAMES[sheet]
    for row in _mutable_rows()[sheet]:
        fields = row.fields()
        assert len(fields) == len(names)
        assert fields[names.index("Examples")] == row.examples


@pytest.mark.parametrize("sheet", list(mutable_words_plan.FIELD_NAMES))
def test_mutable_back_templates_render_examples_through_add_title(sheet):
    for card_index in range(mutable_words.TEMPLATE_COUNTS_BY_SHEET[sheet]):
        qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
        assert 'id="examples"' not in qfmt
        assert afmt.count('<div id="examples">{{Examples}}</div>') == 1
        assert afmt.count('addTitle("examples", "Examples");') == 1


def test_examples_css_covers_the_examples_id_and_its_detail_children():
    for selector in ("#examples", "#examples .title", "#examples .body"):
        assert re.search(
            rf"^{re.escape(selector)} \{{", examples_field.EXAMPLES_CSS, re.M
        )
    assert "#examples" not in mutable_words_plan.EXTRA_CSS


def test_all_seven_note_types_register_with_checks_on(tmp_path):
    source_path = os.path.join(str(tmp_path), "source.anki2")
    _build_synthetic_source_collection(source_path)
    snapshot = os.path.join(str(tmp_path), "snapshot.anki2")
    shutil.copy2(source_path, snapshot)

    build_col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    try:
        source_col = Collection(snapshot)
        try:
            immutable = immutable_words.clone_note_type(
                source_col, build_col, immutable_words.NEW_NOTE_TYPE_NAME
            )
            mutable = mutable_words.build_note_types(source_col, build_col)
        finally:
            source_col.close()
        registered = [immutable, *mutable.values()]
        assert len(registered) == 7
        assert len({note_type["id"] for note_type in registered}) == 7
        for note_type in registered:
            names = [field["name"] for field in note_type["flds"]]
            assert names.index("Examples") == names.index("Additional Info") + 1
    finally:
        build_col.close()
