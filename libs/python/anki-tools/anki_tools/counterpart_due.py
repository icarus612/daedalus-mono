#!/usr/bin/env python3
"""Find cards left in the new queue while a sibling has already been studied.

A note's cards are two sides of one word -- listening and recall, or a
verb's two aspects. Once one side has been reviewed the word is not new any
more, so leaving the other side sitting in the new queue is wrong: it waits
behind hundreds of genuinely unseen words instead of coming up while the
word is still fresh.

This condition reappears continuously. Every review of a card whose sibling
is still new creates another one, so a single sweep never settles it -- the
sweep has to be re-runnable.

SUSPENDED cards are never selected. A suspended card was deliberately taken
out of circulation, and Anki's `set_due_date` silently unsuspends whatever
it touches, so including one here would quietly undo that decision.

Pure module: standard library only, no `anki` import. `counterpart_due_cli`
is the command.
"""

from collections.abc import Iterable

NEW_TYPE = 0
SUSPENDED_QUEUE = -1


def find_orphaned_counterparts(
    rows: Iterable[tuple[int, int, int, int]],
) -> list[int]:
    """Card ids that are new while a sibling of the same note is not.

    `rows` is `(card_id, note_id, type, queue)` straight out of the `cards`
    table. Returns ids in ascending order so a run is reproducible.
    Suspended cards are excluded, and a note whose cards are *all* new is
    not a hit -- that word simply has not been started.
    """
    by_note: dict[int, list[tuple[int, int, int]]] = {}
    for card_id, note_id, card_type, queue in rows:
        by_note.setdefault(note_id, []).append((card_id, card_type, queue))

    orphaned = []
    for cards in by_note.values():
        if not any(card_type != NEW_TYPE for _, card_type, _ in cards):
            continue
        for card_id, card_type, queue in cards:
            if card_type == NEW_TYPE and queue != SUSPENDED_QUEUE:
                orphaned.append(card_id)
    return sorted(orphaned)


def count_suspended_skipped(
    rows: Iterable[tuple[int, int, int, int]],
) -> int:
    """How many new-with-studied-sibling cards were left alone for being
    suspended -- reported so the skip is visible rather than silent."""
    by_note: dict[int, list[tuple[int, int]]] = {}
    for card_id, note_id, card_type, queue in rows:
        by_note.setdefault(note_id, []).append((card_type, queue))
    skipped = 0
    for cards in by_note.values():
        if not any(t != NEW_TYPE for t, _ in cards):
            continue
        skipped += sum(1 for t, q in cards if t == NEW_TYPE and q == SUSPENDED_QUEUE)
    return skipped
