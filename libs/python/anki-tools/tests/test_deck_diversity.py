"""Anti-clumping under the seeded random tiebreak.

The old round-robin diversity mechanism (deck_rank/deck_counts, forcing a
literal one-card-per-deck rotation) is gone -- the user explicitly rejected
forced per-subject rotation. What must survive is the underlying property
it existed for: Anki card ids are creation timestamps, and a deck's cards
are created and reviewed together, so a plain (ivl, card_id) tiebreak among
tied candidates walks whole subdecks in creation order (deck A drains
entirely, then deck B). The new seeded (state.seed, card_id) tiebreak must
break that correlation -- not by forcing balance, but by making the walk
order genuinely unpredictable with respect to card id.

These tests never construct CardDue with a deck_id kwarg -- that field is
gone. "Deck" here is purely a grouping label this test file assigns itself
(disjoint card-id blocks), used only to check the placement afterwards.
"""

from collections import Counter

from anki_tools.due_plan import CardDue, plan_rebalance


def tied_two_deck_cards(per_deck=30, day=10, ivl=100):
    """Two decks, every card on ONE day, same ivl, and card ids in
    disjoint per-deck blocks (deck A ids below deck B's) -- the shape a
    plain (ivl, card_id) tiebreak would walk deck by deck."""
    cards = []
    cid = 1
    deck_of = {}
    for deck in (1, 2):
        for _ in range(per_deck):
            cards.append(CardDue(cid, day, ivl))
            deck_of[cid] = deck
            cid += 1
    return cards, deck_of


def reference_round_robin_order(card_ids, deck_of):
    """A ~10-line re-derivation of the deleted deck_rank mechanism: rank
    each candidate by its own index within its deck's group (walking the
    candidates in priority order), so ties break by (rank, card_id) --
    literal round-robin across decks, not by seed."""
    seen_per_deck = {}
    rank = {}
    for cid in sorted(card_ids):
        deck = deck_of[cid]
        rank[cid] = seen_per_deck.get(deck, 0)
        seen_per_deck[deck] = rank[cid] + 1
    return sorted(card_ids, key=lambda cid: (rank[cid], cid))


def test_real_placement_differs_from_strict_round_robin_for_some_seed():
    """Direct comparison against the re-derived old mechanism: for at
    least one seed, the real plan_rebalance's card-to-day placement is NOT
    what strict deck-by-deck round robin would have produced."""
    cards, deck_of = tied_two_deck_cards()
    card_ids = [c.card_id for c in cards]
    round_robin_order = reference_round_robin_order(card_ids, deck_of)

    differed = False
    for seed in range(5):
        result = plan_rebalance(
            cards,
            start_day=1,
            min_per_day=None,
            max_per_day=6,
            max_shift=None,
            seed=seed,
        )
        placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
        # The round-robin reference assigns candidates to days in its own
        # priority order, filling each day to max_per_day in turn.
        reference_placed = {}
        for i, cid in enumerate(round_robin_order):
            reference_placed[cid] = i // 6
        if placed != {cid: placed[cid] for cid in card_ids} or any(
            placed[cid] != reference_placed[cid] for cid in card_ids
        ):
            differed = True
            break
    assert differed, "no seed produced a placement different from strict round robin"


def test_same_seed_reproducibility():
    cards, _ = tied_two_deck_cards()
    result_a = plan_rebalance(
        cards, start_day=1, min_per_day=None, max_per_day=6, max_shift=None, seed=3
    )
    result_b = plan_rebalance(
        cards, start_day=1, min_per_day=None, max_per_day=6, max_shift=None, seed=3
    )
    assert result_a.moves == result_b.moves


def test_no_clumping_regression_statistically():
    """Across several seeds: populated days mix both decks at least
    sometimes (mixing happens), and the deck split across days is not
    monotonically ordered by card id (deck A does not simply drain out
    entirely before deck B starts) -- the exact symptom the old (ivl,
    card_id) tiebreak caused."""
    cards, deck_of = tied_two_deck_cards()
    saw_mixed_day = False
    saw_non_monotonic_split = False
    for seed in range(3):
        result = plan_rebalance(
            cards,
            start_day=1,
            min_per_day=None,
            max_per_day=6,
            max_shift=None,
            seed=seed,
        )
        placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
        by_day = {}
        for card_id, day in placed.items():
            by_day.setdefault(day, Counter())[deck_of[card_id]] += 1
        if any(set(mix) == {1, 2} for mix in by_day.values()):
            saw_mixed_day = True
        # Monotonic-by-card-id would mean: every deck-A card lands on a day
        # <= every deck-B card's day (deck A drains first).
        max_day_a = max(day for cid, day in placed.items() if deck_of[cid] == 1)
        min_day_b = min(day for cid, day in placed.items() if deck_of[cid] == 2)
        if max_day_a > min_day_b:
            saw_non_monotonic_split = True
    assert saw_mixed_day
    assert saw_non_monotonic_split


def test_no_lost_or_duplicated_cards():
    cards, _ = tied_two_deck_cards()
    result = plan_rebalance(
        cards, start_day=1, min_per_day=None, max_per_day=6, max_shift=None
    )
    placed = {c.card_id: result.moves.get(c.card_id, c.day) for c in cards}
    assert len(placed) == len(cards)
    assert sum(result.after.values()) == len(cards)
