import csv
import dataclasses
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

VOCAB = DATA_PATH.parent.parent / "russian-vocabulary"

EXPECTED_COUNTS = {
    "Singular Noun Endings": 36,
    "Plural Noun Endings": 24,
    "Adjective Endings": 48,
    "Personal Pronouns": 42,
    "Particles": 3,
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
        if row.table != "Particles":
            assert any(case in row.front for case in CASES)


def test_corrected_neuter_instrumental_endings():
    by_front = {row.front: row.target for row in parse_rows()}
    assert by_front["Singular Nouns: Neuter Hard (-о) → Instrumental ending?"] == "-ом"
    assert by_front["Singular Nouns: Neuter Soft (-е) → Instrumental ending?"] == "-ем"


def test_pronoun_answers_match_table():
    by_front = {row.front: row.target for row in parse_rows()}
    assert by_front["Pronoun: 'She' (Она) → Instrumental?"] == "ей (ней)"
    assert by_front["Pronoun: 'He / It' (Он / Оно) → Prepositional?"] == "нём"


def test_example_words_are_russian():
    for row in parse_rows():
        for example in row.examples:
            assert not re.search("[A-Za-z]", example.base + example.form), row.front


def _plain(word):
    return word.replace("\u0301", "")


def _vocab(name):
    path = VOCAB / name
    return list(csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"))


def test_example_bases_come_from_the_mutable_deck():
    words = {_plain(r["Russian"]) for r in _vocab("nouns.tsv")}
    words |= {_plain(r["Russian (m)"]) for r in _vocab("adjectives.tsv")}
    words |= {_plain(r["Russian"]) for r in _vocab("pronouns.tsv")}
    for row in parse_rows():
        if row.table == "Particles":
            continue
        for example in row.examples:
            assert _plain(example.base) in words, (row.front, example.base)


def test_particle_examples_attach_the_target_to_the_base():
    verbs = {r["Imperfective"] for r in _vocab("verbs.tsv")}
    verbs |= {r["Perfective"] for r in _vocab("verbs.tsv")}
    particles = [row for row in parse_rows() if row.table == "Particles"]
    assert [row.target for row in particles] == ["-то", "-нибудь", "-ка"]
    for row in particles:
        for example in row.examples:
            assert example.form == example.base + row.target
            if row.target == "-ка":
                assert example.note in verbs


def test_noun_example_forms_match_the_deck_columns():
    nouns = {_plain(r["Russian"]): r for r in _vocab("nouns.tsv")}
    columns = {
        ("Singular", "Genitive"): "Genitive Sg",
        ("Plural", "Nominative"): "Plural",
        ("Plural", "Genitive"): "Genitive Pl",
    }
    checked = 0
    for row in parse_rows():
        number = row.front.split(" ", 1)[0]
        case = re.search(r"→ (\w+)", row.front).group(1)
        column = columns.get((number, case))
        if column is None:
            continue
        for example in row.examples:
            assert _plain(example.form) == _plain(nouns[example.base][column])
            checked += 1
    assert checked == 28


def test_each_card_has_a_male_and_a_female_example_line():
    for row in parse_rows():
        html = row.fields()[3]
        assert html.count('class="ex-line"') == 2
        assert html.count("_m2.mp3") == 2 and html.count("_f1.mp3") == 2


def test_rejects_duplicate_front(tmp_path):
    lines = DATA_PATH.read_text(encoding="utf-8").splitlines()
    path = tmp_path / "dup.tsv"
    path.write_text("\n".join([lines[0], lines[1], lines[1]]) + "\n", encoding="utf-8")
    with pytest.raises(SourceError):
        parse_rows(path)


def test_apply_builds_decks_and_is_idempotent(col):
    rows = parse_rows()
    first = apply_rows(col, rows)
    assert (first.added, first.updated, first.unchanged) == (153, 0, 0)
    for table, subdeck in TABLE_SUBDECKS.items():
        deck_id = col.decks.id_for_name(f"{DECK_ROOT}::{subdeck}")
        assert len(col.decks.cids(deck_id)) == EXPECTED_COUNTS[table]
    assert col.models.get(NOTE_TYPE_ID) is not None
    assert all(card.type == 0 for card in map(col.get_card, col.find_cards("")))

    second = apply_rows(col, rows)
    assert (second.added, second.updated, second.unchanged) == (0, 0, 153)
    assert col.note_count() == 153


def test_apply_updates_changed_field_without_new_note(col):
    rows = parse_rows()
    apply_rows(col, rows)
    changed = [dataclasses.replace(rows[0], notes="edited")]
    result = apply_rows(col, changed + rows[1:])
    assert (result.added, result.updated) == (0, 1)
    assert col.note_count() == 153
