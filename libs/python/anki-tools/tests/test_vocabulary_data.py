"""Tests for the committed russian-vocabulary TSV data files and README."""

import subprocess
import zipfile
from pathlib import Path

import pytest

DATA_DIR = (
    Path(__file__).resolve().parents[1] / "anki_tools" / "data" / "russian-vocabulary"
)

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
        "Status",
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
        "Status",
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
        "Status",
    ],
}

EXPECTED_LINE_COUNTS = {
    "nouns.tsv": 542,
    "verbs.tsv": 180,
    "adjectives.tsv": 153,
    "adverbs.tsv": 153,
}

DASH_VALUES = {"—", "–", "-", "--"}

EXPECTED_DASH_COUNTS = {
    ("nouns.tsv", "Plural"): 107,
    ("adverbs.tsv", "Comparative"): 36,
    ("adverbs.tsv", "Adverb"): 22,
    ("adverbs.tsv", "Stress"): 22,
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


def test_readme_mentions_source_and_files():
    readme_path = DATA_DIR / "README.md"
    text = readme_path.read_text(encoding="utf-8")
    assert "russian_vocabulary.xlsx" in text
    assert "vocabulary_source" in text
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
