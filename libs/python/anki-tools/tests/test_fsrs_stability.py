"""Tests for the AnkiMobile FSRS-stability floor.

The real values come from `Languages::Russian::4. Sentences (lingo llama)`,
where six cards sat below the floor and the deck would not open on an
iPhone while loading fine on desktop.
"""

import json
import os

import pytest
from anki.collection import Collection

from anki_tools.fsrs_stability import (
    MIN_STABILITY,
    apply_floor,
    find_low_stability,
    needs_floor,
    stability_of,
)
from anki_tools.fsrs_stability_floor import scan

# The shapes the `cards.data` column actually held on the affected cards.
REAL_BROKEN = '{"pos":58,"s":0.003,"d":9.895,"dr":0.98}'
REAL_ZERO = '{"pos":50,"s":0.0,"d":9.878,"dr":0.98}'
REAL_OK = '{"pos":45,"s":0.01,"d":9.963,"dr":0.98,"decay":0.194,"lrt":1789523511}'


def test_min_stability_is_the_value_that_fixed_the_deck():
    assert MIN_STABILITY == 0.01


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (REAL_BROKEN, 0.003),
        (REAL_ZERO, 0.0),
        (REAL_OK, 0.01),
        ("", None),
        (None, None),
        ("{}", None),
        ('{"d":9.9}', None),
        ("not json", None),
        ("[1,2]", None),
        ('{"s":"0.5"}', None),
        ('{"s":true}', None),
    ],
)
def test_stability_of(data, expected):
    assert stability_of(data) == expected


@pytest.mark.parametrize(
    ("data", "expected"),
    [(REAL_BROKEN, True), (REAL_ZERO, True), (REAL_OK, False), ("", False)],
)
def test_needs_floor(data, expected):
    assert needs_floor(data) is expected


def test_apply_floor_raises_only_the_stability():
    before = json.loads(REAL_BROKEN)
    after = json.loads(apply_floor(REAL_BROKEN))
    assert after["s"] == MIN_STABILITY
    assert {k: v for k, v in after.items() if k != "s"} == {
        k: v for k, v in before.items() if k != "s"
    }


def test_apply_floor_preserves_key_order():
    assert list(json.loads(apply_floor(REAL_BROKEN))) == list(json.loads(REAL_BROKEN))


def test_apply_floor_returns_an_untouched_value_unchanged():
    # Identity, not equality: a caller compares the result to decide whether
    # the row needs writing at all.
    assert apply_floor(REAL_OK) is REAL_OK
    assert apply_floor("") == ""


def test_apply_floor_is_idempotent():
    once = apply_floor(REAL_ZERO)
    assert apply_floor(once) == once


def test_find_low_stability_keeps_input_order_and_skips_clean_rows():
    rows = [(1, REAL_OK), (2, REAL_BROKEN), (3, ""), (4, REAL_ZERO)]
    assert find_low_stability(rows) == [(2, 0.003), (4, 0.0)]


def test_a_custom_floor_is_honoured():
    assert needs_floor(REAL_OK, 0.5) is True
    assert json.loads(apply_floor(REAL_OK, 0.5))["s"] == 0.5


def test_round_trip_through_a_real_collection(tmp_path):
    """End to end against Anki itself: a card written with the broken value
    is found by the scan, floored, and then no longer found. The pre-fix
    assertion is the positive control -- without it a scan that silently
    returned nothing would look identical to a clean collection.
    """
    col = Collection(os.path.join(str(tmp_path), "c.anki2"))
    try:
        model = col.models.by_name("Basic")
        deck_id = col.decks.id("Floor test", create=True)
        broken, clean = [], []
        for data, bucket in ((REAL_BROKEN, broken), (REAL_OK, clean)):
            note = col.new_note(model)
            note["Front"] = data
            note["Back"] = "x"
            col.add_note(note, deck_id)
            card_id = note.card_ids()[0]
            col.db.execute("update cards set data = ? where id = ?", data, card_id)
            bucket.append(card_id)

        found = find_low_stability(scan(col))
        assert [cid for cid, _ in found] == broken  # positive control
        assert clean[0] not in [cid for cid, _ in found]

        for card_id, _ in found:
            data = col.db.scalar("select data from cards where id = ?", card_id)
            col.db.execute(
                "update cards set data = ? where id = ?",
                apply_floor(data),
                card_id,
            )

        assert find_low_stability(scan(col)) == []
        after = col.db.scalar("select data from cards where id = ?", broken[0])
        assert json.loads(after)["s"] == MIN_STABILITY
        assert json.loads(after)["d"] == 9.895  # the rest of the state survived
    finally:
        col.close()


def test_scan_can_be_limited_to_a_deck(tmp_path):
    col = Collection(os.path.join(str(tmp_path), "c.anki2"))
    try:
        model = col.models.by_name("Basic")
        ids = {}
        for deck in ("Kept", "Excluded"):
            deck_id = col.decks.id(deck, create=True)
            note = col.new_note(model)
            note["Front"] = deck
            note["Back"] = "x"
            col.add_note(note, deck_id)
            card_id = note.card_ids()[0]
            col.db.execute(
                "update cards set data = ? where id = ?", REAL_BROKEN, card_id
            )
            ids[deck] = (deck_id, card_id)

        whole = [cid for cid, _ in find_low_stability(scan(col))]
        assert sorted(whole) == sorted(c for _, c in ids.values())

        kept = [cid for cid, _ in find_low_stability(scan(col, [ids["Kept"][0]]))]
        assert kept == [ids["Kept"][1]]
    finally:
        col.close()
