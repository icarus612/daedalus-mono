"""Pure rebalancing core for `anki-rebalance-due`.

Redistributes Anki review-queue due dates within a day window so that no
day holds fewer than `--min` or more than `--max` cards. Everything here is
plain data manipulation over card ids and day numbers - no Anki imports, no
collection access. `anki_tools/rebalance_due.py` is the only caller and owns
all Anki-specific plumbing.
"""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CardDue:
    card_id: int  # Anki card id
    day: int  # absolute due day number, i.e. the review-queue `due` column
    ivl: int  # current interval in days, used only as a move-selection tiebreak


@dataclass
class RunState:
    buckets: dict[int, list[int]]  # day -> card ids on it, kept ascending by card_id
    ivl_by_id: dict[int, int]  # card_id -> ivl
    origin_by_id: dict[int, int]  # card_id -> its ORIGINAL day, before any pass ran
    moved: set[int]  # card ids that have moved at least once THIS RUN
    start_day: int  # window start; nothing is ever placed before it
    end_day: int  # MUTABLE - the reverse pass may extend it
    max_shift: int | None  # cap on EARLIER displacement from origin; None = uncapped


@dataclass(frozen=True)
class RebalanceResult:
    moves: dict[int, int]  # card_id -> new_day, changed cards only
    before: dict[int, int]  # per-day counts, pre-pass
    after: dict[int, int]  # per-day counts, post-pass
    end_day: int  # final horizon (reverse pass may have extended it)
    sink_overflow: int  # how far start_day exceeded max_per_day after the
    # earlier-only max pass; 0 otherwise
    short_days: list[int]  # days left below min_per_day, excluding the exempt tail
    reverse_pass_used: bool  # whether --set-earlier actually fired


class InfeasibleRebalance(Exception):
    """Raised when --max cannot be satisfied without violating the earlier-only
    invariant and set_earlier is False (or, in the set_earlier=True case, the reverse
    pass still leaves days over max - a bug signal). Carries the offending days, their
    counts, and the reason (sink overflow vs shift cap)."""

    def __init__(self, days: list[int], counts: dict[int, int], reason: str) -> None:
        self.days = days
        self.counts = counts
        self.reason = reason
        super().__init__(
            f"cannot satisfy --max on day(s) {days} ({reason}); counts: {counts}"
        )


def validate_bounds(min_per_day: int | None, max_per_day: int | None) -> None:
    if min_per_day is None and max_per_day is None:
        raise ValueError("at least one of --min or --max must be given")
    if min_per_day is not None and min_per_day < 0:
        raise ValueError("--min must be >= 0")
    if max_per_day is not None and max_per_day < 1:
        raise ValueError("--max must be >= 1")
    if (
        min_per_day is not None
        and max_per_day is not None
        and min_per_day > max_per_day
    ):
        raise ValueError("--min must not exceed --max")


def build_buckets(cards: Sequence[CardDue], start_day: int) -> dict[int, list[int]]:
    for card in cards:
        if card.day < start_day:
            raise ValueError(
                f"card {card.card_id} has day {card.day}, "
                f"before start_day {start_day}"
            )
    if not cards:
        return {}
    end_day = max(card.day for card in cards)
    buckets: dict[int, list[int]] = {day: [] for day in range(start_day, end_day + 1)}
    for card in cards:
        buckets[card.day].append(card.card_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def max_move_order(card_ids: Sequence[int], state: RunState) -> list[int]:
    return sorted(
        card_ids,
        key=lambda cid: (cid in state.moved, -state.ivl_by_id[cid], cid),
    )


def min_move_order(card_ids: Sequence[int], state: RunState) -> list[int]:
    return sorted(
        card_ids,
        key=lambda cid: (cid in state.moved, state.ivl_by_id[cid], cid),
    )


def may_move_to(card_id: int, target_day: int, state: RunState) -> bool:
    if target_day < state.start_day:
        return False
    return not (
        state.max_shift is not None
        and target_day < state.origin_by_id[card_id] - state.max_shift
    )


def move_card(card_id: int, from_day: int, to_day: int, state: RunState) -> None:
    state.buckets[from_day].remove(card_id)
    if to_day not in state.buckets:
        state.buckets[to_day] = []
    state.end_day = max(state.end_day, to_day)
    bucket = state.buckets[to_day]
    bucket.append(card_id)
    bucket.sort()
    state.moved.add(card_id)


def apply_max_pass(state: RunState, max_per_day: int) -> None:
    for d in range(state.end_day, state.start_day, -1):
        excess = len(state.buckets[d]) - max_per_day
        if excess <= 0:
            continue
        moved_here = 0
        for cid in max_move_order(state.buckets[d], state):
            if moved_here == excess:
                break
            if may_move_to(cid, d - 1, state):
                move_card(cid, d, d - 1, state)
                moved_here += 1


def apply_reverse_max_pass(state: RunState, max_per_day: int) -> None:
    d = state.start_day
    while True:
        excess = len(state.buckets[d]) - max_per_day
        if excess > 0:
            for cid in max_move_order(state.buckets[d], state)[:excess]:
                move_card(cid, d, d + 1, state)
        if d >= state.end_day and len(state.buckets.get(d + 1, [])) == 0:
            break
        d += 1


def _reached_exempt_tail(state: RunState, d: int) -> bool:
    """True once every day beyond d is empty - the trailing tail where the
    min pass (and the short_days report) stop enforcing --min (D6.1's "the
    tail is exempt" rule). Shared by apply_min_pass and _short_days so the
    two never drift out of sync."""
    return all(
        len(state.buckets.get(day, [])) == 0 for day in range(d + 1, state.end_day + 1)
    )


def apply_min_pass(state: RunState, min_per_day: int) -> None:
    for d in range(state.start_day, state.end_day + 1):
        if _reached_exempt_tail(state, d):
            break
        deficit = min_per_day - len(state.buckets[d])
        if deficit <= 0:
            continue
        for _ in range(deficit):
            picked: tuple[int, int] | None = None
            for s in range(d + 1, state.end_day + 1):
                source = state.buckets.get(s)
                if not source:
                    continue
                for cid in min_move_order(source, state):
                    if may_move_to(cid, d, state):
                        picked = (cid, s)
                        break
                if picked is not None:
                    break
            if picked is None:
                break
            cid, s = picked
            move_card(cid, s, d, state)


def _days_over_max(state: RunState, max_per_day: int) -> list[int]:
    return [
        d
        for d in range(state.start_day, state.end_day + 1)
        if len(state.buckets.get(d, [])) > max_per_day
    ]


def _infeasible_reason(state: RunState, over_max: Sequence[int]) -> str:
    if state.start_day in over_max:
        return "sink overflow"
    return "shift cap"


def _short_days(state: RunState, min_per_day: int | None) -> list[int]:
    if min_per_day is None:
        return []
    short: list[int] = []
    for d in range(state.start_day, state.end_day + 1):
        if _reached_exempt_tail(state, d):
            break
        if len(state.buckets.get(d, [])) < min_per_day:
            short.append(d)
    return short


def _check_post_conditions(
    state: RunState,
    max_per_day: int | None,
    max_shift: int | None,
    set_earlier: bool,
    reverse_pass_used: bool,
) -> None:
    all_ids = [cid for ids in state.buckets.values() for cid in ids]
    if len(all_ids) != len(set(all_ids)):
        raise AssertionError("duplicate card id present across buckets")
    if set(all_ids) != set(state.origin_by_id):
        raise AssertionError("multiset of card ids not preserved")
    if len(all_ids) != len(state.origin_by_id):
        raise AssertionError("card count changed")

    current_day_by_id = {cid: day for day, ids in state.buckets.items() for cid in ids}

    for cid, day in current_day_by_id.items():
        if day < state.start_day:
            raise AssertionError(f"card {cid} landed below start_day {state.start_day}")

    for cid in state.moved:
        origin = state.origin_by_id[cid]
        new_day = current_day_by_id[cid]
        if not set_earlier:
            if new_day >= origin:
                raise AssertionError(
                    f"card {cid} did not move strictly earlier: "
                    f"origin {origin}, new day {new_day}"
                )
        elif new_day > origin and not reverse_pass_used:
            raise AssertionError(f"card {cid} moved later without a reverse pass")

    if max_per_day is not None:
        for d in range(state.start_day, state.end_day + 1):
            if len(state.buckets.get(d, [])) > max_per_day:
                raise AssertionError(
                    f"day {d} holds more than max_per_day {max_per_day}"
                )

    if max_shift is not None:
        for cid, origin in state.origin_by_id.items():
            new_day = current_day_by_id[cid]
            if new_day < origin - max_shift:
                raise AssertionError(
                    f"card {cid} shifted earlier than max_shift {max_shift} allows"
                )


def plan_rebalance(
    cards: Sequence[CardDue],
    start_day: int,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None = 14,
    set_earlier: bool = False,
) -> RebalanceResult:
    validate_bounds(min_per_day, max_per_day)

    if not cards:
        return RebalanceResult(
            moves={},
            before={},
            after={},
            end_day=start_day - 1,
            sink_overflow=0,
            short_days=[],
            reverse_pass_used=False,
        )

    buckets = build_buckets(cards, start_day)
    end_day = max(card.day for card in cards)
    state = RunState(
        buckets=buckets,
        ivl_by_id={card.card_id: card.ivl for card in cards},
        origin_by_id={card.card_id: card.day for card in cards},
        moved=set(),
        start_day=start_day,
        end_day=end_day,
        max_shift=max_shift,
    )
    before = {day: len(ids) for day, ids in state.buckets.items()}

    sink_overflow = 0
    reverse_pass_used = False

    if max_per_day is not None:
        apply_max_pass(state, max_per_day)
        sink_overflow = max(0, len(state.buckets[state.start_day]) - max_per_day)
        over_max = _days_over_max(state, max_per_day)
        if over_max:
            if not set_earlier:
                raise InfeasibleRebalance(
                    over_max,
                    {d: len(state.buckets[d]) for d in over_max},
                    _infeasible_reason(state, over_max),
                )
            apply_reverse_max_pass(state, max_per_day)
            reverse_pass_used = True
            over_max = _days_over_max(state, max_per_day)
            if over_max:
                raise InfeasibleRebalance(
                    over_max,
                    {d: len(state.buckets[d]) for d in over_max},
                    _infeasible_reason(state, over_max),
                )

    if min_per_day is not None:
        apply_min_pass(state, min_per_day)

    after = {day: len(ids) for day, ids in state.buckets.items()}
    moves = {
        cid: day
        for day, ids in state.buckets.items()
        for cid in ids
        if day != state.origin_by_id[cid]
    }
    short_days = _short_days(state, min_per_day)

    _check_post_conditions(
        state, max_per_day, max_shift, set_earlier, reverse_pass_used
    )

    return RebalanceResult(
        moves=moves,
        before=before,
        after=after,
        end_day=state.end_day,
        sink_overflow=sink_overflow,
        short_days=short_days,
        reverse_pass_used=reverse_pass_used,
    )
