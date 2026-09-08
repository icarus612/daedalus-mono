"""Per-day deck diversity.

Cards tied on the same due day are genuinely tied. The pre-diversity
tiebreak was (ivl, card_id), which is deck-CORRELATED -- Anki card ids are
creation timestamps and a deck's cards are created and reviewed together --
so it walked whole subdecks in creation order. These tests pin the fix.
"""

from collections import Counter

from anki_tools.due_plan import CardDue, plan_rebalance


def tied_two_deck_cards(per_deck=30, day=10, ivl=100):
    """The reported shape: two decks, every card on ONE day, same ivl, and
    card ids in disjoint per-deck blocks (deck A ids below deck B's)."""
    cards = []
    cid = 1
    for deck in (1, 2):
        for _ in range(per_deck):
            cards.append(CardDue(card_id=cid, day=day, ivl=ivl, deck_id=deck))
            cid += 1
    return cards


def deck_of(cards):
    return {c.card_id: c.deck_id for c in cards}


def test_tied_day_is_split_between_decks_not_walked_deck_by_deck():
    cards = tied_two_deck_cards()
    owner = deck_of(cards)
    result = plan_rebalance(
        cards, start_day=1, min_per_day=None, max_per_day=6, max_shift=None
    )
    placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
    by_day = {}
    for card_id, day in placed.items():
        by_day.setdefault(day, Counter())[owner[card_id]] += 1

    # Every populated day must draw on both decks, never one deck as a block.
    for day, mix in by_day.items():
        assert set(mix) == {1, 2}, f"day {day} is single-deck: {dict(mix)}"
        assert abs(mix[1] - mix[2]) <= 1, f"day {day} lopsided: {dict(mix)}"


def test_diversity_does_not_lose_or_duplicate_cards():
    cards = tied_two_deck_cards()
    result = plan_rebalance(
        cards, start_day=1, min_per_day=None, max_per_day=6, max_shift=None
    )
    placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
    assert len(placed) == len(cards)
    assert sum(result.after.values()) == len(cards)


def test_min_pass_fills_underfull_days_from_under_represented_deck():
    """Day 1 is empty and day 2 holds a lopsided mix; the floor pass should
    pull from the deck that is missing at the destination."""
    cards = [CardDue(card_id=i, day=2, ivl=50, deck_id=1) for i in range(1, 9)]
    cards += [CardDue(card_id=i, day=2, ivl=50, deck_id=2) for i in range(9, 17)]
    owner = deck_of(cards)
    result = plan_rebalance(
        cards, start_day=1, min_per_day=4, max_per_day=8, max_shift=None
    )
    placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
    day1 = Counter(owner[cid] for cid, d in placed.items() if d == 1)
    assert set(day1) == {1, 2}, f"day 1 drew one deck only: {dict(day1)}"


def test_single_deck_ordering_is_unchanged_by_the_deck_term():
    """The regression guard: with one group (or none), diversity must be
    inert -- identical moves to a run that never knew about decks."""
    plain = [CardDue(card_id=i, day=10, ivl=100 + i) for i in range(1, 31)]
    grouped = [CardDue(card_id=i, day=10, ivl=100 + i, deck_id=7) for i in range(1, 31)]
    a = plan_rebalance(
        plain, start_day=1, min_per_day=None, max_per_day=5, max_shift=None
    )
    b = plan_rebalance(
        grouped, start_day=1, min_per_day=None, max_per_day=5, max_shift=None
    )
    assert a.moves == b.moves
