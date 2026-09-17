"""Pure rebalancing core for `anki-rebalance-due`.

Redistributes Anki review-queue due dates within a day window so that no
day holds fewer than `--min` or more than `--max` cards. Everything here is
plain data manipulation over card ids and day numbers - no Anki imports, no
collection access. `anki_tools/rebalance_due.py` is the only caller and owns
all Anki-specific plumbing.

Phase 6 adds: a pure feasibility precheck (`check_feasibility` and its two
legs, `check_hard_feasibility` / `analyze_shape`), explicit range windowing
(`RunState.max_end_day`, `may_move_later_to`), and sliding-target shaping
(`build_target_line`, `apply_shape_pass`). The three original passes and
`plan_rebalance`'s orchestration now take per-day `DayTargets` mappings
instead of scalar bounds; `constant_targets` reproduces the pre-Phase-6
scalar behaviour exactly.

Phase 7 adds: active sibling-separation repair (`apply_separation_repair_pass`)
and a horizon safety ceiling (`RunState.horizon_ceiling`) independent of
`--range`.
"""

import math
import random
from bisect import bisect_left
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CardDue:
    card_id: int  # Anki card id
    day: int  # absolute due day number, i.e. the review-queue `due` column
    ivl: int  # current interval in days, used only as a move-selection tiebreak
    note_id: int | None = None  # sibling-grouping key; None = no sibling info
    min_separation: int = 0  # required days from any sibling; 0 = disabled


@dataclass
class RunState:
    buckets: dict[int, list[int]]  # day -> card ids on it, kept ascending by card_id
    ivl_by_id: dict[int, int]  # card_id -> ivl
    origin_by_id: dict[int, int]  # card_id -> its ORIGINAL day, before any pass ran
    moved: set[int]  # card ids that have moved at least once THIS RUN
    start_day: int  # window start; nothing is ever placed before it
    end_day: int  # MUTABLE - the reverse pass may extend it (unless max_end_day set)
    max_shift: int | None  # cap on EARLIER displacement from origin; None = uncapped
    max_end_day: (
        int | None
    )  # containment ceiling; None = unbounded (horizon may extend)
    # card_id -> its CURRENT day, kept live on every move (see separation_ok).
    day_by_id: dict[int, int] = field(default_factory=dict)
    # card_id -> other card ids sharing its note_id; absent means no siblings.
    siblings_by_id: dict[int, list[int]] = field(default_factory=dict)
    # card_id -> its resolved min_separation, read through .get(cid, 0) so a
    # card absent from the map is treated as unconstrained.
    separation_by_id: dict[int, int] = field(default_factory=dict)
    # Diagnostic: card ids most recently rejected specifically by separation
    # (see may_move_to / _infeasible_reason), never by start_day/max_shift.
    separation_blocked: set[int] = field(default_factory=set)
    seed: int = 0  # seeds the deterministic random tiebreak in *_move_order
    horizon_ceiling: int | None = None  # absolute day; None = no extra ceiling
    # beyond max_end_day. Set only by the caller when no explicit --range
    # was given (see may_move_later_to).


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
    over_target_days: list[int]  # days left above T(d) in sliding mode; [] in flat mode


class InfeasibleRebalance(Exception):
    """Raised when --max cannot be satisfied without violating the earlier-only
    invariant and set_earlier is False (or, in the set_earlier=True case, the reverse
    pass still leaves days over max - typically because --range's ceiling refuses
    the reverse pass, or a bug signal if no --range was given). Carries the
    offending days, their counts, and the reason (sink overflow vs min separation
    vs range ceiling vs shift cap).

    "min separation" (Phase 7): either excess left on a day after the
    max/reverse-max pass was refused every candidate specifically by the
    sibling-separation gate (recorded into `state.separation_blocked` by
    `may_move_to`/`apply_reverse_max_pass`), rather than by start_day or
    max_shift; OR a sibling pair still in violation after
    `apply_separation_repair_pass` could not be repaired at all (neither
    member had a legal earlier day, and - when set_earlier - the later
    member had no legal later day either). The latter is a placement-time
    vs. active-repair distinction, not a different failure mode: both
    report the same reason string since both mean separation could not be
    satisfied under the current bounds."""

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


def build_buckets(
    cards: Sequence[CardDue], start_day: int, end_day: int | None = None
) -> dict[int, list[int]]:
    """Group cards by day. `end_day`, when given, is an explicit window
    ceiling (range mode, 6.2): every card must land at or below it, and the
    returned dict spans every day in `[start_day, end_day]` even when empty.
    `end_day=None` (default) reproduces the pre-Phase-6 behaviour exactly:
    the ceiling is derived as the maximum card day, and an empty input
    returns `{}`."""
    for card in cards:
        if card.day < start_day:
            raise ValueError(
                f"card {card.card_id} has day {card.day}, before start_day {start_day}"
            )
        if end_day is not None and card.day > end_day:
            raise ValueError(
                f"card {card.card_id} has day {card.day}, after end_day {end_day}"
            )
    if not cards:
        if end_day is None:
            return {}
        return {day: [] for day in range(start_day, end_day + 1)}
    bucket_end = end_day if end_day is not None else max(card.day for card in cards)
    buckets: dict[int, list[int]] = {
        day: [] for day in range(start_day, bucket_end + 1)
    }
    for card in cards:
        buckets[card.day].append(card.card_id)
    for ids in buckets.values():
        ids.sort()
    return buckets


def max_move_order(card_ids: Sequence[int], state: RunState) -> list[int]:
    """Order for moving cards OFF a day. The largest-ivl card still goes
    first (a one-day nudge is proportionally smallest for it); ties are
    broken by a seeded random draw, `tie`, computed ONCE per call as
    `random.Random(hash((state.seed, cid))).random()` for each candidate - purely
    a function of `(seed, cid)`, never of call order or iteration order, so
    the same card gets the same draw regardless of which day or pass asks.

    This replaced an earlier per-deck round-robin rank term (removed):
    Anki card ids are creation timestamps, and a deck's cards are created
    (and reviewed, and thus ivl-tied) together, so the plain (ivl, card_id)
    tiebreak walked whole subdecks in creation order. A forced round-robin
    fixed that but was rejected in favor of picking among genuine ties at
    random.

    Because ties are now broken randomly rather than by ascending card id,
    the old claim that a single-group input reproduces the pre-diversity
    ordering exactly no longer holds in general - it still holds trivially
    whenever there are no genuine ties (every candidate has a distinct
    ivl), since then `tie` never enters the comparison."""

    def priority(cid: int) -> tuple[int, int]:
        return (-state.ivl_by_id[cid], cid)

    tie = {cid: random.Random(hash((state.seed, cid))).random() for cid in card_ids}
    return sorted(
        card_ids,
        key=lambda cid: (cid in state.moved, -state.ivl_by_id[cid], tie[cid], cid),
    )


def min_move_order(card_ids: Sequence[int], state: RunState) -> list[int]:
    """Order for pulling cards INTO a day. Ties are broken by the same
    seeded random draw as `max_move_order` (recomputed here, never shared
    across the two functions, since each call's `tie` is stateless and
    depends only on `(state.seed, cid)`).

    Because ties are now broken randomly rather than by ascending card id,
    the old claim that a single-group input reproduces the pre-diversity
    ordering exactly no longer holds in general - it still holds trivially
    whenever there are no genuine ties (every candidate has a distinct
    ivl), since then `tie` never enters the comparison."""
    tie = {cid: random.Random(hash((state.seed, cid))).random() for cid in card_ids}
    return sorted(
        card_ids,
        key=lambda cid: (cid in state.moved, state.ivl_by_id[cid], tie[cid], cid),
    )


def separation_ok(card_id: int, target_day: int, state: RunState) -> bool:
    """False iff placing `card_id` on `target_day` would land it within its
    resolved required separation of a sibling's CURRENT day. Always reads
    `state.day_by_id` - never a snapshot - since a sibling that has itself
    already moved this run must be checked at its new day, not its origin
    day. A card absent from `siblings_by_id` (no siblings, or its note_id
    was None) is always OK."""
    siblings = state.siblings_by_id.get(card_id)
    if not siblings:
        return True
    for sibling in siblings:
        required = max(
            state.separation_by_id.get(card_id, 0),
            state.separation_by_id.get(sibling, 0),
        )
        if required <= 0:
            continue
        sibling_day = state.day_by_id[sibling]
        if abs(target_day - sibling_day) < required:
            return False
    return True


def may_move_to(card_id: int, target_day: int, state: RunState) -> bool:
    if target_day < state.start_day:
        return False
    if (
        state.max_shift is not None
        and target_day < state.origin_by_id[card_id] - state.max_shift
    ):
        return False
    if not separation_ok(card_id, target_day, state):
        state.separation_blocked.add(card_id)
        return False
    return True


def may_move_later_to(target_day: int, state: RunState) -> bool:
    """Later-direction gate. False when either ceiling would be crossed:
    `max_end_day` (the explicit --range containment ceiling, set only when
    the caller gave an explicit range) or `horizon_ceiling` (a maxIvl-derived
    safety ceiling the caller sets only when no --range was given, so a
    later move still has SOME bound even without an explicit window)."""
    if state.max_end_day is not None and target_day > state.max_end_day:
        return False
    if state.horizon_ceiling is not None and target_day > state.horizon_ceiling:
        return False
    return True


def _clear_of_separation_at_or_before(card_id: int, day: int, state: RunState) -> int:
    """The largest day <= `day` where separation_ok(card_id, ..., state) holds,
    considering ONLY the separation gate (ignores start_day/max_shift entirely
    - callers check those separately against the result). Computed by
    repeatedly pushing `day` below whichever sibling's forbidden interval it
    currently falls inside, rather than scanning day by day. Converges in at
    most len(siblings) iterations: pushing past one sibling's zone can only
    ever land inside ANOTHER sibling's zone, never back into the first (each
    push strictly decreases `day`)."""
    siblings = state.siblings_by_id.get(card_id)
    if not siblings:
        return day
    changed = True
    while changed:
        changed = False
        for sibling in siblings:
            required = max(
                state.separation_by_id.get(card_id, 0),
                state.separation_by_id.get(sibling, 0),
            )
            if required <= 0:
                continue
            sibling_day = state.day_by_id[sibling]
            if abs(day - sibling_day) < required:
                day = sibling_day - required
                changed = True
    return day


def _clear_of_separation_at_or_after(card_id: int, day: int, state: RunState) -> int:
    """Symmetric to `_clear_of_separation_at_or_before`: the smallest day
    >= `day` that clears every sibling's forbidden zone."""
    siblings = state.siblings_by_id.get(card_id)
    if not siblings:
        return day
    changed = True
    while changed:
        changed = False
        for sibling in siblings:
            required = max(
                state.separation_by_id.get(card_id, 0),
                state.separation_by_id.get(sibling, 0),
            )
            if required <= 0:
                continue
            sibling_day = state.day_by_id[sibling]
            if abs(day - sibling_day) < required:
                day = sibling_day + required
                changed = True
    return day


def _first_legal_earlier_day(
    card_id: int, state: RunState, ceiling: "DayTargets | None", floor_day: int
) -> int | None:
    """The largest day >= floor_day, <= card_id's current day, that clears
    every sibling's separation zone AND has capacity headroom under
    `ceiling` (len(bucket) < ceiling[day], via the same
    `ceiling.get(day, ceiling[state.start_day])` fallback convention
    `apply_reverse_max_pass` already uses for days beyond the precomputed
    range). `ceiling=None` means no capacity ceiling to respect (mirrors
    "no --max given" everywhere else in this module). Returns None when no
    such day exists at or above floor_day. Repeatedly re-clears separation
    after every capacity-forced step down, since stepping past one
    sibling's zone can land inside another's."""
    day = state.day_by_id[card_id]
    while True:
        day = _clear_of_separation_at_or_before(card_id, day, state)
        if day < floor_day:
            return None
        if ceiling is None or len(state.buckets.get(day, [])) < ceiling.get(
            day, ceiling[state.start_day]
        ):
            return day
        day -= 1


def _first_legal_later_day(
    card_id: int, state: RunState, ceiling: "DayTargets | None"
) -> int | None:
    """Symmetric to `_first_legal_earlier_day` for the later direction.
    Bounded by `may_move_later_to` (both max_end_day and horizon_ceiling),
    never by max_shift - matches `_resolve_later_target`'s existing
    later-direction contract. Returns None when `may_move_later_to` refuses
    before capacity headroom is found."""
    day = state.day_by_id[card_id]
    while True:
        day = _clear_of_separation_at_or_after(card_id, day, state)
        if not may_move_later_to(day, state):
            return None
        if ceiling is None or len(state.buckets.get(day, [])) < ceiling.get(
            day, ceiling[state.start_day]
        ):
            return day
        day += 1


def _repair_pair(
    cid: int,
    sib: int,
    state: RunState,
    ceiling: "DayTargets | None",
    set_earlier: bool,
) -> tuple[bool, bool]:
    """Attempts to repair one currently-violating sibling pair. Identifies
    lo/hi by current day (lo = earlier or equal). Tries moving lo earlier
    first via `_first_legal_earlier_day`, bounded below by
    `max(state.start_day, state.origin_by_id[lo] - state.max_shift)` (or
    just `state.start_day` when `max_shift is None`) - cumulative from
    ORIGIN, exactly like every other earlier-direction move in this module.
    Only when that fails AND `set_earlier` is True, tries moving hi later
    via `_first_legal_later_day`. Returns `(repaired, moved_later)` -
    `moved_later` is True only when the hi branch actually fired. Never
    moves both members for one pair."""
    if state.day_by_id[cid] <= state.day_by_id[sib]:
        lo, hi = cid, sib
    else:
        lo, hi = sib, cid

    floor_day = state.start_day
    if state.max_shift is not None:
        floor_day = max(floor_day, state.origin_by_id[lo] - state.max_shift)

    target = _first_legal_earlier_day(lo, state, ceiling, floor_day)
    if target is not None:
        move_card(lo, state.day_by_id[lo], target, state)
        return True, False

    if set_earlier:
        target = _first_legal_later_day(hi, state, ceiling)
        if target is not None:
            move_card(hi, state.day_by_id[hi], target, state)
            return True, True

    return False, False


def apply_separation_repair_pass(
    state: RunState, ceiling: "DayTargets | None", set_earlier: bool
) -> tuple[set[int], bool]:
    """Actively relocates cards to fix sibling pairs that are ALREADY in
    violation at call time - this is not a placement gate, it is an active
    repair. Builds the pair list once from `state.siblings_by_id`
    (deduplicated, `cid < sib`, sorted for determinism), then makes exactly
    one forward pass: for each pair still violating at the moment it is
    visited (a prior pair's repair may have already fixed it - re-checked
    here, not assumed), calls `_repair_pair`. Returns
    `(unrepaired_card_ids, any_later_move_used)`. Groups of 3+ siblings are
    handled correctly: a repair move always targets a day clearing EVERY
    sibling of the card being moved (via `_clear_of_separation_at_or_*`),
    so fixing pair (a, b) can never silently leave (a, c) violating if c
    was already resolved."""
    pairs = sorted(
        {
            (min(cid, sib), max(cid, sib))
            for cid, sibs in state.siblings_by_id.items()
            for sib in sibs
        }
    )
    unrepaired: set[int] = set()
    moved_later = False
    for cid, sib in pairs:
        required = max(
            state.separation_by_id.get(cid, 0), state.separation_by_id.get(sib, 0)
        )
        if required <= 0:
            continue
        if abs(state.day_by_id[cid] - state.day_by_id[sib]) >= required:
            continue
        fixed, used_later = _repair_pair(cid, sib, state, ceiling, set_earlier)
        moved_later = moved_later or used_later
        if not fixed:
            unrepaired.add(cid)
            unrepaired.add(sib)
    return unrepaired, moved_later


def _resolve_earlier_target(
    card_id: int, ceiling_day: int, state: RunState
) -> int | None:
    """The day to actually move `card_id` to when the pass's preferred
    target is `ceiling_day` (normally one day earlier than its current
    bucket) but a legal day could be even earlier. Returns `ceiling_day`
    unchanged when it is already legal (the overwhelmingly common case: no
    siblings, or separation already satisfied). When only the separation
    gate blocks `ceiling_day`, jumps directly to the nearest earlier day
    that clears every sibling's forbidden zone, so a mover can leap past a
    stationary sibling's zone in one placement instead of being retried one
    day at a time by the pass's own day-by-day cascade - that cascade only
    ever advances by whatever step the CALLER requests, and separation's
    forbidden interval is usually far wider than one day. Returns None when
    no day within [start_day, origin - max_shift] (the same earlier-only
    bound `may_move_to` already enforces) clears every sibling - the
    caller's excess then stays unresolved on its origin day, which is what
    makes it visible to `_infeasible_reason`'s "min separation" branch.
    Records into `state.separation_blocked` only on total failure, never on
    an intermediate day probed while searching, so a successful jump never
    leaves behind a stale entry that could misattribute an unrelated later
    infeasibility."""
    if ceiling_day < state.start_day:
        return None
    floor_day = state.start_day
    if state.max_shift is not None:
        floor_day = max(floor_day, state.origin_by_id[card_id] - state.max_shift)
    if ceiling_day < floor_day:
        return None
    target = _clear_of_separation_at_or_before(card_id, ceiling_day, state)
    if target < floor_day:
        state.separation_blocked.add(card_id)
        return None
    return target


def _resolve_later_target(card_id: int, floor_day: int, state: RunState) -> int | None:
    """Symmetric to `_resolve_earlier_target`, for the reverse (later)
    direction: the day to move `card_id` to when the pass's preferred
    target is `floor_day` (normally one day later) but a legal day could be
    further out. Bounded by `may_move_later_to` (the containment ceiling),
    never by max_shift - the reverse pass ignores max_shift by design, same
    as it always has."""
    if not may_move_later_to(floor_day, state):
        return None
    target = _clear_of_separation_at_or_after(card_id, floor_day, state)
    if not may_move_later_to(target, state):
        state.separation_blocked.add(card_id)
        return None
    return target


def move_card(card_id: int, from_day: int, to_day: int, state: RunState) -> None:
    state.buckets[from_day].remove(card_id)
    if to_day not in state.buckets:
        state.buckets[to_day] = []
    state.end_day = max(state.end_day, to_day)
    bucket = state.buckets[to_day]
    bucket.append(card_id)
    bucket.sort()
    state.moved.add(card_id)
    state.day_by_id[card_id] = to_day


# DayTargets: day -> per-day number, defined for every day in the window.
DayTargets = Mapping[int, int]


def constant_targets(start_day: int, end_day: int, value: int) -> dict[int, int]:
    return {day: value for day in range(start_day, end_day + 1)}


def apply_max_pass(state: RunState, ceiling: DayTargets) -> None:
    for d in range(state.end_day, state.start_day, -1):
        excess = len(state.buckets[d]) - ceiling[d]
        if excess <= 0:
            continue
        moved_here = 0
        for cid in max_move_order(state.buckets[d], state):
            if moved_here == excess:
                break
            target = _resolve_earlier_target(cid, d - 1, state)
            if target is None:
                continue
            move_card(cid, d, target, state)
            moved_here += 1


def apply_reverse_max_pass(state: RunState, ceiling: DayTargets) -> None:
    d = state.start_day
    while True:
        # ceiling is built over the pre-pass horizon; this pass can push
        # state.end_day past that range, so fall back to the uniform
        # start-day value for any day the ceiling doesn't (yet) cover.
        excess = len(state.buckets[d]) - ceiling.get(d, ceiling[state.start_day])
        if excess > 0:
            moved_here = 0
            for cid in max_move_order(state.buckets[d], state):
                if moved_here == excess:
                    break
                target = _resolve_later_target(cid, d + 1, state)
                if target is None:
                    continue
                move_card(cid, d, target, state)
                moved_here += 1
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


def apply_min_pass(state: RunState, floor: DayTargets) -> None:
    for d in range(state.start_day, state.end_day + 1):
        if _reached_exempt_tail(state, d):
            break
        deficit = floor[d] - len(state.buckets[d])
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


def apply_shape_pass(
    state: RunState, target: DayTargets, hard_ceiling: DayTargets
) -> None:
    """Sliding only. Shapes DOWNWARD toward `target` without ever breaching
    `hard_ceiling`. The break on a full receiver is a REFUSAL that stops
    shaping day `d` and moves the sweep on - it never looks at `d - 2`.
    Never raises; days still above `target[d]` on exit become
    `over_target_days`.

    Unlike `apply_max_pass`, this never jumps past a sibling's separation
    zone - it still only ever tries `d - 1` (via `may_move_to`, which
    already refuses a separation-blocked target rather than violating it),
    so a card stuck behind a wide separation zone is left in place the same
    as any other refusal, which may surface as `over_target_days`. This is
    a deliberate scope boundary, not an oversight: sliding mode is already
    documented as best-effort."""
    for d in range(state.end_day, state.start_day, -1):
        while len(state.buckets[d]) > target[d]:
            if len(state.buckets[d - 1]) >= hard_ceiling[d - 1]:
                break  # receiver is AT the hard cap -> refusal, not a skip
            mover: int | None = None
            for cid in max_move_order(state.buckets[d], state):
                if may_move_to(cid, d - 1, state):
                    mover = cid
                    break
            if mover is None:
                break  # shift cap blocks every remaining candidate on this day
            move_card(mover, d, d - 1, state)


def build_target_line(
    start_day: int, end_day: int, min_per_day: int, max_per_day: int
) -> dict[int, int]:
    """T(d) = floor(max - (max - min) * (d - start_day) / (end_day - start_day) + 0.5).

    Rounding is floor(x + 0.5), NOT Python's round() (banker's rounding would
    make T depend on parity) - pinned, not incidental. Degenerate window
    (end_day == start_day) returns {start_day: max_per_day}, no division.
    Endpoints exact by construction: T(start_day) == max_per_day,
    T(end_day) == min_per_day.
    """
    if end_day == start_day:
        return {start_day: max_per_day}
    span = end_day - start_day
    spread = max_per_day - min_per_day
    line: dict[int, int] = {}
    for d in range(start_day, end_day + 1):
        raw = max_per_day - spread * (d - start_day) / span
        line[d] = math.floor(raw + 0.5)
    return line


def fit_target_line(
    line: dict[int, int], total_cards: int, max_per_day: int
) -> dict[int, int]:
    """Raise a ramp until it can actually hold `total_cards`.

    A ramp from max down to min holds roughly span * (max + min) / 2 cards.
    When the deck holds MORE than that, the shape pass has nowhere legal to
    put the surplus: every day is already at its target, so the excess stays
    wherever it originated. In practice that means it lands on the far tail
    (year-interval cards originate there and can only move earlier), which
    reads as a wall of max-height days at the end of the year - the exact
    thing the ramp exists to prevent.

    Spreading the shortfall EVENLY is what keeps the result "as close to the
    ramp as possible": distribute the deficit one card at a time across
    evenly-spaced days, never exceeding the hard `max_per_day`, so the slope
    is preserved and the surplus is invisible rather than piled in one place.

    Returns the line unchanged when it already has the capacity.
    """
    days = sorted(line)
    capacity = sum(line[d] for d in days)
    deficit = total_cards - capacity
    if deficit <= 0:
        return line

    fitted = dict(line)
    # Rounds of evenly-spaced +1s. Each round walks every day that still has
    # headroom under the hard cap, so growth stays proportional to the shape
    # rather than front- or back-loading the surplus.
    while deficit > 0:
        headroom = [d for d in days if fitted[d] < max_per_day]
        if not headroom:
            break  # genuinely cannot fit under --max; caller reports it
        step = max(1, len(headroom) // deficit) if deficit < len(headroom) else 1
        for i in range(0, len(headroom), step):
            if deficit <= 0:
                break
            fitted[headroom[i]] += 1
            deficit -= 1
    return fitted


def _days_over_max(state: RunState, max_per_day: int) -> list[int]:
    return [
        d
        for d in range(state.start_day, state.end_day + 1)
        if len(state.buckets.get(d, [])) > max_per_day
    ]


def _infeasible_reason(
    state: RunState, over_max: Sequence[int], reverse_pass_used: bool = False
) -> str:
    """Distinguishes the four ways --max can remain unsatisfied.

    "sink overflow": start_day itself is still over max_per_day - nowhere
    earlier to push excess cards.
    "min separation": some card left on an over-max day was refused every
    candidate move specifically by the sibling-separation gate (present in
    `state.separation_blocked`) - checked before the range/shift-cap
    reasons below so a separation-caused rejection is never misreported as
    one of those.
    "range ceiling": only reachable once the reverse pass has run
    (`reverse_pass_used`) - apply_reverse_max_pass is gated purely by
    `may_move_later_to` (`max_end_day` and/or `horizon_ceiling`), never by
    max_shift, so excess left over after it ran was refused by one of those
    later-direction ceilings, not by --max-shift. Reachable whether the
    ceiling in play is an explicit --range (`max_end_day`) or the implicit
    maxIvl-derived safety ceiling used when no --range was given
    (`horizon_ceiling`) - reporting "shift cap" in the latter case would be
    wrong, since max_shift never gates the reverse pass at all.
    "shift cap": the earlier-only apply_max_pass left excess in place
    because `may_move_to`'s max_shift gate blocked every candidate - the
    only case reachable before any reverse pass has run.
    """
    if state.start_day in over_max:
        return "sink overflow"
    if any(
        cid in state.separation_blocked
        for d in over_max
        for cid in state.buckets.get(d, [])
    ):
        return "min separation"
    if reverse_pass_used and (
        state.max_end_day is not None or state.horizon_ceiling is not None
    ):
        return "range ceiling"
    return "shift cap"


def _short_days(state: RunState, floor: DayTargets | None) -> list[int]:
    if floor is None:
        return []
    short: list[int] = []
    for d in range(state.start_day, state.end_day + 1):
        if _reached_exempt_tail(state, d):
            break
        if len(state.buckets.get(d, [])) < floor[d]:
            short.append(d)
    return short


def _check_post_conditions(
    state: RunState,
    max_per_day: int | None,
    max_shift: int | None,
    set_earlier: bool,
    later_move_used: bool,
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
        if state.max_end_day is not None and day > state.max_end_day:
            raise AssertionError(
                f"card {cid} landed above max_end_day {state.max_end_day}"
            )

    for cid in state.moved:
        origin = state.origin_by_id[cid]
        new_day = current_day_by_id[cid]
        # horizon_ceiling, unlike max_end_day, has no input-side validation
        # (build_buckets never checks it): a pre-existing card's ORIGIN day
        # may already sit beyond it for reasons unrelated to this run (a
        # stale due date, a since-tightened maxIvl preset). The hard rule is
        # that this tool never PUSHES a card later past the ceiling, not
        # that no card may ever already be there -- so this only fires when
        # a move actually carried a card later past it, never for an
        # untouched card or one this run moved earlier (even if it's still
        # beyond the ceiling afterward, unmoved-forward, that's an
        # improvement or a no-op, never a new violation this run caused).
        if (
            state.horizon_ceiling is not None
            and new_day > origin
            and new_day > state.horizon_ceiling
        ):
            raise AssertionError(
                f"card {cid} was pushed later past horizon_ceiling "
                f"{state.horizon_ceiling}"
            )
        if not set_earlier:
            if new_day >= origin:
                raise AssertionError(
                    f"card {cid} did not move strictly earlier: "
                    f"origin {origin}, new day {new_day}"
                )
        elif new_day > origin and not later_move_used:
            raise AssertionError(
                f"card {cid} moved later without a sanctioned later-mover "
                "(reverse pass or separation repair)"
            )

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

    if state.max_end_day is not None and state.end_day != state.max_end_day:
        raise AssertionError(
            f"end_day {state.end_day} != max_end_day {state.max_end_day} in range mode"
        )


def plan_rebalance(
    cards: Sequence[CardDue],
    start_day: int,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None = 14,
    set_earlier: bool = False,
    sliding: bool = False,
    strict_sliding: bool = False,
    end_day: int | None = None,
    seed: int = 0,
    horizon_ceiling: int | None = None,
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
            over_target_days=[],
        )

    if end_day is None:
        derived_end_day = max(card.day for card in cards)
        buckets = build_buckets(cards, start_day)
    else:
        derived_end_day = end_day
        buckets = build_buckets(cards, start_day, end_day)

    siblings_by_id: dict[int, list[int]] = {}
    by_note: dict[int, list[int]] = {}
    for card in cards:
        if card.note_id is None:
            continue
        by_note.setdefault(card.note_id, []).append(card.card_id)
    for members in by_note.values():
        if len(members) < 2:
            continue
        for cid in members:
            siblings_by_id[cid] = [other for other in members if other != cid]

    state = RunState(
        buckets=buckets,
        ivl_by_id={card.card_id: card.ivl for card in cards},
        origin_by_id={card.card_id: card.day for card in cards},
        moved=set(),
        start_day=start_day,
        end_day=derived_end_day,
        max_shift=max_shift,
        max_end_day=end_day,
        day_by_id={card.card_id: card.day for card in cards},
        siblings_by_id=siblings_by_id,
        separation_by_id={card.card_id: card.min_separation for card in cards},
        seed=seed,
        horizon_ceiling=horizon_ceiling,
    )
    before = {day: len(ids) for day, ids in state.buckets.items()}

    sink_overflow = 0
    reverse_pass_used = False
    over_target_days: list[int] = []

    if max_per_day is not None:
        max_ceiling = constant_targets(state.start_day, state.end_day, max_per_day)
        apply_max_pass(state, max_ceiling)
        sink_overflow = max(0, len(state.buckets[state.start_day]) - max_per_day)
        over_max = _days_over_max(state, max_per_day)
        if over_max:
            if not set_earlier:
                raise InfeasibleRebalance(
                    over_max,
                    {d: len(state.buckets[d]) for d in over_max},
                    _infeasible_reason(state, over_max),
                )
            apply_reverse_max_pass(state, max_ceiling)
            reverse_pass_used = True
            over_max = _days_over_max(state, max_per_day)
            if over_max:
                raise InfeasibleRebalance(
                    over_max,
                    {d: len(state.buckets[d]) for d in over_max},
                    _infeasible_reason(state, over_max, reverse_pass_used),
                )

    repair_ceiling = (
        constant_targets(state.start_day, state.end_day, max_per_day)
        if max_per_day is not None
        else None
    )
    unrepaired, repair_moved_later = apply_separation_repair_pass(
        state, repair_ceiling, set_earlier
    )
    if unrepaired:
        bad_days = sorted({state.day_by_id[cid] for cid in unrepaired})
        raise InfeasibleRebalance(
            bad_days,
            {d: len(state.buckets.get(d, [])) for d in bad_days},
            "min separation",
        )
    later_move_used = reverse_pass_used or repair_moved_later

    if sliding:
        # Both min_per_day and max_per_day are assumed present by the caller
        # (the CLI layer validates this) - T(d) needs both endpoints.
        target = build_target_line(
            state.start_day, state.end_day, min_per_day, max_per_day
        )
        # Size the ramp to the deck before shaping. Without this the surplus
        # has nowhere legal to go and accumulates at the tail.
        in_scope = sum(len(state.buckets[d]) for d in state.buckets)
        target = fit_target_line(target, in_scope, max_per_day)
        hard_ceiling = constant_targets(state.start_day, state.end_day, max_per_day)
        apply_shape_pass(state, target, hard_ceiling)
        apply_min_pass(state, target)
        over_target_days = [
            d
            for d in range(state.start_day, state.end_day + 1)
            if len(state.buckets[d]) > target[d]
        ]
        if strict_sliding and over_target_days:
            detail = ", ".join(
                f"day {d} at {len(state.buckets[d])} vs target {target[d]}"
                for d in over_target_days
            )
            raise InfeasibleRebalance(
                over_target_days,
                {d: len(state.buckets[d]) for d in over_target_days},
                f"sliding target: {detail}",
            )
        short_days = _short_days(state, target)
    elif min_per_day is not None:
        min_floor = constant_targets(state.start_day, state.end_day, min_per_day)
        apply_min_pass(state, min_floor)
        short_days = _short_days(state, min_floor)
    else:
        short_days = _short_days(state, None)

    after = {day: len(ids) for day, ids in state.buckets.items()}
    moves = {
        cid: day
        for day, ids in state.buckets.items()
        for cid in ids
        if day != state.origin_by_id[cid]
    }

    _check_post_conditions(state, max_per_day, max_shift, set_earlier, later_move_used)

    return RebalanceResult(
        moves=moves,
        before=before,
        after=after,
        end_day=state.end_day,
        sink_overflow=sink_overflow,
        short_days=short_days,
        reverse_pass_used=reverse_pass_used,
        over_target_days=over_target_days,
    )


# ---------------------------------------------------------------------------
# Feasibility precheck (6.1c, 6.4) - pure, called by every surface before
# planning. `check_hard_feasibility`'s capacity is ALWAYS constant
# max_per_day/min_per_day, never T(d), in any mode - that is what keeps the
# hard safety gate from rejecting decks DP-F's best-effort sliding default
# exists to serve. `analyze_shape` is informational only (sliding mode),
# capacity is always T(d), and it never gates a run.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HardFeasibility:
    feasible: bool
    violations: list[str]
    binding_prefix: (
        tuple[int, int, int] | None
    )  # (day, cards_due_by_then, capacity_by_then)
    suggested_min: int | None
    suggested_max: int | None


@dataclass(frozen=True)
class ShapeAnalysis:
    shape_reachable: bool
    predicted_over_target_days: list[int]
    shape_gap: int
    min_feasible_max_shift: int | None


@dataclass(frozen=True)
class FeasibilityReport:
    total: int
    first_day: int
    last_day: int
    horizon_days: int
    avg_per_day: float
    mode: str  # "flat" | "sliding"
    capacity: int
    feasible: bool
    violations: list[str]
    binding_prefix: tuple[int, int, int] | None
    suggested_min: int | None
    suggested_max: int | None
    shape_reachable: bool | None  # None in flat mode
    predicted_over_target_days: list[int]
    shape_gap: int
    min_feasible_max_shift: int | None


def _resolve_end_day(
    cards: Sequence[CardDue], start_day: int, end_day: int | None
) -> int:
    if end_day is not None:
        return end_day
    if not cards:
        return start_day - 1
    return max(card.day for card in cards)


def _origin_counts(cards: Sequence[CardDue]) -> dict[int, int]:
    counts: dict[int, int] = {}
    for card in cards:
        counts[card.day] = counts.get(card.day, 0) + 1
    return counts


def window_violations(
    counts: Mapping[int, int],
    start_day: int,
    end_day: int,
    capacity: DayTargets,
    max_shift: int | None,
) -> list[tuple[int, int, int, int]]:
    """For every window [a, b] with start_day <= a <= b <= end_day, report
    (a, b, confined, capacity_in_window) for windows where the cards whose
    ENTIRE legal landing range lies inside [a, b] ("confined") exceed the
    window's summed capacity. O(1) per window via prefix sums over both
    `counts` (by origin day) and `capacity` - D(D+1)/2 windows total."""
    if end_day < start_day:
        return []
    n = end_day - start_day + 1
    count_prefix = [0] * (n + 1)
    cap_prefix = [0] * (n + 1)
    for i in range(n):
        d = start_day + i
        count_prefix[i + 1] = count_prefix[i] + counts.get(d, 0)
        cap_prefix[i + 1] = cap_prefix[i] + capacity[d]

    def count_sum(lo_day: int, hi_idx: int) -> int:
        lo_idx = max(lo_day - start_day, 0)
        if lo_idx > hi_idx:
            return 0
        return count_prefix[hi_idx + 1] - count_prefix[lo_idx]

    violations: list[tuple[int, int, int, int]] = []
    for a_idx in range(n):
        a = start_day + a_idx
        for b_idx in range(a_idx, n):
            b = start_day + b_idx
            cap = cap_prefix[b_idx + 1] - cap_prefix[a_idx]
            if a == start_day:
                confined = count_sum(start_day, b_idx)
            elif max_shift is None:
                confined = 0
            else:
                confined = count_sum(a + max_shift, b_idx)
            if confined > cap:
                violations.append((a, b, confined, cap))
    return violations


def check_hard_feasibility(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int | None,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None,
    *,
    set_earlier: bool = False,
    day_offset_base: int | None = None,
) -> HardFeasibility:
    """`day_offset_base`, when given, is the day number that day-offset 0
    corresponds to (the caller's `today`). It affects only how the window
    violation LABELS its day range, so that the message reads in the same
    offsets every other line of CLI output uses. Omit it and the raw
    absolute day numbers are printed, unchanged."""
    total = len(cards)
    resolved_end_day = _resolve_end_day(cards, start_day, end_day)
    horizon_days = resolved_end_day - start_day + 1

    if total == 0 or horizon_days <= 0:
        return HardFeasibility(
            feasible=True,
            violations=[],
            binding_prefix=None,
            suggested_min=None,
            suggested_max=None,
        )

    counts = _origin_counts(cards)
    violations: list[str] = []
    feasible = True
    binding_prefix: tuple[int, int, int] | None = None

    if max_per_day is not None:
        capacity_total = horizon_days * max_per_day
        if total > capacity_total:
            msg = (
                f"global upper bound violated: {total} cards due in "
                f"{horizon_days} day window, capacity {capacity_total} "
                f"at max={max_per_day}/day"
            )
            if set_earlier:
                violations.append(
                    msg + " (downgraded to warning: --set-earlier can extend "
                    "the horizon to absorb the excess)"
                )
            else:
                violations.append(msg)
                feasible = False

    if min_per_day is not None:
        required_total = horizon_days * min_per_day
        if total < required_total:
            violations.append(
                f"global lower bound violated: {total} cards due in "
                f"{horizon_days} day window, requires {required_total} "
                f"at min={min_per_day}/day"
            )
            feasible = False

    if max_per_day is not None:
        ceiling = constant_targets(start_day, resolved_end_day, max_per_day)
        window_hits = window_violations(
            counts, start_day, resolved_end_day, ceiling, max_shift
        )
        if window_hits:
            worst = max(window_hits, key=lambda w: (w[2] - w[3], -w[1]))
            if day_offset_base is None:
                window_label = f"window [{worst[0]}, {worst[1]}]"
            else:
                window_label = (
                    f"window [day offset {worst[0] - day_offset_base}"
                    f"..{worst[1] - day_offset_base}]"
                )
            msg = (
                f"{window_label} over capacity: "
                f"{worst[2]} cards confined vs {worst[3]} slots "
                f"(gap {worst[2] - worst[3]})"
            )
            if set_earlier:
                violations.append(
                    msg + " (downgraded to warning: --set-earlier can extend "
                    "the horizon to absorb the excess)"
                )
            else:
                violations.append(msg)
                feasible = False

            prefix_hits = [w for w in window_hits if w[0] == start_day]
            if prefix_hits:
                worst_prefix = max(prefix_hits, key=lambda w: (w[2] - w[3], -w[1]))
                binding_prefix = (worst_prefix[1], worst_prefix[2], worst_prefix[3])

    suggested_max: int | None = None
    suggested_min: int | None = None
    if not feasible:
        if max_per_day is not None:
            suggested_max = math.ceil(total / horizon_days)
            running = 0
            for offset, d in enumerate(range(start_day, resolved_end_day + 1)):
                running += counts.get(d, 0)
                suggested_max = max(suggested_max, math.ceil(running / (offset + 1)))
        if min_per_day is not None:
            suggested_min = total // horizon_days

    return HardFeasibility(
        feasible=feasible,
        violations=violations,
        binding_prefix=binding_prefix,
        suggested_min=suggested_min,
        suggested_max=suggested_max,
    )


def _min_feasible_shift(
    counts: Mapping[int, int],
    start_day: int,
    end_day: int,
    target: DayTargets,
    horizon_days: int,
) -> int | None:
    def reachable(shift: int) -> bool:
        return not window_violations(counts, start_day, end_day, target, shift)

    if not reachable(horizon_days):
        return None
    return bisect_left(range(horizon_days + 1), True, key=reachable)


def analyze_shape(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int,
    target: DayTargets,
    max_shift: int | None,
) -> ShapeAnalysis:
    counts = _origin_counts(cards)
    window_hits = window_violations(counts, start_day, end_day, target, max_shift)
    shape_reachable = not window_hits
    predicted_over_target_days = sorted({b for _a, b, _c, _cap in window_hits})
    shape_gap = 0
    if window_hits:
        worst = max(window_hits, key=lambda w: w[2] - w[3])
        shape_gap = worst[2] - worst[3]

    min_feasible_max_shift: int | None = None
    if not shape_reachable:
        horizon_days = end_day - start_day + 1
        min_feasible_max_shift = _min_feasible_shift(
            counts, start_day, end_day, target, horizon_days
        )

    return ShapeAnalysis(
        shape_reachable=shape_reachable,
        predicted_over_target_days=predicted_over_target_days,
        shape_gap=shape_gap,
        min_feasible_max_shift=min_feasible_max_shift,
    )


def check_feasibility(
    cards: Sequence[CardDue],
    start_day: int,
    end_day: int | None,
    min_per_day: int | None,
    max_per_day: int | None,
    max_shift: int | None,
    *,
    sliding: bool = False,
    set_earlier: bool = False,
    day_offset_base: int | None = None,
) -> FeasibilityReport:
    hard = check_hard_feasibility(
        cards,
        start_day,
        end_day,
        min_per_day,
        max_per_day,
        max_shift,
        set_earlier=set_earlier,
        day_offset_base=day_offset_base,
    )
    resolved_end_day = _resolve_end_day(cards, start_day, end_day)
    horizon_days = resolved_end_day - start_day + 1
    total = len(cards)
    avg_per_day = total / horizon_days if horizon_days > 0 else 0.0

    shape_reachable: bool | None = None
    predicted_over_target_days: list[int] = []
    shape_gap = 0
    min_feasible_max_shift: int | None = None

    if sliding and horizon_days > 0:
        assert min_per_day is not None and max_per_day is not None
        target = build_target_line(
            start_day, resolved_end_day, min_per_day, max_per_day
        )
        capacity_total = sum(target.values())
        shape = analyze_shape(cards, start_day, resolved_end_day, target, max_shift)
        shape_reachable = shape.shape_reachable
        predicted_over_target_days = shape.predicted_over_target_days
        shape_gap = shape.shape_gap
        min_feasible_max_shift = shape.min_feasible_max_shift
    else:
        capacity_total = horizon_days * max_per_day if max_per_day is not None else 0

    return FeasibilityReport(
        total=total,
        first_day=start_day,
        last_day=resolved_end_day,
        horizon_days=horizon_days,
        avg_per_day=avg_per_day,
        mode="sliding" if sliding else "flat",
        capacity=capacity_total,
        feasible=hard.feasible,
        violations=hard.violations,
        binding_prefix=hard.binding_prefix,
        suggested_min=hard.suggested_min,
        suggested_max=hard.suggested_max,
        shape_reachable=shape_reachable,
        predicted_over_target_days=predicted_over_target_days,
        shape_gap=shape_gap,
        min_feasible_max_shift=min_feasible_max_shift,
    )
