"""The `Case` field: the grammatical cases a Russian word governs.

The field holds the canonical case names alone, comma-joined in the order
`case-government.tsv` lists them; the card template renders them as pills
(`case_pill`). The TSV is the only source of which words govern which cases,
and optionally which gloss line of the translation goes with which case.

`residual_info_for_row` strips the governed case from the Prepositions section's
`Info` column, which names it by construction.

Pure text -- no Anki imports.
"""

import csv
import re
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

CASE_FIELD = "Case"

GOVERNING_SECTION = "Prepositions"

CASE_GOVERNMENT_PATH = Path(__file__).parent / "data" / "case-government.tsv"
LINE_CASE_SEPARATOR = " || "
LINE_CASE_ARROW = " => "


# Spelled out, never abbreviated: "prep." is reference-book shorthand that
# also looks like "preposition" -- the one thing it does not mean.
CASE_NAMES = (
    ("Nominative", "Nominative"),
    ("Genitive", "Genitive"),
    ("Dative", "Dative"),
    ("Accusative", "Accusative"),
    ("Instrumental", "Instrumental"),
    ("Prepositional", "Prepositional"),
)

# A dash clause is editorial commentary, not a second governed case:
# `вопреки`'s "Dative -- one of the few Genitive-looking ones that takes
# Dative" governs the dative ALONE, and reading the whole cell yields a
# wrong "Dative or Genitive".
_COMMENTARY = re.compile(r"\s+[—–-]\s+")


def case_name(info: str) -> str:
    """The governed case named by an `Info` cell, e.g. `Accusative or Prepositional`.

    Cases appear in the order the cell names them, so a two-case preposition
    reads the way the document writes it (`в / во` -> `Accusative or
    Prepositional`, never the table's own order).
    """
    governed = _COMMENTARY.split(info, maxsplit=1)[0]
    found = [
        (match.start(), name)
        for full, name in CASE_NAMES
        if (match := re.search(full, governed, re.I))
    ]
    if not found:
        return ""
    return " or ".join(name for _, name in sorted(found))


def residual_info_for_row(pos: str, info: str) -> str:
    """The `Additional Info` a row keeps once `Case` renders the case.

    The Prepositions section's `Info` column leads with the governed case (the
    pill renders it, and routing deletes any when-clause), so only the dash
    commentary after it survives. Every other section's `info` is unchanged.
    """
    if pos != GOVERNING_SECTION:
        return info
    parts = _COMMENTARY.split(info, maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


@dataclass(frozen=True)
class CaseGovernment:
    cases: tuple[str, ...]
    line_cases: Mapping[str, str]


_CANONICAL = frozenset(full for full, _ in CASE_NAMES)
_LINE_CASE_HEADERS = ("meaning→case", "meaning->case")


def _parse_cases(cell: str) -> tuple[str, ...]:
    names = tuple(name.strip() for name in cell.split(","))
    for name in names:
        if name not in _CANONICAL:
            raise ValueError(f"unknown case name: {name!r}")
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate case name in {cell!r}")
    return names


def _parse_line_cases(cell: str, cases: tuple[str, ...]) -> dict[str, str]:
    if not cell.strip():
        return {}
    line_cases: dict[str, str] = {}
    for entry in cell.split(LINE_CASE_SEPARATOR):
        line, arrow, case = entry.partition(LINE_CASE_ARROW)
        line, case = line.strip(), case.strip()
        if not arrow or not line:
            raise ValueError(f"malformed meaning->case entry: {entry!r}")
        if case not in _CANONICAL:
            raise ValueError(f"unknown case name: {case!r}")
        if case not in cases:
            raise ValueError(f"line case {case!r} is not in cases {cases}")
        line_cases[line] = case
    return line_cases


def load_case_government(path: Path | str | None = None) -> dict[str, CaseGovernment]:
    """Read the case-government TSV into `{guid: CaseGovernment}`.

    Columns are found by header name; only `guid` and `cases` are required.
    A row with a blank `cases` cell is not a governor and yields no entry.
    With no `path`, a missing default file yields `{}`.
    """
    if path is None:
        if not CASE_GOVERNMENT_PATH.exists():
            return {}
        source = CASE_GOVERNMENT_PATH
    else:
        source = Path(path)
        if not source.exists():
            raise FileNotFoundError(source)

    with source.open(encoding="utf-8", newline="") as handle:
        rows = [
            row
            for row in csv.reader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
            if any(cell.strip() for cell in row)
        ]
    if not rows:
        return {}

    header = [cell.strip().casefold() for cell in rows[0]]
    for required in ("guid", "cases"):
        if required not in header:
            raise ValueError(f"missing required column: {required}")
    guid_at, cases_at = header.index("guid"), header.index("cases")
    line_at = next(
        (header.index(name) for name in _LINE_CASE_HEADERS if name in header), None
    )

    def cell(row: list[str], index: int | None) -> str:
        return row[index] if index is not None and index < len(row) else ""

    government: dict[str, CaseGovernment] = {}
    for row in rows[1:]:
        guid = cell(row, guid_at).strip()
        cases_cell = cell(row, cases_at).strip()
        if guid in government:
            raise ValueError(f"duplicate guid: {guid!r}")
        if not cases_cell:
            continue
        cases = _parse_cases(cases_cell)
        government[guid] = CaseGovernment(
            cases, _parse_line_cases(cell(row, line_at), cases)
        )
    return government


def case_value(government: Mapping[str, CaseGovernment], guid: str) -> str:
    """The comma-joined cases `guid` governs, `""` for an unlisted guid."""
    entry = government.get(guid)
    return ", ".join(entry.cases) if entry else ""


@lru_cache(maxsize=1)
def default_government() -> dict[str, CaseGovernment]:
    """`load_case_government()`, memoised -- callers must not mutate it."""
    return load_case_government()
