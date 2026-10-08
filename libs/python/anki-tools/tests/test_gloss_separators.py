import csv
import re
from pathlib import Path

import pytest

from anki_tools.gloss_separators import normalize_gloss

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"

TOP_LEVEL_SEPARATOR = re.compile(r"[;,]")


def _top_level_text(value: str) -> str:
    """`value` with every parenthetical, quoted run, tag and entity removed."""
    without_markup = re.sub(r"<[^>]*>|&[a-zA-Z#0-9]+;", "", value)
    without_quotes = re.sub(r'"[^"]*"|“[^”]*”', "", without_markup)
    return re.sub(r"\([^()]*\)", "", without_quotes)


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("about, regarding (whom/what)", "about / regarding (whom/what)"),
        ("earth; land; ground", "earth / land / ground"),
        ("OK, all right, fine", "OK / all right / fine"),
        ("nothing; it's OK, no problem", "nothing / it's OK / no problem"),
        ("past; last (week, year)", "past / last (week, year)"),
    ],
)
def test_top_level_separators_become_slashes(source: str, expected: str) -> None:
    assert normalize_gloss(source) == expected


@pytest.mark.parametrize(
    "source",
    [
        "you (singular, informal)",
        "-self (emphatic: myself, yourself, himself...)",
        "in / at (where)<br>into (where/what)",
        "it is possible/allowed to",
        "despite the fact that",
    ],
)
def test_protected_punctuation_is_untouched(source: str) -> None:
    assert normalize_gloss(source) == source


def test_semicolon_inside_parentheses_survives() -> None:
    source = "also, in addition (same subject, an extra thing; more formal)"
    assert normalize_gloss(source) == (
        "also / in addition (same subject, an extra thing; more formal)"
    )


def test_comma_inside_quotes_survives() -> None:
    source = 'time, occasion (as in "once, twice...")'
    assert normalize_gloss(source) == 'time / occasion (as in "once, twice...")'


def test_html_passes_through_opaquely() -> None:
    source = "through, across (what/where)<br>in (when/time)"
    assert normalize_gloss(source) == (
        "through / across (what/where)<br>in (when/time)"
    )


def test_normalization_is_idempotent() -> None:
    for source in ("a, b; c", "x (y, z)", 'q, "r, s"', "m<br>n, o"):
        once = normalize_gloss(source)
        assert normalize_gloss(once) == once


def test_tsv_english_columns_carry_no_top_level_separator() -> None:
    offenders: list[str] = []
    for path in sorted(DATA_DIR.glob("*.tsv")):
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                gloss = (row.get("English") or "").strip()
                if TOP_LEVEL_SEPARATOR.search(_top_level_text(gloss)):
                    offenders.append(f"{path.name}: {gloss}")
    assert offenders == []


def test_source_word_list_english_column_carries_no_top_level_separator() -> None:
    offenders: list[str] = []
    for line in SOURCE_LIST.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        if TOP_LEVEL_SEPARATOR.search(_top_level_text(cells[2])):
            offenders.append(cells[2])
    assert offenders == []
