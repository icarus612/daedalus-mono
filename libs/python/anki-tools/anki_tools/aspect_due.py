#!/usr/bin/env python3
"""Decide which perfective verb cards may be due, under either reading of
the aspect rule.

A Mutable Verbs note carries four cards: template ords 0 and 1 prompt the
IMPERFECTIVE aspect, ords 2 and 3 the PERFECTIVE one. Seeing both
perfective sides in the same day's queue is what the rule exists to stop.

The ask admits two readings and this module implements both, selected by
`rule`:

`gate`  -- a perfective card may be due only once some imperfective side of
           the same note has been studied.
`space` -- both aspects may be due, but never both perfective cards on the
           same day; the second one is deferred.

Nothing here ever selects a SUSPENDED card: `set_due_date` silently
unsuspends whatever it touches, so including one would quietly undo a
deliberate decision. Nothing here ever selects a NEW card for a due date
either -- `set_due_date` would convert it into a review card. New cards are
ordered by position, so the rule moves them instead, which is what
`plan_new_queue_pushbacks` returns.

Pure module: standard library only, no `anki` import. `aspect_due_cli` is
the command.
"""

from collections.abc import Iterable
from typing import NamedTuple

VERB_NOTE_TYPE = "Russian - Mutable Verbs (Ellis Version)"

IMPERFECTIVE_ORDS = (0, 1)
PERFECTIVE_ORDS = (2, 3)

IMPERFECTIVE = "imperfective"
PERFECTIVE = "perfective"

NEW_TYPE = 0
LEARNING_TYPE = 1
REVIEW_TYPE = 2
RELEARNING_TYPE = 3
SUSPENDED_QUEUE = -1

RULE_GATE = "gate"
RULE_SPACE = "space"
RULES = (RULE_GATE, RULE_SPACE)

REASON_GATE = "perfective due while no imperfective side has been studied"
REASON_SPACE = "second perfective side due the same day"


class Card(NamedTuple):
    id: int
    ord: int
    type: int
    queue: int
    due: int


class Violation(NamedTuple):
    note_id: int
    card_id: int
    reason: str


def check_rule(rule: str) -> str:
    if rule not in RULES:
        raise ValueError(f"rule must be one of {RULES}, got {rule!r}")
    return rule


def aspect_of(card_ord: int) -> str:
    if card_ord in IMPERFECTIVE_ORDS:
        return IMPERFECTIVE
    if card_ord in PERFECTIVE_ORDS:
        return PERFECTIVE
    raise ValueError(f"not a Mutable Verbs template ord: {card_ord!r}")


def group_by_note(
    rows: Iterable[tuple[int, int, int, int, int, int]],
) -> dict[int, list[Card]]:
    """`(card_id, note_id, ord, type, queue, due)` rows, grouped per note
    and ordered by template ord."""
    by_note: dict[int, list[Card]] = {}
    for card_id, note_id, card_ord, card_type, queue, due in rows:
        by_note.setdefault(note_id, []).append(
            Card(card_id, card_ord, card_type, queue, due)
        )
    for cards in by_note.values():
        cards.sort(key=lambda card: card.ord)
    return by_note


def is_suspended(card: Card) -> bool:
    return card.queue == SUSPENDED_QUEUE


def is_new(card: Card) -> bool:
    return card.type == NEW_TYPE


def has_been_studied(card: Card) -> bool:
    """Suspension hides a card; it does not erase its review history."""
    return card.type != NEW_TYPE


def is_due(card: Card, today: int) -> bool:
    """Whether the card sits in today's queue. Overdue counts; suspended and
    new never do. A learning card's `due` is a timestamp rather than a day
    number, and such a card is in today's queue by definition."""
    if is_suspended(card) or is_new(card):
        return False
    if card.type == REVIEW_TYPE:
        return card.due <= today
    return True


def _of_aspect(cards: list[Card], aspect: str) -> list[Card]:
    return [card for card in cards if aspect_of(card.ord) == aspect]


def _gate_is_open(cards: list[Card]) -> bool:
    return any(has_been_studied(card) for card in _of_aspect(cards, IMPERFECTIVE))


def _first_kept_last(cards: list[Card]) -> list[Card]:
    """The most overdue card first, so it is the one the space rule keeps."""
    return sorted(cards, key=lambda card: (card.due, card.ord))


def find_violations(
    rows: Iterable[tuple[int, int, int, int, int, int]],
    rule: str,
    today: int,
) -> list[Violation]:
    check_rule(rule)
    violations: list[Violation] = []
    for note_id, cards in group_by_note(rows).items():
        due_perfective = [
            card for card in _of_aspect(cards, PERFECTIVE) if is_due(card, today)
        ]
        if rule == RULE_GATE:
            if due_perfective and not _gate_is_open(cards):
                violations += [
                    Violation(note_id, card.id, REASON_GATE) for card in due_perfective
                ]
        else:
            violations += [
                Violation(note_id, card.id, REASON_SPACE)
                for card in _first_kept_last(due_perfective)[1:]
            ]
    return sorted(
        violations, key=lambda violation: (violation.note_id, violation.card_id)
    )


def plan_deferrals(
    rows: Iterable[tuple[int, int, int, int, int, int]],
    rule: str,
    today: int,
) -> list[int]:
    """Card ids to push out by a day or more. Same selection as
    `find_violations`, so report and fix can never diverge."""
    return sorted(
        {violation.card_id for violation in find_violations(rows, rule, today)}
    )


def count_suspended_skipped(
    rows: Iterable[tuple[int, int, int, int, int, int]],
    rule: str,
    today: int,
) -> int:
    """How many cards the rule would have deferred but for their being
    suspended -- reported so the skip is visible rather than silent."""
    check_rule(rule)
    suspended_ids = set()
    shadow = []
    for note_id, cards in group_by_note(rows).items():
        for card in cards:
            if is_suspended(card):
                suspended_ids.add(card.id)
            shadow.append((card.id, note_id, card.ord, card.type, 0, card.due))
    picked = {violation.card_id for violation in find_violations(shadow, rule, today)}
    return len(picked & suspended_ids)


def plan_new_queue_pushbacks(
    rows: Iterable[tuple[int, int, int, int, int, int]],
    rule: str,
) -> list[int]:
    """New perfective cards the rule wants behind their imperfective
    siblings. The new queue is ordered by position rather than by day, so
    these are repositioned, never given a due date."""
    check_rule(rule)
    pushed: list[int] = []
    for cards in group_by_note(rows).values():
        new_perfective = [
            card
            for card in _of_aspect(cards, PERFECTIVE)
            if is_new(card) and not is_suspended(card)
        ]
        if rule == RULE_GATE:
            if not _gate_is_open(cards):
                pushed += [card.id for card in new_perfective]
        else:
            pushed += [card.id for card in _first_kept_last(new_perfective)[1:]]
    return sorted(pushed)
