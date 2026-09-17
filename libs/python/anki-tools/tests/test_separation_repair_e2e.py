"""Builder-owned e2e suite for lane l2 (rebalance-min-separation).

Verifies the plan's acceptance criteria across the whole chunk (`due_plan.py`
+ `rebalance_due.py` together, through the real CLI and a real Anki
`Collection`) -- not just the two packets' own contract slices:

1. Sibling separation, daily load, and the horizon all hold SIMULTANEOUSLY
   in the final plan, checked over EVERY note/day -- not a sample.
2. The fixture is deliberately sized so ordinary `--min`/`--max` load
   balancing has NO reason to touch any note (every origin day sits
   comfortably inside the band): this isolates active repair as the ONLY
   possible explanation for any move, which is exactly what distinguishes
   this lane from lane 1's placement-only `--min-separation` (which never
   touches a pair nothing else forces it to move). A `--min-separation 0`
   control run against a byte-identical copy of the same starting
   collection proves the negative side directly: with the constraint off,
   these same pairs are left exactly where they started -- confirming load
   balancing alone genuinely never would have fixed them, so the positive
   run's fix is attributable to repair, not to a lucky day-count coincidence.
3. `ivl` is preserved for every card, moved or not.
4. No card lands past the horizon (`today + maxIvl`, since no `--range` is
   given here).
"""

import os
import shutil
import sys

import pytest
from anki.collection import Collection

from anki_tools.rebalance_due import main

MAX_IVL = 730  # matches the real collection's "All Cards" preset
MIN_SEPARATION = 180  # matches the real run this lane was written to fix
N_NOTES = 300
N_VIOLATING = 225  # ~75%, mirrors the real 1,664-of-2,741 proportion
CLOSE_GAP = 3  # well under MIN_SEPARATION, mirrors the "0-1 days apart" cases
FAR_GAP = 400  # already well clear of MIN_SEPARATION -- must be left alone
MAX_PER_DAY = 10
MIN_PER_DAY = 0


def _assign_deck_config(col, deck_id, config_name, max_ivl):
    conf = col.decks.add_config(config_name)
    conf["rev"]["maxIvl"] = max_ivl
    col.decks.update_config(conf)
    deck = col.decks.get(deck_id)
    deck["conf"] = conf["id"]
    col.decks.save(deck)


def _add_card(col, deck_id, *, due, ivl):
    note = col.new_note(col.models.by_name("Basic"))
    note["Front"] = "front"
    note["Back"] = "back"
    col.add_note(note, deck_id)
    card = note.cards()[0]
    card.type = 2
    card.queue = 2
    card.due = due
    card.ivl = ivl
    card.factor = 2500
    card.reps = 3
    col.update_card(card)
    return card.id


def _build_realistic_collection(col_path):
    """`N_NOTES` notes, one per distinct origin day, each note's two cards
    (front/back, built as two separate `Basic` notes sharing a synthetic
    "sibling" relationship is not how real notes work -- a genuine note
    needs `note_id` sharing, so this uses one `Basic (and reversed card)`
    note per pair, exactly like the rest of this test suite) placed either
    `CLOSE_GAP` apart (violating) or `FAR_GAP` apart (already fine). One
    note per day keeps every day's count at 2 -- comfortably inside
    [MIN_PER_DAY, MAX_PER_DAY] with zero balancing pressure, by
    construction, for every single note."""
    col = Collection(col_path)
    deck_id = col.decks.id("programming::coding")
    _assign_deck_config(col, deck_id, "wide_preset", MAX_IVL)
    today = col.sched.today
    start_day = today + 1

    model = col.models.by_name("Basic (and reversed card)")
    violating_pairs = []
    ok_pairs = []
    for i in range(N_NOTES):
        origin = start_day + i
        note = col.new_note(model)
        note["Front"] = "front"
        note["Back"] = "back"
        col.add_note(note, deck_id)
        card_a, card_b = note.cards()
        gap = CLOSE_GAP if i < N_VIOLATING else FAR_GAP
        for card, due in ((card_a, origin), (card_b, origin + gap)):
            card.type = 2
            card.queue = 2
            card.due = due
            card.ivl = 10 + (i % 50)
            card.factor = 2500
            card.reps = 3
            col.update_card(card)
        pair = (card_a.id, card_b.id)
        (violating_pairs if i < N_VIOLATING else ok_pairs).append(pair)

    col.close()
    return violating_pairs, ok_pairs


def _run_cli(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["anki-rebalance-due"] + list(argv))
    try:
        main()
    except SystemExit as exc:
        return exc.code
    return 0  # pragma: no cover - main() always raises SystemExit


def _snapshot(col_path, card_ids):
    col = Collection(col_path)
    try:
        return {cid: (col.get_card(cid).due, col.get_card(cid).ivl) for cid in card_ids}
    finally:
        col.close()


@pytest.fixture
def scenario(tmp_path):
    col_path = os.path.join(str(tmp_path), "real.anki2")
    violating_pairs, ok_pairs = _build_realistic_collection(col_path)
    control_path = os.path.join(str(tmp_path), "control.anki2")
    shutil.copy2(col_path, control_path)
    return col_path, control_path, violating_pairs, ok_pairs


def test_repair_fixes_every_violating_note_while_honouring_load_and_horizon(
    scenario, monkeypatch
):
    col_path, control_path, violating_pairs, ok_pairs = scenario
    all_ids = [cid for pair in violating_pairs + ok_pairs for cid in pair]
    before = _snapshot(col_path, all_ids)

    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            str(MIN_PER_DAY),
            "--max",
            str(MAX_PER_DAY),
            "--min-separation",
            str(MIN_SEPARATION),
            "--set-earlier",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code == 0

    col = Collection(col_path)
    try:
        today = col.sched.today
        horizon = today + MAX_IVL

        counts_by_day = {}
        for pair in violating_pairs + ok_pairs:
            for cid in pair:
                day = col.get_card(cid).due
                counts_by_day[day] = counts_by_day.get(day, 0) + 1

        # 1. Sibling separation: every violating pair now meets the bar,
        # checked over EVERY pair, not a sample.
        for card_a, card_b in violating_pairs:
            due_a = col.get_card(card_a).due
            due_b = col.get_card(card_b).due
            assert abs(due_a - due_b) >= MIN_SEPARATION, (card_a, card_b)

        # Already-fine pairs are untouched -- repair must not needlessly
        # move a pair that already satisfies separation.
        for card_a, card_b in ok_pairs:
            due_a = col.get_card(card_a).due
            due_b = col.get_card(card_b).due
            assert due_a == before[card_a][0]
            assert due_b == before[card_b][0]

        # 2. Daily load: every day within --min/--max, over EVERY day that
        # actually holds a card from this fixture.
        for day, count in counts_by_day.items():
            assert MIN_PER_DAY <= count <= MAX_PER_DAY, (day, count)

        # 3. Horizon: no card past today + maxIvl, over EVERY card.
        for cid in all_ids:
            due = col.get_card(cid).due
            assert due <= horizon, (cid, due)

        # 4. Interval preservation: over EVERY card, moved or not.
        for cid in all_ids:
            assert col.get_card(cid).ivl == before[cid][1], cid
    finally:
        col.close()

    # Sensitivity: a byte-identical copy, constraint disabled, proves load
    # balancing alone never would have moved these pairs.
    control_exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            str(MIN_PER_DAY),
            "--max",
            str(MAX_PER_DAY),
            "--min-separation",
            "0",
            "--set-earlier",
            "--yes",
            "--collection",
            control_path,
        ],
        monkeypatch,
    )
    assert control_exit_code == 0
    control_col = Collection(control_path)
    try:
        for card_a, card_b in violating_pairs:
            assert control_col.get_card(card_a).due == before[card_a][0]
            assert control_col.get_card(card_b).due == before[card_b][0]
    finally:
        control_col.close()


def test_repair_reports_infeasible_rather_than_violating_horizon_or_max(
    tmp_path, monkeypatch, capsys
):
    """A separation requirement wider than the horizon can absorb, with no
    --set-earlier and a --max-shift too small to reach it earlier either,
    must raise the existing infeasibility reporting and write nothing --
    never silently exceed --max or the horizon to force a fit."""
    col_path = os.path.join(str(tmp_path), "infeasible.anki2")
    col = Collection(col_path)
    deck_id = col.decks.id("programming::coding")
    _assign_deck_config(col, deck_id, "tiny_preset", 20)
    today = col.sched.today
    start_day = today + 1

    model = col.models.by_name("Basic (and reversed card)")
    note = col.new_note(model)
    note["Front"] = "front"
    note["Back"] = "back"
    col.add_note(note, deck_id)
    card_a, card_b = note.cards()
    for card, due in ((card_a, start_day + 5), (card_b, start_day + 5)):
        card.type = 2
        card.queue = 2
        card.due = due
        card.ivl = 10
        card.factor = 2500
        card.reps = 3
        col.update_card(card)
    ids = (card_a.id, card_b.id)
    col.close()
    before = _snapshot(col_path, ids)

    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "50",
            "--min-separation",
            "180",  # far more than the tiny_preset horizon (today+20) allows
            "--max-shift",
            "2",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code != 0
    err_and_out = capsys.readouterr()
    assert "min separation" in (err_and_out.out + err_and_out.err).lower()

    after = _snapshot(col_path, ids)
    assert after == before  # nothing written on infeasibility
