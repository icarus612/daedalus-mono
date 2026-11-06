import re

import pytest
from anki.collection import Collection

from anki_tools.grammar_deck import (
    DATA_PATH,
    DECK_ROOT,
    NOTE_TYPE_ID,
    TABLE_SUBDECKS,
    SourceError,
    apply_rows,
    parse_rows,
)

EXPECTED_COUNTS = {
    "Singular Noun Endings": 36,
    "Plural Noun Endings": 24,
    "Adjective Endings": 48,
    "Personal Pronouns": 42,
}
CASES = (
    "Nominative",
    "Genitive",
    "Dative",
    "Accusative",
    "Instrumental",
    "Prepositional",
)


@pytest.fixture
def col(tmp_path):
    collection = Collection(str(tmp_path / "c.anki2"))
    yield collection
    collection.close()


def test_source_covers_every_table_cell():
    rows = parse_rows()
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.table] = counts.get(row.table, 0) + 1
    assert counts == EXPECTED_COUNTS
    for row in rows:
        assert row.type == "Grammar Rule"
        assert any(case in row.front for case in CASES)


def test_corrected_neuter_instrumental_endings():
    by_front = {row.front: row.target for row in parse_rows()}
    assert by_front["Singular Nouns: Neuter Hard (-о) → Instrumental ending?"] == "-ом"
    assert by_front["Singular Nouns: Neuter Soft (-е) → Instrumental ending?"] == "-ем"


def test_pronoun_answers_match_table():
    by_front = {row.front: row.target for row in parse_rows()}
    assert by_front["Pronoun: 'She' (Она) → Instrumental?"] == "ей (ней)"
    assert by_front["Pronoun: 'He / It' (Он / Оно) → Prepositional?"] == "нём"


def test_targets_and_examples_are_russian_only_where_expected():
    for row in parse_rows():
        assert not re.search("[A-Za-z]", row.example), row.front


def test_rejects_duplicate_front(tmp_path):
    lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
    path = tmp_path / "dup.tsv"
    path.write_text("\n".join([lines[0], lines[1], lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(SourceError):
        parse_rows(path)


def test_apply_builds_decks_and_is_idempotent(col):
    rows = parse_rows()
    first = apply_rows(col, rows)
    assert (first.added, first.updated, first.unchanged) == (150, 0, 0)
    for table, subdeck in TABLE_SUBDECKS.items():
        deck_id = col.decks.id_for_name(f"{DECK_ROOT}::{subdeck}")
        assert len(col.decks.cids(deck_id)) == EXPECTED_COUNTS[table]
    assert col.models.get(NOTE_TYPE_ID) is not None
    assert all(card.type == 0 for card in map(col.get_card, col.find_cards("")))

    second = apply_rows(col, rows)
    assert (second.added, second.updated, second.unchanged) == (0, 0, 150)
    assert col.note_count() == 150


def test_apply_updates_changed_field_without_new_note(col):
    rows = parse_rows()
    apply_rows(col, rows)
    changed = [rows[0].__class__(**{**rows[0].__dict__, "notes": "edited"})]
    result = apply_rows(col, changed + rows[1:])
    assert (result.added, result.updated) == (0, 1)
    assert col.note_count() == 150
