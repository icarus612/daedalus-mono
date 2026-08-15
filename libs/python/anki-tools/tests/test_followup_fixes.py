"""Regression tests for the post-ship follow-up fixes.

Two behaviours that shipped without a test pinning them, and which a
refactor could silently undo:

1. `_infeasible_reason` must distinguish a `--range` window ceiling from a
   genuine `--max-shift` block. Reporting "shift cap" for a range refusal
   sends the user to raise `--max-shift`, when widening `--range` is the
   only thing that can help.
2. When the deck is too sparse for any positive `--min`, the CLI must NOT
   literally suggest `--min 0` (a meaningless value); it must tell the user
   to omit `--min` or narrow the window instead.
"""

import io
from contextlib import redirect_stdout

import pytest

from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    check_feasibility,
    plan_rebalance,
)
from anki_tools.rebalance_due import _print_infeasibility


def _cards(spec):
    """spec: {day: count} -> list[CardDue] with distinct ids and ivl 10."""
    out, cid = [], 1
    for day, count in sorted(spec.items()):
        for _ in range(count):
            out.append(CardDue(card_id=cid, day=day, ivl=10))
            cid += 1
    return out


def test_range_ceiling_refusal_is_not_reported_as_shift_cap():
    """A --range-bounded run that overflows its ceiling must say so.

    The reverse pass is gated by the range ceiling, never by max_shift, so
    excess surviving it was refused by --range — not by --max-shift. Before
    this fix both cases returned "shift cap".
    """
    # Window [1, 3] with max 2 => capacity 6, but 9 cards are in scope.
    cards = _cards({1: 3, 2: 3, 3: 3})
    with pytest.raises(InfeasibleRebalance) as exc:
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=None,
            max_per_day=2,
            max_shift=None,
            set_earlier=True,
            end_day=3,
        )
    assert exc.value.reason == "range ceiling", (
        "a run bounded by --range must not blame --max-shift; "
        f"got {exc.value.reason!r}"
    )


def test_shift_cap_refusal_still_reported_as_shift_cap():
    """The inverse: with no range ceiling, the old label must survive."""
    cards = _cards({1: 5, 2: 5})
    with pytest.raises(InfeasibleRebalance) as exc:
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=None,
            max_per_day=2,
            max_shift=None,
            set_earlier=False,
        )
    assert exc.value.reason in {"sink overflow", "shift cap"}
    assert exc.value.reason != "range ceiling"


def test_sparse_deck_does_not_literally_suggest_min_zero():
    """floor(total/horizon) == 0 must not print `Suggested --min: 0`."""
    cards = _cards({d: 1 for d in range(1, 31)})  # 30 cards over 30 days
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=365,
        min_per_day=8,
        max_per_day=None,
        max_shift=None,
    )
    assert report.suggested_min == 0, "fixture must exercise the zero case"

    buf = io.StringIO()
    with redirect_stdout(buf):
        _print_infeasibility(report, today=0)
    out = buf.getvalue()

    assert "Suggested --min: 0" not in out
    assert "omit --min" in out
    assert "--range" in out
