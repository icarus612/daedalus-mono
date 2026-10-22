#!/usr/bin/env python3
"""Report, and optionally make due today, every card still new while a
sibling has been studied. Re-runnable by design -- see
`anki_tools.counterpart_due` for why the condition keeps coming back.
"""

import argparse

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.counterpart_due import (
    count_suspended_skipped,
    find_orphaned_counterparts,
)
from anki_tools.rebalance_due import get_anki_collection_path, resolve_deck_ids


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-counterpart-due",
        description=(
            "Find cards left in the new queue while a sibling of the same "
            "note has already been studied. With --fix, make them due today. "
            "Without a DECK the whole collection is scanned."
        ),
    )
    parser.add_argument(
        "deck",
        metavar="DECK",
        nargs="?",
        default=None,
        help="Limit to this deck and its subdecks.",
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


def scan(col, deck_ids=None):
    """`(card_id, note_id, type, queue)` for the cards in scope.

    Scoped by DECK, the scan still reads every card of any note that has one
    in scope -- a sibling in another deck is what makes a card an orphan, so
    missing it would hide the very thing being looked for.
    """
    if deck_ids is None:
        return col.db.all("select id, nid, type, queue from cards")
    placeholders = ",".join("?" for _ in deck_ids)
    return col.db.all(
        "select id, nid, type, queue from cards where nid in "
        f"(select nid from cards where did in ({placeholders}))",
        *list(deck_ids),
    )


def main():
    args = build_parser().parse_args()
    collection_path = args.collection_path or get_anki_collection_path()
    try:
        col = Collection(collection_path)
    except DBError as exc:
        print(f"Could not open the collection: {exc}")
        print("Make sure Anki is not running when you execute this script.")
        raise SystemExit(1)
    except AnkiException as exc:
        print(f"Anki reported an error opening the collection: {exc}")
        raise SystemExit(1)

    try:
        deck_ids = None
        if args.deck is not None:
            try:
                deck_ids = resolve_deck_ids(col, args.deck)
            except ValueError as exc:
                print(str(exc))
                raise SystemExit(1)

        rows = scan(col, deck_ids)
        orphaned = find_orphaned_counterparts(rows)
        skipped = count_suspended_skipped(rows)
        deck_of = {d.id: d.name for d in col.decks.all_names_and_ids()}
        print(f"{len(orphaned)} card(s) new while a sibling has been studied.")
        if skipped:
            print(f"{skipped} more left alone because they are suspended.")
        for card_id in orphaned:
            card = col.get_card(card_id)
            word = card.note().fields[0]
            print(
                f"  {card_id}  ord{card.ord}  {word[:24]}  {deck_of.get(card.did, '?')}"
            )

        if not orphaned:
            print("Nothing to do.")
            return
        if not args.fix:
            print("\nRe-run with --fix to make them due today.")
            return

        # Plain "0" -- due today, interval left alone. A trailing "!" would
        # overwrite the interval instead, which is not wanted here.
        col.sched.set_due_date(orphaned, "0")
        remaining = find_orphaned_counterparts(scan(col, deck_ids))
        print(f"Made {len(orphaned)} card(s) due today.")
        print(f"Still new with a studied sibling: {len(remaining)}")
    finally:
        col.close()


if __name__ == "__main__":
    main()
