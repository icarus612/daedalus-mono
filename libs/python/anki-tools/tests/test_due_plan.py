"""Contract tests for ``anki_tools.due_plan`` (Packet B).

Written from the plan's subphases 2.1-2.5 acceptance criteria alone. The
implementation under test (``anki_tools/due_plan.py``) is never read by this
file's author -- every expectation below is derived from the contract text
(the plan and the lane's packet contract), not from observed behaviour.
"""

import re

import pytest

from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    RunState,
    apply_max_pass,
    apply_min_pass,
    apply_reverse_max_pass,
    build_buckets,
    max_move_order,
    may_move_to,
    min_move_order,
    move_card,
    plan_rebalance,
    validate_bounds,
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
):
    """Build a RunState directly. Every day in the intended sweep range must
    be present as a key in ``buckets`` (including empty days) -- exactly
    what build_buckets guarantees in production, and what apply_max_pass /
    apply_reverse_max_pass / apply_min_pass assume when indexing by day."""
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
    )


def state_from_counts(counts, start_day, max_shift=None):
    """Build a RunState with sequential unique card ids, ``counts[i]`` cards
    on day ``start_day + i``. Every card starts on its own (untouched)
    origin day with ivl=1, so selection-order ties break on card_id."""
    buckets = {}
    next_id = 1
    for offset, count in enumerate(counts):
        day = start_day + offset
        buckets[day] = list(range(next_id, next_id + count))
        next_id += count
    return make_state(buckets, start_day, max_shift=max_shift)


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
    apply_max_pass(state, max_per_day=2)
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [1, 2, 2]


def test_apply_max_pass_no_sink_overflow():
    state = state_from_counts([0, 0, 40], start_day=1)
    apply_max_pass(state, max_per_day=16)
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 16, 16]
    sink_overflow = max(0, len(state.buckets[1]) - 16)
    assert sink_overflow == 0


def test_apply_max_pass_sink_overflow():
    state = state_from_counts([0, 0, 60], start_day=1)
    apply_max_pass(state, max_per_day=16)
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

    apply_max_pass(state, max_per_day=3)

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
    apply_max_pass(state, max_per_day=3)
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
    apply_max_pass(state, max_per_day=0)
    assert state.buckets[10] == []
    assert state.buckets[9] == [1]
    assert state.buckets[8] == []
    # Day 9 stays over max (1 card > max 0 there) -- no exception raised.


def test_apply_max_pass_invariants_no_later_moves_no_floor_breach_multiset():
    state = state_from_counts([0, 0, 0, 40], start_day=1)
    before_ids = all_ids(state.buckets)
    origin = dict(state.origin_by_id)

    apply_max_pass(state, max_per_day=16)

    after_ids = all_ids(state.buckets)
    assert after_ids == before_ids
    assert total_cards(state.buckets) == len(after_ids)
    for day, ids in state.buckets.items():
        assert day >= state.start_day
        for card_id in ids:
            assert day <= origin[card_id]  # never moved later


def test_apply_max_pass_idempotent_on_a_conforming_distribution():
    state = state_from_counts([5, 5, 5], start_day=1)
    apply_max_pass(state, max_per_day=5)
    snapshot = {day: list(ids) for day, ids in state.buckets.items()}
    apply_max_pass(state, max_per_day=5)
    assert state.buckets == snapshot


def test_apply_max_pass_deterministic():
    def run():
        state = state_from_counts([0, 0, 60], start_day=1)
        apply_max_pass(state, max_per_day=16)
        return {day: list(ids) for day, ids in state.buckets.items()}

    assert run() == run()


# ---------------------------------------------------------------------------
# 2.3 -- apply_reverse_max_pass
# ---------------------------------------------------------------------------


def test_apply_reverse_max_pass_resolves_sink_overflow_and_extends_horizon():
    state = state_from_counts([28, 16, 16], start_day=1)
    apply_reverse_max_pass(state, max_per_day=16)
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 12]
    assert state.end_day == 4
    assert total_cards(state.buckets) == 60


def test_apply_reverse_max_pass_multi_day_cascade_no_extension_needed():
    state = state_from_counts([40, 0, 0], start_day=1)
    apply_reverse_max_pass(state, max_per_day=16)
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [16, 16, 8]
    assert state.end_day == 3


def test_apply_reverse_max_pass_extends_beyond_the_original_horizon():
    state = state_from_counts([50], start_day=1)
    apply_reverse_max_pass(state, max_per_day=16)
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 2]
    assert state.end_day == 4


def test_apply_reverse_max_pass_only_ever_moves_cards_later():
    state = state_from_counts([28, 16, 16], start_day=1)
    before_days = {cid: day for day, ids in state.buckets.items() for cid in ids}

    apply_reverse_max_pass(state, max_per_day=16)

    after_days = {cid: day for day, ids in state.buckets.items() for cid in ids}
    moved_ids = [cid for cid in after_days if after_days[cid] != before_days[cid]]
    assert moved_ids  # sanity: this scenario does move cards
    for cid in moved_ids:
        assert after_days[cid] > before_days[cid]


def test_apply_reverse_max_pass_is_not_blocked_by_the_shift_cap():
    state = state_from_counts([28, 16, 16], start_day=1, max_shift=0)
    apply_reverse_max_pass(state, max_per_day=16)
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [16, 16, 16, 12]


def test_apply_reverse_max_pass_never_lands_below_start_day():
    state = state_from_counts([28, 16, 16], start_day=1)
    apply_reverse_max_pass(state, max_per_day=16)
    assert all(day >= state.start_day for day in state.buckets)
    # start_day itself ends exactly at max_per_day, having begun above it.
    assert len(state.buckets[1]) == 16


def test_apply_reverse_max_pass_multiset_preserved_and_deterministic():
    def run():
        state = state_from_counts([28, 16, 16], start_day=1)
        apply_reverse_max_pass(state, max_per_day=16)
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
    apply_min_pass(state, min_per_day=8)
    assert [len(state.buckets[d]) for d in (1, 2, 3, 4)] == [8, 15, 20, 20]


def test_apply_min_pass_cascades_through_and_disturbs_an_at_minimum_day():
    state = state_from_counts([0, 8, 20], start_day=1)
    day2_originals = set(state.buckets[2])

    apply_min_pass(state, min_per_day=8)

    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 8, 12]
    # Day 2 gave up its original cards to day 1 and refilled from day 3 --
    # proves surplus-hunting (leaving at-minimum days undisturbed) is not
    # the implemented behaviour.
    assert set(state.buckets[2]) != day2_originals


def test_apply_min_pass_no_surplus_cascade():
    state = state_from_counts([0, 8, 8], start_day=1)
    apply_min_pass(state, min_per_day=8)
    assert [len(state.buckets[d]) for d in (1, 2, 3)] == [8, 8, 0]


def test_apply_min_pass_exempts_the_trailing_days():
    state = state_from_counts([8, 3], start_day=1)
    before = {day: list(ids) for day, ids in state.buckets.items()}
    apply_min_pass(state, min_per_day=8)
    after = {day: list(ids) for day, ids in state.buckets.items()}
    assert before == after


def test_apply_min_pass_shift_cap_leaves_a_day_short_without_raising():
    state = state_from_counts([0, 20], start_day=1, max_shift=0)
    apply_min_pass(state, min_per_day=8)
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

    apply_min_pass(state, min_per_day=8)

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
    apply_min_pass(state, min_per_day=2)
    assert set(state.buckets[1]) == {3, 4}
    assert set(state.buckets[2]) == {1, 2}


def test_apply_min_pass_invariants_no_later_moves_no_floor_breach_multiset():
    state = state_from_counts([3, 20, 20, 20], start_day=1)
    before_ids = all_ids(state.buckets)
    before_days = {cid: day for day, ids in state.buckets.items() for cid in ids}

    apply_min_pass(state, min_per_day=8)

    after_days = {cid: day for day, ids in state.buckets.items() for cid in ids}
    for card_id, day in after_days.items():
        assert day >= state.start_day
        assert day <= before_days[card_id]
    assert all_ids(state.buckets) == before_ids


def test_apply_min_pass_deterministic():
    def run():
        state = state_from_counts([3, 20, 20, 20], start_day=1)
        apply_min_pass(state, min_per_day=8)
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
