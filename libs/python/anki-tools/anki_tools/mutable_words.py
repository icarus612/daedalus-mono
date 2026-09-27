#!/usr/bin/env python3
"""Build the `anki-mutable-words` `.apkg` package.

Clones the source note type's CSS/shell into four fresh note types (one per
sheet: Nouns, Verbs, Adjectives, Adverbs) inside a scratch collection, builds
the four-deck tree from the parsed `russian-vocabulary` TSVs, and exports the
result as a standalone `.apkg` -- all without ever mutating the real Anki
collection. Doubles as its own CLI entry point
(`anki-build-mutable-words` / `python -m anki_tools.mutable_words`).
"""

import argparse
import os
import shutil
import tempfile
import time

from anki.collection import Collection, DeckIdLimit
from anki.errors import AnkiException, DBError
from anki.import_export_pb2 import ExportAnkiPackageOptions
from anki.models import NotetypeDict
from anki.utils import to_json_bytes

from anki_tools import audio_naming, mutable_words_plan
from anki_tools.audio_naming import get_anki_collection_path
from anki_tools.immutable_words import assert_unmodified

# Source note type's own name has a trailing space typo; look it up by id,
# never by name, exactly like immutable_words.py does.
SOURCE_NOTETYPE_ID = 1698803891108

TEMPLATE_COUNTS_BY_SHEET: dict[str, int] = {
    "Nouns": 2,
    "Verbs": 4,
    "Adjectives": 2,
    "Adverbs": 2,
}

_AUDIO_FIELD_NAMES = ("Audio", "Audio Imperfective", "Audio Perfective")


def build_note_types(
    source_col: Collection, build_col: Collection
) -> dict[str, NotetypeDict]:
    """Clone the source note type's shell into four new note types in
    `build_col`, one per sheet, keyed by sheet name.

    Read-only on `source_col`: calls only `.models.get(...)` and
    `.models.copy(nt, add=False)` on it. Fields and templates are built
    fresh per `mutable_words_plan.FIELD_NAMES`/`build_template` -- never
    copied from the source note type's own fields.
    """
    source_note_type = source_col.models.get(SOURCE_NOTETYPE_ID)
    if source_note_type is None:
        raise ValueError(
            f"No note type with id {SOURCE_NOTETYPE_ID} in source collection"
        )

    note_types: dict[str, NotetypeDict] = {}
    for sheet, name in mutable_words_plan.NOTE_TYPE_NAMES.items():
        cloned = source_col.models.copy(source_note_type, add=False)
        cloned["name"] = name

        fields = []
        for ord_, field_name in enumerate(mutable_words_plan.FIELD_NAMES[sheet]):
            field = build_col.models.new_field(field_name)
            field["id"] = None
            field["ord"] = ord_
            fields.append(field)
        cloned["flds"] = fields

        templates = []
        for card_index in range(TEMPLATE_COUNTS_BY_SHEET[sheet]):
            template = build_col.models.new_template(f"Card {card_index + 1}")
            qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
            template["qfmt"] = qfmt
            template["afmt"] = afmt
            template["ord"] = card_index
            template["id"] = mutable_words_plan.build_template_id(sheet, card_index)
            templates.append(template)
        cloned["tmpls"] = templates

        cloned["id"] = mutable_words_plan.build_note_type_id(sheet)
        cloned["mod"] = int(time.time())

        returned_id = build_col._backend.add_or_update_notetype(
            json=to_json_bytes(cloned), preserve_usn_and_mtime=True, skip_checks=False
        )
        note_types[sheet] = build_col.models.get(returned_id)

    return note_types


def build_deck_tree(
    build_col: Collection,
    rows_by_sheet: dict[str, list],
    note_types: dict[str, NotetypeDict],
) -> dict[str, int]:
    """Create the four subdecks and one note per row across all sheets.

    Every note's GUID is `row.guid`, never Anki's own randomly-minted
    default, so a rebuilt `.apkg` re-imports in place.
    """
    deck_names = mutable_words_plan.all_subdeck_names()
    deck_ids = {name: build_col.decks.id(name, create=True) for name in deck_names}
    counts = {name: 0 for name in deck_names}

    for sheet, rows in rows_by_sheet.items():
        note_type = note_types[sheet]
        field_names = mutable_words_plan.FIELD_NAMES[sheet]
        for row in rows:
            note = build_col.new_note(note_type)
            note.guid = row.guid
            for field_name, value in zip(field_names, row.fields()):
                note[field_name] = value
            build_col.add_note(note, deck_ids[row.deck])
            counts[row.deck] += 1

    return counts


def attach_media(build_col: Collection, audio_dir: str) -> tuple[list[str], list[str]]:
    """Copy every filename referenced by any note's audio field(s) from
    `audio_dir` into `build_col`'s media folder.

    Checks each note's own `keys()` rather than assuming a single audio
    field name, since Verbs notes carry two ("Audio Imperfective"/
    "Audio Perfective") while the other sheets carry one ("Audio"). Never
    raises on a missing source file. Returns `(found, missing)`, both
    sorted, over the union of referenced filenames across every note.
    """
    referenced: set[str] = set()
    for note_id in build_col.find_notes(""):
        note = build_col.get_note(note_id)
        for field_name in _AUDIO_FIELD_NAMES:
            if field_name in note:
                referenced.update(audio_naming.parse_audio_filenames(note[field_name]))

    found: list[str] = []
    missing: list[str] = []
    for name in sorted(referenced):
        source_path = os.path.join(audio_dir, name)
        if not os.path.isfile(source_path):
            missing.append(name)
            continue
        added_name = build_col.media.add_file(source_path)
        if added_name != name:
            raise RuntimeError(
                f"Anki renamed {name!r} to {added_name!r} while adding it to "
                "the collection's media folder"
            )
        found.append(name)

    return sorted(found), sorted(missing)


def export_package(
    build_col: Collection, root_deck_name: str, out_path: str, force: bool = False
) -> None:
    """Export `build_col`'s `root_deck_name` subtree to `out_path` as a
    standalone `.apkg`.

    Raises `FileExistsError` if `out_path` already exists and `force` is
    False. Raises `ValueError` if `root_deck_name` doesn't exist.
    """
    if os.path.exists(out_path) and not force:
        raise FileExistsError(
            f"{out_path!r} already exists; pass --force to overwrite it"
        )

    root_deck_id = build_col.decks.id(root_deck_name, create=False)
    if root_deck_id is None:
        raise ValueError(f"No such deck: {root_deck_name!r}")

    options = ExportAnkiPackageOptions(
        with_scheduling=False,
        with_deck_configs=False,
        with_media=True,
        legacy=False,
    )
    build_col.export_anki_package(
        out_path=out_path, options=options, limit=DeckIdLimit(root_deck_id)
    )


def print_deck_table(counts: dict[str, int], cards_per_note: dict[str, int]) -> None:
    """Print a notes/cards table per deck plus a total row.

    `cards_per_note` supplies the real per-deck template count -- never a
    fixed ratio, since Verbs has 4 cards per note against 2 for the rest.
    """
    rule = "-" * 50
    print(rule)
    print(f"{'Deck':<40} | {'Notes':>5} | {'Cards':>5}")
    print(rule)
    total_notes = 0
    total_cards = 0
    for name in mutable_words_plan.all_subdeck_names():
        notes = counts.get(name, 0)
        cards = notes * cards_per_note.get(name, 0)
        total_notes += notes
        total_cards += cards
        print(f"{name:<40} | {notes:>5} | {cards:>5}")
    print(rule)
    print(f"{'Total':<40} | {total_notes:>5} | {total_cards:>5}")
    print(rule)


def build_parser() -> argparse.ArgumentParser:
    default_source_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "russian-vocabulary"
    )
    parser = argparse.ArgumentParser(
        prog="anki-build-mutable-words",
        description=(
            "Build the anki-mutable-words .apkg package from the "
            "russian-vocabulary TSVs, without touching the live Anki "
            "collection."
        ),
    )
    parser.add_argument(
        "--source-dir",
        dest="source_dir",
        type=str,
        default=default_source_dir,
        help="Directory holding nouns.tsv, verbs.tsv, adjectives.tsv, adverbs.tsv.",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        type=str,
        default=None,
        help="Where to write the .apkg. Required unless --dry-run is given.",
    )
    parser.add_argument(
        "--audio-dir",
        dest="audio_dir",
        type=str,
        default=None,
        help=(
            "Directory of already-generated audio files to attach as real "
            "media before export. Omit to export with AudioRefs "
            "[sound:...] tags marking the names as used but no bytes "
            "attached."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        type=str,
        default=None,
        help="Override the auto-detected collection path.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help=(
            "Parse the source TSVs and print per-deck counts, but write "
            "nothing and never open any Anki collection."
        ),
    )
    parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        default=False,
        help="Allow --out to overwrite an existing file.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    rows_by_sheet = {
        "Nouns": mutable_words_plan.parse_nouns(
            os.path.join(args.source_dir, "nouns.tsv")
        ),
        "Verbs": mutable_words_plan.parse_verbs(
            os.path.join(args.source_dir, "verbs.tsv")
        ),
        "Adjectives": mutable_words_plan.parse_adjectives(
            os.path.join(args.source_dir, "adjectives.tsv")
        ),
        "Adverbs": mutable_words_plan.parse_adverbs(
            os.path.join(args.source_dir, "adverbs.tsv")
        ),
    }

    if args.dry_run:
        counts = {
            mutable_words_plan.subdeck_name(sheet): len(rows)
            for sheet, rows in rows_by_sheet.items()
        }
        cards_per_note = {
            mutable_words_plan.subdeck_name(sheet): TEMPLATE_COUNTS_BY_SHEET[sheet]
            for sheet in rows_by_sheet
        }
        print_deck_table(counts, cards_per_note)
        print("Dry run: nothing written.")
        raise SystemExit(0)

    if not args.out_path:
        parser.error("--out is required unless --dry-run is given")

    if os.path.exists(args.out_path) and not args.force:
        print(f"{args.out_path!r} already exists; pass --force to overwrite it")
        raise SystemExit(1)

    collection_path = args.collection_path or get_anki_collection_path()
    mtime_before = os.path.getmtime(collection_path)

    try:
        source_col = Collection(collection_path)
    except DBError as exc:
        print(f"Could not open the collection: {exc}")
        print("Make sure Anki is not running when you execute this script.")
        raise SystemExit(1)
    except AnkiException as exc:
        print(f"Anki reported an error opening the collection: {exc}")
        raise SystemExit(1)

    tmp_dir = tempfile.mkdtemp(prefix="anki-mutable-words-")
    try:
        build_col = Collection(os.path.join(tmp_dir, "build.anki2"))
        try:
            note_types = build_note_types(source_col, build_col)
        finally:
            source_col.close()
            assert_unmodified(collection_path, mtime_before)

        deck_counts = build_deck_tree(build_col, rows_by_sheet, note_types)
        cards_per_note = {
            mutable_words_plan.subdeck_name(sheet): len(note_types[sheet]["tmpls"])
            for sheet in rows_by_sheet
        }
        print_deck_table(deck_counts, cards_per_note)

        if args.audio_dir:
            found, missing = attach_media(build_col, args.audio_dir)
            print(f"Attached {len(found)} media file(s) from {args.audio_dir!r}.")
            if missing:
                print(f"WARNING: {len(missing)} referenced audio file(s) not found:")
                for name in missing:
                    print(f"  missing: {name}")

        export_package(
            build_col, mutable_words_plan.DECK_ROOT, args.out_path, force=args.force
        )
        build_col.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"Wrote {args.out_path}")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
