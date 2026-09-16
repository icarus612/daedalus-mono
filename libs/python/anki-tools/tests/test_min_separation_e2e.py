"""Builder-owned e2e suite for lane l1 (rebalance-min-separation).

Verifies the plan's acceptance criteria across the whole chunk
(`due_plan.py` + `rebalance_due.py` together, through the real CLI), not
just the two packets' own contract slices:

1. No note ends with siblings closer than its resolved separation, checked
   over EVERY note in a realistic deck shape -- not a sample.
2. Two different deck presets resolved correctly in one run.
3. Same-seed reproducibility survives at CLI/collection scale, not just on
   small pure-core fixtures.

The fixture forces every single note's sibling pair to be touched by real
capacity pressure (one note per origin day, `--max 1`), rather than relying
on chance clumping -- `--min-separation` only constrains a move the planner
was already making for capacity reasons, it does not proactively go fix a
quiet pair nothing else touches, so leaving that to chance would make the
"every note" claim untestable rather than proven.
"""

import os
import shutil
import sys

import pytest
from anki.collection import Collection

from anki_tools.rebalance_due import main

PY_MAX_IVL = 730  # matches the real collection's "All Cards" preset
GO_MAX_IVL = 200  # a second, smaller preset, resolved independently
PY_SEPARATION = PY_MAX_IVL // 2  # 365
GO_SEPARATION = GO_MAX_IVL // 2  # 100
N_PY_NOTES = 300
N_GO_NOTES = 200


def _assign_deck_config(col, deck_id, config_name, max_ivl):
    conf = col.decks.add_config(config_name)
    conf["rev"]["maxIvl"] = max_ivl
    col.decks.update_config(conf)
    deck = col.decks.get(deck_id)
    deck["conf"] = conf["id"]
    col.decks.save(deck)


def _sibling_pair(col, deck_id, *, due, ivl):
    model = col.models.by_name("Basic (and reversed card)")
    note = col.new_note(model)
    note["Front"] = "front"
    note["Back"] = "back"
    col.add_note(note, deck_id)
    cards = note.cards()
    for card in cards:
        card.type = 2
        card.queue = 2
        card.due = due
        card.ivl = ivl
        card.factor = 2500
        card.reps = 3
        col.update_card(card)
    return cards[0].id, cards[1].id


def _build_realistic_collection(col_path):
    """Two subdecks under one root, each on its own preset, each note
    parked alone on its own origin day so `--max 1` forces exactly one
    sibling of EVERY note to move -- no note is left to chance."""
    col = Collection(col_path)
    python_id = col.decks.id("programming::python")
    golang_id = col.decks.id("programming::golang")
    _assign_deck_config(col, python_id, "python_preset", PY_MAX_IVL)
    _assign_deck_config(col, golang_id, "golang_preset", GO_MAX_IVL)

    today = col.sched.today
    start_day = today + 1
    base = start_day + 700  # ample room below for a 365-day jump + margin

    python_pairs = [
        _sibling_pair(col, python_id, due=base + i, ivl=10 + (i % 50))
        for i in range(N_PY_NOTES)
    ]
    golang_pairs = [
        _sibling_pair(col, golang_id, due=base + N_PY_NOTES + i, ivl=10 + (i % 50))
        for i in range(N_GO_NOTES)
    ]
    col.close()
    return python_pairs, golang_pairs


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["anki-rebalance-due"] + list(argv))
    try:
        main()
    except SystemExit as exc:
        return exc.code
    return 0  # pragma: no cover - main() always raises SystemExit


def _final_days(col_path, pairs):
    col = Collection(col_path)
    try:
        return [(col.get_card(a).due, col.get_card(b).due) for a, b in pairs]
    finally:
        col.close()


def test_every_note_respects_its_deck_resolved_separation_at_scale(
    tmp_path, monkeypatch
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    python_pairs, golang_pairs = _build_realistic_collection(col_path)

    exit_code = _run_cli(
        [
            "programming",
            "--max",
            "1",
            "--max-shift",
            "1000",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code == 0

    python_days = _final_days(col_path, python_pairs)
    golang_days = _final_days(col_path, golang_pairs)

    # Every pair was actually touched, so the check below isn't vacuous.
    assert all(d1 != d2 for d1, d2 in python_days)
    assert all(d1 != d2 for d1, d2 in golang_days)

    # The acceptance bar: EVERY note, not a sample.
    python_violations = [
        (d1, d2) for d1, d2 in python_days if abs(d1 - d2) < PY_SEPARATION
    ]
    golang_violations = [
        (d1, d2) for d1, d2 in golang_days if abs(d1 - d2) < GO_SEPARATION
    ]
    assert python_violations == []
    assert golang_violations == []


def test_same_seed_reproduces_the_same_plan_at_scale(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    python_pairs, golang_pairs = _build_realistic_collection(col_path)
    copy_path = os.path.join(str(tmp_path), "copy.anki2")
    shutil.copy2(col_path, copy_path)

    common_args = [
        "programming",
        "--max",
        "1",
        "--max-shift",
        "1000",
        "--seed",
        "99",
        "--yes",
        "--collection",
    ]
    assert _run_cli(common_args + [col_path], monkeypatch) == 0
    assert _run_cli(common_args + [copy_path], monkeypatch) == 0

    all_pairs = python_pairs + golang_pairs
    assert _final_days(col_path, all_pairs) == _final_days(copy_path, all_pairs)


@pytest.mark.parametrize("min_separation_arg", [-1])
def test_two_presets_resolve_independently_at_scale(
    tmp_path, monkeypatch, min_separation_arg
):
    """Default (-1) resolution exercised over the SAME realistic run as the
    main test above, pinned here on its own so a future change to the main
    test's parameters can't accidentally stop covering two distinct presets
    in one run."""
    col_path = os.path.join(str(tmp_path), "test.anki2")
    _build_realistic_collection(col_path)

    exit_code = _run_cli(
        [
            "programming",
            "--max",
            "1",
            "--max-shift",
            "1000",
            "--min-separation",
            str(min_separation_arg),
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code == 0
    assert PY_SEPARATION != GO_SEPARATION  # the two presets genuinely differ
