#!/usr/bin/env python3
"""Spread the cards of an ordered GUID list over upcoming days.

New cards given a due day become review cards due that day, so the order of
the list is the order the words are met. Refuses anything that is not a plain
new card, and verifies afterwards that no other card changed.
"""

import argparse
import datetime
import os
import sys
from collections import Counter
from dataclasses import dataclass

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.rebalance_due import get_anki_collection_path, pdash

NEW = 0
REVIEW_QUEUE = 2


class NewDueError(ValueError):
    pass


@dataclass(frozen=True)
class DayGroup:
    day_offset: int
    card_ids: tuple[int, ...]
    note_guids: tuple[str, ...]


def read_guid_list(path):
    guids = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            guid = line.strip()
            if not guid or guid.startswith("#"):
                continue
            guids.append(guid)
    duplicates = sorted(g for g, n in Counter(guids).items() if n > 1)
    if duplicates:
        raise NewDueError(f"Duplicate GUID(s) in {path}: {', '.join(duplicates)}")
    return guids


def collection_today_date(col):
    return datetime.datetime.fromtimestamp(col.sched.day_cutoff - 86400).date()


def offset_for_date(target, today):
    offset = (target - today).days
    if offset < 0:
        raise NewDueError(f"{target} is before today ({today})")
    return offset


def _note_cards(col, guid):
    row = col.db.first("select id from notes where guid = ?", guid)
    if row is None:
        raise NewDueError(f"No note with GUID {guid!r}")
    return col.db.all(
        "select id, type, queue from cards where nid = ? order by ord", row[0]
    )


def plan(col, guids, first_offset, per_day, same_day_siblings=True):
    if per_day <= 0:
        raise NewDueError(f"--per-day must be positive, got {per_day}")
    notes = []
    for guid in guids:
        cards = _note_cards(col, guid)
        if not cards:
            raise NewDueError(f"Note {guid!r} has no cards")
        for card_id, card_type, queue in cards:
            if card_type != NEW or queue != NEW:
                raise NewDueError(
                    f"Card {card_id} of note {guid!r} is not a plain new card "
                    f"(type={card_type}, queue={queue})"
                )
        notes.append((guid, [card_id for card_id, _, _ in cards]))

    slots = []
    if same_day_siblings:
        sizes = {len(card_ids) for _, card_ids in notes}
        if len(sizes) > 1:
            raise NewDueError(
                f"Notes have differing card counts {sorted(sizes)}; "
                "use --no-same-day-siblings"
            )
        size = sizes.pop() if sizes else 1
        if per_day % size:
            raise NewDueError(
                f"--per-day {per_day} is not a multiple of {size} cards per note"
            )
        notes_per_day = per_day // size
        for index, (guid, card_ids) in enumerate(notes):
            day = first_offset + index // notes_per_day
            slots.extend((day, card_id, guid) for card_id in card_ids)
    else:
        flat = [(card_id, guid) for guid, card_ids in notes for card_id in card_ids]
        for index, (card_id, guid) in enumerate(flat):
            slots.append((first_offset + index // per_day, card_id, guid))

    by_day = {}
    for day, card_id, guid in slots:
        cards, found = by_day.setdefault(day, ([], []))
        cards.append(card_id)
        if guid not in found:
            found.append(guid)
    return [
        DayGroup(day, tuple(cards), tuple(found))
        for day, (cards, found) in sorted(by_day.items())
    ]


def _planned_ids(groups):
    return [card_id for group in groups for card_id in group.card_ids]


def _in_clause(values):
    return ",".join("?" for _ in values)


def _target_deck_ids(col, card_ids):
    rows = col.db.all(
        f"select distinct did from cards where id in ({_in_clause(card_ids)})",
        *card_ids,
    )
    return [did for (did,) in rows]


def histogram(col, groups):
    planned = _planned_ids(groups)
    if not planned:
        return {}
    deck_ids = _target_deck_ids(col, planned)
    today = col.sched.today
    counts = {}
    for group in groups:
        others = col.db.scalar(
            f"select count() from cards where queue = {REVIEW_QUEUE} "
            f"and due = ? and did in ({_in_clause(deck_ids)}) "
            f"and id not in ({_in_clause(planned)})",
            today + group.day_offset,
            *deck_ids,
            *planned,
        )
        counts[group.day_offset] = len(group.card_ids) + others
    return counts


def _snapshot(col, deck_ids):
    rows = col.db.all(
        "select id, type, queue, due, ivl from cards "
        f"where did in ({_in_clause(deck_ids)})",
        *deck_ids,
    )
    return {row[0]: tuple(row[1:]) for row in rows}


def apply(col, groups):
    planned = _planned_ids(groups)
    if not planned:
        return
    before = _snapshot(col, _target_deck_ids(col, planned))
    today = col.sched.today
    for group in groups:
        col.sched.set_due_date(list(group.card_ids), str(group.day_offset))
    expected = {
        card_id: today + group.day_offset
        for group in groups
        for card_id in group.card_ids
    }
    after = _snapshot(col, _target_deck_ids(col, planned))
    for card_id, due in expected.items():
        if card_id not in after or after[card_id][2] != due:
            raise NewDueError(f"Card {card_id} did not land on day {due}")
    for card_id, state in before.items():
        if card_id not in expected and after.get(card_id) != state:
            raise NewDueError(f"Unplanned card {card_id} changed: {state}")


def _print_plan(col, groups, today):
    pdash()
    for group in groups:
        day = today + datetime.timedelta(days=group.day_offset)
        print(
            f"+{group.day_offset:<4} {day}  {len(group.card_ids)} card(s), "
            f"{len(group.note_guids)} note(s)"
        )
    pdash()
    print("Cards per day after the change (planned + already due):")
    for offset, count in histogram(col, groups).items():
        print(f"  +{offset:<4} {count}")
    pdash()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-new-due",
        description=(
            "Give new cards a due day, in the order of a GUID list, a fixed "
            "number of cards per day."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    parser.add_argument(
        "--guid-file", required=True, help="One note GUID per line, in order."
    )
    first = parser.add_mutually_exclusive_group(required=True)
    first.add_argument(
        "--first-due", type=datetime.date.fromisoformat, help="First day, YYYY-MM-DD."
    )
    first.add_argument("--start-offset", type=int, help="First day as days from today.")
    parser.add_argument("--per-day", type=int, required=True, help="Cards due per day.")
    parser.add_argument(
        "--no-same-day-siblings",
        action="store_true",
        help="Spread cards individually instead of keeping a note's cards together.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Plan, write nothing.")
    parser.add_argument("--yes", action="store_true", help="Skip the prompt.")
    return parser


def _backup(col, collection_path):
    backup_dir = os.path.join(os.path.dirname(collection_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    created = col.create_backup(
        backup_folder=backup_dir, force=True, wait_for_completion=True
    )
    if not created:
        print("Backup skipped: collection unchanged since last backup.")


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
            today = collection_today_date(col)
            first_offset = (
                args.start_offset
                if args.start_offset is not None
                else offset_for_date(args.first_due, today)
            )
            if first_offset < 0:
                raise NewDueError(f"--start-offset must be >= 0, got {first_offset}")
            groups = plan(
                col,
                read_guid_list(args.guid_file),
                first_offset,
                args.per_day,
                same_day_siblings=not args.no_same_day_siblings,
            )
            _print_plan(col, groups, today)
            if args.dry_run:
                print("Dry run: nothing written.")
                return 0
            if not args.yes and input("Apply these changes? [y/N] ").lower() != "y":
                print("Aborted.")
                return 0
            _backup(col, path)
            apply(col, groups)
        except (NewDueError, OSError) as error:
            print(str(error), file=sys.stderr)
            return 1
        print(f"Scheduled {len(_planned_ids(groups))} card(s).")
        return 0
    finally:
        col.close()


if __name__ == "__main__":
    raise SystemExit(main())
