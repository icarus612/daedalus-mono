#!/usr/bin/env python3
"""Find, and optionally fix, cards whose FSRS stability is below AnkiMobile's
minimum -- the state that makes a deck open fine on desktop and fail with
"invalid params" on an iPhone.

Read-only by default: it prints what it found and exits. `--fix` writes,
behind the same backup-before-planning discipline `anki-rebalance-due`
uses. Why the floor exists and why clamping is lossless is documented in
`anki_tools.fsrs_stability`.
"""

import argparse
import datetime
import os

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.fsrs_stability import (
    MIN_STABILITY,
    apply_floor,
    find_low_stability,
)
from anki_tools.rebalance_due import get_anki_collection_path, resolve_deck_ids


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-fsrs-stability-floor",
        description=(
            "Report cards whose FSRS stability is below AnkiMobile's minimum, "
            "and with --fix raise them to it. Without a DECK the whole "
            "collection is scanned."
        ),
    )
    parser.add_argument(
        "deck",
        metavar="DECK",
        nargs="?",
        default=None,
        help="Limit the scan to this deck and its subdecks.",
    )
    parser.add_argument(
        "--min",
        dest="minimum",
        type=float,
        default=MIN_STABILITY,
        help=f"Stability floor to enforce. Default: {MIN_STABILITY}.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Write the floor to every offending card. Omit to only report.",
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    parser.add_argument(
        "--backup-dir",
        dest="backup_dir",
        default=None,
        help="Where --fix writes its backup. Defaults to the profile's backups/.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip the backup --fix otherwise takes first.",
    )
    return parser


def scan(col, deck_ids=None):
    """`(card_id, data)` for every card carrying FSRS memory state."""
    sql = "select id, data from cards where data is not null and data != ''"
    params = []
    if deck_ids is not None:
        placeholders = ",".join("?" for _ in deck_ids)
        sql += f" and did in ({placeholders})"
        params = list(deck_ids)
    return col.db.all(sql, *params)


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
        offenders = find_low_stability(rows, args.minimum)
        deck_of = {d.id: d.name for d in col.decks.all_names_and_ids()}
        print(f"{len(rows)} card(s) carry FSRS memory state.")
        print(
            f"{len(offenders)} below the {args.minimum} floor "
            "(AnkiMobile rejects these)."
        )
        for card_id, stability in offenders:
            did = col.db.scalar("select did from cards where id = ?", card_id)
            print(f"  {card_id}  stability={stability!r}  {deck_of.get(did, '?')}")

        if not offenders:
            print("Nothing to do.")
            return
        if not args.fix:
            print("\nRe-run with --fix to raise them to the floor.")
            return

        if not args.no_backup:
            backup_dir = args.backup_dir or os.path.join(
                os.path.dirname(collection_path), "backups"
            )
            os.makedirs(backup_dir, exist_ok=True)
            col.create_backup(
                backup_folder=backup_dir, force=True, wait_for_completion=True
            )
            print(f"Backup written to {backup_dir}")

        now = int(datetime.datetime.now().timestamp())
        written = 0
        for card_id, _ in offenders:
            data = col.db.scalar("select data from cards where id = ?", card_id)
            floored = apply_floor(data, args.minimum)
            if floored == data:
                continue
            col.db.execute(
                "update cards set data = ?, mod = ?, usn = -1 where id = ?",
                floored,
                now,
                card_id,
            )
            written += 1
        remaining = find_low_stability(scan(col, deck_ids), args.minimum)
        print(f"Raised {written} card(s) to {args.minimum}.")
        print(f"Still below the floor: {len(remaining)}")
    finally:
        col.close()


if __name__ == "__main__":
    main()
