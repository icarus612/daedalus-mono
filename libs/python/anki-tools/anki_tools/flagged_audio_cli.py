#!/usr/bin/env python3
"""Regenerate the audio for every flagged card's word.

Reports by default. `--fix` hands the words to `word_audio --replace`, which
archives each old file before writing the new one, so a regeneration is
reversible from the archive directory.

The collection is opened READ-ONLY and the flags are left alone: clearing
them is the user's signal that a word now sounds right, not this tool's to
spend.
"""

import argparse
import subprocess
import sys

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.audio_naming import get_anki_collection_path
from anki_tools.flagged_audio import (
    FLAG_NAMES,
    MODE_DOUBLE,
    MODE_SINGLE,
    count_by_flag,
    words_to_regenerate,
)

HEADWORD_FIELDS = ("Russian", "Imperfective", "Perfective")

SLOTS = {MODE_SINGLE: ("f1", "m2"), MODE_DOUBLE: ("f1", "f2", "m1", "m2")}


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-flagged-audio",
        description=(
            "Find every flagged card and regenerate the audio for its word. "
            "Reports unless --fix is given."
        ),
    )
    parser.add_argument(
        "--flag",
        dest="flags",
        action="append",
        type=int,
        choices=sorted(FLAG_NAMES),
        default=None,
        help="Only this flag colour. Repeatable. Default: every colour.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Regenerate the audio. Omit to only report.",
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    return parser


def scan(col):
    """`(flags, notetype_name, headwords)` per flagged card.

    Headword fields are read by NAME rather than by index: the two families
    disagree on field order, and a verb keeps its aspects in two fields.
    """
    rows = []
    for card_id in col.db.list("select id from cards where (flags & 7) != 0"):
        card = col.get_card(card_id)
        note = card.note()
        names = [field["name"] for field in note.note_type()["flds"]]
        headwords = [
            note.fields[names.index(name)] for name in HEADWORD_FIELDS if name in names
        ]
        rows.append((card.flags, note.note_type()["name"], headwords))
    return rows


def regenerate(mode, words):
    command = [
        sys.executable,
        "-m",
        "anki_tools.word_audio",
        "--mode",
        mode,
        "--replace",
        "--yes",
        "--",
        *words,
    ]
    print(f"\n$ {' '.join(command[3:])}")
    return subprocess.run(command, check=False).returncode


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.collection_path or get_anki_collection_path()

    try:
        col = Collection(path)
    except (AnkiException, DBError) as error:
        print(f"could not open {path}: {error}", file=sys.stderr)
        return 2
    try:
        rows = scan(col)
    finally:
        col.close()

    counts = count_by_flag(rows)
    if not counts:
        print("no flagged cards")
        return 0

    print("flagged cards by colour:")
    for flag, count in counts.items():
        print(f"  {FLAG_NAMES[flag]:10} {count}")

    picked = words_to_regenerate(rows, flags_wanted=args.flags)
    if not picked:
        print("no words matched the requested flags")
        return 0

    total_files = sum(len(words) * len(SLOTS[mode]) for mode, words in picked.items())
    print(f"\n{sum(len(w) for w in picked.values())} word(s), {total_files} file(s):")
    for mode, words in picked.items():
        print(f"  {mode} ({'/'.join(SLOTS[mode])}): {', '.join(words)}")

    if not args.fix:
        print("\nreport only -- pass --fix to regenerate")
        return 0

    failed = [mode for mode, words in picked.items() if regenerate(mode, words)]
    if failed:
        print(f"\nregeneration failed for: {', '.join(failed)}", file=sys.stderr)
        return 1
    print(
        "\nflags left as they were -- clear them yourself once the audio sounds right"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
