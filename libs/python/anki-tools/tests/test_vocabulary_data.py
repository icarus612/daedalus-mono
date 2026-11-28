"""Tests for the committed russian-vocabulary TSV data files and README."""

import re
import subprocess
import zipfile
from pathlib import Path

import pytest

DATA_DIR = (
    Path(__file__).resolve().parents[1] / "anki_tools" / "data" / "russian-vocabulary"
)

PRONOUN_SLOT_COLUMNS = [
    "Nominative f.",
    "Nominative n.",
    "Nominative pl.",
    "Genitive",
    "Genitive f.",
    "Genitive pl.",
    "Genitive (н-)",
    "Dative",
    "Dative f.",
    "Dative pl.",
    "Dative (н-)",
    "Accusative",
    "Accusative m. living",
    "Accusative n.",
    "Accusative f.",
    "Accusative pl.",
    "Accusative pl. living",
    "Accusative (н-)",
    "Instrumental",
    "Instrumental f.",
    "Instrumental pl.",
    "Instrumental (н-)",
    "Prepositional",
    "Prepositional f.",
    "Prepositional pl.",
]

EXPECTED_HEADERS = {
    "nouns.tsv": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Gender",
        "Plural",
        "Genitive Sg",
        "Genitive Pl",
        "Animate",
        "Category",
        "Additional Info",
        "Examples",
        "Status",
        "Degrees",
    ],
    "verbs.tsv": [
        "#",
        "Imperfective",
        "Perfective",
        "English",
        "Stress",
        "Conjugation",
        "я (1sg)",
        "ты (2sg)",
        "они (3pl)",
        "Past (m / f)",
        "Case / Preposition",
        "Additional Info",
        "Examples",
        "Status",
        "Case",
    ],
    "adjectives.tsv": [
        "#",
        "Russian (m)",
        "English",
        "Stress",
        "Feminine",
        "Neuter",
        "Plural",
        "Short Form",
        "Comparative",
        "Opposite",
        "Stem Type",
        "Additional Info",
        "Examples",
        "Status",
    ],
    "adverbs.tsv": [
        "#",
        "Adverb",
        "English",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Examples",
        "Status",
        "Case",
    ],
    "pronouns.tsv": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Pronoun Type",
        "Additional Info",
        "Examples",
        *PRONOUN_SLOT_COLUMNS,
        "Status",
    ],
    "numerals.tsv": [
        "#",
        "Russian",
        "English",
        "Stress",
        "Numeral Type",
        "Case Governed",
        "Gender Forms",
        "Genitive",
        "Additional Info",
        "Examples",
        "Status",
    ],
}

EXPECTED_LINE_COUNTS = {
    "nouns.tsv": 2122,
    "verbs.tsv": 224,
    "adjectives.tsv": 194,
    "adverbs.tsv": 168,
    "pronouns.tsv": 31,
    "numerals.tsv": 56,
}

DASH_VALUES = {"—", "–", "-", "--"}

EXPECTED_DASH_COUNTS = {
    ("nouns.tsv", "Plural"): 206,
    ("verbs.tsv", "я (1sg)"): 2,
    ("verbs.tsv", "ты (2sg)"): 2,
    ("verbs.tsv", "они (3pl)"): 2,
    ("verbs.tsv", "Past (m / f)"): 2,
    ("adjectives.tsv", "Short Form"): 7,
    ("adjectives.tsv", "Comparative"): 9,
    ("adjectives.tsv", "Opposite"): 8,
    ("adverbs.tsv", "Comparative"): 45,
    ("adverbs.tsv", "Adverb"): 22,
    ("adverbs.tsv", "Stress"): 22,
    ("numerals.tsv", "Gender Forms"): 44,
}

FILENAMES = list(EXPECTED_HEADERS)


def _read_lines(filename):
    path = DATA_DIR / filename
    raw = path.read_bytes()
    assert b"\r\n" not in raw
    text = raw.decode("utf-8")
    assert not text.startswith("﻿")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def _read_rows(filename):
    return [line.split("\t") for line in _read_lines(filename)]


@pytest.mark.parametrize("filename", FILENAMES)
def test_header_row(filename):
    rows = _read_rows(filename)
    assert rows[0] == EXPECTED_HEADERS[filename]


@pytest.mark.parametrize("filename", FILENAMES)
def test_line_count(filename):
    lines = _read_lines(filename)
    assert len(lines) == EXPECTED_LINE_COUNTS[filename]


@pytest.mark.parametrize("filename", FILENAMES)
def test_no_embedded_tabs_in_fields(filename):
    rows = _read_rows(filename)
    header = rows[0]
    for row in rows[1:]:
        assert len(row) == len(header)


def test_dash_only_cell_census():
    actual_counts = {}
    for filename in FILENAMES:
        rows = _read_rows(filename)
        header = rows[0]
        data_rows = rows[1:]
        for col_index, col_name in enumerate(header):
            count = sum(1 for row in data_rows if row[col_index].strip() in DASH_VALUES)
            actual_counts[(filename, col_name)] = count

    for key, expected in EXPECTED_DASH_COUNTS.items():
        assert actual_counts[key] == expected

    for key, count in actual_counts.items():
        if key not in EXPECTED_DASH_COUNTS:
            assert count == 0, f"unexpected dash-only cells at {key}: {count}"


DEGREES_ANCHORS = {
    "телефон": "0",
    "автор": "0",
    "министр": "1",
    "федерация": "1",
    "церковь": "1",
    "брат": "2",
    "нос": "2",
    "вода": "2",
    "стол": "3",
    "город": "3",
    "дом": "3",
}


def _noun_degrees():
    rows = _read_rows("nouns.tsv")
    header = rows[0]
    return {
        row[header.index("Russian")]: row[header.index("Degrees")] for row in rows[1:]
    }


def test_every_noun_has_a_degrees_value_from_zero_to_three():
    rows = _read_rows("nouns.tsv")
    column = rows[0].index("Degrees")
    assert {row[column] for row in rows[1:]} <= {"0", "1", "2", "3"}


def test_degrees_anchors_hold():
    degrees = _noun_degrees()
    assert {word: degrees[word] for word in DEGREES_ANCHORS} == DEGREES_ANCHORS


def test_readme_states_tsvs_are_only_source():
    readme_path = DATA_DIR / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    assert "only source" in text
    for filename in FILENAMES:
        assert filename in text


def _find_workspace_root(start):
    current = start
    for _ in range(8):
        candidate = current / "pyproject.toml"
        if candidate.is_file() and "[tool.uv.workspace]" in candidate.read_text(
            encoding="utf-8"
        ):
            return current
        current = current.parent
    raise RuntimeError("could not locate uv workspace root")


def test_wheel_build_includes_tsv_data(tmp_path):
    workspace_root = _find_workspace_root(DATA_DIR)
    dist_dir = tmp_path / "dist"
    result = subprocess.run(
        [
            "uv",
            "build",
            "--package",
            "anki-tools",
            "--wheel",
            "--out-dir",
            str(dist_dir),
        ],
        cwd=workspace_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    wheels = list(dist_dir.glob("anki_tools-*.whl"))
    assert len(wheels) == 1
    with zipfile.ZipFile(wheels[0]) as archive:
        names = set(archive.namelist())

    for filename in FILENAMES:
        assert f"anki_tools/data/russian-vocabulary/{filename}" in names


SOURCE_LIST = (
    Path(__file__).resolve().parents[1] / "tests" / "data" / "source-word-list.md"
)

_PARENTHETICAL = re.compile(r"\([^)]*\)")
_LINE_BREAK = re.compile(r"<br\s*/?>|</?div>|</?p>")
_TRAILING_CUE = re.compile(r"\(([^)]*)\)\s*$")


def _top_level_senses(line):
    """The `/`-separated glosses on one line, ignoring `/` inside parens."""
    pieces, buffer, depth = [], [], 0
    for char in _PARENTHETICAL.sub("", line):
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        if char == "/" and depth == 0:
            pieces.append("".join(buffer))
            buffer = []
        else:
            buffer.append(char)
    pieces.append("".join(buffer))
    return [p.strip() for p in pieces if p.strip()]


def _english_cells():
    for filename in FILENAMES:
        rows = _read_rows(filename)
        english = rows[0].index("English")
        for row in rows[1:]:
            if row[1] and row[1] not in DASH_VALUES:
                yield filename, row[1], row[english]
    for line in SOURCE_LIST.read_text(encoding="utf-8").split("\n"):
        if not line.startswith("| ") or "---" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3 and cells[0].isdigit():
            yield "source-word-list.md", cells[1], cells[2]


def _cues_enumerating_two_senses(cells):
    """Cells whose trailing cue lists two meanings for a multi-sense line."""
    offenders = []
    for filename, word, cell in cells:
        for line in _LINE_BREAK.split(cell):
            cue = _TRAILING_CUE.search(line)
            if cue and ", or " in cue.group(1) and len(_top_level_senses(line)) > 1:
                offenders.append((filename, word, line.strip()))
    return offenders


def test_a_cue_never_enumerates_two_senses_on_one_line():
    """Distinct senses go on their own line via `<br>`, each with its own
    cue -- the shape the immutable prepositions established."""
    assert _cues_enumerating_two_senses(_english_cells()) == []


def test_the_two_sense_cue_check_catches_the_shape_it_guards():
    tainted = [("nouns.tsv", "число", "number / date (a numeral, or a calendar day)")]
    assert _cues_enumerating_two_senses(tainted) == [
        ("nouns.tsv", "число", "number / date (a numeral, or a calendar day)")
    ]


COMBINING_ACUTE = "\u0301"


def _pronoun_records():
    rows = _read_rows("pronouns.tsv")
    header = rows[0]
    return [dict(zip(header, row, strict=True)) for row in rows[1:]]


def _pronoun(russian):
    matches = [
        record
        for record in _pronoun_records()
        if record["Russian"].replace(COMBINING_ACUTE, "") == russian
    ]
    assert len(matches) == 1, russian
    return matches[0]


def _filled_slots(record):
    return {column: record[column] for column in PRONOUN_SLOT_COLUMNS if record[column]}


def test_pronoun_slot_cells_hold_exactly_one_form():
    for record in _pronoun_records():
        for column, cell in _filled_slots(record).items():
            for banned in (" ", "/", ",", "·", "living", "ни о"):
                assert banned not in cell, (record["Russian"], column, cell)
            assert cell == cell.strip(), (record["Russian"], column, cell)


def test_pronoun_slot_cells_total_375():
    total = sum(len(_filled_slots(record)) for record in _pronoun_records())
    assert total == 375


def test_pronoun_slot_column_order_and_width():
    header = _read_rows("pronouns.tsv")[0]
    assert len(PRONOUN_SLOT_COLUMNS) == 25
    assert len(header) == 33
    assert header[7:32] == PRONOUN_SLOT_COLUMNS
    assert header[-1] == "Status"
    assert "Gender Forms" not in header
    assert all(len(row) == 33 for row in _read_rows("pronouns.tsv"))


def test_pronoun_old_oblique_column_is_gone():
    assert "Oblique Forms" not in _read_rows("pronouns.tsv")[0]


@pytest.mark.parametrize(
    ("russian", "column", "expected"),
    [
        ("тот", "Genitive", "того́"),
        ("тот", "Genitive f.", "той"),
        ("тот", "Genitive pl.", "тех"),
        ("тот", "Accusative", "тот"),
        ("тот", "Accusative m. living", "того́"),
        ("тот", "Accusative n.", "то"),
        ("тот", "Accusative f.", "ту"),
        ("тот", "Accusative pl.", "те"),
        ("тот", "Accusative pl. living", "тех"),
        ("он", "Genitive", "его́"),
        ("он", "Genitive (н-)", "него́"),
        ("он", "Prepositional", "нём"),
        ("она", "Prepositional", "ней"),
        ("они", "Prepositional", "них"),
        ("я", "Genitive", "меня́"),
        ("никто", "Prepositional", "нико́м"),
        ("ничто", "Prepositional", "ничём"),
        ("тот", "Nominative f.", "та"),
        ("который", "Genitive f.", "кото́рой"),
        ("какой", "Instrumental pl.", "каки́ми"),
        ("самый", "Genitive", "са́мого"),
    ],
)
def test_pronoun_slot_spot_checks(russian, column, expected):
    assert _pronoun(russian)[column] == expected


def test_single_form_pronouns_leave_extra_slots_empty():
    record = _pronoun("я")
    extras = [c for c in PRONOUN_SLOT_COLUMNS if c not in _PRIMARY_SLOTS]
    assert all(record[column] == "" for column in extras)


_PRIMARY_SLOTS = {
    "Genitive",
    "Dative",
    "Accusative",
    "Instrumental",
    "Prepositional",
}
