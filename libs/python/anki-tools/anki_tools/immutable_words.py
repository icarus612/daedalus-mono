#!/usr/bin/env python3
"""Build the `anki-immutable-words` `.apkg` package.

Clones the source "Russian - Immutable Words" note type into a scratch
collection (stripping the `Part of Speech` field from its templates and
rewriting audio playback), builds the four-deck tree from the parsed source
word-list document, and exports the result as a standalone `.apkg` -- all
without ever mutating the real Anki collection. Doubles as its own CLI
entry point (`anki-build-immutable-words` / `python -m anki_tools.immutable_words`).
"""

import argparse
import os
import shutil
import tempfile

from anki.collection import Collection, DeckIdLimit
from anki.errors import AnkiException, DBError
from anki.import_export_pb2 import ExportAnkiPackageOptions
from anki.models import NotetypeDict

from anki_tools import audio_naming
from anki_tools.audio_naming import get_anki_collection_path
from anki_tools.immutable_words_plan import (
    DECK_ROOT,
    FIELD_NAMES,
    SourceDocumentError,
    WordRow,
    all_subdeck_names,
    counts_by_deck,
    parse_word_list,
    rewrite_audio_playback,
    strip_part_of_speech,
)

# Source note type's own name has a trailing space typo; look it up by id,
# never by name, to sidestep that entirely.
SOURCE_NOTETYPE_ID = 1698803891108
# exact, no trailing space
NEW_NOTE_TYPE_NAME = "Russian - Immutable Words (Ellis Version)"


def clone_note_type(
    source_col: Collection, build_col: Collection, new_name: str
) -> NotetypeDict:
    """Clone the source note type into `build_col` under `new_name`.

    Read-only on `source_col`: calls only `.models.get(...)` and
    `.models.copy(nt, add=False)` on it, nothing else, ever. Applies
    `strip_part_of_speech` then `rewrite_audio_playback` (in that order) to
    every template's `qfmt` and `afmt` -- 4 sides total across the note
    type's 2 templates. Appends a 7th field, `AudioRefs`, invented here (not
    copied from the source) via `build_col.models.new_field`, so the
    registered note type has 7 fields total, matching
    `immutable_words_plan.FIELD_NAMES`. No template side ever references
    `{{AudioRefs}}` -- see `FIELD_NAMES`'s comment for why. Registers the
    transformed dict into `build_col` and returns the registered version
    (looked up fresh, since the dict passed to `add_dict` still has `id == 0`
    after it returns).
    """
    source_note_type = source_col.models.get(SOURCE_NOTETYPE_ID)
    if source_note_type is None:
        raise ValueError(
            f"No note type with id {SOURCE_NOTETYPE_ID} in source collection"
        )

    cloned = source_col.models.copy(source_note_type, add=False)
    cloned["name"] = new_name

    for template in cloned["tmpls"]:
        template["qfmt"] = rewrite_audio_playback(
            strip_part_of_speech(template["qfmt"])
        )
        template["afmt"] = rewrite_audio_playback(
            strip_part_of_speech(template["afmt"])
        )

    audio_refs_field = build_col.models.new_field("AudioRefs")
    audio_refs_field["ord"] = len(cloned["flds"])
    cloned["flds"].append(audio_refs_field)

    build_col.models.add_dict(cloned)
    return build_col.models.by_name(new_name)


def assert_unmodified(collection_path: str, mtime_before: float) -> None:
    """Raise AssertionError if `collection_path`'s mtime has changed.

    Caller is responsible for capturing `mtime_before` via
    `os.path.getmtime` before ever opening the collection.
    """
    mtime_after = os.path.getmtime(collection_path)
    if mtime_after != mtime_before:
        raise AssertionError(
            f"Collection at {collection_path!r} was modified "
            f"(mtime {mtime_before} -> {mtime_after})"
        )


def build_deck_tree(
    build_col: Collection, rows: list[WordRow], note_type: NotetypeDict
) -> dict[str, int]:
    """Create the four subdecks and one note per row.

    Returns per-deck note counts keyed by full deck path, in
    `all_subdeck_names()` order, with all four keys always present (0 if a
    deck got no rows). Never sets the Audio field to anything other than
    what `row.fields()` already provides.
    """
    deck_names = all_subdeck_names()
    deck_ids = {name: build_col.decks.id(name, create=True) for name in deck_names}
    counts = {name: 0 for name in deck_names}

    for row in rows:
        note = build_col.new_note(note_type)
        for field_name, value in zip(FIELD_NAMES, row.fields()):
            note[field_name] = value
        build_col.add_note(note, deck_ids[row.deck])
        counts[row.deck] += 1

    return counts


def attach_media(build_col: Collection, audio_dir: str) -> tuple[list[str], list[str]]:
    """Copy every filename referenced by any note's `Audio` field from
    `audio_dir` into `build_col`'s own media folder, so `export_package`
    (called after this, with `with_media=True`) actually bundles real bytes
    instead of shipping references to files that were never present in the
    scratch collection's media directory.

    Does NOT touch `AudioRefs` -- that field's `[sound:...]` tags already
    mark these filenames as used for Anki's media-usage scan; this function
    only supplies the bytes those tags (and the plain `Audio` names) point
    at. Never raises on a missing source file -- deck-before-audio: a note
    whose recordings do not exist yet must still export and import cleanly
    -- so the caller decides what to do with `missing`.

    Returns `(found, missing)`, both sorted lists of bare filenames, over
    the UNION of every referenced filename across every note in `build_col`
    (not per-note), so a file shared by two notes (e.g. the `да`/`да` case)
    is only copied once.
    """
    referenced: set[str] = set()
    for note_id in build_col.find_notes(""):
        note = build_col.get_note(note_id)
        referenced.update(audio_naming.parse_audio_filenames(note["Audio"]))

    found: list[str] = []
    missing: list[str] = []
    for name in referenced:
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
    """Export `build_col`'s root deck tree to `out_path` as a `.apkg`.

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


def print_deck_table(counts: dict[str, int]) -> None:
    rule = "-" * 50
    print(rule)
    print(f"{'Deck':<40} | {'Notes':>5} | {'Cards':>5}")
    print(rule)
    total_notes = 0
    total_cards = 0
    for name in all_subdeck_names():
        notes = counts.get(name, 0)
        cards = notes * 2
        total_notes += notes
        total_cards += cards
        print(f"{name:<40} | {notes:>5} | {cards:>5}")
    print(rule)
    print(f"{'Total':<40} | {total_notes:>5} | {total_cards:>5}")
    print(rule)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-build-immutable-words",
        description=(
            "Build the anki-immutable-words .apkg package from the source "
            "word-list document, without touching the live Anki collection."
        ),
    )
    parser.add_argument(
        "--source",
        dest="source_path",
        type=str,
        required=True,
        help=(
            "Path to the source word-list markdown document. Required -- "
            "the source document's permanent repo location isn't settled "
            "by this lane (a later, unrelated step relocates it), so this "
            "flag intentionally has no baked-in default."
        ),
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        type=str,
        default=None,
        help="Where to write the .apkg. Required unless --dry-run is given.",
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
            "Parse the source and print per-deck counts, but write nothing "
            "and never open any Anki collection."
        ),
    )
    parser.add_argument(
        "--force",
        dest="force",
        action="store_true",
        default=False,
        help="Allow --out to overwrite an existing file.",
    )
    parser.add_argument(
        "--audio-dir",
        dest="audio_dir",
        type=str,
        default=None,
        help=(
            "Directory of already-generated <word>_<slot>.mp3 files (see "
            "anki_tools.elevenlabs_tts, DEFAULT_OUTPUT_DIR) to attach as real "
            "media before export. Omit to export with AudioRefs [sound:...] "
            "tags marking the names as used but no bytes attached -- an "
            "explicit opt-in, matching this package's existing "
            "--all-voices-style convention of never defaulting to a real path "
            "on the user's machine."
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        with open(args.source_path, encoding="utf-8") as f:
            source_text = f.read()
    except OSError as exc:
        print(f"Could not read source document at {args.source_path!r}: {exc}")
        raise SystemExit(1)

    try:
        rows = parse_word_list(source_text)
    except SourceDocumentError as exc:
        print(f"Could not parse source document: {exc}")
        raise SystemExit(1)

    counts = counts_by_deck(rows)

    if args.dry_run:
        print_deck_table(counts)
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

    tmp_dir = tempfile.mkdtemp(prefix="anki-immutable-words-")
    try:
        build_col = Collection(os.path.join(tmp_dir, "build.anki2"))
        try:
            note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
        finally:
            source_col.close()
            assert_unmodified(collection_path, mtime_before)

        deck_counts = build_deck_tree(build_col, rows, note_type)
        print_deck_table(deck_counts)

        if args.audio_dir:
            found, missing = attach_media(build_col, args.audio_dir)
            print(f"Attached {len(found)} media file(s) from {args.audio_dir!r}.")
            if missing:
                print(f"WARNING: {len(missing)} referenced audio file(s) not found:")
                for name in missing:
                    print(f"  missing: {name}")

        export_package(build_col, DECK_ROOT, args.out_path, force=args.force)
        build_col.close()
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"Wrote {args.out_path}")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
