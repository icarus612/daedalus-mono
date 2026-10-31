#!/usr/bin/env python3
"""Report, and optionally make due today, every phrase-sourced word whose
cards are all still new.

Re-runnable by design -- see `anki_tools.phrase_due` for why the condition
keeps coming back and why its predicate is the complement of
`counterpart_due`'s rather than a copy of it.

Reports unless `--fix` is given. Suspended cards are never touched and the
number skipped for that reason is printed.
"""

import argparse
import sys

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.phrase_due import (
    build_taught_index,
    count_suspended_skipped,
    find_all_new_cards,
    resolve_phrase_note_ids,
)
from anki_tools.rebalance_due import get_anki_collection_path, resolve_deck_ids

PHRASE_DECK = "Languages::Russian::5. Russian Phrases"

TAUGHT_TYPE_PREFIXES = ("Russian - Mutable", "Russian - Immutable")
VERB_TYPE_SUFFIX = "Verbs (Ellis Version)"

# Plain "0" -- due today, interval left alone. A trailing "!" would
# overwrite the interval instead: a prior run used that form and rewrote 138
# intervals, sending `в / во` from 1 day to 690.
DUE_TODAY = "0"


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-phrase-due",
        description=(
            "Find words taught in the phrase deck that still have every card "
            "in the new queue, and with --fix make those cards due today. "
            "Suspended cards are never selected."
        ),
    )
    parser.add_argument(
        "--deck",
        default=PHRASE_DECK,
        help=f"The phrase deck to source words from. Default: {PHRASE_DECK}",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Set every card found due today. Omit to only report.",
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    return parser


def taught_notes(col):
    """`(note_id, headwords)` for every note of the taught Russian decks.

    A verb contributes both aspects, since a phrase may use either one.
    """
    type_names = {
        model.id: model.name
        for model in col.models.all_names_and_ids()
        if model.name.startswith(TAUGHT_TYPE_PREFIXES)
    }
    if not type_names:
        return []
    placeholders = ",".join("?" for _ in type_names)
    rows = col.db.all(
        f"select id, mid, flds from notes where mid in ({placeholders})",
        *type_names,
    )
    notes = []
    for note_id, mid, flds in rows:
        fields = flds.split("\x1f")
        headwords = [fields[0]]
        if type_names[mid].endswith(VERB_TYPE_SUFFIX) and len(fields) > 1:
            headwords.append(fields[1])
        notes.append((note_id, headwords))
    return notes


def phrase_texts(col, deck_ids):
    """The headword field of every note with a card in the phrase deck."""
    placeholders = ",".join("?" for _ in deck_ids)
    rows = col.db.all(
        "select distinct n.flds from notes n join cards c on c.nid = n.id "
        f"where c.did in ({placeholders})",
        *deck_ids,
    )
    return [flds.split("\x1f")[0] for (flds,) in rows]


def scan(col, note_ids):
    """`(card_id, note_id, type, queue)` for every card of these notes.

    Every card is read, not just the ones in a particular deck: the
    predicate is a property of the whole note, so a sibling left out would
    make an already-started word look untouched.
    """
    note_ids = list(note_ids)
    if not note_ids:
        return []
    placeholders = ",".join("?" for _ in note_ids)
    return col.db.all(
        f"select id, nid, type, queue from cards where nid in ({placeholders})",
        *note_ids,
    )


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.collection_path or get_anki_collection_path()
    try:
        col = Collection(path)
    except (AnkiException, DBError) as error:
        print(f"could not open {path}: {error}", file=sys.stderr)
        return 2

    try:
        try:
            deck_ids = resolve_deck_ids(col, args.deck)
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 1

        notes = taught_notes(col)
        word_of = {note_id: headwords[0] for note_id, headwords in notes}
        phrase_note_ids = resolve_phrase_note_ids(
            phrase_texts(col, deck_ids), build_taught_index(notes)
        )
        rows = scan(col, phrase_note_ids)
        due = find_all_new_cards(rows, phrase_note_ids)
        skipped = count_suspended_skipped(rows, phrase_note_ids)

        note_of = {card_id: note_id for card_id, note_id, _, _ in rows}
        per_word = {}
        for card_id in due:
            per_word.setdefault(note_of[card_id], []).append(card_id)

        print(
            f"{len(per_word)} phrase-sourced word(s) with every card new, "
            f"{len(due)} card(s) to make due."
        )
        for note_id in sorted(per_word, key=lambda n: word_of.get(n, "")):
            print(f"  {word_of.get(note_id, '?')}  {len(per_word[note_id])} card(s)")
        if skipped:
            print(f"{skipped} more card(s) left alone because they are suspended.")

        if not due:
            print("Nothing to do.")
            return 0
        if not args.fix:
            print("\nRe-run with --fix to make them due today.")
            return 0

        col.sched.set_due_date(due, DUE_TODAY)
        remaining = find_all_new_cards(scan(col, phrase_note_ids), phrase_note_ids)
        print(f"Made {len(due)} card(s) due today.")
        print(f"Still all-new afterwards: {len(remaining)}")
        return 0
    finally:
        col.close()


if __name__ == "__main__":
    raise SystemExit(main())
