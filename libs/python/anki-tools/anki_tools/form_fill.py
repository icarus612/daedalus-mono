"""Pure form generator and reviewable fill artifact for empty inflection cells."""

import csv
import json
import re
import unicodedata
import urllib.parse
from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from anki_tools import mutable_words_plan as plan
from anki_tools.form_census import (
    EMPTY_MARKERS,
    MISSING,
    SHEETS,
    EmptyCell,
    NotesByGuid,
    census_cells,
    is_empty,
    sheet_for_note_type_name,
)

Entries = dict[str, list[dict]]
OpenRussianIndex = dict[str, dict[str, list[dict[str, str]]]]

GENERATED_FIELDS: dict[str, tuple[str, ...]] = {
    "Nouns": ("Plural", "Genitive Sg", "Genitive Pl"),
    "Verbs": ("Conjugation", "я (1sg)", "ты (2sg)", "они (3pl)", "Past (m / f)"),
    "Adjectives": ("Short Form", "Comparative"),
    "Adverbs": ("Comparative",),
}
STATUS_FILLED = "missing-filled"
STATUS_NOT_APPLICABLE = "not-applicable"
STATUS_UNRESOLVED = "unresolved"
EXCLUDED_BY_PLAN: frozenset[tuple[str, str]] = frozenset(
    {
        ("Numerals", "Gender Forms"),
        ("Numerals", "Genitive"),
        ("Pronouns", "Oblique Forms"),
        ("Adverbs", "Formation"),
    }
)
COLUMNS = (
    "note type",
    "headword",
    "guid",
    "field",
    "generated value",
    "reference (source + entry URL)",
    "status",
)

_ACUTE = "́"
_VOWELS = frozenset("аеёиоуыэюяАЕЁИОУЫЭЮЯ")
_POS = {"Nouns": "noun", "Verbs": "verb", "Adjectives": "adj", "Adverbs": "adv"}
_IGNORED_TAGS = frozenset({"dated", "obsolete", "archaic", "colloquial"})
_DROPPED_FORM_TAGS = frozenset(
    {"table-tags", "inflection-template", "class", "romanization"}
)
_KAIKKI_POS = frozenset({"noun", "verb", "adj", "adv"})
_OPENRUSSIAN_FILES = {
    "nouns": "nouns.csv",
    "verbs": "verbs.csv",
    "adjectives": "adjectives.csv",
}
_OPENRUSSIAN_SHEETS = {"Nouns": "nouns", "Verbs": "verbs", "Adjectives": "adjectives"}
_OPENRUSSIAN_COLUMNS = {
    ("Nouns", "Plural"): "pl_nom",
    ("Nouns", "Genitive Sg"): "sg_gen",
    ("Nouns", "Genitive Pl"): "pl_gen",
    ("Adjectives", "Comparative"): "comparative",
    ("Verbs", "я (1sg)"): "presfut_sg1",
    ("Verbs", "ты (2sg)"): "presfut_sg2",
    ("Verbs", "они (3pl)"): "presfut_pl3",
}
_SHORT_FORM_COLUMNS = ("short_m", "short_f", "short_n", "short_pl")
_FIRST_SG = frozenset({"first-person", "singular"})
_SECOND_SG = frozenset({"second-person", "singular"})
_THIRD_PL = frozenset({"third-person", "plural"})


class OverlapError(ValueError):
    """A fill row targets a cell that is excluded."""


class NonEmptyTargetError(ValueError):
    """A fill row targets a cell that already holds text."""


@dataclass(frozen=True)
class FillRow:
    """One reviewable row of the fill artifact."""

    note_type: str
    headword: str
    guid: str
    field: str
    value: str
    reference: str
    status: str


@dataclass(frozen=True)
class OracleResult:
    """Agreement of generated values with the house values of one field."""

    exact: int
    spelling_only: int
    differs: int
    no_output: int
    no_entry: int
    disagreements: tuple[tuple[str, str, str, str], ...]


def normalize_lemma(text: str) -> str:
    """Lookup key: parenthesised part, stress marks and case removed."""
    without_parens = re.sub(r"\([^)]*\)", "", text)
    return (
        unicodedata.normalize("NFC", without_parens.replace(_ACUTE, "")).lower().strip()
    )


def lemma_for(sheet: str, fields: dict[str, str]) -> str:
    """Normalized lemma of a note, empty when its source field is empty."""
    if sheet == "Nouns":
        return normalize_lemma(fields.get("Russian", ""))
    if sheet == "Adjectives":
        return normalize_lemma(fields.get("Russian (m)", ""))
    if sheet == "Adverbs":
        return normalize_lemma(fields.get("Adverb", ""))
    if sheet == "Verbs":
        imperfective = fields.get("Imperfective", "")
        if is_empty(imperfective):
            return normalize_lemma(fields.get("Perfective", ""))
        return normalize_lemma(imperfective)
    return ""


def _house_token(token: str) -> str:
    token = token.replace("ё" + _ACUTE, "ё").replace("Ё" + _ACUTE, "Ё")
    if sum(1 for char in token if char in _VOWELS) == 1:
        token = token.replace(_ACUTE, "")
    return token


def house_stress(form: str) -> str:
    """House stress format: no mark on ё or on single-vowel words."""
    text = unicodedata.normalize("NFC", form)
    return re.sub(r"\S+", lambda match: _house_token(match.group()), text)


def strip_optional_prefix(form: str) -> str:
    """Remove a leading optional '(по)' prefix."""
    return re.sub(r"^\(по\)", "", form)


def wiktionary_url(lemma: str) -> str:
    """English Wiktionary entry URL of a lemma, Russian section."""
    return f"https://en.wiktionary.org/wiki/{urllib.parse.quote(lemma)}#Russian"


def strip_footnote_marks(form: str) -> str:
    """Remove Wiktionary footnote marks ('*' and '^') from a form."""
    return form.replace("*", "").replace("^", "")


def _clean(form: str) -> str | None:
    cleaned = house_stress(strip_optional_prefix(strip_footnote_marks(form)))
    if cleaned == "" or cleaned == "-" or re.search(r"\s", cleaned):
        return None
    return cleaned


def _sheet_forms(
    sheet: str, lemma: str, entries: Entries
) -> list[tuple[str, frozenset[str]]]:
    pos = _POS[sheet]
    return [
        (form, frozenset(tags))
        for entry in entries.get(lemma, [])
        if entry.get("pos") == pos
        for form, tags in entry.get("forms", [])
        if not _IGNORED_TAGS & set(tags)
    ]


def _first(
    forms: Sequence[tuple[str, frozenset[str]]], required: Collection[str]
) -> str | None:
    needed = set(required)
    for form, tags in forms:
        if needed <= tags:
            return _clean(form)
    return None


def _first_person_form(
    forms: Sequence[tuple[str, frozenset[str]]], person: Collection[str]
) -> str | None:
    present = _first(forms, {"present", *person})
    if present is not None:
        return present
    return _first(forms, {"future", *person})


def _short_form(forms: Sequence[tuple[str, frozenset[str]]]) -> str | None:
    def pick(gender: str) -> str | None:
        return _first(forms, {"short-form", gender})

    plural = None
    for form, tags in forms:
        if {"short-form", "plural"} <= tags and not tags & {
            "masculine",
            "feminine",
            "neuter",
        }:
            plural = _clean(form)
            break
    masculine, feminine = pick("masculine"), pick("feminine")
    if masculine is None or feminine is None:
        return None
    parts = [masculine, feminine, pick("neuter"), plural]
    return ", ".join(part for part in parts if part is not None)


def _past(forms: Sequence[tuple[str, frozenset[str]]]) -> str | None:
    masculine = _first(forms, {"past", "singular", "masculine"})
    feminine = _first(forms, {"past", "singular", "feminine"})
    if masculine is None or feminine is None:
        return None
    return f"{masculine} / {feminine}"


def _conjugation_class(second_sg: str | None, third_pl: str | None) -> str | None:
    if second_sg is None or third_pl is None:
        return None

    def base(form: str) -> str:
        text = form.replace(_ACUTE, "").lower()
        return text[:-2] if text.endswith(("ся", "сь")) else text

    second, third = base(second_sg), base(third_pl)
    if second.endswith(("ешь", "ёшь")) and third.endswith(("ут", "ют")):
        return "1st (-ешь)"
    if second.endswith("ишь") and third.endswith(("ат", "ят")):
        return "2nd (-ишь)"
    return None


def generate_value(
    sheet: str, field: str, fields: dict[str, str], entries: Entries
) -> str | None:
    """Value for one cell from the extract entries, None when not producible."""
    if field not in GENERATED_FIELDS.get(sheet, ()):
        return None
    forms = _sheet_forms(sheet, lemma_for(sheet, fields), entries)
    if sheet == "Nouns":
        required = {
            "Plural": {"nominative", "plural"},
            "Genitive Sg": {"genitive", "singular"},
            "Genitive Pl": {"genitive", "plural"},
        }[field]
        return _first(forms, required)
    if sheet == "Adverbs":
        return _first(forms, {"comparative"})
    if sheet == "Adjectives":
        if field == "Comparative":
            return _first(forms, {"comparative"})
        return _short_form(forms)
    if field == "я (1sg)":
        return _first_person_form(forms, _FIRST_SG)
    if field == "ты (2sg)":
        return _first_person_form(forms, _SECOND_SG)
    if field == "они (3pl)":
        return _first_person_form(forms, _THIRD_PL)
    if field == "Past (m / f)":
        return _past(forms)
    return _conjugation_class(
        _first_person_form(forms, _SECOND_SG), _first_person_form(forms, _THIRD_PL)
    )


def load_openrussian(directory: str | Path) -> OpenRussianIndex:
    """Index the OpenRussian nouns, verbs and adjectives CSVs by normalized bare."""
    index: OpenRussianIndex = {}
    for kind, filename in _OPENRUSSIAN_FILES.items():
        by_bare: dict[str, list[dict[str, str]]] = {}
        with open(Path(directory) / filename, encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                key = normalize_lemma(row.get("bare") or "")
                if key:
                    by_bare.setdefault(key, []).append(row)
        index[kind] = by_bare
    return index


def _or_house(value: str) -> str:
    return house_stress(value.replace("'", _ACUTE))


def _or_column(rows: Iterable[dict[str, str]], column: str) -> str | None:
    for row in rows:
        value = (row.get(column) or "").strip()
        if value:
            return _or_house(value)
    return None


def openrussian_value(
    sheet: str, field: str, fields: dict[str, str], index: OpenRussianIndex
) -> str | None:
    """Value for one cell from the OpenRussian index, None when absent."""
    kind = _OPENRUSSIAN_SHEETS.get(sheet)
    if kind is None or field not in GENERATED_FIELDS.get(sheet, ()):
        return None
    rows = index.get(kind, {}).get(lemma_for(sheet, fields), [])
    if sheet == "Adjectives" and field == "Short Form":
        for row in rows:
            parts = [
                _or_house(row[column].strip())
                for column in _SHORT_FORM_COLUMNS
                if (row.get(column) or "").strip()
            ]
            if parts:
                return ", ".join(parts)
        return None
    if field == "Past (m / f)":
        for row in rows:
            masculine = (row.get("past_m") or "").strip()
            feminine = (row.get("past_f") or "").strip()
            if masculine and feminine:
                return f"{_or_house(masculine)} / {_or_house(feminine)}"
        return None
    if field == "Conjugation":
        return _conjugation_class(
            _or_column(rows, "presfut_sg2"), _or_column(rows, "presfut_pl3")
        )
    return _or_column(rows, _OPENRUSSIAN_COLUMNS[(sheet, field)])


def _fold(text: str) -> str:
    return unicodedata.normalize("NFC", text).replace(_ACUTE, "").lower()


def cross_check(generated: str, other: str | None) -> str:
    """Compare a generated value with the OpenRussian one."""
    if other is None:
        return "no-entry"
    if unicodedata.normalize("NFC", generated) == unicodedata.normalize("NFC", other):
        return "agree"
    if _fold(generated) == _fold(other):
        return "spelling-only"
    return "differs"


def parse_routing_exclusions(path: str | Path) -> frozenset[tuple[str, str, str]]:
    """(sheet, headword, destination field) triples routed by a routing TSV."""
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    if not lines:
        return frozenset()
    header = [column.strip().lower() for column in lines[0].split("\t")]

    def column(prefix: str) -> int:
        return next(i for i, name in enumerate(header) if name.startswith(prefix))

    note_type_at = column("note type")
    headword_at = column("headword")
    destination_at = column("destination field")
    triples: set[tuple[str, str, str]] = set()
    for line in lines[1:]:
        cells = line.split("\t")
        if max(note_type_at, headword_at, destination_at) >= len(cells):
            continue
        destination = cells[destination_at].strip()
        if destination == "" or destination.lower() == "delete":
            continue
        note_type = cells[note_type_at].strip()
        sheet = (
            note_type if note_type in SHEETS else sheet_for_note_type_name(note_type)
        )
        if sheet is None:
            continue
        triples.add((sheet, cells[headword_at].strip(), destination))
    return frozenset(triples)


def plan_exclusions(
    routing_path: str | Path | None,
) -> tuple[frozenset[tuple[str, ...]], str]:
    """Plan exclusions (plus routing triples when the file exists) and their source."""
    if routing_path is not None and Path(routing_path).is_file():
        excluded: frozenset[tuple[str, ...]] = (
            EXCLUDED_BY_PLAN | parse_routing_exclusions(routing_path)
        )
        return excluded, f"plan list + {Path(routing_path).name}"
    return (
        frozenset(EXCLUDED_BY_PLAN),
        "plan list (case-text-routing.tsv not yet committed)",
    )


def is_excluded(
    sheet: str, headword: str, field: str, excluded: Collection[tuple[str, ...]]
) -> bool:
    """Whether a cell is excluded by sheet and field or by headword."""
    return (sheet, field) in excluded or (sheet, headword, field) in excluded


def candidate_cells(
    tsv_notes: dict[str, NotesByGuid],
    collection_notes: dict[str, NotesByGuid],
    excluded: Collection[tuple[str, ...]],
) -> list[EmptyCell]:
    """Missing, empty-in-both, non-excluded cells in census order."""
    return [
        cell
        for cell in census_cells(tsv_notes)
        if cell.status == MISSING
        and cell.marker == ""
        and not is_excluded(cell.sheet, cell.headword, cell.field, excluded)
        and collection_notes.get(cell.sheet, {})
        .get(cell.guid, {})
        .get(cell.field, "")
        .strip()
        == ""
    ]


def build_rows(
    tsv_notes: dict[str, NotesByGuid],
    collection_notes: dict[str, NotesByGuid],
    entries: Entries,
    excluded: Collection[tuple[str, ...]],
    openrussian: OpenRussianIndex | None = None,
) -> list[FillRow]:
    """Fill rows for every candidate cell, validated before return."""
    rows: list[FillRow] = []
    for cell in candidate_cells(tsv_notes, collection_notes, excluded):
        fields = tsv_notes[cell.sheet][cell.guid]
        value = generate_value(cell.sheet, cell.field, fields, entries)
        if value is None:
            rows.append(
                FillRow(
                    cell.sheet,
                    cell.headword,
                    cell.guid,
                    cell.field,
                    "",
                    "",
                    STATUS_UNRESOLVED,
                )
            )
            continue
        reference = "kaikki.org Wiktionary extract " + wiktionary_url(
            lemma_for(cell.sheet, fields)
        )
        if openrussian is not None:
            other = openrussian_value(cell.sheet, cell.field, fields, openrussian)
            outcome = cross_check(value, other)
            reference += f"; OpenRussian: {outcome}"
            if outcome == "differs":
                reference += f" ({other})"
        rows.append(
            FillRow(
                cell.sheet,
                cell.headword,
                cell.guid,
                cell.field,
                value,
                reference,
                STATUS_FILLED,
            )
        )
    assert_no_overlap(rows, excluded)
    assert_targets_empty(rows, tsv_notes, collection_notes)
    return rows


def assert_no_overlap(
    rows: Iterable[FillRow], excluded: Collection[tuple[str, ...]]
) -> None:
    """Raise OverlapError on the first row whose cell is excluded."""
    for row in rows:
        if is_excluded(row.note_type, row.headword, row.field, excluded):
            raise OverlapError(
                f"excluded cell: {row.note_type} / {row.headword} / {row.field}"
            )


def assert_targets_empty(
    rows: Iterable[FillRow],
    tsv_notes: dict[str, NotesByGuid],
    collection_notes: dict[str, NotesByGuid],
) -> None:
    """Raise NonEmptyTargetError on the first row whose cell holds any text."""
    for row in rows:
        for source in (tsv_notes, collection_notes):
            current = source.get(row.note_type, {}).get(row.guid, {}).get(row.field, "")
            if current.strip():
                raise NonEmptyTargetError(
                    f"non-empty target: {row.note_type} / {row.headword} / {row.field}"
                )


def check_oracle(
    tsv_notes: dict[str, NotesByGuid], entries: Entries
) -> dict[tuple[str, str], OracleResult]:
    """Compare generated values with the non-empty house values."""
    results: dict[tuple[str, str], OracleResult] = {}
    for sheet, field_names in GENERATED_FIELDS.items():
        headword_field = plan.FIELD_NAMES[sheet][0]
        for field in field_names:
            exact = spelling_only = differs = no_output = no_entry = 0
            disagreements: list[tuple[str, str, str, str]] = []
            for fields in tsv_notes.get(sheet, {}).values():
                house = fields.get(field, "").strip()
                if house in EMPTY_MARKERS:
                    continue
                if not _sheet_forms_exist(sheet, lemma_for(sheet, fields), entries):
                    no_entry += 1
                    continue
                generated = generate_value(sheet, field, fields, entries)
                if generated is None:
                    no_output += 1
                elif unicodedata.normalize("NFC", house) == generated:
                    exact += 1
                elif _fold(house) == _fold(generated):
                    spelling_only += 1
                else:
                    differs += 1
                    disagreements.append(
                        (fields.get(headword_field, ""), field, house, generated)
                    )
            results[(sheet, field)] = OracleResult(
                exact,
                spelling_only,
                differs,
                no_output,
                no_entry,
                tuple(disagreements),
            )
    return results


def _sheet_forms_exist(sheet: str, lemma: str, entries: Entries) -> bool:
    pos = _POS[sheet]
    return any(entry.get("pos") == pos for entry in entries.get(lemma, []))


def render_artifact(rows: Iterable[FillRow], header_lines: Iterable[str]) -> str:
    """Tab-separated artifact text with a commented header block."""
    lines = [f"# {line}" if line else "#" for line in header_lines]
    lines.append("\t".join(COLUMNS))
    for row in rows:
        cells = (
            row.note_type,
            row.headword,
            row.guid,
            row.field,
            row.value,
            row.reference,
            row.status,
        )
        if any("\t" in cell or "\n" in cell for cell in cells):
            raise ValueError(f"tab or newline in row: {row.guid} / {row.field}")
        lines.append("\t".join(cells))
    return "\n".join(lines) + "\n"


def parse_artifact(text: str) -> list[FillRow]:
    """Inverse of render_artifact."""
    rows: list[FillRow] = []
    header_seen = False
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        cells = line.split("\t")
        if not header_seen:
            if tuple(cells) != COLUMNS:
                raise ValueError(f"unexpected header: {line!r}")
            header_seen = True
            continue
        if len(cells) != len(COLUMNS):
            raise ValueError(
                f"expected {len(COLUMNS)} columns, got {len(cells)}: {line!r}"
            )
        rows.append(FillRow(*cells))
    if not header_seen:
        raise ValueError("missing column header")
    return rows


def extract_entries(jsonl_path: str | Path, lemmas: Collection[str]) -> Entries:
    """Stream a kaikki jsonl, keeping entries for the given normalized lemmas."""
    entries: Entries = {}
    with open(jsonl_path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            lemma = normalize_lemma(record.get("word", ""))
            if lemma not in lemmas or record.get("pos") not in _KAIKKI_POS:
                continue
            forms = [
                [item["form"], item.get("tags", [])]
                for item in record.get("forms", [])
                if not _DROPPED_FORM_TAGS & set(item.get("tags", []))
            ]
            entries.setdefault(lemma, []).append({"pos": record["pos"], "forms": forms})
    return entries
