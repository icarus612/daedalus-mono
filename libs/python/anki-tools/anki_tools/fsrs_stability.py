#!/usr/bin/env python3
"""Keep every card's FSRS stability at or above AnkiMobile's minimum.

A card's FSRS memory state lives in the `cards.data` column as JSON --
`{"s": <stability>, "d": <difficulty>, ...}`. AnkiMobile validates those
values more strictly than the desktop client: a stability small enough to
round toward zero is rejected outright, and the whole deck then fails to
open on the phone with "invalid params" while loading fine on desktop.

Six cards in `Languages::Russian::4. Sentences (lingo llama)` reached that
state (stabilities around 0.003, 0.0018 and 0.0) and made the deck
unopenable on an iPhone. Raising each to MIN_STABILITY fixed it. The
numbers are already tiny -- a card at 0.003 is due immediately either way
-- so clamping costs no scheduling fidelity.

Pure module: standard library only, no `anki` import, so the arithmetic is
testable without a collection. `fsrs_stability_floor.py` is the CLI.
"""

import json
from collections.abc import Iterable

# AnkiMobile's floor. Anything at or above this survives its validation;
# anything below is what made the deck refuse to open.
MIN_STABILITY = 0.01

STABILITY_KEY = "s"


def stability_of(data: str) -> float | None:
    """The stability in a `cards.data` value, or None when it carries none.

    Tolerates the shapes the column actually takes: empty string, NULL
    (passed as None), a JSON object without an `s` key, and malformed JSON
    left by older clients -- none of which is an error worth raising
    mid-scan.
    """
    if not data:
        return None
    try:
        parsed = json.loads(data)
    except (ValueError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    value = parsed.get(STABILITY_KEY)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def needs_floor(data: str, minimum: float = MIN_STABILITY) -> bool:
    """Whether this card's stability sits below `minimum`.

    A card with no memory state at all does NOT need flooring -- it has
    nothing for AnkiMobile to reject. Only a present-but-too-small value
    counts.
    """
    stability = stability_of(data)
    return stability is not None and stability < minimum


def apply_floor(data: str, minimum: float = MIN_STABILITY) -> str:
    """`data` with its stability raised to `minimum`, every other key kept.

    Returns the value unchanged when it needs no flooring, so a caller can
    compare identity to decide whether to write. Key order is preserved:
    the column is round-tripped through `json.loads`/`json.dumps` rather
    than rebuilt, so a diff of the collection shows only `s` moving.
    """
    if not needs_floor(data, minimum):
        return data
    parsed = json.loads(data)
    parsed[STABILITY_KEY] = minimum
    return json.dumps(parsed, separators=(",", ":"))


def find_low_stability(
    rows: Iterable[tuple[int, str]], minimum: float = MIN_STABILITY
) -> list[tuple[int, float]]:
    """`(card_id, stability)` for every row below `minimum`, input order kept.

    `rows` is `(card_id, data)` pairs straight out of the `cards` table.
    """
    found = []
    for card_id, data in rows:
        stability = stability_of(data)
        if stability is not None and stability < minimum:
            found.append((card_id, stability))
    return found
