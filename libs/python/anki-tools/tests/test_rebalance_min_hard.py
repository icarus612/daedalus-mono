"""Contract tests: --min is a hard per-day bound, like --max (packet P3)."""

import os
import random
import sys
from collections import Counter

import pytest
from anki.collection import Collection

from anki_tools import due_stats, rebalance_due
from anki_tools.due_plan import (
    CardDue,
    InfeasibleRebalance,
    RunState,
    _enforce_hard_bounds,
    apply_min_pass,
    check_feasibility,
    constant_targets,
    plan_rebalance,
)

REPRO_COUNTS = [9, 6, 5, 5, 3, 2, 0, 0, 1, 1]
DECK = "programming::coding"


def cards_from_counts(counts, start_day, ivl=1):
    cards = []
    next_id = 1
    for offset, count in enumerate(counts):
        for _ in range(count):
            cards.append(CardDue(next_id, start_day + offset, ivl + next_id % 7))
            next_id += 1
    return cards


def _final_counts(cards, result):
    final = Counter()
    for card in cards:
        final[result.moves.get(card.card_id, card.day)] += 1
    return final


def _state(buckets, start_day, **kwargs):
    day_by_id = {cid: d for d, ids in buckets.items() for cid in ids}
    all_ids = list(day_by_id)
    return RunState(
        buckets={d: list(ids) for d, ids in buckets.items()},
        ivl_by_id={cid: 1 for cid in all_ids},
        origin_by_id=dict(day_by_id),
        day_by_id=dict(day_by_id),
        moved=set(),
        start_day=start_day,
        end_day=max(buckets),
        max_shift=kwargs.get("max_shift"),
        max_end_day=kwargs.get("max_end_day"),
        siblings_by_id=kwargs.get("siblings_by_id", {}),
        separation_by_id=kwargs.get("separation_by_id", {}),
        seed=0,
        horizon_ceiling=None,
    )


def _state_from_counts(counts, start_day, **kwargs):
    buckets = {}
    next_id = 1
    for offset, count in enumerate(counts):
        buckets[start_day + offset] = list(range(next_id, next_id + count))
        next_id += count
    return _state(buckets, start_day, **kwargs)


def _sizes(state):
    return [len(state.buckets[d]) for d in sorted(state.buckets)]


def _add_card(col, deck_id, *, due, ivl=30):
    note = col.new_note(col.models.by_name("Basic"))
    note["Front"] = "q"
    note["Back"] = "a"
    col.add_note(note, deck_id)
    card = note.cards()[0]
    card.type = 2
    card.queue = 2
    card.due = due
    card.ivl = ivl
    card.factor = 2500
    card.reps = 3
    col.update_card(card)
    return card


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["anki-rebalance-due"] + list(argv))
    try:
        rebalance_due.main()
    except SystemExit as exc:
        return exc.code
    return 0


def _snapshot_due_ivl(col_path, card_ids):
    col = Collection(col_path)
    try:
        return {cid: (col.get_card(cid).due, col.get_card(cid).ivl) for cid in card_ids}
    finally:
        col.close()


def _build_collection(tmp_path, offset_counts):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    deck_id = col.decks.id(DECK)
    today = col.sched.today
    ids = []
    for offset, count in offset_counts:
        for i in range(count):
            ids.append(_add_card(col, deck_id, due=today + offset, ivl=10 + i).id)
    col.close()
    return col_path, ids, today


def _due_counts(col_path, ids):
    col = Collection(col_path)
    try:
        return Counter(col.get_card(cid).due for cid in ids), col.sched.today
    finally:
        col.close()


# 1 -- pure core repro


def test_repro_shape_every_day_within_hard_min_and_max():
    cards = cards_from_counts(REPRO_COUNTS, start_day=1)
    assert len(cards) == 32
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=3,
        max_per_day=4,
        max_shift=14,
        set_earlier=True,
        end_day=10,
    )
    final = _final_counts(cards, result)
    assert sum(final[d] for d in range(1, 11)) == 32
    assert all(final[d] in (3, 4) for d in range(1, 11))
    assert result.short_days == []


def test_flat_mode_short_days_always_empty_on_return():
    cards = cards_from_counts([6, 6, 6], start_day=1)
    result = plan_rebalance(
        cards, start_day=1, min_per_day=4, max_per_day=8, max_shift=14
    )
    assert result.short_days == []


# 2, 3 -- planner raises "min unmet"


def test_trailing_short_day_raises_min_unmet_with_day_listed():
    cards = cards_from_counts([8, 3], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc:
        plan_rebalance(
            cards,
            start_day=1,
            min_per_day=8,
            max_per_day=None,
            max_shift=14,
            set_earlier=False,
        )
    assert "min unmet" in exc.value.reason
    assert 2 in exc.value.days


def test_shift_cap_blocking_fill_raises_min_unmet():
    cards = cards_from_counts([0, 20], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc:
        plan_rebalance(cards, start_day=1, min_per_day=8, max_per_day=None, max_shift=0)
    assert "min unmet" in exc.value.reason


# 4 -- sliding


def test_sliding_never_returns_a_day_below_min():
    cards = cards_from_counts([10] * 6, start_day=1)
    result = plan_rebalance(
        cards,
        start_day=1,
        min_per_day=8,
        max_per_day=16,
        max_shift=14,
        sliding=True,
    )
    final = _final_counts(cards, result)
    for day in range(1, result.end_day + 1):
        assert 8 <= final[day] <= 16


# 5, 6 -- CLI parsing


def test_parse_range_span():
    assert rebalance_due.parse_range("0-10") == (0, 10)


def test_parse_range_single_zero():
    assert rebalance_due.parse_range("0") == (0, 0)


def test_parse_range_negative_start_is_malformed():
    with pytest.raises(ValueError):
        rebalance_due.parse_range("-1-5")


def test_rebalance_due_parser_start_offset_defaults_to_zero():
    args = rebalance_due.build_parser().parse_args(["programming"])
    assert args.start_offset == 0


def test_due_stats_parser_start_offset_defaults_to_zero():
    args = due_stats.build_parser().parse_args(["programming"])
    assert args.start_offset == 0


# 7 -- e2e apply


def test_e2e_apply_repro_shape_every_offset_within_bounds(tmp_path, monkeypatch):
    col_path, ids, _ = _build_collection(
        tmp_path, [(i + 1, n) for i, n in enumerate(REPRO_COUNTS)]
    )
    code = _run_cli(
        [
            "programming",
            "--range",
            "1-10",
            "--min",
            "3",
            "--max",
            "4",
            "--set-earlier",
            "--yes",
            "--no-backup",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert code == 0
    counts, today = _due_counts(col_path, ids)
    assert sum(counts.values()) == 32
    assert all(counts[today + off] in (3, 4) for off in range(1, 11))


# 8 -- e2e infeasible


def test_e2e_planner_infeasible_exits_nonzero_and_writes_nothing(tmp_path, monkeypatch):
    col_path, ids, _ = _build_collection(tmp_path, [(2, 20)])
    before = _snapshot_due_ivl(col_path, ids)
    code = _run_cli(
        [
            "programming",
            "--range",
            "1-2",
            "--min",
            "8",
            "--max-shift",
            "0",
            "--yes",
            "--no-backup",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert code != 0
    assert _snapshot_due_ivl(col_path, ids) == before


def test_e2e_precheck_infeasible_exits_nonzero_and_writes_nothing(
    tmp_path, monkeypatch
):
    col_path, ids, _ = _build_collection(tmp_path, [(1, 20), (2, 20)])
    before = _snapshot_due_ivl(col_path, ids)
    code = _run_cli(
        [
            "programming",
            "--range",
            "1-2",
            "--max",
            "5",
            "--yes",
            "--no-backup",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert code != 0
    assert _snapshot_due_ivl(col_path, ids) == before


# 9 -- today inclusive


@pytest.mark.parametrize("range_args", [["--range", "0-3"], []])
def test_e2e_card_due_today_in_scope_overdue_untouched(
    tmp_path, monkeypatch, range_args
):
    col_path, ids, today = _build_collection(tmp_path, [(0, 1), (1, 3), (-1, 1)])
    in_scope_ids, overdue_ids = ids[:4], ids[4:]
    before = _snapshot_due_ivl(col_path, ids)
    code = _run_cli(
        ["programming", *range_args, "--max", "2", "--yes", "--no-backup"]
        + ["--collection", col_path],
        monkeypatch,
    )
    assert code == 0
    after = _snapshot_due_ivl(col_path, ids)
    assert sum(1 for cid in in_scope_ids if after[cid][0] == today) == 2
    assert all(after[cid] == before[cid] for cid in overdue_ids)


# 10 -- unit: _enforce_hard_bounds


def test_enforce_hard_bounds_max_unmet():
    state = _state_from_counts([3, 6, 3], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc:
        _enforce_hard_bounds(state, 3, 4)
    assert "max unmet" in exc.value.reason
    assert 2 in exc.value.days


def test_enforce_hard_bounds_min_unmet_reported_before_max():
    state = _state_from_counts([6, 2], start_day=1)
    with pytest.raises(InfeasibleRebalance) as exc:
        _enforce_hard_bounds(state, 3, 4)
    assert "min unmet" in exc.value.reason
    assert 2 in exc.value.days


def test_enforce_hard_bounds_accepts_conforming_and_none_bounds():
    state = _state_from_counts([3, 4, 3], start_day=1)
    _enforce_hard_bounds(state, 3, 4)
    _enforce_hard_bounds(state, None, None)
    _enforce_hard_bounds(_state_from_counts([0, 9], start_day=1), None, None)


# 10 -- unit: apply_min_pass


def _floor(state, value):
    return constant_targets(state.start_day, state.end_day + 1000, value)


def test_apply_min_pass_without_set_earlier_never_moves_later():
    state = _state_from_counts([10, 0], start_day=1)
    moved = apply_min_pass(state, _floor(state, 3), False)
    assert moved is False
    assert _sizes(state) == [10, 0]


def test_apply_min_pass_fills_from_later_days_first():
    state = _state_from_counts([0, 5], start_day=1)
    moved = apply_min_pass(state, _floor(state, 3), True)
    assert moved is False
    assert _sizes(state) == [3, 2]


def test_apply_min_pass_borrows_from_nearest_earlier_surplus_above_floor():
    state = _state_from_counts([5, 5, 0], start_day=1)
    moved = apply_min_pass(state, _floor(state, 3), True)
    assert moved is True
    assert _sizes(state) == [4, 3, 3]


def test_apply_min_pass_never_borrows_below_earlier_days_floor():
    state = _state_from_counts([3, 3, 0], start_day=1)
    moved = apply_min_pass(state, _floor(state, 3), True)
    assert moved is False
    assert _sizes(state) == [3, 3, 0]


def test_apply_min_pass_skips_separation_blocked_candidate():
    state = _state(
        {1: [1, 2], 2: [3, 4, 5], 3: [7]},
        start_day=1,
        siblings_by_id={3: [7], 7: [3]},
        separation_by_id={3: 5, 7: 5},
    )
    moved = apply_min_pass(state, _floor(state, 2), True)
    assert moved is True
    assert state.day_by_id[3] == 2
    assert state.day_by_id[7] == 3
    assert sorted(state.buckets[3]) in ([4, 7], [5, 7])
    assert _sizes(state) == [2, 2, 2]


def test_apply_min_pass_respects_max_end_day():
    state = _state_from_counts([5, 5, 0], start_day=1, max_end_day=2)
    moved = apply_min_pass(state, _floor(state, 3), True)
    assert moved is False
    assert _sizes(state) == [5, 5, 0]


# 11 -- precheck vs planner agreement


def _grid_cases():
    rng = random.Random(20260511)
    cases = []
    for _ in range(60):
        counts = [rng.randint(0, 8) for _ in range(rng.randint(3, 6))]
        min_per_day = rng.choice([None, 2, 3])
        max_per_day = rng.choice([3, 4, 6])
        if min_per_day is not None and min_per_day > max_per_day:
            continue
        cases.append(
            (
                counts,
                min_per_day,
                max_per_day,
                rng.choice([0, 2, None]),
                rng.choice([False, True]),
                rng.choice([False, True]),
            )
        )
    return cases


@pytest.mark.parametrize(
    "counts,min_per_day,max_per_day,max_shift,set_earlier,use_end_day",
    _grid_cases(),
)
def test_precheck_infeasible_implies_planner_raises_and_return_is_in_bounds(
    counts, min_per_day, max_per_day, max_shift, set_earlier, use_end_day
):
    cards = cards_from_counts(counts, start_day=1)
    end_day = len(counts) if use_end_day else None
    report = check_feasibility(
        cards,
        start_day=1,
        end_day=end_day,
        min_per_day=min_per_day,
        max_per_day=max_per_day,
        max_shift=max_shift,
        set_earlier=set_earlier,
    )
    try:
        result = plan_rebalance(
            cards,
            start_day=1,
            min_per_day=min_per_day,
            max_per_day=max_per_day,
            max_shift=max_shift,
            set_earlier=set_earlier,
            end_day=end_day,
        )
    except InfeasibleRebalance:
        return
    assert report.feasible is True
    final = _final_counts(cards, result)
    for day in range(1, result.end_day + 1):
        if min_per_day is not None:
            assert final[day] >= min_per_day
        assert final[day] <= max_per_day
