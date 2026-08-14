#!/usr/bin/env python3
"""Read-only feasibility/shape report for an Anki deck's due-date window.

The sibling report command to `anki-rebalance-due` (DP-A): same deck
argument, `--start-offset`/`--range`/`--collection`/`--min`/`--max`/
`--sliding` semantics, but it never plans, never writes, never backs up.
Every number printed here comes from `anki_tools.due_plan`'s pure
functions -- this file never recomputes totals, the target line, or the
range slice itself.
"""
import argparse

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.due_plan import (
    analyze_shape,
    build_target_line,
    check_feasibility,
    check_hard_feasibility,
)
from anki_tools.rebalance_due import (
    collect_cards,
    get_anki_collection_path,
    parse_range,
    resolve_deck_ids,
)

# Matches anki-rebalance-due's own --max-shift default. anki-due-stats has
# no --max-shift flag of its own (plan.md 1264 pins its flag surface without
# one) -- every "would this be reachable" figure it reports assumes a run
# using the default shift cap, and separately reports the minimum shift
# that WOULD reach the full sliding shape via the 6.4 bisection.
DEFAULT_MAX_SHIFT = 14


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-due-stats",
        description=(
            "Read-only report on an Anki deck's due-date window: totals, "
            "feasible --min/--max ranges, and the sliding-shape profile. "
            "Opens the collection read-only, writes nothing, takes no "
            "backup, and exits 0 whether the deck is feasible or not."
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
        help="Minimum number of cards due per day, to check feasibility for.",
    )
    parser.add_argument(
        "--max",
        dest="max_per_day",
        type=int,
        default=None,
        help="Maximum number of cards due per day, to check feasibility for.",
    )
    parser.add_argument(
        "--sliding",
        dest="sliding",
        action="store_true",
        default=False,
        help=(
            "Report against a sliding per-day target (from --max at the "
            "window start down to --min at the horizon) instead of a flat "
            "band. Requires both --min and --max."
        ),
    )
    window_group = parser.add_mutually_exclusive_group()
    window_group.add_argument(
        "--start-offset",
        dest="start_offset",
        type=int,
        default=1,
        help=(
            "Days after today where the window begins. Default: 1 "
            "(tomorrow). Mutually exclusive with --range."
        ),
    )
    window_group.add_argument(
        "--range",
        dest="range_raw",
        type=str,
        default=None,
        help=(
            "Day-offset window LO-HI (e.g. 8-30), or a bare N meaning "
            "N-N. Reports on this slice alone. Mutually exclusive with "
            "--start-offset."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        type=str,
        default=None,
        help="Override the auto-detected collection path.",
    )
    return parser


def _print_window_summary(report, start_day, resolved_end_day, today):
    print(
        f"{report.total} in-scope card(s) over a {report.horizon_days}-day "
        f"window (day offset {start_day - today}..{resolved_end_day - today}), "
        f"average {report.avg_per_day:.2f}/day."
    )


def _print_feasible_ranges(cards, start_day, resolved_end_day, today):
    # Force both hard checks to trip so `check_hard_feasibility` computes
    # its `suggested_min`/`suggested_max` -- both formulas depend only on
    # `total`/`horizon_days`/the origin-day counts, never on the bounds fed
    # in here, so probing with deliberately-infeasible bounds reads off the
    # real feasible flat range without reimplementing the formulas.
    probe = check_hard_feasibility(
        cards,
        start_day,
        resolved_end_day,
        10**9,
        0,
        DEFAULT_MAX_SHIFT,
    )
    print(
        f"Feasible flat range: --min {probe.suggested_min}, "
        f"--max {probe.suggested_max}."
    )
    return probe.suggested_min, probe.suggested_max


def _print_shape_profile(
    cards, start_day, resolved_end_day, today, min_bound, max_bound
):
    if min_bound is None or max_bound is None or min_bound >= max_bound:
        return
    target = build_target_line(start_day, resolved_end_day, min_bound, max_bound)
    shape = analyze_shape(cards, start_day, resolved_end_day, target, DEFAULT_MAX_SHIFT)
    print(
        f"Sliding shape (min={min_bound}, max={max_bound}) reachable at "
        f"--max-shift {DEFAULT_MAX_SHIFT}: {shape.shape_reachable}."
    )
    if not shape.shape_reachable:
        offsets = [d - today for d in shape.predicted_over_target_days]
        print(
            f"  Worst-window gap: {shape.shape_gap} card(s); "
            f"over-target day offset(s): {offsets}"
        )
        if shape.min_feasible_max_shift is not None:
            print(
                f"  A --max-shift of at least {shape.min_feasible_max_shift} "
                "would make the sliding shape reachable."
            )
        else:
            print(
                "  No --max-shift can reach this shape; widen the window "
                "or raise --max."
            )


def _print_user_pair(report, today):
    mode = "sliding" if report.mode == "sliding" else "flat"
    status = "feasible" if report.feasible else "INFEASIBLE"
    print(f"--min/--max pair ({mode}): {status}")
    if not report.feasible:
        for violation in report.violations:
            print(f"  - {violation}")
        if report.binding_prefix is not None:
            day, due_by_then, capacity_by_then = report.binding_prefix
            print(
                f"  Binding: by day offset {day - today}, {due_by_then} "
                f"card(s) due against {capacity_by_then} slot(s)."
            )
        if report.suggested_min is not None:
            print(f"  Suggested --min: {report.suggested_min}")
        if report.suggested_max is not None:
            print(f"  Suggested --max: {report.suggested_max}")
    if report.mode == "sliding" and report.shape_reachable is False:
        offsets = [d - today for d in report.predicted_over_target_days]
        print(
            f"  Sliding shape not reachable at --max-shift {DEFAULT_MAX_SHIFT} "
            f"(gap {report.shape_gap}, over-target day offset(s): {offsets})."
        )
        if report.min_feasible_max_shift is not None:
            print(
                f"  --max-shift {report.min_feasible_max_shift} would reach "
                "the full sliding shape."
            )


def main():
    parser = build_parser()
    args = parser.parse_args()

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

        if not cards:
            print("No in-scope cards in this window.")
            raise SystemExit(0)

        resolved_end_day = (
            end_day if end_day is not None else max(card.day for card in cards)
        )

        report = check_feasibility(
            cards,
            start_day,
            end_day,
            args.min_per_day,
            args.max_per_day,
            DEFAULT_MAX_SHIFT,
            sliding=args.sliding,
        )

        _print_window_summary(report, start_day, resolved_end_day, today)
        suggested_min, suggested_max = _print_feasible_ranges(
            cards, start_day, resolved_end_day, today
        )

        profile_min = (
            args.min_per_day if args.min_per_day is not None else suggested_min
        )
        profile_max = (
            args.max_per_day if args.max_per_day is not None else suggested_max
        )
        _print_shape_profile(
            cards, start_day, resolved_end_day, today, profile_min, profile_max
        )

        if args.min_per_day is not None or args.max_per_day is not None:
            _print_user_pair(report, today)

        raise SystemExit(0)
    finally:
        col.close()


if __name__ == "__main__":
    main()
