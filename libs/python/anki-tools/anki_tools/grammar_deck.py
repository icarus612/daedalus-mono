#!/usr/bin/env python3
"""Install the Russian grammar-rule deck from `data/russian-grammar/case-endings.tsv`.

Writes straight into the real collection: one note type, one subdeck per source
table, one note per row. Notes are keyed by a deterministic GUID, so a re-run
updates them in place and never touches their scheduling.
"""

import argparse
import csv
import os
import time
from dataclasses import dataclass
from pathlib import Path

from anki.collection import Collection
from anki.errors import AnkiException, DBError
from anki.utils import to_json_bytes

from anki_tools.anki_identity import guid_for_row, notetype_id_for_name
from anki_tools.audio_naming import get_anki_collection_path

DATA_PATH = Path(__file__).parent / "data" / "russian-grammar" / "case-endings.tsv"
DECK_ROOT = "Languages::Russian::2. Grammar"
OPTIONS_SOURCE_DECK = "Languages::Russian"
NOTE_TYPE_NAME = "Russian - Grammar Rules (Ellis Version)"
NOTE_TYPE_ID = notetype_id_for_name(NOTE_TYPE_NAME)
GUID_NAMESPACE = "Grammar"
FIELD_NAMES = ("Type", "Front", "Target", "Example", "Notes")
TABLE_SUBDECKS = {
    "Singular Noun Endings": "a. Singular Noun Endings",
    "Plural Noun Endings": "b. Plural Noun Endings",
    "Adjective Endings": "c. Adjective Endings",
    "Personal Pronouns": "d. Personal Pronouns",
}

QFMT = '<div class="type">{{Type}}</div>\n<div class="front">{{Front}}</div>'
AFMT = (
    "{{FrontSide}}\n<hr id=answer>\n"
    '<div class="target">{{Target}}</div>\n'
    '{{#Example}}<div class="example">{{Example}}</div>{{/Example}}\n'
    '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}'
)
CSS = """.card { font-family: arial; font-size: 22px; text-align: center;
  color: black; background-color: white; }
.type { font-size: 14px; color: #888; }
.front { margin-top: 8px; }
.target { font-size: 34px; font-weight: bold; margin: 12px 0; }
.example { font-size: 22px; color: #1a5fb4; }
.notes { font-size: 16px; color: #666; margin-top: 12px; }
.nightMode .card, .card.nightMode { color: white; background-color: #2f2f31; }
.nightMode .type, .nightMode .notes { color: #aaa; }
.nightMode .example { color: #99c1f1; }
"""


@dataclass(frozen=True)
class GrammarRow:
    table: str
    type: str
    front: str
    target: str
    example: str
    notes: str

    @property
    def guid(self) -> str:
        return guid_for_row(self.front, GUID_NAMESPACE)

    @property
    def deck(self) -> str:
        return f"{DECK_ROOT}::{TABLE_SUBDECKS[self.table]}"

    def fields(self) -> list[str]:
        return [self.type, self.front, self.target, self.example, self.notes]


class SourceError(Exception):
    pass


def parse_rows(path: str | os.PathLike = DATA_PATH) -> list[GrammarRow]:
    """Parse the TSV, rejecting unknown tables, blank targets and duplicate fronts."""
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows = [
            GrammarRow(
                table=r["Table"],
                type=r["Type"],
                front=r["Front"],
                target=r["Target"],
                example=r["Example"],
                notes=r["Notes"],
            )
            for r in reader
        ]
    seen: set[str] = set()
    for row in rows:
        if row.table not in TABLE_SUBDECKS:
            raise SourceError(f"unknown table {row.table!r} for {row.front!r}")
        if not row.front.strip() or not row.target.strip():
            raise SourceError(f"blank front or target: {row!r}")
        if row.front in seen:
            raise SourceError(f"duplicate front: {row.front!r}")
        seen.add(row.front)
    return rows


def ensure_notetype(col: Collection) -> dict:
    """Create the note type under its fixed id, or update its templates in place."""
    existing = col.models.get(NOTE_TYPE_ID)
    if existing is not None:
        existing["tmpls"][0]["qfmt"] = QFMT
        existing["tmpls"][0]["afmt"] = AFMT
        existing["css"] = CSS
        col.models.update_dict(existing)
        return col.models.get(NOTE_TYPE_ID)
    model = col.models.new(NOTE_TYPE_NAME)
    for name in FIELD_NAMES:
        col.models.add_field(model, col.models.new_field(name))
    model["sortf"] = FIELD_NAMES.index("Front")
    template = col.models.new_template("Rule")
    template["qfmt"] = QFMT
    template["afmt"] = AFMT
    col.models.add_template(model, template)
    model["css"] = CSS
    model["id"] = NOTE_TYPE_ID
    model["mod"] = int(time.time())
    model["usn"] = -1
    # add_dict panics on a preset id; this call keeps ours (usn -1 so it syncs).
    col._backend.add_or_update_notetype(
        json=to_json_bytes(model), preserve_usn_and_mtime=True, skip_checks=False
    )
    return col.models.get(NOTE_TYPE_ID)


def ensure_decks(col: Collection) -> dict[str, int]:
    """Create the deck tree, giving new decks the parent Russian deck's options."""
    source = col.decks.by_name(OPTIONS_SOURCE_DECK)
    conf_id = source["conf"] if source is not None else 1
    deck_ids: dict[str, int] = {}
    for name in [DECK_ROOT] + [f"{DECK_ROOT}::{s}" for s in TABLE_SUBDECKS.values()]:
        is_new = col.decks.id_for_name(name) is None
        deck_id = col.decks.id(name, create=True)
        if is_new:
            deck = col.decks.get(deck_id)
            deck["conf"] = conf_id
            col.decks.save(deck)
        deck_ids[name] = deck_id
    return deck_ids


@dataclass(frozen=True)
class ApplyResult:
    added: int
    updated: int
    unchanged: int


def apply_rows(col: Collection, rows: list[GrammarRow]) -> ApplyResult:
    """Add missing notes and refresh changed fields; scheduling is never touched."""
    model = ensure_notetype(col)
    deck_ids = ensure_decks(col)
    added = updated = unchanged = 0
    for row in rows:
        note_id = col.db.scalar("select id from notes where guid = ?", row.guid)
        if note_id is None:
            note = col.new_note(model)
            note.guid = row.guid
            for name, value in zip(FIELD_NAMES, row.fields()):
                note[name] = value
            col.add_note(note, deck_ids[row.deck])
            added += 1
            continue
        note = col.get_note(note_id)
        if [note[name] for name in FIELD_NAMES] == row.fields():
            unchanged += 1
            continue
        for name, value in zip(FIELD_NAMES, row.fields()):
            note[name] = value
        col.update_note(note)
        updated += 1
    return ApplyResult(added, updated, unchanged)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-grammar-deck",
        description="Install or refresh the Russian grammar-rule deck.",
    )
    parser.add_argument("--collection", default=None)
    parser.add_argument("--source", default=str(DATA_PATH))
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = parse_rows(args.source)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.deck] = counts.get(row.deck, 0) + 1
    for deck, n in counts.items():
        print(f"{deck}: {n}")
    if args.dry_run:
        print(f"Dry run: {len(rows)} rows parsed, nothing written.")
        return
    collection_path = args.collection or get_anki_collection_path()
    try:
        col = Collection(collection_path)
    except (DBError, AnkiException) as exc:
        print(f"Could not open the collection (is Anki running?): {exc}")
        raise SystemExit(1)
    try:
        if not args.no_backup:
            backup_dir = os.path.join(os.path.dirname(collection_path), "backups")
            col.create_backup(
                backup_folder=backup_dir, force=True, wait_for_completion=True
            )
        result = apply_rows(col, rows)
        print(
            f"added {result.added}, updated {result.updated}, "
            f"unchanged {result.unchanged}"
        )
    finally:
        col.close()


if __name__ == "__main__":
    main()
