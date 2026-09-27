"""Read the "Russian Vocabulary" workbook and emit per-sheet TSV files.

The only module in this package allowed to import `openpyxl`. Reads the
`Nouns`, `Verbs`, `Adjectives` and `Adverbs` sheets (never `Key`), validates
each sheet's header row against `EXPECTED_HEADERS`, and normalizes cell
values into plain strings suitable for a tab-delimited export.
"""

import argparse
import os
import unicodedata
from pathlib import Path

import openpyxl

SHEETS: tuple[str, ...] = ("Nouns", "Verbs", "Adjectives", "Adverbs")

EXPECTED_HEADERS: dict[str, tuple[str, ...]] = {
    "Nouns": (
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
    ),
    "Verbs": (
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
    ),
    "Adjectives": (
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
    ),
    "Adverbs": (
        "#",
        "Adverb",
        "English",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Status",
    ),
}


class WorkbookError(Exception):
    """Raised when the workbook's structure or contents are invalid."""


def _normalize_cell(value: object) -> str:
    """Normalize one raw cell value into its exported string form.

    Dash-only strings are passed through unchanged after stripping and NFC
    normalization -- they must never collapse to `""`.
    """
    if value is None:
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return str(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value.strip())
    return str(value)


def read_sheet(workbook_path: str, sheet: str) -> list[dict[str, str]]:
    """Read `sheet` from `workbook_path` into normalized row dicts.

    Validates the header row against `EXPECTED_HEADERS[sheet]`, drops
    all-empty rows, and rejects any cell containing a tab, `\\r` or `\\n`
    after normalization.
    """
    expected = EXPECTED_HEADERS[sheet]

    workbook = openpyxl.load_workbook(workbook_path, read_only=True, data_only=True)
    try:
        worksheet = workbook[sheet]
        rows_iter = worksheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            header_row = ()

        found = tuple(_normalize_cell(value) for value in header_row)
        if found != expected:
            raise WorkbookError(
                f"Sheet {sheet!r} has an unexpected header row.\n"
                f"Expected: {expected}\n"
                f"Found:    {found}"
            )

        results: list[dict[str, str]] = []
        data_row_number = 0
        for raw_row in rows_iter:
            data_row_number += 1
            padded = list(raw_row) + [None] * (len(expected) - len(raw_row))
            normalized = [_normalize_cell(value) for value in padded[: len(expected)]]

            if all(cell == "" for cell in normalized):
                continue

            for column_name, cell in zip(expected, normalized):
                if "\t" in cell or "\r" in cell or "\n" in cell:
                    raise WorkbookError(
                        f"Sheet {sheet!r}, data row {data_row_number}, "
                        f"column {column_name!r} contains a tab or "
                        "newline character"
                    )

            results.append(dict(zip(expected, normalized)))

        return results
    finally:
        workbook.close()


def write_tsv(
    rows: list[dict[str, str]], headers: tuple[str, ...], out_path: str
) -> None:
    """Write `rows` to `out_path` as a tab-delimited file with `headers` first."""
    with open(out_path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\t".join(headers) + "\n")
        for row in rows:
            handle.write("\t".join(row[column] for column in headers) + "\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-vocabulary-source",
        description=(
            "Read the Russian Vocabulary workbook's Nouns/Verbs/Adjectives/"
            "Adverbs sheets and emit one TSV file per sheet."
        ),
    )
    parser.add_argument(
        "--workbook",
        dest="workbook_path",
        type=str,
        default=os.path.expanduser("~/Downloads/russian_vocabulary.xlsx"),
        help="Path to the source .xlsx workbook.",
    )
    parser.add_argument(
        "--out-dir",
        dest="out_dir",
        type=str,
        default=str(Path(__file__).parent / "data" / "russian-vocabulary"),
        help="Directory to write the per-sheet .tsv files into.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Print per-sheet row counts and write nothing.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        sheet_rows = {sheet: read_sheet(args.workbook_path, sheet) for sheet in SHEETS}
    except WorkbookError as exc:
        print(str(exc))
        raise SystemExit(1)

    if args.dry_run:
        for sheet in SHEETS:
            print(f"{sheet}: {len(sheet_rows[sheet])} rows")
        raise SystemExit(0)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for sheet in SHEETS:
        out_path = out_dir / f"{sheet.lower()}.tsv"
        write_tsv(sheet_rows[sheet], EXPECTED_HEADERS[sheet], str(out_path))

    raise SystemExit(0)


if __name__ == "__main__":
    main()
