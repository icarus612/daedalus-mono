import ast
import copy
import os

import pytest

import anki_tools
from anki_tools import immutable_words_plan as iwp
from anki_tools import mutable_words_plan as mwp
from anki_tools import source_drift as sd
from anki_tools import variant_pairs

IMMUTABLE_TYPE = "Russian - Immutable Words (Ellis Version)"
SHEETS = ("Nouns", "Verbs", "Adjectives", "Adverbs", "Pronouns", "Numerals")
TSV_NAMES = {sheet: f"{sheet.lower()}.tsv" for sheet in SHEETS}
REAL_SOURCE_DIR = os.path.join(
    os.path.dirname(anki_tools.__file__), "data", "russian-vocabulary"
)
FIXTURE_ROWS = 3

WORD_LIST = """# Fixture

### Prepositions (Предлоги)
| Rank | Russian | English | Info | Examples |
|---|---|---|---|---|
| 1 | в | in | Prepositional for location | — |
| 2 | на | on | Accusative for motion onto | — |

### Conjunctions (Союзы)
| Rank | Russian | English |
|---|---|---|
| 1 | и | and |

### Particles (Частицы)
| Rank | Russian | English |
|---|---|---|
| 1 | не | not |

### Indeclinable Nouns (Несклоняемые)
| Rank | Russian | English |
|---|---|---|
| 1 | кино | cinema |

### Base Adverbs (Наречия)
| Rank | Russian | English | Info | Examples |
|---|---|---|---|---|
| 1 | очень | very | — | — |
"""


def write_source(tmp_path, word_list=WORD_LIST):
    source_dir = tmp_path / "vocab"
    source_dir.mkdir()
    for name in TSV_NAMES.values():
        with open(os.path.join(REAL_SOURCE_DIR, name), encoding="utf-8") as handle:
            head = [next(handle) for _ in range(FIXTURE_ROWS + 1)]
        (source_dir / name).write_text("".join(head), encoding="utf-8")
    return word_list, str(source_dir)


def collection_notes(expected):
    return [sd.CollectionNote(e.guid, e.note_type, dict(e.fields)) for e in expected]


def note(guid="g1", note_type=IMMUTABLE_TYPE, headword="в", **fields):
    return sd.ExpectedNote(guid, note_type, headword, dict(fields))


def stored(guid="g1", note_type=IMMUTABLE_TYPE, **fields):
    return sd.CollectionNote(guid, note_type, dict(fields))


def test_managed_note_types_are_immutable_variant_pairs_and_six_mutable_names():
    expected = {
        IMMUTABLE_TYPE,
        variant_pairs.NOTE_TYPE_NAME,
        *mwp.NOTE_TYPE_NAMES.values(),
    }
    assert sd.managed_note_types() == frozenset(expected)
    assert len(sd.managed_note_types()) == 8


def test_expected_notes_covers_every_source_row(tmp_path):
    text, source_dir = write_source(tmp_path)
    result = sd.expected_notes(text, source_dir)
    assert len(result) == len(iwp.parse_word_list(text)) + 4 + 6 * FIXTURE_ROWS
    assert len({e.guid for e in result}) == len(result)
    by_type = {e.note_type for e in result}
    assert by_type == set(sd.managed_note_types())


def test_expected_immutable_note_matches_the_plan_row(tmp_path):
    text, source_dir = write_source(tmp_path)
    row = iwp.parse_word_list(text)[0]
    found = next(e for e in sd.expected_notes(text, source_dir) if e.guid == row.guid)
    assert found.note_type == IMMUTABLE_TYPE
    assert found.headword == row.russian
    assert found.fields == dict(zip(iwp.FIELD_NAMES, row.fields()))


def test_expected_variant_pair_notes_match_the_table(tmp_path):
    text, source_dir = write_source(tmp_path)
    by_guid = {e.guid: e for e in sd.expected_notes(text, source_dir)}
    pairs = variant_pairs.load_pairs()
    assert pairs
    for pair in pairs:
        found = by_guid[pair.guid]
        assert found.note_type == variant_pairs.NOTE_TYPE_NAME
        assert found.headword == pair.headword
        assert found.fields == dict(zip(variant_pairs.FIELD_NAMES, pair.fields()))


@pytest.mark.parametrize(
    ("sheet", "parser"),
    [
        ("Nouns", mwp.parse_nouns),
        ("Verbs", mwp.parse_verbs),
        ("Adjectives", mwp.parse_adjectives),
        ("Adverbs", mwp.parse_adverbs),
        ("Pronouns", mwp.parse_pronouns),
        ("Numerals", mwp.parse_numerals),
    ],
)
def test_expected_mutable_notes_match_the_plan_rows(tmp_path, sheet, parser):
    text, source_dir = write_source(tmp_path)
    rows = parser(os.path.join(source_dir, TSV_NAMES[sheet]))
    by_guid = {e.guid: e for e in sd.expected_notes(text, source_dir)}
    assert rows
    for row in rows:
        built = by_guid[row.guid]
        assert built.note_type == mwp.NOTE_TYPE_NAMES[sheet]
        assert built.fields == dict(zip(mwp.FIELD_NAMES[sheet], row.fields()))
        assert built.headword


def test_expected_verb_headword_is_the_imperfective(tmp_path):
    text, source_dir = write_source(tmp_path)
    verbs = mwp.parse_verbs(os.path.join(source_dir, "verbs.tsv"))
    by_guid = {e.guid: e for e in sd.expected_notes(text, source_dir)}
    assert (
        by_guid[verbs[0].guid].headword == by_guid[verbs[0].guid].fields["Imperfective"]
    )


def test_expected_notes_raises_for_a_missing_tsv(tmp_path):
    text, source_dir = write_source(tmp_path)
    expected = sd.expected_notes(text, source_dir)
    assert expected
    os.remove(os.path.join(source_dir, "verbs.tsv"))
    with pytest.raises(FileNotFoundError):
        sd.expected_notes(text, source_dir)


def test_identical_collection_reports_nothing(tmp_path):
    text, source_dir = write_source(tmp_path)
    expected = sd.expected_notes(text, source_dir)
    report = sd.compare(expected, collection_notes(expected))
    assert (report.drift, report.orphans, report.missing) == ([], [], [])


def test_a_changed_value_is_one_drift_row_with_all_six_columns():
    report = sd.compare(
        [note(Translation="in", Case="Prepositional")],
        [stored(Translation="inside", Case="Prepositional")],
    )
    assert report.drift == [
        sd.DriftRow("g1", IMMUTABLE_TYPE, "в", "Translation", "inside", "in")
    ]


@pytest.mark.parametrize(
    ("collection_value", "source_value"),
    [("in ", "in"), ("In", "in"), (" in", "in"), ("in<br>", "in"), ("", "in")],
)
def test_comparison_is_exact_with_no_normalisation(collection_value, source_value):
    report = sd.compare(
        [note(Translation=source_value)], [stored(Translation=collection_value)]
    )
    assert [r.field for r in report.drift] == ["Translation"]


def test_an_equal_value_is_not_drift():
    report = sd.compare([note(Translation="in")], [stored(Translation="in")])
    assert report.drift == []


def test_a_field_the_collection_lacks_is_skipped():
    report = sd.compare([note(Translation="in", Case="x")], [stored(Translation="in")])
    assert report.drift == []


def test_a_field_only_the_collection_has_is_ignored():
    report = sd.compare(
        [note(Translation="in")], [stored(Translation="in", Extra="whatever")]
    )
    assert report.drift == []


def test_orphans_are_unmatched_notes_of_managed_types_only():
    foreign = stored("g3", "LlamaNote", Front="x")
    managed = stored("g2", mwp.NOTE_TYPE_NAMES["Nouns"], Russian="дом")
    report = sd.compare(
        [note(Translation="in")], [stored(Translation="in"), managed, foreign]
    )
    assert report.orphans == [managed]


def test_foreign_note_type_with_a_source_guid_is_still_not_an_orphan():
    report = sd.compare([], [stored("g9", "LlamaNote", Front="x")])
    assert report.orphans == []


def test_missing_lists_source_rows_without_a_collection_note():
    absent = note("g2", headword="на", Translation="on")
    report = sd.compare([note(Translation="in"), absent], [stored(Translation="in")])
    assert report.missing == [absent]
    assert report.orphans == []


def test_drift_is_sorted_by_type_headword_then_field_order():
    noun_type = mwp.NOTE_TYPE_NAMES["Nouns"]
    expected = [
        note("g1", IMMUTABLE_TYPE, "б", Translation="s", Case="s"),
        note("g2", IMMUTABLE_TYPE, "а", Translation="s", Case="s"),
        note("g3", noun_type, "я", Translation="s"),
    ]
    actual = [
        stored("g1", IMMUTABLE_TYPE, Translation="c", Case="c"),
        stored("g2", IMMUTABLE_TYPE, Translation="c", Case="c"),
        stored("g3", noun_type, Translation="c"),
    ]
    keys = [
        (r.note_type, r.headword, r.field) for r in sd.compare(expected, actual).drift
    ]
    assert keys == sorted(keys, key=lambda k: (k[0], k[1]))
    assert keys[:2] == [
        (IMMUTABLE_TYPE, "а", "Translation"),
        (IMMUTABLE_TYPE, "а", "Case"),
    ]


def test_compare_does_not_mutate_inputs_and_is_deterministic():
    expected = [note(Translation="in"), note("g2", headword="на", Translation="on")]
    actual = [
        stored(Translation="x"),
        stored("g7", mwp.NOTE_TYPE_NAMES["Nouns"], Russian="д"),
    ]
    before = copy.deepcopy((expected, actual))
    first = sd.compare(expected, actual)
    second = sd.compare(expected, actual)
    assert (expected, actual) == before
    assert first == second
    assert first.drift and first.orphans and first.missing


def test_source_drift_imports_nothing_from_anki():
    with open(sd.__file__, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
    assert imported
    assert not [name for name in imported if name.split(".")[0] == "anki"]
    assert not [name for name in imported if name.endswith("immutable_words")]


def test_dataclasses_are_frozen():
    with pytest.raises(AttributeError):
        note().guid = "other"
