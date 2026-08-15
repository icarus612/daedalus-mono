"""Contract tests for ``anki_tools.due_plan`` (Packet B, extended by Packet D).

Written from the plan's subphases 2.1-2.5 (Packet B) and 6.1c/6.2/6.3/6.4
(Packet D) acceptance criteria alone. The implementation under test
(``anki_tools/due_plan.py``) is never read by this file's author -- every
expectation below is derived from the contract text (the plan and the
lane's packet contract), not from observed behaviour.

The 2.1-2.5 tests below were written before Phase 6 superseded
``apply_max_pass``/``apply_reverse_max_pass``/``apply_min_pass``'s scalar
signatures with a ``DayTargets`` mapping and added a required ``max_end_day``
field to ``RunState`` (Packet D, subphase 6.3/6.2). Their call sites and the
``make_state``/``state_from_counts`` helpers were mechanically adapted to
the new signatures (via the new ``wide_ceiling`` helper below, itself built
on ``constant_targets``) so the file stays importable and the original
suite keeps running -- no assertion, expected value, or test name in that
section was changed. This is exactly the packet's own "constant_targets fed
to the three original passes reproduces the pre-Phase-6 scalar behaviour
move-for-move" regression anchor, exercised now across the whole pre-Phase-6
suite instead of just one dedicated case.
"""

import re
import time
from collections import Counter

import pytest

from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    RunState,
    analyze_shape,
    apply_max_pass,
    apply_min_pass,
    apply_reverse_max_pass,
    apply_shape_pass,
    build_buckets,
    build_target_line,
    check_feasibility,
    check_hard_feasibility,
    constant_targets,
    fit_target_line,
    max_move_order,
    may_move_later_to,
    may_move_to,
    min_move_order,
    move_card,
    plan_rebalance,
    validate_bounds,
    window_violations,
)

# ---------------------------------------------------------------------------
# Helpers -- not part of the contract, purely test scaffolding.
# ---------------------------------------------------------------------------


def make_state(
    buckets,
    start_day,
    end_day=None,
    max_shift=None,
    ivl_by_id=None,
    origin_by_id=None,
    moved=None,
    max_end_day=None,
):
    """Build a RunState directly. Every day in the intended sweep range must
    be present as a key in ``buckets`` (including empty days) -- exactly
    what build_buckets guarantees in production, and what apply_max_pass /
    apply_reverse_max_pass / apply_min_pass assume when indexing by day.

    ``max_end_day`` defaults to ``None`` (unbounded/no --range), which is
    the Phase 6 default path and reproduces pre-Phase-6 behaviour exactly
    -- see Packet D's RunState contract."""
    all_ids = [cid for ids in buckets.values() for cid in ids]
    if ivl_by_id is None:
        ivl_by_id = {cid: 1 for cid in all_ids}
    if origin_by_id is None:
        origin_by_id = {}
        for day, ids in buckets.items():
            for cid in ids:
                origin_by_id[cid] = day
    if end_day is None:
        end_day = max(buckets.keys())
    return RunState(
        buckets={day: list(ids) for day, ids in buckets.items()},
        ivl_by_id=dict(ivl_by_id),
        origin_by_id=dict(origin_by_id),
        moved=set(moved or ()),
        start_day=start_day,
        end_day=end_day,
        max_shift=max_shift,
        max_end_day=max_end_day,
    )


def state_from_counts(counts, start_day, max_shift=None, max_end_day=None):
    """Build a RunState with sequential unique card ids, ``counts[i]`` cards
    on day ``start_day + i``. Every card starts on its own (untouched)
    origin day with ivl=1, so selection-order ties break on card_id."""
    buckets = {}
    next_id = 1
    for offset, count in enumerate(counts):
        day = start_day + offset
        buckets[day] = list(range(next_id, next_id + count))
        next_id += count
    return make_state(buckets, start_day, max_shift=max_shift, max_end_day=max_end_day)


def wide_ceiling(state, value, buffer=1000):
    """A constant DayTargets ceiling/floor built from a scalar, wide enough
    to cover any horizon extension apply_reverse_max_pass might perform.

    Packet D's own acceptance criterion (6.3) requires that
    ``constant_targets`` fed to the three original passes reproduces the
    pre-Phase-6 scalar behaviour move-for-move -- this is the DayTargets
    adaptation of every 2.2-2.4 scalar call site in this file, needed
    because 6.3 supersedes their scalar signatures with a DayTargets
    mapping. The buffer only matters for apply_reverse_max_pass, which may
    extend state.end_day beyond what was known when the mapping was built;
    apply_max_pass/apply_min_pass never look past the existing window, so
    the extra keys are simply unused there."""
    return constant_targets(state.start_day, state.end_day + buffer, value)


def cards_from_counts(counts, start_day, ivl=1):
    cards = []
    next_id = 1
    for offset, count in enumerate(counts):
        day = start_day + offset
        for _ in range(count):
            cards.append(CardDue(next_id, day, ivl))
            next_id += 1
    return cards


def all_ids(buckets):
    ids = set()
    for values in buckets.values():
        ids.update(values)
    return ids


def total_cards(buckets):
    return sum(len(values) for values in buckets.values())


def check_postconditions(
    cards, start_day, result, *, max_per_day, set_earlier, max_shift=14
):
    """Re-check plan_rebalance's own stated post-conditions (plan 2.5,
    items 1-5) from the outside, against a RebalanceResult."""
    origin = {c.card_id: c.day for c in cards}
    original_ids = set(origin.keys())

    # (5) multiset preserved -- moves only ever reference real card ids.
    assert set(result.moves.keys()) <= original_ids

    for card_id, new_day in result.moves.items():
        # (1) no card lands below start_day.
        assert new_day >= start_day
        # (2) direction discipline.
        if not set_earlier:
            assert new_day < origin[card_id]
        else:
            assert new_day < origin[card_id] or result.reverse_pass_used
        # (4) shift cap respected.
        if max_shift is not None:
            assert new_day >= origin[card_id] - max_shift

    # (3) max respected across the whole horizon.
    if max_per_day is not None:
        for day in range(start_day, result.end_day + 1):
            assert result.after.get(day, 0) <= max_per_day

    assert sum(result.before.values()) == len(cards)
    assert sum(result.after.values()) == len(cards)


# ---------------------------------------------------------------------------
# 2.1 -- data shapes, validate_bounds, build_buckets, selection orders,
#        may_move_to, move_card
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "min_per_day,max_per_day",
    [
        (None, None),  # neither given
        (-1, None),  # negative min
        (None, 0),  # max below 1
        (10, 5),  # min > max
    ],
    ids=["both-none", "negative-min", "max-below-one", "min-exceeds-max"],
)
def test_validate_bounds_raises_value_error(min_per_day, max_per_day):
    with pytest.raises(ValueError):
        validate_bounds(min_per_day, max_per_day)


@pytest.mark.parametrize(
    "min_per_day,max_per_day",
    [
        (5, None),  # min only
        (None, 5),  # max only
        (5, 10),  # both, min < max
        (5, 5),  # both, min == max
    ],
    ids=["min-only", "max-only", "min-lt-max", "min-eq-max"],
)
def test_validate_bounds_accepts(min_per_day, max_per_day):
    assert validate_bounds(min_per_day, max_per_day) is None


def test_build_buckets_groups_and_pads_empty_days():
    cards = [CardDue(1, 10, 5), CardDue(2, 10, 90), CardDue(3, 12, 1)]
    buckets = build_buckets(cards, start_day=10)
    assert set(buckets.keys()) == {10, 11, 12}
    assert buckets[11] == []
    assert buckets[10] == [1, 2]
    assert buckets[12] == [3]
    # end_day is derived from the data (the max day among the cards).
    assert max(buckets.keys()) == 12


def test_build_buckets_raises_for_card_before_start_day():
    cards = [CardDue(1, 5, 3)]
    with pytest.raises(ValueError) as exc_info:
        build_buckets(cards, start_day=10)
    message = str(exc_info.value)
    assert "1" in message
    assert "5" in message


def test_move_orders_are_exact_reverses_when_nothing_has_moved():
    state = make_state(
        {10: [1, 2]},
        start_day=10,
        ivl_by_id={1: 5, 2: 90},
        origin_by_id={1: 10, 2: 10},
    )
    assert max_move_order([1, 2], state) == [2, 1]
    assert min_move_order([1, 2], state) == [1, 2]


def test_max_move_order_untouched_first_outranks_ivl():
    state = make_state(
        {10: [1, 2]},
        start_day=10,
        ivl_by_id={1: 5, 2: 90},
        origin_by_id={1: 10, 2: 10},
        moved={2},
    )
    # Card 2 has the larger ivl but has already moved this run, so the
    # untouched card 1 outranks it -- proves untouched-first is primary,
    # not merely a tiebreak.
    assert max_move_order([1, 2], state) == [1, 2]


def test_move_orders_degrade_to_pure_ivl_once_everything_has_moved():
    state = make_state(
        {10: [1, 2]},
        start_day=10,
        ivl_by_id={1: 5, 2: 90},
        origin_by_id={1: 10, 2: 10},
        moved={1, 2},
    )
    assert max_move_order([1, 2], state) == [2, 1]
    assert min_move_order([1, 2], state) == [1, 2]


def test_move_orders_break_ties_by_ascending_card_id():
    state = make_state(
        {10: [5, 3]},
        start_day=10,
        ivl_by_id={5: 7, 3: 7},
        origin_by_id={5: 10, 3: 10},
    )
    assert max_move_order([5, 3], state) == [3, 5]
    assert min_move_order([5, 3], state) == [3, 5]


def test_may_move_to_false_below_start_day():
    state = make_state({10: [1]}, start_day=10, origin_by_id={1: 10})
    assert may_move_to(1, 9, state) is False


def test_may_move_to_shift_cap_boundaries_are_inclusive():
    state = make_state({20: [1]}, start_day=1, origin_by_id={1: 20}, max_shift=14)
    assert may_move_to(1, 6, state) is True  # exactly 14 days earlier
    assert may_move_to(1, 5, state) is False  # 15 days earlier


def test_may_move_to_never_blocks_a_later_target():
    state = make_state({20: [1]}, start_day=1, origin_by_id={1: 20}, max_shift=0)
    assert may_move_to(1, 100, state) is True


def test_move_card_relocates_extends_moved_and_keeps_ascending_order():
    state = make_state({10: [1, 2], 11: [3]}, start_day=10, end_day=11)
    move_card(1, 10, 11, state)
    assert state.buckets[10] == [2]
    assert state.buckets[11] == [1, 3]
    assert 1 in state.moved
    assert state.end_day == 11


def test_move_card_extends_end_day_for_a_new_destination_day():
    state = make_state({10: [1]}, start_day=10, end_day=10)
    move_card(1, 10, 11, state)
    assert state.buckets[11] == [1]
    assert state.end_day == 11


# ---------------------------------------------------------------------------
# 2.2 -- apply_max_pass
# ---------------------------------------------------------------------------


def test_apply_max_pass_basic_cascade():
    state = state_from_counts([0, 0, 5], start_day=1)
    apply_max_pass(state, wide_ceiling(state, 2))
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [1, 2, 2]


def test_apply_max_pass_no_sink_overflow():
    state = state_from_counts([0, 0, 40], start_day=1)
    apply_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 16, 16]
    sink_overflow = max(0, len(state.buckets[1]) - 16)
    assert sink_overflow == 0


def test_apply_max_pass_sink_overflow():
    state = state_from_counts([0, 0, 60], start_day=1)
    apply_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [28, 16, 16]
    sink_overflow = max(0, len(state.buckets[1]) - 16)
    assert sink_overflow == 12


def test_apply_max_pass_one_day_rule_card_identity():
    """Counts alone ([3, 3, 3] either way) don't distinguish the correct
    one-day-rule behaviour from the rejected 'nearest day with room'
    behaviour -- only card identity does. Do NOT assert that any card
    moved twice: under the untouched-first key, day 2's excess is drawn
    from its own untouched originals once the day-3 arrivals are in
    state.moved, so no card here changes day more than once, and an
    assertion to the contrary is unsatisfiable by contract."""
    state = state_from_counts([0, 3, 6], start_day=1)
    day2_originals = set(state.buckets[2])
    day3_originals = set(state.buckets[3])

    apply_max_pass(state, wide_ceiling(state, 3))

    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [3, 3, 3]
    # Correct: day 3's overflow lands on day 2 (even though day 2 was
    # already full), so day 1 ends up with day 2's original cards.
    assert set(state.buckets[1]) == day2_originals
    # Day 2's post-pass residents came from day 3, never from day 2.
    assert set(state.buckets[2]) <= day3_originals
    assert len(state.buckets[2]) == 3
    assert set(state.buckets[3]) == day3_originals - set(state.buckets[2])
    # Wrong ("nearest day with room") would instead put day-3 originals
    # directly on day 1 and leave day 2's originals untouched.
    assert set(state.buckets[1]) != day3_originals


def test_apply_max_pass_prefers_untouched_over_already_moved():
    state = make_state(
        {1: [], 2: [], 3: [], 4: [], 5: [1, 2, 3, 4, 5]},
        start_day=1,
        end_day=5,
        ivl_by_id={i: 1 for i in range(1, 6)},
        origin_by_id={i: 5 for i in range(1, 6)},
        moved={1, 2},
    )
    apply_max_pass(state, wide_ceiling(state, 3))
    # Excess of 2 is drawn from the untouched pool {3, 4, 5}; the
    # already-moved {1, 2} are only ever picked once untouched cards run
    # out, which does not happen here.
    assert state.buckets[4] == [3, 4]
    assert state.buckets[5] == [1, 2, 5]


def test_apply_max_pass_shift_cap_blocks_further_cascade_without_raising():
    # A card originating on day 10 can reach day 9 but not day 8 under
    # max_shift=1.
    state = make_state(
        {8: [], 9: [], 10: [1]},
        start_day=8,
        end_day=10,
        origin_by_id={1: 10},
        max_shift=1,
    )
    apply_max_pass(state, wide_ceiling(state, 0))
    assert state.buckets[10] == []
    assert state.buckets[9] == [1]
    assert state.buckets[8] == []
    # Day 9 stays over max (1 card > max 0 there) -- no exception raised.


def test_apply_max_pass_invariants_no_later_moves_no_floor_breach_multiset():
    state = state_from_counts([0, 0, 0, 40], start_day=1)
    before_ids = all_ids(state.buckets)
    origin = dict(state.origin_by_id)

    apply_max_pass(state, wide_ceiling(state, 16))

    after_ids = all_ids(state.buckets)
    assert after_ids == before_ids
    assert total_cards(state.buckets) == len(after_ids)
    for day, ids in state.buckets.items():
        assert day >= state.start_day
        for card_id in ids:
            assert day <= origin[card_id]  # never moved later


def test_apply_max_pass_idempotent_on_a_conforming_distribution():
    state = state_from_counts([5, 5, 5], start_day=1)
    apply_max_pass(state, wide_ceiling(state, 5))
    snapshot = {day: list(ids) for day, ids in state.buckets.items()}
    apply_max_pass(state, wide_ceiling(state, 5))
    assert state.buckets == snapshot


def test_apply_max_pass_deterministic():
    def run():
        state = state_from_counts([0, 0, 60], start_day=1)
        apply_max_pass(state, wide_ceiling(state, 16))
        return {day: list(ids) for day, ids in state.buckets.items()}

    assert run() == run()


# ---------------------------------------------------------------------------
# 2.3 -- apply_reverse_max_pass
# ---------------------------------------------------------------------------


def test_apply_reverse_max_pass_resolves_sink_overflow_and_extends_horizon():
    state = state_from_counts([28, 16, 16], start_day=1)
    apply_reverse_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 12]
    assert state.end_day == 4
    assert total_cards(state.buckets) == 60


def test_apply_reverse_max_pass_multi_day_cascade_no_extension_needed():
    state = state_from_counts([40, 0, 0], start_day=1)
    apply_reverse_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [16, 16, 8]
    assert state.end_day == 3


def test_apply_reverse_max_pass_extends_beyond_the_original_horizon():
    state = state_from_counts([50], start_day=1)
    apply_reverse_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 2]
    assert state.end_day == 4


def test_apply_reverse_max_pass_only_ever_moves_cards_later():
    state = state_from_counts([28, 16, 16], start_day=1)
    before_days = {cid: day for day, ids in state.buckets.items() for cid in ids}

    apply_reverse_max_pass(state, wide_ceiling(state, 16))

    after_days = {cid: day for day, ids in state.buckets.items() for cid in ids}
    moved_ids = [cid for cid in after_days if after_days[cid] != before_days[cid]]
    assert moved_ids  # sanity: this scenario does move cards
    for cid in moved_ids:
        assert after_days[cid] > before_days[cid]


def test_apply_reverse_max_pass_is_not_blocked_by_the_shift_cap():
    state = state_from_counts([28, 16, 16], start_day=1, max_shift=0)
    apply_reverse_max_pass(state, wide_ceiling(state, 16))
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 12]


def test_apply_reverse_max_pass_never_lands_below_start_day():
    state = state_from_counts([28, 16, 16], start_day=1)
    apply_reverse_max_pass(state, wide_ceiling(state, 16))
    assert all(day >= state.start_day for day in state.buckets)
    # start_day itself ends exactly at max_per_day, having begun above it.
    assert len(state.buckets[1]) == 16


def test_apply_reverse_max_pass_multiset_preserved_and_deterministic():
    def run():
        state = state_from_counts([28, 16, 16], start_day=1)
        apply_reverse_max_pass(state, wide_ceiling(state, 16))
        return {day: sorted(ids) for day, ids in state.buckets.items()}

    first = run()
    second = run()
    assert first == second
    combined_ids = set()
    for ids in first.values():
        combined_ids.update(ids)
    assert combined_ids == set(range(1, 61))


# ---------------------------------------------------------------------------
# 2.4 -- apply_min_pass
# ---------------------------------------------------------------------------


def test_apply_min_pass_basic_pull_from_nearest_day():
    state = state_from_counts([3, 20, 20, 20], start_day=1)
    apply_min_pass(state, wide_ceiling(state, 8))
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [8, 15, 20, 20]


def test_apply_min_pass_cascades_through_and_disturbs_an_at_minimum_day():
    state = state_from_counts([0, 8, 20], start_day=1)
    day2_originals = set(state.buckets[2])

    apply_min_pass(state, wide_ceiling(state, 8))

    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 8, 12]
    # Day 2 gave up its original cards to day 1 and refilled from day 3 --
    # proves surplus-hunting (leaving at-minimum days undisturbed) is not
    # the implemented behaviour.
    assert set(state.buckets[2]) != day2_originals


def test_apply_min_pass_no_surplus_cascade():
    state = state_from_counts([0, 8, 8], start_day=1)
    apply_min_pass(state, wide_ceiling(state, 8))
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 8, 0]


def test_apply_min_pass_exempts_the_trailing_days():
    state = state_from_counts([8, 3], start_day=1)
    before = {day: list(ids) for day, ids in state.buckets.items()}
    apply_min_pass(state, wide_ceiling(state, 8))
    after = {day: list(ids) for day, ids in state.buckets.items()}
    assert before == after


def test_apply_min_pass_shift_cap_leaves_a_day_short_without_raising():
    state = state_from_counts([0, 20], start_day=1, max_shift=0)
    apply_min_pass(state, wide_ceiling(state, 8))
    assert len(state.buckets[1]) == 0
    assert len(state.buckets[2]) == 20


def test_apply_min_pass_keeps_hunting_past_a_cap_blocked_source():
    """The N17 case: the nearest non-empty later day (day 2) is entirely
    cap-blocked, but a legal source exists one day further out (day 3).
    The fill from day 3 MUST happen -- an implementation that abandons
    day 1 at the first blocked source (leaving it short) fails this."""
    state = make_state(
        {
            1: [],
            2: [101, 102],
            3: [201, 202, 203, 204, 205, 206, 207, 208],
        },
        start_day=1,
        end_day=3,
        ivl_by_id={cid: 1 for cid in (101, 102, *range(201, 209))},
        origin_by_id={
            101: 16,
            102: 16,
            **{cid: 3 for cid in range(201, 209)},
        },
        max_shift=14,
    )

    apply_min_pass(state, wide_ceiling(state, 8))

    assert len(state.buckets[1]) == 8
    assert set(state.buckets[1]) <= set(range(201, 209))
    assert state.buckets[2] == [101, 102]  # cap-blocked, untouched


def test_apply_min_pass_prefers_untouched_source_cards():
    state = make_state(
        {1: [], 2: [1, 2, 3, 4]},
        start_day=1,
        end_day=2,
        ivl_by_id={1: 1, 2: 1, 3: 1, 4: 1},
        origin_by_id={1: 2, 2: 2, 3: 2, 4: 2},
        moved={1, 2},
    )
    apply_min_pass(state, wide_ceiling(state, 2))
    assert set(state.buckets[1]) == {3, 4}
    assert set(state.buckets[2]) == {1, 2}


def test_apply_min_pass_invariants_no_later_moves_no_floor_breach_multiset():
    state = state_from_counts([3, 20, 20, 20], start_day=1)
    before_ids = all_ids(state.buckets)
    before_days = {cid: day for day, ids in state.buckets.items() for cid in ids}

    apply_min_pass(state, wide_ceiling(state, 8))

    after_days = {cid: day for day, ids in state.buckets.items() for cid in ids}
    for card_id, day in after_days.items():
        assert day >= state.start_day
        assert day <= before_days[card_id]
    assert all_ids(state.buckets) == before_ids


def test_apply_min_pass_deterministic():
    def run():
        state = state_from_counts([3, 20, 20, 20], start_day=1)
        apply_min_pass(state, wide_ceiling(state, 8))
        return {day: sorted(ids) for day, ids in state.buckets.items()}

    assert run() == run()


# ---------------------------------------------------------------------------
# 2.5 -- plan_rebalance orchestration, infeasibility, post-conditions
# ---------------------------------------------------------------------------


def test_plan_rebalance_validates_bounds_before_anything_else():
    cards = [CardDue(1, 10, 3)]
    with pytest.raises(ValueError):
        plan_rebalance(cards, start_day=1, min_per_day=None, max_per_day=None)


def test_plan_rebalance_empty_input_returns_fully_defined_empty_result():
    result = plan_rebalance([], start_day=5, min_per_day=8, max_per_day=16)
    assert result.moves == {}
    assert result.before == {}
    assert result.after == {}
    assert result.end_day == 4  # start_day - 1, deliberately
    assert result.sink_overflow == 0
    assert result.short_days == []
    assert result.reverse_pass_used is False


def test_plan_rebalance_single_card_produces_no_moves():
    cards = [CardDue(1, 10, 3)]
    result = plan_rebalance(cards, start_day=1, min_per_day=None, max_per_day=16)
    assert result.moves == {}


def test_plan_rebalance_moves_dict_contains_only_changed_cards():
    cards = cards_from_counts([0, 0, 5], start_day=1)
    result = plan_rebalance(cards, start_day=1, min_per_day=None, max_per_day=2)
    origin = {c.card_id: c.day for c in cards}
    assert len(result.moves) == 3
    for card_id, new_day in result.moves.items():
        assert new_day != origin[card_id]


def test_plan_rebalance_postconditions_max_only():
    cards = cards_from_counts([0, 0, 40], start_day=1)
    result = plan_rebalance(cards, start_day=1, min_per_day=None, max_per_day=16)
    check_postconditions(
        cards, 1, result, max_per_day=16, set_earlier=False, max_shift=14
    )


def test_plan_rebalance_postconditions_min_only():
    cards = cards_from_counts([3, 20, 20, 20], start_day=1)
    result = plan_rebalance(cards, start_day=1, min_per_day=8, max_per_day=None)
    check_postconditions(
        cards, 1, result, max_per_day=None, set_earlier=False, max_shift=14
    )


def test_plan_rebalance_postconditions_min_and_max_given():
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=14,
        set_earlier=True,
    )
    check_postconditions(
        cards, 1, result, max_per_day=16, set_earlier=True, max_shift=14
    )


def test_plan_rebalance_flagship_trace_requires_set_earlier_true():
    """The user's real-world case, traced end to end against the plan's
    own pseudocode. This input is only feasible with set_earlier=True --
    see test_plan_rebalance_default_infeasibility_raises below for what
    the very same input does under the default."""
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)

    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=14,
        set_earlier=True,
    )

    assert result.reverse_pass_used is True
    assert result.end_day == 6  # no extension needed for this input
    assert [result.after.get(d, 0) for d in range(1, 7)] == [
        16,
        16,
        10,
        9,
        16,
        1,
    ]
    assert result.short_days == []
    # sink_overflow is retained from the earlier-only max pass even though
    # the reverse pass went on to resolve it.
    assert result.sink_overflow == 8
    assert sum(result.after.values()) == 68


def test_plan_rebalance_default_infeasibility_raises_and_names_days():
    """The same distribution as the flagship trace, but under the default
    set_earlier=False -- this MUST raise, not return a partial result."""
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc_info:
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=8,
            max_per_day=16,
            max_shift=14,
            set_earlier=False,
        )
    # The offending day is day 1 (the sink, per the plan's own trace of
    # this exact input: max pass alone leaves over_max == [1]).
    assert re.search(r"\b1\b", str(exc_info.value))


def test_plan_rebalance_set_earlier_extends_horizon_when_needed():
    cards = cards_from_counts([50], start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
        set_earlier=True,
    )
    assert result.reverse_pass_used is True
    assert result.end_day == 4
    for day in range(1, result.end_day + 1):
        assert result.after.get(day, 0) <= 16
    assert sum(result.after.values()) == 50


def test_plan_rebalance_cap_induced_shortfall_is_reported_not_raised():
    cards = cards_from_counts([0, 20], start_day=1)
    result = plan_rebalance(
        cards, start_day=1, min_per_day=8, max_per_day=None, max_shift=0
    )
    assert result.short_days != []
    assert 1 in result.short_days


def test_plan_rebalance_deterministic():
    def run():
        cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
        result = plan_rebalance(
            cards,
            start_day=1,
            min_per_day=8,
            max_per_day=16,
            max_shift=14,
            set_earlier=True,
        )
        return result.moves, result.after

    assert run() == run()


# ---------------------------------------------------------------------------
# Packet D (Phase 6) -- shared core additions: subphases 6.1c, 6.2, 6.3, 6.4.
#
# Written from the lane contract's "Packet D" section and the cited plan.md
# line ranges (959-974, 1042-1052, 1160-1174, 1224-1232, plus the pinned
# pseudocode at 1070-1081, 1133-1151, 1186-1211) alone. The implementation
# is never read.
# ---------------------------------------------------------------------------


def real_block_cards():
    """The plan's own verified real-world fixture (plan.md 6.4): days
    244-328 inclusive at exactly 16 cards/day (1360 cards total), embedded
    in a full 365-day deck horizon where every other day has none. Used
    for the DP-B/DP-F boundary criterion and the cap-reachability table."""
    cards = []
    next_id = 1
    for day in range(244, 329):
        for _ in range(16):
            cards.append(CardDue(next_id, day, 1))
            next_id += 1
    return cards


def real_block_counts():
    return Counter(c.day for c in real_block_cards())


# --- 6.2: RunState.max_end_day, may_move_later_to, build_buckets upper bound


def test_may_move_later_to_true_when_max_end_day_is_none():
    state = make_state({1: []}, start_day=1, end_day=1, max_end_day=None)
    assert may_move_later_to(10_000, state) is True


def test_may_move_later_to_respects_the_containment_ceiling():
    state = make_state({1: []}, start_day=1, end_day=1, max_end_day=5)
    assert may_move_later_to(5, state) is True  # exactly the ceiling
    assert may_move_later_to(6, state) is False  # one past it


def test_apply_reverse_max_pass_stops_advancing_past_the_containment_ceiling():
    """The pass must leave the excess in place and stop -- not raise --
    once may_move_later_to refuses (plan.md 1013-1024)."""
    state = make_state({1: list(range(1, 51))}, start_day=1, end_day=1, max_end_day=3)
    # Ceiling is wide enough that only the containment gate (not the
    # ceiling dict itself) is what stops the extension.
    ceiling = constant_targets(1, 10, 16)

    apply_reverse_max_pass(state, ceiling)

    assert state.end_day == 3  # never extended past the ceiling
    assert 4 not in state.buckets
    assert len(state.buckets[1]) == 16
    assert len(state.buckets[2]) == 16
    assert len(state.buckets[3]) == 18  # stays over max_per_day; no raise here


def test_may_move_to_start_day_floor_takes_precedence_over_the_shift_cap():
    """6.2's downward-containment claim: the window floor is checked
    independently of, and takes precedence over, the shift cap -- no new
    code, but the range-mode combination must be asserted."""
    state = make_state(
        {100: [1]},
        start_day=100,
        end_day=110,
        max_end_day=110,
        origin_by_id={1: 103},
        max_shift=14,
    )
    assert may_move_to(1, 100, state) is True  # exactly the floor (LO)
    # The shift cap alone (103 - 14 = 89) would allow this, but the range
    # floor forbids it.
    assert may_move_to(1, 99, state) is False


def test_build_buckets_raises_for_card_after_explicit_end_day():
    cards = [CardDue(1, 20, 3)]
    with pytest.raises(ValueError) as exc_info:
        build_buckets(cards, start_day=10, end_day=15)
    message = str(exc_info.value)
    assert "1" in message
    assert "20" in message


def test_build_buckets_no_upper_check_when_end_day_is_omitted():
    # end_day=None is the unbounded default path -- must remain unaffected.
    cards = [CardDue(1, 999, 3)]
    buckets = build_buckets(cards, start_day=10)
    assert 999 in buckets


def test_build_buckets_pads_to_the_explicit_end_day_including_empty_tail():
    cards = [CardDue(1, 10, 3)]
    buckets = build_buckets(cards, start_day=10, end_day=13)
    assert set(buckets.keys()) == {10, 11, 12, 13}
    assert buckets[13] == []


def test_build_buckets_single_day_range_is_legal_and_degenerate():
    cards = [CardDue(1, 5, 3), CardDue(2, 5, 1)]
    buckets = build_buckets(cards, start_day=5, end_day=5)
    assert set(buckets.keys()) == {5}
    assert buckets[5] == [1, 2]


def test_plan_rebalance_end_day_set_is_never_extended_even_with_set_earlier():
    """6.2 acceptance: with end_day set, state.end_day == end_day on exit
    even when set_earlier=True and the reverse pass runs -- no horizon
    extension is possible in range mode."""
    cards = cards_from_counts([50], start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=None,
        max_per_day=16,
        max_shift=None,
        set_earlier=True,
        end_day=10,
    )
    assert result.end_day == 10


def test_plan_rebalance_range_mode_upward_containment_raises_infeasible_not_new_type():
    """Excess that HI cannot absorb raises the existing InfeasibleRebalance,
    naming the offending days -- not a new exception type (6.2)."""
    cards = cards_from_counts([50], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc_info:
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=None,
            max_per_day=16,
            max_shift=None,
            set_earlier=True,
            end_day=2,  # far too small to absorb 50 cards at 16/day
        )
    assert re.search(r"\b2\b", str(exc_info.value))


def test_plan_rebalance_range_mode_shift_cap_clamped_by_start_day_floor():
    """A card whose shift budget would reach past LO is clamped to LO, not
    to the shift-cap-implied day (plan.md 1015, 1047)."""
    cards = cards_from_counts([8], start_day=103)  # 8 cards, all due day 103
    result = plan_rebalance(
        cards,
        start_day=100,
        min_per_day=None,
        max_per_day=2,
        max_shift=14,
        end_day=110,
    )
    assert all(day >= 100 for day in result.moves.values())
    assert min(result.moves.values()) == 100  # cascade reaches exactly LO


# --- 6.3: constant_targets / DayTargets-based passes / apply_shape_pass /
#          build_target_line / the two-stage sliding sequence


def test_constant_targets_builds_a_dict_covering_the_whole_window():
    assert constant_targets(5, 8, 12) == {5: 12, 6: 12, 7: 12, 8: 12}


def test_constant_targets_reproduces_pre_phase6_scalar_behaviour_move_for_move():
    """Packet D's own regression anchor (6.3): constant_targets fed to the
    three original passes must reproduce the pre-Phase-6 scalar behaviour
    exactly, move for move -- exercised directly here (rather than through
    the wide_ceiling test-helper used for the bulk of the 2.2-2.4 suite
    above, which is the same guarantee exercised across dozens of
    fixtures)."""
    state = state_from_counts([0, 0, 40], start_day=1)
    ceiling = constant_targets(1, 3, 16)
    assert ceiling == {1: 16, 2: 16, 3: 16}
    apply_max_pass(state, ceiling)
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 16, 16]


@pytest.mark.parametrize(
    "start_day,end_day,min_per_day,max_per_day,expected",
    [
        (1, 6, 8, 16, {1: 16, 2: 14, 3: 13, 4: 11, 5: 10, 6: 8}),
        (5, 5, 8, 16, {5: 16}),  # degenerate: end_day == start_day
    ],
    ids=["worked-example", "degenerate-single-day"],
)
def test_build_target_line_matches_pinned_examples(
    start_day, end_day, min_per_day, max_per_day, expected
):
    assert build_target_line(start_day, end_day, min_per_day, max_per_day) == expected


def test_build_target_line_endpoints_and_monotonicity():
    line = build_target_line(1, 20, 4, 30)
    assert line[1] == 30
    assert line[20] == 4
    values = [line[d] for d in range(1, 21)]
    assert values == sorted(values, reverse=True)  # non-increasing


def test_build_target_line_uses_floor_x_plus_half_not_bankers_rounding():
    """Pinned rounding rule (plan.md 1078): floor(x + 0.5), never round().
    T(2) here lands on exactly n + 0.5 with n=4 (even) -- round()'s
    banker's rounding would resolve the tie down to 4 (the even
    neighbour); floor(x + 0.5) always resolves it up, to 5."""
    line = build_target_line(1, 3, 0, 9)
    assert line == {1: 9, 2: 5, 3: 0}
    assert round(4.5) == 4  # sanity: this is exactly the tie round() would
    # resolve the other way, confirming the test actually distinguishes
    # the two rounding rules rather than agreeing with both by accident.


def test_apply_shape_pass_refusal_is_not_a_skip_to_the_next_day():
    """When day d-1 is already at its hard ceiling, apply_shape_pass must
    refuse the move and leave day d exactly as is -- it must NOT reach
    past the full day to land cards on d-2 instead (plan.md 1147: 'it does
    not look at d-2')."""
    state = make_state(
        {1: [100, 101], 2: [201, 202], 3: [1, 2, 3, 4, 5], 4: []},
        start_day=1,
        end_day=4,
    )
    target = {1: 2, 2: 2, 3: 1, 4: 5}
    hard_ceiling = {1: 2, 2: 2, 3: 5, 4: 5}

    apply_shape_pass(state, target, hard_ceiling)

    assert state.buckets[3] == [1, 2, 3, 4, 5]  # refused; nothing moved out
    assert state.buckets[1] == [100, 101]  # nothing skipped past the full day
    assert state.buckets[2] == [201, 202]  # receiver stayed exactly at cap


def test_apply_shape_pass_shift_cap_blocks_candidates_without_raising():
    state = make_state(
        {1: [], 2: [1, 2, 3]},
        start_day=1,
        end_day=2,
        origin_by_id={1: 2, 2: 2, 3: 2},
        max_shift=0,  # no card may move earlier at all
    )
    target = {1: 0, 2: 0}
    hard_ceiling = {1: 5, 2: 5}

    apply_shape_pass(state, target, hard_ceiling)

    assert state.buckets[2] == [1, 2, 3]  # every candidate was shift-blocked
    assert state.buckets[1] == []


def test_apply_shape_pass_shapes_down_toward_target_when_unobstructed():
    state = make_state({1: [], 2: [1, 2, 3, 4]}, start_day=1, end_day=2)
    target = {1: 4, 2: 1}
    hard_ceiling = {1: 4, 2: 4}

    apply_shape_pass(state, target, hard_ceiling)

    assert len(state.buckets[2]) == 1
    assert len(state.buckets[1]) == 3


@pytest.mark.parametrize(
    "counts,start_day,min_per_day,max_per_day,max_shift",
    [
        ([0, 0, 0, 0, 0, 90], 1, 8, 16, None),
        ([0] * 9 + [45], 1, 8, 16, 2),
        ([28, 16, 16], 1, 8, 16, None),
    ],
    ids=["two-stage-fixture", "cap-blocked-fixture", "reverse-pass-fixture"],
)
def test_apply_shape_pass_never_breaches_the_hard_ceiling(
    counts, start_day, min_per_day, max_per_day, max_shift
):
    # Establish the HARD result first, exactly as plan_rebalance's own
    # steps 1-2 do: apply_max_pass, then apply_reverse_max_pass too if the
    # sink itself is still over cap (the "reverse-pass-fixture" case, e.g.
    # [28, 16, 16], needs this -- apply_max_pass alone never sheds FROM
    # start_day, only ever TO it).
    state = state_from_counts(counts, start_day, max_shift=max_shift)
    hard_ceiling = constant_targets(start_day, state.end_day, max_per_day)
    apply_max_pass(state, hard_ceiling)
    if len(state.buckets.get(start_day, [])) > max_per_day:
        apply_reverse_max_pass(
            state, constant_targets(start_day, state.end_day + 1000, max_per_day)
        )
    hard_ceiling = constant_targets(start_day, state.end_day, max_per_day)
    target = build_target_line(start_day, state.end_day, min_per_day, max_per_day)

    apply_shape_pass(state, target, hard_ceiling)

    for day in range(start_day, state.end_day + 1):
        assert len(state.buckets.get(day, [])) <= max_per_day


def test_two_stage_necessity_flat_cap_prevents_sink_overflow_shape_alone_would_cause():
    """The plan's central invariant (6.3, plan.md 1117, 1167): the hard
    result must be established FIRST by the unchanged flat-cap pass,
    because shedding straight toward T(d) sheds more cards earlier and can
    pile the sink above max_per_day on a deck that is perfectly feasible
    under the flat cap.

    90 cards, all due day 6, window 1-6, min=8 max=16: the correct
    two-stage sliding sequence (run via plan_rebalance) must leave every
    day at or under max_per_day and must not raise. As a guard, a naive
    single-stage apply_max_pass(state, T) on the identical input must
    drive start_day (day 1) above max_per_day -- proving the two stages
    are necessary, not merely a stylistic choice."""
    cards = cards_from_counts([0, 0, 0, 0, 0, 90], start_day=1)

    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=None,
        sliding=True,
    )
    for day in range(1, result.end_day + 1):
        assert result.after.get(day, 0) <= 16

    # Guard: the naive single-stage substitution the plan forbids.
    naive_state = state_from_counts([0, 0, 0, 0, 0, 90], start_day=1)
    target = build_target_line(1, 6, 8, 16)
    apply_max_pass(naive_state, target)
    assert len(naive_state.buckets[1]) > 16


def test_flat_mode_is_bit_identical_through_the_shared_daytargets_path():
    """Flat mode is the same code path with a constant line (plan.md
    1094): driving apply_max_pass/apply_min_pass with constant_targets
    must reproduce the exact pre-phase flat move set."""
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=14,
        set_earlier=True,
        sliding=False,
    )
    assert result.over_target_days == []  # always empty in flat mode
    assert [result.after.get(d, 0) for d in range(1, 7)] == [16, 16, 10, 9, 16, 1]


def test_sliding_cap_blocked_reports_over_target_days_without_raising():
    """DP-F: a merely shape-unreachable (not hard-infeasible) sliding run
    proceeds and reports over_target_days -- it is not a failure."""
    cards = cards_from_counts([0] * 9 + [45], start_day=1)  # 45 cards, day 10
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=2,
        sliding=True,
    )
    assert result.over_target_days != []
    for day in range(1, result.end_day + 1):
        assert result.after.get(day, 0) <= 16


def test_strict_sliding_raises_on_the_same_cap_blocked_case():
    cards = cards_from_counts([0] * 9 + [45], start_day=1)
    with pytest.raises(InfeasibleRebalance):
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=8,
            max_per_day=16,
            max_shift=2,
            sliding=True,
            strict_sliding=True,
        )


def test_sliding_reachable_distribution_ends_with_empty_over_target_days():
    cards = cards_from_counts([16, 16, 16, 16, 16], start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=None,
        sliding=True,
    )
    # 80 cards over 5 days cannot fit under the RAW 16..8 ramp (capacity 60),
    # so plan_rebalance sizes the ramp to the supply first (fit_target_line).
    # Assert against the fitted line — asserting against the raw one would
    # demand the planner discard 20 cards.
    raw = build_target_line(1, result.end_day, 8, 16)
    fitted = fit_target_line(raw, len(cards), 16)
    for day in range(1, result.end_day + 1):
        assert result.after.get(day, 0) <= 16
        assert result.after.get(day, 0) <= fitted[day] or day in (
            result.over_target_days
        )


# --- 6.4: check_hard_feasibility / analyze_shape / check_feasibility /
#          window_violations


def test_check_feasibility_flagship_precheck_trace():
    """The plan's own flagship distribution (identical to 2.5's), run
    through the precheck instead of the planner. Pins binding_prefix,
    avg_per_day, and suggested_max -- and, the whole reason the prefix
    check exists, that a naive global-average-only check would have
    missed this distribution entirely."""
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=None,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
    )
    assert report.feasible is False
    assert report.binding_prefix == (2, 40, 32)
    assert report.avg_per_day == pytest.approx(11.33, abs=0.01)
    assert report.suggested_max == 20
    # The defect this criterion exists to catch: a global-average-alone
    # check would have PASSED (11.33 <= 16) even though the planner
    # provably cannot satisfy this distribution.
    assert report.avg_per_day <= 16


def test_check_hard_feasibility_uncapped_matches_the_6_1_prefix_condition():
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    hard = check_hard_feasibility(
        cards,
        start_day=1,
        end_day=None,
        min_per_day=None,
        max_per_day=16,
        max_shift=None,
    )
    assert hard.feasible is False
    assert hard.binding_prefix == (2, 40, 32)


def test_check_feasibility_set_earlier_downgrades_violation_to_a_warning():
    cards = cards_from_counts([0, 40, 2, 0, 25, 1], start_day=1)
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=None,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
        set_earlier=True,
    )
    assert report.feasible is True
    joined = " ".join(report.violations).lower()
    assert any(kw in joined for kw in ("extend", "horizon", "set_earlier", "warn"))


def test_check_feasibility_feasible_flat_distribution_has_no_violations():
    cards = cards_from_counts([5, 5, 5], start_day=1)
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=None,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
    )
    assert report.feasible is True
    assert report.violations == []


def test_check_feasibility_min_omitted_runs_no_lower_bound_check():
    """A max-only run cannot fail on avg < min -- because the lower-bound
    check never runs at all when min_per_day is omitted."""
    cards = cards_from_counts([1] + [0] * 98 + [1], start_day=1)  # very sparse
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=None,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
    )
    assert report.feasible is True


def test_dp_b_dp_f_boundary_cap_unreachable_but_max_feasible_passes_the_hard_gate():
    """The DP-B/DP-F boundary criterion (plan.md 969; contract's own
    explicit highlight for this packet). The hard gate must NEVER be wired
    to sum(T(d)) -- doing so would hard-fail exactly the decks DP-F's
    best-effort default exists to serve. Tested via the two callers
    directly (check_hard_feasibility / analyze_shape) rather than through
    check_feasibility's composed min_per_day, to isolate the upper-bound
    claim ("total <= D * max_per_day") the plan itself cites as the sole
    reason for feasible=True here from the unrelated global lower-bound
    check, which the plan's own text does not address for this fixture."""
    cards = real_block_cards()

    hard = check_hard_feasibility(
        cards,
        start_day=1,
        end_day=365,
        min_per_day=None,
        max_per_day=16,
        max_shift=14,
    )
    assert hard.feasible is True

    target = build_target_line(1, 365, 8, 16)
    shape = analyze_shape(cards, start_day=1, end_day=365, target=target, max_shift=14)
    assert shape.shape_reachable is False
    assert shape.predicted_over_target_days != []
    assert shape.min_feasible_max_shift == 48


def test_min_feasible_max_shift_bisection_matches_the_verified_boundary():
    """47 is the last infeasible probe, 48 the first feasible one -- pins
    the exact bisection boundary from plan.md's verified table. At 48 the
    shape is already reached, so min_feasible_max_shift being None there
    (nothing left to suggest) is consistent with the field's own docstring
    ("what WOULD reach the shape") -- only asserted non-None on the
    not-yet-reachable side, where a suggestion is meaningful."""
    cards = real_block_cards()
    target = build_target_line(1, 365, 8, 16)

    shape_at_47 = analyze_shape(cards, 1, 365, target=target, max_shift=47)
    shape_at_48 = analyze_shape(cards, 1, 365, target=target, max_shift=48)

    assert shape_at_47.shape_reachable is False
    assert shape_at_48.shape_reachable is True
    assert shape_at_47.min_feasible_max_shift == 48


@pytest.mark.parametrize(
    "max_shift,feasible,worst_window",
    [
        (14, False, (230, 328, 1360, 980)),
        (30, False, (214, 328, 1360, 1156)),
        (60, True, None),
    ],
    ids=["shift-14-infeasible", "shift-30-infeasible", "shift-60-feasible"],
)
def test_window_violations_reproduces_the_real_block_reachability_table(
    max_shift, feasible, worst_window
):
    """Reproduces plan.md 1213-1220's verified table exactly."""
    counts = real_block_counts()
    target = build_target_line(1, 365, 8, 16)

    violations = window_violations(counts, 1, 365, target, max_shift)

    if feasible:
        assert violations == []
    else:
        assert violations != []
        worst = max(violations, key=lambda v: v[2] - v[3])
        assert worst == worst_window


def test_window_violations_full_horizon_completes_quickly():
    """D(D+1)/2 = 66,795 windows at D=365, O(1) each via prefix sums -- a
    correctness-and-performance criterion together, per the plan (line
    1210's own correction: not O(D^2), do not approximate)."""
    counts = real_block_counts()
    target = build_target_line(1, 365, 8, 16)

    start = time.monotonic()
    violations = window_violations(counts, 1, 365, target, 14)
    elapsed = time.monotonic() - start

    assert elapsed < 5.0
    assert violations != []


def test_shape_feasibility_is_monotone_in_max_shift():
    """Feasibility is monotone in the cap -- a larger max_shift only
    shrinks every confined set, so once feasible it must stay feasible for
    every larger max_shift (the property the 6.4 bisection depends on)."""
    counts = real_block_counts()
    target = build_target_line(1, 365, 8, 16)

    seen_feasible = False
    for shift in (0, 5, 14, 30, 47, 48, 60, 100, 365):
        is_feasible = window_violations(counts, 1, 365, target, shift) == []
        if is_feasible:
            seen_feasible = True
        elif seen_feasible:
            pytest.fail(
                f"feasibility flipped back to False at max_shift={shift} "
                "after being True at a smaller max_shift"
            )
    assert seen_feasible  # sanity: some probed shift was actually feasible


def test_two_callers_distinguishable_same_window_different_capacity():
    """The B25 regression this criterion exists to catch (plan.md 1230):
    on the 6.1 counterexample window (1..10, min=8 max=16 sliding, 46
    cards of origin <= 3 -- concentrated on day 3 so only the a=1,b=3
    prefix window is ever in play under max_shift=None), the hard leg
    (constant max_per_day capacity) and the shape leg (T(d) capacity) MUST
    give different answers on the identical window. A single shared
    result for both callers is exactly the defect this test exists to
    catch."""
    cards = [CardDue(cid, 3, 1) for cid in range(1, 47)]  # 46 cards, origin day 3
    counts = Counter(c.day for c in cards)

    hard_capacity = constant_targets(1, 10, 16)
    hard_violations = window_violations(counts, 1, 10, hard_capacity, None)
    assert hard_violations == []  # 46 <= 48

    shape_capacity = build_target_line(1, 10, 8, 16)
    assert sum(shape_capacity[d] for d in range(1, 4)) == 45
    shape_violations = window_violations(counts, 1, 10, shape_capacity, None)
    assert len(shape_violations) == 1
    assert shape_violations[0] == (1, 3, 46, 45)  # 46 > 45

    # Same distinction through the real callers, not just the raw kernel.
    hard = check_hard_feasibility(cards, 1, 10, None, 16, max_shift=None)
    assert hard.feasible is True
    shape = analyze_shape(cards, 1, 10, target=shape_capacity, max_shift=None)
    assert shape.shape_reachable is False
