#!/usr/bin/env python3
"""Report where a collection's word notes differ from the source documents.

Read-only: the collection file is copied to a temp dir and the copy is read.
"""

import argparse
import os
import shutil
import sys
import tempfile

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools import immutable_words, source_drift
from anki_tools.audio_naming import get_anki_collection_path

assert source_drift.IMMUTABLE_NOTE_TYPE_NAME == immutable_words.NEW_NOTE_TYPE_NAME

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV_HEADER = "guid\tnote type\theadword\tfield\tcollection value\tsource value"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-source-drift",
        description=(
            "Report fields whose stored value differs from the value built "
            "from the source word list and vocabulary TSVs, plus orphan and "
            "missing notes. Read-only."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    parser.add_argument(
        "--word-list",
        dest="word_list",
        default=os.path.join(PACKAGE_DIR, "tests", "data", "source-word-list.md"),
        help="Immutable-words source document.",
    )
    parser.add_argument(
        "--source-dir",
        dest="source_dir",
        default=os.path.join(PACKAGE_DIR, "anki_tools", "data", "russian-vocabulary"),
        help="Directory holding the mutable-words TSVs.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "tsv"),
        default="text",
        help="Output format. Default: text.",
    )
    return parser


def copy_collection(path, directory):
    target = os.path.join(directory, "collection.anki2")
    shutil.copyfile(path, target)
    wal = path + "-wal"
    if os.path.exists(wal):
        shutil.copyfile(wal, target + "-wal")
    return target


def read_managed_notes(col):
    managed = source_drift.managed_note_types()
    notes = []
    for entry in col.models.all_names_and_ids():
        if entry.name not in managed:
            continue
        names = [f["name"] for f in col.models.get(entry.id)["flds"]]
        for guid, flds in col.db.all(
            "select guid, flds from notes where mid = ?", entry.id
        ):
            notes.append(
                source_drift.CollectionNote(
                    guid=guid,
                    note_type=entry.name,
                    fields=dict(zip(names, flds.split("\x1f"))),
                )
            )
    return notes


def load_collection_notes(path):
    with tempfile.TemporaryDirectory() as directory:
        col = Collection(copy_collection(path, directory))
        try:
            return read_managed_notes(col)
        finally:
            col.close()


def _flat(value):
    return " ".join(value.split("\t")).replace("\n", " ").replace("\r", " ")


def render_tsv(report):
    lines = [TSV_HEADER]
    for row in report.drift:
        lines.append(
            "\t".join(
                _flat(value)
                for value in (
                    row.guid,
                    row.note_type,
                    row.headword,
                    row.field,
                    row.collection_value,
                    row.source_value,
                )
            )
        )
    return "\n".join(lines)


def render_text(report, path):
    drifted = len({row.guid for row in report.drift})
    lines = [
        f"collection: {path}",
        f"drift: {len(report.drift)} field(s) on {drifted} note(s)",
        f"orphans: {len(report.orphans)}",
        f"missing: {len(report.missing)}",
    ]
    for row in report.drift:
        lines.append(
            f"  {row.guid} | {row.note_type} | {row.headword} | {row.field} | "
            f"collection: {_flat(row.collection_value)!r} | "
            f"source: {_flat(row.source_value)!r}"
        )
    lines.extend(["", f"== orphans ({len(report.orphans)}) =="])
    for note in report.orphans:
        first = next(iter(note.fields.values()), "")
        lines.append(f"  {note.guid} | {note.note_type} | {_flat(first)}")
    lines.extend(["", f"== missing ({len(report.missing)}) =="])
    for note in report.missing:
        lines.append(f"  {note.guid} | {note.note_type} | {note.headword}")
    return "\n".join(lines)


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.collection_path or get_anki_collection_path()

    with open(args.word_list, encoding="utf-8") as handle:
        expected = source_drift.expected_notes(handle.read(), args.source_dir)

    try:
        mtime_before = os.path.getmtime(path)
        actual = load_collection_notes(path)
    except (OSError, DBError, AnkiException) as error:
        print(f"could not open {path}: {error}", file=sys.stderr)
        return 2
    immutable_words.assert_unmodified(path, mtime_before)

    report = source_drift.compare(expected, actual)
    print(render_tsv(report) if args.format == "tsv" else render_text(report, path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
