#!/usr/bin/env python3
"""Rebalance the due dates of review cards in an Anki deck (and its subdecks).

Spreads out clumpy review queues so no single day has too many or too few
cards due, without touching each card's memory state (`ivl`).

Phase 6 adds a feasibility precheck run before any backup is taken, moves
the backup ahead of planning on every surface (including `--dry-run`), and
adds `--range` (an explicit day-offset window) and `--sliding`/
`--strict-sliding` (a per-day target line instead of a flat band).
"""
import argparse
import os

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    check_feasibility,
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
    resolved_names = [col.decks.name(did) for did in child_ids]
    print(f"Resolved deck(s): {', '.join(resolved_names)}")
    return list(child_ids)


def parse_range(raw: str) -> tuple[int, int]:
    """Parse a `--range` argument: `LO-HI` or a bare `N` meaning `N-N`.

    Both `LO` and `HI` are day offsets from today. Raises `ValueError` with
    a message naming the specific problem (malformed, `LO < 1`, `HI < LO`)
    -- callers turn that into `parser.error(...)`. Shared by `due_stats.py`
    so `--range` is parsed identically on both surfaces.
    """
    text = raw.strip()
    if "-" in text:
        lo_str, hi_str = text.split("-", 1)
    else:
        lo_str = hi_str = text
    try:
        lo = int(lo_str)
        hi = int(hi_str)
    except ValueError:
        raise ValueError(
            f"--range must be LO-HI or a bare N (e.g. 8-30 or 12), got {raw!r}"
        )
    if lo < 1:
        raise ValueError(f"--range LO must be >= 1 (today or the past), got {lo}")
    if hi < lo:
        raise ValueError(f"--range HI must be >= LO, got HI={hi} < LO={lo}")
    return lo, hi


def collect_cards(col, deck_ids, start_day, end_day=None):
    cards = []
    skip_new = 0
    skip_learning = 0
    skip_suspended = 0
    skip_buried = 0
    skip_overdue = 0
    skip_outside_range = 0

    for did in deck_ids:
        for cid in col.decks.cids(did, children=False):
            card = col.get_card(cid)

            if card.queue == -1:
                skip_suspended += 1
                continue
            if card.queue in (-2, -3):
                skip_buried += 1
                continue
            if card.queue == 0 and card.type == 0:
                skip_new += 1
                continue
            if card.queue in (1, 3) or card.type == 1:
                skip_learning += 1
                continue
            if not (card.queue == 2 and card.type == 2):
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
            if end_day is not None and card.due > end_day:
                skip_outside_range += 1
                continue

            cards.append(CardDue(card_id=card.id, day=card.due, ivl=card.ivl))

    skip_msg = (
        f"Skipped {skip_new} new, {skip_learning} learning, "
        f"{skip_suspended} suspended, {skip_buried} buried, "
        f"{skip_overdue} already due or overdue"
    )
    if end_day is not None:
        skip_msg += f", {skip_outside_range} outside --range"
    skip_msg += "; filtered-deck cards are not visible to this route."
    print(skip_msg)

    return cards


def render_histogram(before, after, max_per_day, today, short_days, sliding=False):
    """Render the day-by-day plan.

    `short_days` means different things per mode: in flat mode it is days
    below --min, in sliding mode days below the ramp TARGET (due_plan's
    _short_days is handed `target` there, not the min floor). Labelling both
    "below --min" was wrong and alarming — a day holding 10 cards with
    --min 8 is not below the minimum, it just missed the ramp.
    """
    rule = "-" * 50
    lines = [rule, "Day offset | Before | After  | Note"]
    all_days = sorted(set(before) | set(after))
    short_days_set = set(short_days)
    short_label = "  <- under ramp target" if sliding else "  <- below --min"
    for day in all_days:
        before_count = before.get(day, 0)
        after_count = after.get(day, 0)
        offset = day - today
        marker = ""
        if day in short_days_set:
            marker = short_label
        if max_per_day is not None and after_count > max_per_day:
            marker = "  <- above --max"
        lines.append(f"{offset:>10} | {before_count:>6} | {after_count:>6}{marker}")
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
        "--sliding",
        dest="sliding",
        action="store_true",
        default=False,
        help=(
            "Replace the flat --min/--max band with a per-day target that "
            "slides from --max at the start of the window down to --min at "
            "the horizon, instead of a constant cap. Requires both --min "
            "and --max. --max-shift may prevent the shape from being "
            "fully reached; see anki-due-stats for the profile."
        ),
    )
    parser.add_argument(
        "--strict-sliding",
        dest="strict_sliding",
        action="store_true",
        default=False,
        help=(
            "With --sliding, fail instead of best-effort when the sliding "
            "target cannot be fully reached under --max-shift. Has no "
            "effect without --sliding."
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
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument(
        "--start-offset",
        dest="start_offset",
        type=int,
        default=1,
        help=(
            "Days after today where the rebalance window begins. Default: "
            "1 (tomorrow) -- cards due today or overdue are never touched. "
            "Mutually exclusive with --range."
        ),
    )
    window_group.add_argument(
        "--range",
        dest="range_raw",
        type=str,
        default=None,
        help=(
            "Day-offset window LO-HI (e.g. 8-30), or a bare N meaning "
            "N-N. Cards outside the window are left untouched. Mutually "
            "exclusive with --start-offset."
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
        help="Skip taking a backup before planning.",
    )
    return parser


def _parse_max_shift(raw):
    if raw.strip().lower() == "none":
        return None
    return int(raw)


def _print_infeasibility(report, today):
    print(
        f"Infeasible: {report.total} card(s) over a {report.horizon_days}-day "
        f"window, average {report.avg_per_day:.2f}/day."
    )
    for violation in report.violations:
        print(f"  - {violation}")
    if report.binding_prefix is not None:
        day, due_by_then, capacity_by_then = report.binding_prefix
        print(
            f"Binding: by day offset {day - today}, {due_by_then} card(s) "
            f"due against {capacity_by_then} slot(s)."
        )
    if report.suggested_min is not None:
        if report.suggested_min == 0:
            print(
                "The deck is too sparse for any positive --min over this "
                "window; omit --min entirely, or narrow the window with "
                "--range to a denser slice."
            )
        else:
            print(f"Suggested --min: {report.suggested_min}")
    if report.suggested_max is not None:
        print(f"Suggested --max: {report.suggested_max}")


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

    if args.sliding and (args.min_per_day is None or args.max_per_day is None):
        parser.error("--sliding requires both --min and --max")

    range_bounds = None
    if args.range_raw is not None:
        try:
            range_bounds = parse_range(args.range_raw)
        except ValueError as exc:
            parser.error(str(exc))

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
        if range_bounds is not None:
            lo, hi = range_bounds
            start_day = today + lo
            end_day = today + hi
        else:
            start_day = today + args.start_offset
            end_day = None

        cards = collect_cards(col, deck_ids, start_day, end_day)

        report = check_feasibility(
            cards,
            start_day,
            end_day,
            args.min_per_day,
            args.max_per_day,
            max_shift,
            sliding=args.sliding,
            set_earlier=args.set_earlier,
        )
        if not report.feasible:
            _print_infeasibility(report, today)
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

        pre_reverse_end_day = max((card.day for card in cards), default=start_day - 1)

        try:
            result = plan_rebalance(
                cards,
                start_day,
                args.min_per_day,
                args.max_per_day,
                max_shift=max_shift,
                set_earlier=args.set_earlier,
                sliding=args.sliding,
                strict_sliding=args.strict_sliding,
                end_day=end_day,
            )
        except InfeasibleRebalance as exc:
            print(f"Could not satisfy the constraints ({exc.reason}).")
            print(str(exc))
            if exc.reason in ("sink overflow", "shift cap"):
                print(
                    "Try re-running with --set-earlier, or a larger "
                    "--max-shift (or --max-shift none)."
                )
            else:
                print(
                    "This came from --strict-sliding refusing an "
                    "over-target day; drop --strict-sliding for "
                    "best-effort shaping instead."
                )
            raise SystemExit(1)

        histogram = render_histogram(
            result.before,
            result.after,
            args.max_per_day,
            today,
            result.short_days,
            sliding=args.sliding,
        )
        print(histogram)

        # In --range mode `result.end_day` is pinned to the declared range
        # ceiling regardless of whether anything actually moved there (the
        # window cannot grow past --range's HI at all -- Packet D's
        # containment ceiling forces InfeasibleRebalance instead), so the
        # "extended" comparison only means anything when the horizon is
        # actually free to grow, i.e. no explicit --range was given.
        if end_day is None and result.end_day > pre_reverse_end_day:
            print(
                f"Some cards were moved to LATER dates to satisfy --max; "
                f"the horizon was extended to day offset "
                f"{result.end_day - today}."
            )

        if result.short_days:
            label = (
                "Days under the sliding ramp target"
                if args.sliding
                else "Days still below --min after the shift cap"
            )
            print(label + ": " + ", ".join(str(d - today) for d in result.short_days))

        if result.over_target_days:
            print(
                "Days still above the sliding target after shaping: "
                + ", ".join(str(d - today) for d in result.over_target_days)
            )
            if report.min_feasible_max_shift is not None:
                print(
                    f"A --max-shift of at least {report.min_feasible_max_shift} "
                    "would reach the full sliding shape."
                )

        # The ramp is a SOFT target: --min/--max are the hard bounds and are
        # always honoured exactly, but the shape is best-effort by design
        # (DP-F). Say so out loud when it was not fully met, so an imperfect
        # ramp reads as "as close as the cap allows" rather than a failure.
        # This lands directly above the existing y/N confirm, so it needs no
        # new prompt and leaves --yes/--dry-run flows untouched.
        if args.sliding and (result.short_days or result.over_target_days):
            print()
            print(
                f"NOTE: the sliding ramp was not met exactly — "
                f"{len(result.over_target_days)} day(s) above target, "
                f"{len(result.short_days)} day(s) under it."
            )
            print(
                "      Your --min/--max bounds ARE enforced exactly; only the "
                "ramp shape is approximate."
            )
            if report.min_feasible_max_shift is not None:
                print(
                    f"      --max-shift {report.min_feasible_max_shift} or more "
                    "would reach the full shape."
                )
            print()

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

        moved_days = apply_moves(col, result.moves, today)
        print(f"Applied {move_count} move(s) across {moved_days} day(s).")
        raise SystemExit(0)
    finally:
        col.close()


if __name__ == "__main__":
    main()
