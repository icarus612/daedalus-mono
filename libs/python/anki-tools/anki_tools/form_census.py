"""Pure census of empty inflection fields in the TSV sources and an Anki collection."""

import os
import shutil
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path

from anki_tools import mutable_words_plan as plan

EMPTY_MARKERS: frozenset[str] = frozenset({"", "—", "–", "-", "--"})
SHEETS: tuple[str, ...] = (
    "Nouns",
    "Verbs",
    "Adjectives",
    "Adverbs",
    "Pronouns",
    "Numerals",
)
INFLECTION_FIELDS: dict[str, tuple[str, ...]] = {
    "Nouns": ("Plural", "Genitive Sg", "Genitive Pl"),
    "Verbs": (
        "Perfective",
        "Conjugation",
        "я (1sg)",
        "ты (2sg)",
        "они (3pl)",
        "Past (m / f)",
    ),
    "Adjectives": ("Feminine", "Neuter", "Plural", "Short Form", "Comparative"),
    "Adverbs": ("Comparative",),
    "Pronouns": ("Gender Forms", "Oblique Forms"),
    "Numerals": ("Gender Forms", "Genitive"),
}

NotesByGuid = dict[str, dict[str, str]]

NOT_APPLICABLE = "not-applicable"
MISSING = "missing"

_TSV_FILES = {
    "Nouns": ("nouns.tsv", plan.parse_nouns),
    "Verbs": ("verbs.tsv", plan.parse_verbs),
    "Adjectives": ("adjectives.tsv", plan.parse_adjectives),
    "Adverbs": ("adverbs.tsv", plan.parse_adverbs),
    "Pronouns": ("pronouns.tsv", plan.parse_pronouns),
    "Numerals": ("numerals.tsv", plan.parse_numerals),
}
_NO_PLURAL_MARKERS = ("no plural", "uncountable", "singular-only", "singular only")
_RELATIONAL_ENDINGS = ("ский", "цкий", "ской")


def is_empty(value: str, *, dash_rule: bool = True) -> bool:
    """Whether a stripped value counts as empty (dash markers too when dash_rule)."""
    stripped = value.strip()
    if dash_rule:
        return stripped in EMPTY_MARKERS
    return stripped == ""


def sheet_for_note_type_name(name: str) -> str | None:
    """Map a note type name such as 'Russian - Mutable Nouns (...)' to its sheet."""
    for sheet in SHEETS:
        if f"Mutable {sheet}" in name:
            return sheet
    return None


def tsv_census_notes(data_dir: str | os.PathLike) -> dict[str, NotesByGuid]:
    """Parse the six TSVs in data_dir into {sheet: {guid: {field: value}}}."""
    result: dict[str, NotesByGuid] = {}
    for sheet, (filename, parse) in _TSV_FILES.items():
        names = plan.FIELD_NAMES[sheet]
        rows = parse(str(Path(data_dir) / filename))
        result[sheet] = {row.guid: dict(zip(names, row.fields())) for row in rows}
    return result


def _copy_collection(source: Path, target_dir: Path) -> Path:
    copy = target_dir / source.name
    shutil.copy2(source, copy)
    for suffix in ("-wal", "-shm"):
        sibling = source.with_name(source.name + suffix)
        if sibling.exists():
            shutil.copy2(sibling, target_dir / sibling.name)
    return copy


def collection_census_notes(
    collection_path: str | os.PathLike,
) -> dict[str, NotesByGuid]:
    """Read the mutable note types from a copy of an Anki collection, read-only."""
    source = Path(collection_path)
    if not source.is_file():
        raise FileNotFoundError(str(source))
    result: dict[str, NotesByGuid] = {sheet: {} for sheet in SHEETS}
    with tempfile.TemporaryDirectory() as tmp:
        copy = _copy_collection(source, Path(tmp))
        conn = sqlite3.connect(f"file:{copy}?mode=ro", uri=True)
        try:
            for ntid, name in conn.execute("SELECT id, name FROM notetypes"):
                sheet = sheet_for_note_type_name(name)
                if sheet is None:
                    continue
                field_names = dict(
                    conn.execute(
                        "SELECT ord, name FROM fields WHERE ntid = ?", (ntid,)
                    ).fetchall()
                )
                for guid, flds in conn.execute(
                    "SELECT guid, flds FROM notes WHERE mid = ?", (ntid,)
                ):
                    values = flds.split("\x1f")
                    result[sheet][guid] = {
                        field_names[ord_]: value
                        for ord_, value in enumerate(values)
                        if ord_ in field_names
                    }
        finally:
            conn.close()
    return result


def note_counts(notes: dict[str, NotesByGuid]) -> dict[str, int]:
    """Number of notes per sheet."""
    return {sheet: len(by_guid) for sheet, by_guid in notes.items()}


def empty_counts(
    notes: dict[str, NotesByGuid],
    *,
    dash_rule: bool = True,
    guids: dict[str, set[str]] | None = None,
) -> dict[str, dict[str, int]]:
    """Per sheet and inflection field, how many notes hold an empty value."""
    counts: dict[str, dict[str, int]] = {}
    for sheet, fields in INFLECTION_FIELDS.items():
        by_guid = notes.get(sheet, {})
        allowed = None if guids is None else guids.get(sheet, set())
        counts[sheet] = {
            field: sum(
                1
                for guid, values in by_guid.items()
                if (allowed is None or guid in allowed)
                and is_empty(values.get(field, ""), dash_rule=dash_rule)
            )
            for field in fields
        }
    return counts


@dataclass(frozen=True)
class Reconciliation:
    """Empty-field counts of the TSV against the collection."""

    tsv_counts: dict[str, dict[str, int]]
    collection_counts: dict[str, dict[str, int]]
    orphans: dict[str, tuple[str, ...]]
    unbuilt: dict[str, tuple[str, ...]]
    mismatches: dict[tuple[str, str], tuple[int, int]]

    @property
    def reconciles(self) -> bool:
        return not self.mismatches


def reconcile(
    tsv_notes: dict[str, NotesByGuid],
    collection_notes: dict[str, NotesByGuid],
    *,
    dash_rule: bool = True,
) -> Reconciliation:
    """Compare empty counts over the GUIDs present on both sides."""
    tsv_counts = empty_counts(tsv_notes, dash_rule=dash_rule)
    shared: dict[str, set[str]] = {}
    orphans: dict[str, tuple[str, ...]] = {}
    unbuilt: dict[str, tuple[str, ...]] = {}
    for sheet in INFLECTION_FIELDS:
        tsv_guids = set(tsv_notes.get(sheet, {}))
        collection_guids = set(collection_notes.get(sheet, {}))
        shared[sheet] = tsv_guids & collection_guids
        orphans[sheet] = tuple(sorted(collection_guids - tsv_guids))
        unbuilt[sheet] = tuple(sorted(tsv_guids - collection_guids))
    tsv_shared = empty_counts(tsv_notes, dash_rule=dash_rule, guids=shared)
    collection_counts = empty_counts(
        collection_notes, dash_rule=dash_rule, guids=shared
    )
    mismatches = {
        (sheet, field): (tsv_shared[sheet][field], collection_counts[sheet][field])
        for sheet, fields in INFLECTION_FIELDS.items()
        for field in fields
        if tsv_shared[sheet][field] != collection_counts[sheet][field]
    }
    return Reconciliation(
        tsv_counts=tsv_counts,
        collection_counts=collection_counts,
        orphans=orphans,
        unbuilt=unbuilt,
        mismatches=mismatches,
    )


@dataclass(frozen=True)
class EmptyCell:
    """One empty inflection cell and its classification."""

    sheet: str
    guid: str
    headword: str
    field: str
    marker: str
    status: str
    reason: str


def _structural_reason(sheet: str, field: str, fields: dict[str, str]) -> str | None:
    if sheet == "Nouns":
        info = fields.get("Additional Info", "").lower()
        if "indeclinable" in info:
            return "indeclinable noun"
        if field in ("Plural", "Genitive Pl") and any(
            marker in info for marker in _NO_PLURAL_MARKERS
        ):
            return "noun has no plural (singular-only or uncountable)"
        if field == "Genitive Sg" and fields.get("Gender", "").strip() == "pl-only":
            return "plural-only noun has no singular"
    if sheet == "Adjectives" and field in ("Short Form", "Comparative"):
        base = fields.get("Russian (m)", "").strip().replace("́", "")
        if base.endswith(_RELATIONAL_ENDINGS):
            return "relational adjective has no short form or comparative"
    return None


def classify_cells(sheet: str, guid: str, fields: dict[str, str]) -> list[EmptyCell]:
    """Classify each empty inflection field of one note."""
    headword = fields.get(plan.FIELD_NAMES[sheet][0], "")
    cells: list[EmptyCell] = []
    for field in INFLECTION_FIELDS[sheet]:
        marker = fields.get(field, "").strip()
        if marker not in EMPTY_MARKERS:
            continue
        if marker != "":
            status = NOT_APPLICABLE
            reason = f"the source marks this form as absent with '{marker}'"
        else:
            structural = _structural_reason(sheet, field, fields)
            if structural is not None:
                status = NOT_APPLICABLE
                reason = structural
            else:
                status = MISSING
                reason = "the reference must supply the value or show it does not exist"
        cells.append(EmptyCell(sheet, guid, headword, field, marker, status, reason))
    return cells


def census_cells(notes: dict[str, NotesByGuid]) -> list[EmptyCell]:
    """Classified empty cells over all sheets in SHEETS order."""
    return [
        cell
        for sheet in SHEETS
        for guid, fields in notes.get(sheet, {}).items()
        for cell in classify_cells(sheet, guid, fields)
    ]
