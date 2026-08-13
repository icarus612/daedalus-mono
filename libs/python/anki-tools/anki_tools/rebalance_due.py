#!/usr/bin/env python3
"""Rebalance the due dates of review cards in an Anki deck (and its subdecks).

Spreads out clumpy review queues so no single day has too many or too few
cards due, without touching each card's memory state (`ivl`).
"""
import argparse
import os

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    plan_rebalance,
    validate_bounds,
)


def get_anki_collection_path():
    if os.name == "nt":  # Windows
        return os.path.expanduser(
            "~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2"
        )
    elif os.name == "posix":  # macOS/Linux
        return os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    else:
        raise OSError("Unsupported operating system")


def pdash():
    print("-" * 50)


def resolve_deck_ids(col, deck_name):
    deck_id = col.decks.id_for_name(deck_name)
    if deck_id is None:
        raise ValueError(f"No such deck: {deck_name!r}")
    child_ids = col.decks.deck_and_child_ids(deck_id)
    return list(child_ids)


def collect_cards(col, deck_ids, start_day):
    cards = []
    skip_new = 0
    skip_learning = 0
    skip_suspended = 0
    skip_overdue = 0

    for did in deck_ids:
        for cid in col.decks.cids(did, children=False):
            card = col.get_card(cid)

            if card.queue == -1:
                skip_suspended += 1
                continue
            if card.queue == 0 and card.type == 0:
                skip_new += 1
                continue
            if card.queue in (1, 3) or card.type == 1:
                skip_learning += 1
                continue
            if not (card.queue == 2 and card.type == 2):
                # any other non-review state (e.g. buried) counts as skipped
                # learning/other rather than silently vanishing.
                skip_learning += 1
                continue
            if card.odid != 0:
                # Defensive only: a filtered card carries the filtered deck's
                # id in `did`, so enumerating by `did in deck_ids` can never
                # actually return one. Filtered-deck cards are not visible to
                # this enumeration route and are left untouched.
                continue
            if card.due < start_day:
                skip_overdue += 1
                continue

            cards.append(CardDue(card_id=card.id, day=card.due, ivl=card.ivl))

    print(
        f"Skipped {skip_new} new, {skip_learning} learning, "
        f"{skip_suspended} suspended, {skip_overdue} already due or overdue; "
        f"filtered-deck cards are not visible to this route."
    )

    return cards


def render_histogram(before, after, min_per_day, max_per_day):
    rule = "-" * 50
    lines = [rule, "Day offset | Before | After  | Note"]
    all_days = sorted(set(before) | set(after))
    for day in all_days:
        before_count = before.get(day, 0)
        after_count = after.get(day, 0)
        marker = ""
        if min_per_day is not None and after_count < min_per_day:
            marker = "  <- below --min"
        if max_per_day is not None and after_count > max_per_day:
            marker = "  <- above --max"
        lines.append(f"{day:>10} | {before_count:>6} | {after_count:>6}{marker}")
    lines.append(rule)
    return "\n".join(lines)


def apply_moves(col, moves, today):
    by_day = {}
    for card_id, target_day in moves.items():
        by_day.setdefault(target_day, []).append(card_id)

    for target_day, cids in by_day.items():
        col.sched.set_due_date(cids, str(target_day - today))

    return len(by_day)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-rebalance-due",
        description=(
            "Rebalance the due dates of review cards in an Anki deck, "
            "including all of its subdecks, so no day is over- or "
            "under-loaded."
        ),
    )
    parser.add_argument(
        "deck",
        metavar="DECK",
        help=(
            "Full Anki deck name including '::' separators, e.g. "
            "programming::coding. Its subdecks are always included."
        ),
    )
    parser.add_argument(
        "--min",
        dest="min_per_day",
        type=int,
        default=None,
        help="Minimum number of cards due per day.",
    )
    parser.add_argument(
        "--max",
        dest="max_per_day",
        type=int,
        default=None,
        help="Maximum number of cards due per day.",
    )
    parser.add_argument(
        "--max-shift",
        dest="max_shift",
        type=str,
        default="14",
        help=(
            "Furthest a card may move earlier than its own scheduled day, "
            "cumulative from where it started. Accepts an integer or the "
            "literal 'none' to disable the cap. Default: 14."
        ),
    )
    parser.add_argument(
        "--set-earlier",
        dest="set_earlier",
        action="store_true",
        default=False,
        help=(
            "Allow a reverse pass to push excess cards to LATER dates when "
            "--max cannot otherwise be satisfied. This is the only mode in "
            "which a card's due date can move further away."
        ),
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Plan and print the result, but write nothing.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="yes",
        action="store_true",
        default=False,
        help="Skip the interactive confirmation prompt.",
    )
    parser.add_argument(
        "--start-offset",
        dest="start_offset",
        type=int,
        default=1,
        help=(
            "Days after today where the rebalance window begins. Default: "
            "1 (tomorrow) -- cards due today or overdue are never touched."
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
        "--backup-dir",
        dest="backup_dir",
        type=str,
        default=None,
        help="Directory to store the backup in. Default: <collection dir>/backups.",
    )
    parser.add_argument(
        "--no-backup",
        dest="no_backup",
        action="store_true",
        default=False,
        help="Skip taking a backup before writing.",
    )
    return parser


def _parse_max_shift(raw):
    if raw.strip().lower() == "none":
        return None
    return int(raw)


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        validate_bounds(args.min_per_day, args.max_per_day)
    except ValueError as exc:
        parser.error(str(exc))

    try:
        max_shift = _parse_max_shift(args.max_shift)
    except ValueError:
        parser.error(
            f"--max-shift must be an integer or 'none', got {args.max_shift!r}"
        )

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
        try:
            deck_ids = resolve_deck_ids(col, args.deck)
        except ValueError as exc:
            print(str(exc))
            raise SystemExit(1)

        today = col.sched.today
        start_day = today + args.start_offset

        cards = collect_cards(col, deck_ids, start_day)

        try:
            result = plan_rebalance(
                cards,
                start_day,
                args.min_per_day,
                args.max_per_day,
                max_shift=max_shift,
                set_earlier=args.set_earlier,
            )
        except InfeasibleRebalance as exc:
            print("Could not satisfy --max without --set-earlier.")
            print(str(exc))
            print(
                "Try re-running with --set-earlier, or a larger --max-shift "
                "(or --max-shift none)."
            )
            raise SystemExit(1)

        histogram = render_histogram(
            result.before, result.after, args.min_per_day, args.max_per_day
        )
        print(histogram)

        if result.reverse_pass_used:
            print(
                f"Some cards were moved to LATER dates to satisfy --max; "
                f"the horizon was extended to day offset {result.end_day}."
            )

        if result.short_days:
            print(
                "Days still below --min after the shift cap: "
                + ", ".join(str(d) for d in result.short_days)
            )

        move_count = len(result.moves)
        print(f"{move_count} card(s) would move.")

        if args.dry_run:
            print("Dry run: nothing written.")
            raise SystemExit(0)

        if move_count == 0:
            print("Nothing to do.")
            raise SystemExit(0)

        if not args.yes:
            answer = input("Apply these changes? [y/N] ")
            if answer.strip().lower() != "y":
                print("Aborted: nothing written.")
                raise SystemExit(1)

        if not args.no_backup:
            backup_dir = args.backup_dir or os.path.join(
                os.path.dirname(collection_path), "backups"
            )
            os.makedirs(backup_dir, exist_ok=True)
            created = col.create_backup(
                backup_folder=backup_dir, force=True, wait_for_completion=True
            )
            if not created:
                print("Backup skipped: collection unchanged since last backup.")

        moved_days = apply_moves(col, result.moves, today)
        print(f"Applied {move_count} move(s) across {moved_days} day(s).")
        raise SystemExit(0)
    finally:
        col.close()


if __name__ == "__main__":
    main()
