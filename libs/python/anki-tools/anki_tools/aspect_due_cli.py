#!/usr/bin/env python3
"""Report, and optionally enforce, the verb aspect rule over the Mutable
Verbs note type.

`--rule` has no default on purpose: the two readings of the ask differ in
what they do to 192 all-new notes, so the rule is named explicitly or
nothing runs. See `anki_tools.aspect_due` for what each one means.
"""

import argparse
import sys

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.aspect_due import (
    NEW_TYPE,
    RULES,
    VERB_NOTE_TYPE,
    count_suspended_skipped,
    find_violations,
    group_by_note,
    plan_deferrals,
    plan_new_queue_pushbacks,
)
from anki_tools.rebalance_due import get_anki_collection_path


def positive_days(raw):
    try:
        days = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"--days must be a whole number, got {raw!r}")
    if days < 1:
        raise argparse.ArgumentTypeError(f"--days must be at least 1, got {raw!r}")
    return days


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-aspect-due",
        description=(
            "Keep the two perfective sides of a verb out of the same day's "
            "queue. --rule gate holds a perfective card until an "
            "imperfective side has been studied; --rule space allows both "
            "aspects but defers the second perfective card."
        ),
    )
    parser.add_argument(
        "--rule",
        required=True,
        choices=RULES,
        help="Which reading of the aspect rule to apply. Required.",
    )
    parser.add_argument(
        "--days",
        type=positive_days,
        default=1,
        help="How far to defer a card the rule rejects. Default 1.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply the rule. Omit to only report.",
    )
    parser.add_argument(
        "--include-new",
        dest="include_new",
        action="store_true",
        help=(
            "Also move the new perfective cards the rule rejects to the "
            "back of the new queue. Off by default."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    return parser


def scan(col):
    """`(card_id, note_id, ord, type, queue, due)` for every Mutable Verbs
    card."""
    note_type = col.models.by_name(VERB_NOTE_TYPE)
    if note_type is None:
        raise LookupError(f"no such note type: {VERB_NOTE_TYPE!r}")
    return col.db.all(
        "select c.id, c.nid, c.ord, c.type, c.queue, c.due from cards c "
        "join notes n on n.id = c.nid where n.mid = ?",
        note_type["id"],
    )


def highest_new_position(col):
    return col.db.scalar("select max(due) from cards where type = ?", NEW_TYPE) or 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.collection_path or get_anki_collection_path()
    try:
        col = Collection(path)
    except (AnkiException, DBError) as error:
        print(f"could not open {path}: {error}", file=sys.stderr)
        return 2
    try:
        return _run(col, args)
    finally:
        col.close()


def _run(col, args):
    try:
        rows = scan(col)
    except LookupError as error:
        print(str(error), file=sys.stderr)
        return 2

    today = col.sched.today
    grouped = group_by_note(rows)
    cards_by_id = {card.id: card for cards in grouped.values() for card in cards}
    violations = find_violations(rows, args.rule, today)
    deferrals = plan_deferrals(rows, args.rule, today)
    skipped = count_suspended_skipped(rows, args.rule, today)
    pushbacks = plan_new_queue_pushbacks(rows, args.rule)

    print(f"rule: {args.rule}")
    print(f"{len(grouped)} verb note(s), {len(rows)} card(s).")
    print(f"{len(violations)} perfective card(s) break the rule.")
    for violation in violations:
        card = cards_by_id[violation.card_id]
        print(
            f"  {violation.card_id}  ord{card.ord}  "
            f"{_headwords(col, violation.note_id)}  due {card.due}"
        )
    if skipped:
        print(f"{skipped} more left alone because they are suspended.")
    if pushbacks:
        print(f"{len(pushbacks)} new perfective card(s) also break the rule.")
        if not args.include_new:
            print("  pass --include-new to move them to the back of the new queue.")

    actionable = list(deferrals) + (pushbacks if args.include_new else [])
    if not actionable:
        if not violations and not pushbacks:
            print("Nothing to do.")
        return 0
    if not args.fix:
        print(
            f"\nreport only -- re-run with --fix to act on {len(actionable)} card(s)."
        )
        return 0

    if deferrals:
        # Plain "N" -- due in N days, interval left alone. A trailing "!"
        # would overwrite the interval instead.
        col.sched.set_due_date(deferrals, str(args.days))
        print(f"Deferred {len(deferrals)} card(s) by {args.days} day(s).")
    if args.include_new and pushbacks:
        col.sched.reposition_new_cards(
            pushbacks,
            starting_from=highest_new_position(col) + 1,
            step_size=1,
            randomize=False,
            shift_existing=False,
        )
        print(f"Moved {len(pushbacks)} new card(s) to the back of the new queue.")

    remaining = find_violations(scan(col), args.rule, col.sched.today)
    print(f"still breaking the rule: {len(remaining)}")
    return 1 if remaining else 0


def _headwords(col, note_id):
    fields = col.get_note(note_id).fields
    imperfective = fields[0] if fields else "?"
    perfective = fields[1] if len(fields) > 1 else "?"
    return f"{imperfective} / {perfective}"


if __name__ == "__main__":
    raise SystemExit(main())
