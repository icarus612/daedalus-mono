"""Tests for the verb-aspect rule: both readings of it, over per-note
card-state combinations."""

import pytest

from anki_tools.aspect_due import (
    IMPERFECTIVE,
    IMPERFECTIVE_ORDS,
    LEARNING_TYPE,
    NEW_TYPE,
    PERFECTIVE,
    PERFECTIVE_ORDS,
    REVIEW_TYPE,
    RULE_GATE,
    RULE_SPACE,
    RULES,
    SUSPENDED_QUEUE,
    Card,
    aspect_of,
    check_rule,
    count_suspended_skipped,
    find_violations,
    group_by_note,
    has_been_studied,
    is_due,
    plan_deferrals,
    plan_new_queue_pushbacks,
)

TODAY = 1885

NEW = (NEW_TYPE, 0, 500)
DUE = (REVIEW_TYPE, 2, TODAY - 1)
DUE_TODAY = (REVIEW_TYPE, 2, TODAY)
DUE_LATER = (REVIEW_TYPE, 2, TODAY + 9)
LEARNING = (LEARNING_TYPE, 1, 1_700_000_000)
SUSPENDED_DUE = (REVIEW_TYPE, SUSPENDED_QUEUE, TODAY - 1)
SUSPENDED_NEW = (NEW_TYPE, SUSPENDED_QUEUE, 500)

# name, four states by ord, then expected ords for:
# gate deferrals, space deferrals, gate new-queue pushbacks, space pushbacks
CASES = [
    (
        "both perfective due, imperfectives studied",
        [DUE, DUE, DUE, DUE],
        [],
        [3],
        [],
        [],
    ),
    ("all four new", [NEW, NEW, NEW, NEW], [], [], [2, 3], [3]),
    (
        "perfective due, imperfective still new",
        [NEW, NEW, DUE, DUE],
        [2, 3],
        [3],
        [],
        [],
    ),
    ("one perfective due, the other still new", [NEW, NEW, DUE, NEW], [2], [], [3], []),
    (
        "suspended perfective beside a due one",
        [NEW, NEW, DUE, SUSPENDED_DUE],
        [2],
        [],
        [],
        [],
    ),
    ("everything studied, nothing due yet", [DUE_LATER] * 4, [], [], [], []),
    ("imperfectives studied, perfectives new", [DUE, DUE, NEW, NEW], [], [], [], [3]),
    ("both perfective in learning", [DUE, DUE, LEARNING, LEARNING], [], [3], [], []),
]

NOTE_ID = 7000


def rows_for(states, note_id=NOTE_ID):
    return [
        (note_id * 10 + card_ord, note_id, card_ord, card_type, queue, due)
        for card_ord, (card_type, queue, due) in enumerate(states)
    ]


def ords_of(card_ids, note_id=NOTE_ID):
    return sorted(card_id - note_id * 10 for card_id in card_ids)


@pytest.mark.parametrize(
    "name,states,gate_deferred,space_deferred,gate_pushed,space_pushed", CASES
)
def test_each_rule_defers_exactly_the_expected_cards(
    name, states, gate_deferred, space_deferred, gate_pushed, space_pushed
):
    rows = rows_for(states)
    assert ords_of(plan_deferrals(rows, RULE_GATE, TODAY)) == gate_deferred
    assert ords_of(plan_deferrals(rows, RULE_SPACE, TODAY)) == space_deferred


@pytest.mark.parametrize(
    "name,states,gate_deferred,space_deferred,gate_pushed,space_pushed", CASES
)
def test_each_rule_pushes_back_exactly_the_expected_new_cards(
    name, states, gate_deferred, space_deferred, gate_pushed, space_pushed
):
    rows = rows_for(states)
    assert ords_of(plan_new_queue_pushbacks(rows, RULE_GATE)) == gate_pushed
    assert ords_of(plan_new_queue_pushbacks(rows, RULE_SPACE)) == space_pushed


@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize(
    "name,states,gate_deferred,space_deferred,gate_pushed,space_pushed", CASES
)
def test_no_rule_ever_defers_a_new_or_suspended_card(
    rule, name, states, gate_deferred, space_deferred, gate_pushed, space_pushed
):
    rows = rows_for(states)
    by_id = {row[0]: row for row in rows}
    for card_id in plan_deferrals(rows, rule, TODAY):
        _, _, _, card_type, queue, _ = by_id[card_id]
        assert card_type != NEW_TYPE
        assert queue != SUSPENDED_QUEUE


@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize(
    "name,states,gate_deferred,space_deferred,gate_pushed,space_pushed", CASES
)
def test_no_rule_ever_pushes_back_a_studied_or_suspended_card(
    rule, name, states, gate_deferred, space_deferred, gate_pushed, space_pushed
):
    rows = rows_for(states)
    by_id = {row[0]: row for row in rows}
    for card_id in plan_new_queue_pushbacks(rows, rule):
        _, _, _, card_type, queue, _ = by_id[card_id]
        assert card_type == NEW_TYPE
        assert queue != SUSPENDED_QUEUE


@pytest.mark.parametrize("rule", RULES)
@pytest.mark.parametrize(
    "name,states,gate_deferred,space_deferred,gate_pushed,space_pushed", CASES
)
def test_no_rule_ever_touches_an_imperfective_card(
    rule, name, states, gate_deferred, space_deferred, gate_pushed, space_pushed
):
    rows = rows_for(states)
    touched = plan_deferrals(rows, rule, TODAY) + plan_new_queue_pushbacks(rows, rule)
    assert all(o in PERFECTIVE_ORDS for o in ords_of(touched))


def test_a_note_breaking_the_gate_rule_is_reported():
    """Positive control for gate: without this the empty results above
    would be satisfied by logic that never reports anything."""
    rows = rows_for([NEW, NEW, DUE, DUE])
    violations = find_violations(rows, RULE_GATE, TODAY)
    assert [v.card_id for v in violations] == [NOTE_ID * 10 + 2, NOTE_ID * 10 + 3]
    assert {v.note_id for v in violations} == {NOTE_ID}
    assert all("imperfective" in v.reason for v in violations)


def test_a_note_breaking_the_space_rule_is_reported():
    """Positive control for space, same reason."""
    rows = rows_for([DUE, DUE, DUE, DUE])
    violations = find_violations(rows, RULE_SPACE, TODAY)
    assert [v.card_id for v in violations] == [NOTE_ID * 10 + 3]
    assert all("same day" in v.reason for v in violations)


def test_the_two_rules_disagree_about_the_collection_as_it_stands():
    rows = rows_for([DUE, DUE, DUE, DUE])
    assert find_violations(rows, RULE_GATE, TODAY) == []
    assert find_violations(rows, RULE_SPACE, TODAY) != []


def test_space_keeps_the_more_overdue_perfective_and_defers_the_other():
    rows = rows_for([DUE, DUE, (REVIEW_TYPE, 2, TODAY - 5), DUE_TODAY])
    assert ords_of(plan_deferrals(rows, RULE_SPACE, TODAY)) == [3]
    rows = rows_for([DUE, DUE, DUE_TODAY, (REVIEW_TYPE, 2, TODAY - 5)])
    assert ords_of(plan_deferrals(rows, RULE_SPACE, TODAY)) == [2]


def test_a_suspended_perfective_is_counted_as_skipped_not_selected():
    rows = rows_for([NEW, NEW, DUE, SUSPENDED_DUE])
    assert ords_of(plan_deferrals(rows, RULE_GATE, TODAY)) == [2]
    assert count_suspended_skipped(rows, RULE_GATE, TODAY) == 1
    rows = rows_for([DUE, DUE, DUE, SUSPENDED_DUE])
    assert plan_deferrals(rows, RULE_SPACE, TODAY) == []
    assert count_suspended_skipped(rows, RULE_SPACE, TODAY) == 1


def test_a_suspended_new_perfective_is_never_repositioned():
    rows = rows_for([NEW, NEW, NEW, SUSPENDED_NEW])
    assert ords_of(plan_new_queue_pushbacks(rows, RULE_GATE)) == [2]


def test_nothing_is_skipped_when_nothing_is_suspended():
    rows = rows_for([DUE, DUE, DUE, DUE])
    assert count_suspended_skipped(rows, RULE_SPACE, TODAY) == 0


def test_a_suspended_review_card_still_counts_as_studied_history():
    assert has_been_studied(Card(1, 0, REVIEW_TYPE, SUSPENDED_QUEUE, TODAY))
    assert not has_been_studied(Card(2, 0, NEW_TYPE, 0, 1))


def test_the_gate_opens_on_a_suspended_but_reviewed_imperfective():
    rows = rows_for([SUSPENDED_DUE, NEW, DUE, DUE])
    assert plan_deferrals(rows, RULE_GATE, TODAY) == []


@pytest.mark.parametrize("card_ord", IMPERFECTIVE_ORDS)
def test_ords_zero_and_one_are_the_imperfective_sides(card_ord):
    assert aspect_of(card_ord) == IMPERFECTIVE


@pytest.mark.parametrize("card_ord", PERFECTIVE_ORDS)
def test_ords_two_and_three_are_the_perfective_sides(card_ord):
    assert aspect_of(card_ord) == PERFECTIVE


def test_the_aspect_map_covers_every_template_and_nothing_else():
    assert IMPERFECTIVE_ORDS == (0, 1)
    assert PERFECTIVE_ORDS == (2, 3)
    with pytest.raises(ValueError):
        aspect_of(4)


@pytest.mark.parametrize(
    "state,expected",
    [
        (NEW, False),
        (DUE, True),
        (DUE_TODAY, True),
        (DUE_LATER, False),
        (LEARNING, True),
        (SUSPENDED_DUE, False),
        (SUSPENDED_NEW, False),
    ],
)
def test_what_counts_as_sitting_in_todays_queue(state, expected):
    card_type, queue, due = state
    assert is_due(Card(1, 2, card_type, queue, due), TODAY) is expected


def test_rows_are_grouped_by_note_and_ordered_by_template():
    rows = rows_for([DUE, DUE, DUE, DUE]) + rows_for([NEW] * 4, note_id=8000)
    grouped = group_by_note(rows)
    assert sorted(grouped) == [NOTE_ID, 8000]
    assert [c.ord for c in grouped[NOTE_ID]] == [0, 1, 2, 3]


def test_a_note_missing_a_card_is_handled_rather_than_crashing():
    rows = rows_for([DUE, DUE, DUE, DUE])[:3]
    assert plan_deferrals(rows, RULE_SPACE, TODAY) == []
    assert plan_deferrals(rows, RULE_GATE, TODAY) == []


def test_results_are_sorted_so_a_run_is_reproducible():
    rows = list(reversed(rows_for([NEW, NEW, DUE, DUE])))
    assert plan_deferrals(rows, RULE_GATE, TODAY) == sorted(
        plan_deferrals(rows, RULE_GATE, TODAY)
    )


@pytest.mark.parametrize("bad", ["Gate", "", "both", None, "spacing"])
def test_an_unrecognised_rule_is_refused_rather_than_defaulted(bad):
    with pytest.raises(ValueError):
        check_rule(bad)
    with pytest.raises(ValueError):
        find_violations(rows_for([DUE] * 4), bad, TODAY)
    with pytest.raises(ValueError):
        plan_new_queue_pushbacks(rows_for([NEW] * 4), bad)


def test_there_are_exactly_two_rules_and_neither_is_a_default():
    assert RULES == (RULE_GATE, RULE_SPACE)
