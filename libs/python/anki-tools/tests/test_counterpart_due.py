"""Tests for the new-card-with-a-studied-sibling sweep."""

import os

from anki.collection import Collection

from anki_tools.counterpart_due import (
    count_suspended_skipped,
    find_orphaned_counterparts,
)
from anki_tools.counterpart_due_cli import scan

# (card_id, note_id, type, queue)
STUDIED = 2
NEW = 0


def test_a_new_card_beside_a_studied_sibling_is_found():
    rows = [(1, 10, STUDIED, 2), (2, 10, NEW, 0)]
    assert find_orphaned_counterparts(rows) == [2]


def test_a_note_whose_cards_are_all_new_is_not_a_hit():
    rows = [(1, 11, NEW, 0), (2, 11, NEW, 0)]
    assert find_orphaned_counterparts(rows) == []


def test_a_note_whose_cards_are_all_studied_is_not_a_hit():
    rows = [(1, 12, STUDIED, 2), (2, 12, STUDIED, 2)]
    assert find_orphaned_counterparts(rows) == []


def test_a_suspended_new_card_is_never_selected():
    rows = [(1, 13, STUDIED, 2), (2, 13, NEW, -1)]
    assert find_orphaned_counterparts(rows) == []
    assert count_suspended_skipped(rows) == 1


def test_a_buried_new_card_is_still_selected():
    # Burying is Anki's own transient hiding, not a decision to exclude.
    rows = [(1, 14, STUDIED, 2), (2, 14, NEW, -2)]
    assert find_orphaned_counterparts(rows) == [2]


def test_all_new_siblings_of_one_note_are_returned():
    rows = [(1, 15, STUDIED, 2), (2, 15, NEW, 0), (3, 15, NEW, 0)]
    assert find_orphaned_counterparts(rows) == [2, 3]


def test_learning_and_relearning_count_as_studied():
    for card_type in (1, 3):
        rows = [(1, 16, card_type, 1), (2, 16, NEW, 0)]
        assert find_orphaned_counterparts(rows) == [2]


def test_results_are_sorted_regardless_of_input_order():
    rows = [(9, 17, NEW, 0), (3, 17, STUDIED, 2), (5, 17, NEW, 0)]
    assert find_orphaned_counterparts(rows) == [5, 9]


def test_suspended_skip_count_ignores_untouched_notes():
    rows = [(1, 18, NEW, -1), (2, 18, NEW, 0)]
    assert count_suspended_skipped(rows) == 0


def _two_card_model(col):
    model = col.models.by_name("Basic (and reversed card)")
    assert model is not None
    return model


def test_end_to_end_against_a_real_collection(tmp_path):
    """The sweep over Anki's own tables, then the fix, then re-running it.

    The pre-fix assertion is the positive control: a scan that silently
    returned nothing would otherwise be indistinguishable from a clean
    collection.
    """
    col = Collection(os.path.join(str(tmp_path), "c.anki2"))
    try:
        model = _two_card_model(col)
        deck_id = col.decks.id("Counterpart test", create=True)
        note = col.new_note(model)
        note["Front"] = "слово"
        note["Back"] = "word"
        col.add_note(note, deck_id)
        first, second = note.card_ids()

        # Study one side only, leaving its sibling new.
        col.sched.set_due_date([first], "3")
        assert col.get_card(first).type != NEW
        assert col.get_card(second).type == NEW

        found = find_orphaned_counterparts(scan(col))
        assert found == [second]  # positive control

        col.sched.set_due_date(found, "0")
        assert find_orphaned_counterparts(scan(col)) == []
        fixed = col.get_card(second)
        assert fixed.type != NEW
        assert fixed.due == col.sched.today
    finally:
        col.close()


def test_deck_scope_still_sees_siblings_in_other_decks(tmp_path):
    """A sibling moved to another deck is what makes a card an orphan, so a
    deck-scoped scan must still read it or the orphan goes unnoticed.
    """
    col = Collection(os.path.join(str(tmp_path), "c.anki2"))
    try:
        model = _two_card_model(col)
        here = col.decks.id("Here", create=True)
        elsewhere = col.decks.id("Elsewhere", create=True)
        note = col.new_note(model)
        note["Front"] = "дом"
        note["Back"] = "house"
        col.add_note(note, here)
        first, second = note.card_ids()
        col.set_deck([first], elsewhere)
        col.sched.set_due_date([first], "3")

        assert find_orphaned_counterparts(scan(col, [here])) == [second]
    finally:
        col.close()
