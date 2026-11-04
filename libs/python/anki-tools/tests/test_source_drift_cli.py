import hashlib
import json
import os
import stat

import pytest
from anki.collection import Collection

import anki_tools
from anki_tools import mutable_words_plan as mwp
from anki_tools import source_drift as sd
from anki_tools import source_drift_cli as cli

IMMUTABLE_TYPE = "Russian - Immutable Words (Ellis Version)"
TSV_NAMES = [
    f"{sheet.lower()}.tsv"
    for sheet in ("Nouns", "Verbs", "Adjectives", "Adverbs", "Pronouns", "Numerals")
]
REAL_SOURCE_DIR = os.path.join(
    os.path.dirname(anki_tools.__file__), "data", "russian-vocabulary"
)
PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIXTURE_ROWS = 3
TSV_HEADER = "guid\tnote type\theadword\tfield\tcollection value\tsource value"

WORD_LIST = """### Prepositions (Предлоги)
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


@pytest.fixture
def sources(tmp_path):
    word_list = tmp_path / "words.md"
    word_list.write_text(WORD_LIST, encoding="utf-8")
    source_dir = tmp_path / "vocab"
    source_dir.mkdir()
    for name in TSV_NAMES:
        with open(os.path.join(REAL_SOURCE_DIR, name), encoding="utf-8") as handle:
            head = [next(handle) for _ in range(FIXTURE_ROWS + 1)]
        (source_dir / name).write_text("".join(head), encoding="utf-8")
    return str(word_list), str(source_dir)


def build_collection(path, expected, overrides=None, extra=()):
    overrides = overrides or {}
    fields_by_type = {}
    for item in list(expected) + [e for e in extra]:
        fields_by_type.setdefault(item.note_type, list(item.fields))
    col = Collection(str(path))
    try:
        for type_name, field_names in fields_by_type.items():
            models = col.models
            notetype = models.new(type_name)
            for field_name in field_names:
                models.add_field(notetype, models.new_field(field_name))
            template = models.new_template("Card 1")
            template["qfmt"] = "{{" + field_names[0] + "}}"
            template["afmt"] = "{{FrontSide}}"
            models.add_template(notetype, template)
            models.add(notetype)
        for item in list(expected) + list(extra):
            if item in extra and item.guid in overrides.get("skip", ()):
                continue
            built = col.new_note(col.models.by_name(item.note_type))
            built.guid = item.guid
            for field_name, value in item.fields.items():
                built[field_name] = overrides.get((item.guid, field_name), value)
            col.add_note(built, 1)
    finally:
        col.close()


def fingerprint(path):
    with open(path, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    return digest, os.stat(path).st_mtime_ns


def run(path, sources, *extra):
    word_list, source_dir = sources
    return cli.main(
        [
            "--collection",
            str(path),
            "--word-list",
            word_list,
            "--source-dir",
            source_dir,
            *extra,
        ]
    )


@pytest.fixture
def expected(sources):
    with open(sources[0], encoding="utf-8") as handle:
        return sd.expected_notes(handle.read(), sources[1])


def three_flips(expected):
    immutable = [e for e in expected if e.note_type == IMMUTABLE_TYPE]
    noun = next(e for e in expected if e.note_type == mwp.NOTE_TYPE_NAMES["Nouns"])
    chosen = [
        (noun, "Translation"),
        (immutable[0], "English Distinction"),
        (immutable[1], "Case"),
    ]
    return chosen, {(n.guid, f): "FLIPPED" for n, f in chosen}


def test_clean_collection_reports_no_drift_orphans_or_missing(
    tmp_path, sources, expected, capsys
):
    path = tmp_path / "c.anki2"
    build_collection(path, expected)
    assert run(path, sources) == 0
    out = capsys.readouterr().out
    assert "drift: 0 field(s) on 0 note(s)" in out
    assert "orphans: 0" in out and "missing: 0" in out
    assert str(path) in out


def test_tsv_of_a_clean_collection_is_header_only(tmp_path, sources, expected, capsys):
    path = tmp_path / "c.anki2"
    build_collection(path, expected)
    assert run(path, sources, "--format", "tsv") == 0
    assert capsys.readouterr().out.splitlines() == [TSV_HEADER]


def test_three_flipped_values_are_reported_exactly(tmp_path, sources, expected, capsys):
    chosen, overrides = three_flips(expected)
    path = tmp_path / "c.anki2"
    build_collection(path, expected, overrides)
    assert run(path, sources, "--format", "tsv") == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == TSV_HEADER
    rows = [line.split("\t") for line in lines[1:]]
    assert len(rows) == 3
    got = {(r[0], r[3]): r for r in rows}
    assert set(got) == {(n.guid, f) for n, f in chosen}
    for item, field in chosen:
        row = got[(item.guid, field)]
        assert row == [
            item.guid,
            item.note_type,
            item.headword,
            field,
            "FLIPPED",
            item.fields[field],
        ]


def test_text_report_counts_and_lists_the_flipped_values(
    tmp_path, sources, expected, capsys
):
    chosen, overrides = three_flips(expected)
    path = tmp_path / "c.anki2"
    build_collection(path, expected, overrides)
    assert run(path, sources) == 0
    out = capsys.readouterr().out
    assert "drift: 3 field(s) on 3 note(s)" in out
    for item, field in chosen:
        line = next(ln for ln in out.splitlines() if item.guid in ln and field in ln)
        assert "FLIPPED" in line and item.headword in line


def test_orphan_and_missing_sections_with_positive_control(
    tmp_path, sources, expected, capsys
):
    noun_type = mwp.NOTE_TYPE_NAMES["Nouns"]
    noun_fields = next(e for e in expected if e.note_type == noun_type).fields
    orphan = sd.ExpectedNote(
        "orphan-guid", noun_type, "x", dict(noun_fields, Russian="призрак")
    )
    foreign = sd.ExpectedNote("foreign-guid", "LlamaNote", "y", {"Front": "чужой"})
    dropped = expected[0]
    kept = [e for e in expected if e.guid != dropped.guid]
    path = tmp_path / "c.anki2"
    build_collection(path, kept, extra=[orphan, foreign])
    assert run(path, sources) == 0
    out = capsys.readouterr().out
    assert "orphans: 1" in out and "missing: 1" in out
    assert "orphan-guid" in out and "призрак" in out
    assert "foreign-guid" not in out and "чужой" not in out
    assert dropped.guid in out and dropped.headword in out


@pytest.mark.parametrize("with_drift", [False, True])
def test_original_collection_is_untouched(tmp_path, sources, expected, with_drift):
    _, overrides = three_flips(expected)
    path = tmp_path / "c.anki2"
    build_collection(path, expected, overrides if with_drift else None)
    before = fingerprint(path)
    listing = sorted(os.listdir(tmp_path))
    assert run(path, sources) == 0
    assert fingerprint(path) == before
    assert sorted(os.listdir(tmp_path)) == listing


def test_tool_actually_reads_the_collection(tmp_path, sources, expected, capsys):
    """Positive control: reporting drift proves the copy was opened and read."""
    _, overrides = three_flips(expected)
    path = tmp_path / "c.anki2"
    build_collection(path, expected, overrides)
    run(path, sources)
    assert "drift: 3" in capsys.readouterr().out


def test_nonexistent_collection_exits_two(tmp_path, sources, capsys):
    missing = tmp_path / "nope.anki2"
    assert run(missing, sources) == 2
    captured = capsys.readouterr()
    assert captured.err.strip()
    assert not missing.exists()


def test_tsv_values_have_tabs_and_newlines_flattened(
    tmp_path, sources, expected, capsys
):
    target = next(e for e in expected if e.note_type == IMMUTABLE_TYPE)
    path = tmp_path / "c.anki2"
    build_collection(path, expected, {(target.guid, "Translation"): "a\tb\nc"})
    assert run(path, sources, "--format", "tsv") == 0
    lines = capsys.readouterr().out.splitlines()
    rows = [line.split("\t") for line in lines[1:]]
    assert len(rows) == 1 and len(rows[0]) == 6
    assert "\t" not in rows[0][4] and rows[0][4].split() == ["a", "b", "c"]


def test_parser_defaults_and_options():
    parser = cli.build_parser()
    args = parser.parse_args([])
    assert args.format == "text"
    parsed = parser.parse_args(
        [
            "--collection",
            "c",
            "--word-list",
            "w",
            "--source-dir",
            "d",
            "--format",
            "tsv",
        ]
    )
    assert parsed.format == "tsv"
    with pytest.raises(SystemExit):
        parser.parse_args(["--format", "yaml"])


def test_help_exits_zero(capsys):
    with pytest.raises(SystemExit) as info:
        cli.main(["--help"])
    assert info.value.code == 0
    assert "--format" in capsys.readouterr().out


def test_cli_file_has_shebang_and_executable_bit():
    path = os.path.join(PKG_ROOT, "anki_tools", "source_drift_cli.py")
    with open(path, encoding="utf-8") as handle:
        assert handle.readline().strip() == "#!/usr/bin/env python3"
    assert os.stat(path).st_mode & stat.S_IXUSR


def test_package_json_registers_the_bin():
    with open(os.path.join(PKG_ROOT, "package.json"), encoding="utf-8") as handle:
        bins = json.load(handle)["bin"]
    assert bins["anki-source-drift"] == "anki_tools/source_drift_cli.py"


def test_immutable_literal_matches_the_imported_constant():
    from anki_tools import immutable_words

    assert immutable_words.NEW_NOTE_TYPE_NAME == IMMUTABLE_TYPE
    assert IMMUTABLE_TYPE in sd.managed_note_types()
