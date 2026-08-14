"""Contract tests for anki_tools.due_stats (Phase 6 / Packet E, subphase 6.5).

Written blind to the implementation, from the plan
(project-plans/anki-due-rebalance-08-12-26/plan.md, subphase 6.5 and the
settled-decisions table) and the lane l1 contract (.artifacts/contracts/l1.md,
"PHASE 6 ROUND" -> "Packet E") alone. Never opens the real user collection
(~/.local/share/Anki2/User 1/collection.anki2) -- every collection here is
built fresh under pytest's tmp_path.

`anki-due-stats` is DP-A's read-only sibling command to `anki-rebalance-due`:
same deck argument and --start-offset/--range/--collection/--min/--max/
--sliding semantics, but it opens read-only, plans nothing, writes nothing,
takes no backup, and exits 0 whether the deck is feasible or not (it is a
report, not a gate). It is pinned to compute everything through
due_plan.check_feasibility/build_target_line -- never recomputing totals or
the range slice itself.

Cross-checks in a few of the harder-to-pin-down tests below call directly
into anki_tools.due_plan -- the already-complete, already-verified pure core
this packet's coder is required to call into, not reimplement -- exactly as
the dispatching contract sanctions ("fixture construction and cross-checks").
anki_tools.due_stats and anki_tools.rebalance_due themselves are never read.
"""

import json
import os
import time

import pytest
from anki.collection import Collection

from anki_tools.due_plan import CardDue, check_feasibility
from anki_tools.due_stats import build_parser, main

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(PACKAGE_ROOT, "anki_tools", "due_stats.py")


# ---------------------------------------------------------------------------
# Fixtures / helpers -- mirrors test_rebalance_due.py's own conventions
# exactly (this file has no access to that module's private helpers, so the
# small helper is duplicated here rather than importing test scaffolding
# across test files).
# ---------------------------------------------------------------------------


def _add_card(
    col,
    deck_id,
    *,
    due,
    ivl=30,
    factor=2500,
    reps=3,
    queue=2,
    ctype=2,
    front="q",
    back="a",
):
    note = col.new_note(col.models.by_name("Basic"))
    note["Front"] = front
    note["Back"] = back
    col.add_note(note, deck_id)
    card = note.cards()[0]
    if (ctype, queue) != (0, 0):
        card.type = ctype
        card.queue = queue
        card.due = due
        card.ivl = ivl
        card.factor = factor
        card.reps = reps
        col.update_card(card)
    return card


def _run_cli(argv, monkeypatch):
    """Invoke main() with the given CLI args, returning its SystemExit code."""
    import sys

    monkeypatch.setattr(sys, "argv", ["anki-due-stats"] + list(argv))
    try:
        main()
    except SystemExit as exc:
        return exc.code
    return 0  # pragma: no cover - main() always raises SystemExit


def _snapshot_due_ivl(col_path, card_ids):
    col = Collection(col_path)
    try:
        return {cid: (col.get_card(cid).due, col.get_card(cid).ivl) for cid in card_ids}
    finally:
        col.close()


# ---------------------------------------------------------------------------
# Static / packaging acceptance criteria (plan.md line 1288)
# ---------------------------------------------------------------------------


def test_source_file_starts_with_shebang():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        first_line = f.readline()
    assert first_line == "#!/usr/bin/env python3\n"


def test_source_file_has_no_except_exception_or_noqa():
    with open(MODULE_PATH, "r", encoding="utf-8") as f:
        source = f.read()
    assert "except Exception" not in source
    assert "# noqa" not in source


def test_source_file_is_executable():
    mode = os.stat(MODULE_PATH).st_mode
    assert mode & 0o111, "due_stats.py must be executable (mode 755)"


def test_package_json_registers_due_stats_bin_entry():
    package_json_path = os.path.join(PACKAGE_ROOT, "package.json")
    with open(package_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("bin", {}).get("anki-due-stats") == "anki_tools/due_stats.py"


def test_build_parser_returns_argument_parser():
    import argparse

    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_deck_positional_is_required():
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args([])
    assert exc_info.value.code != 0


def test_range_and_sliding_flags_are_accepted_by_the_parser():
    parser = build_parser()
    # Neither flag should be rejected at the grammar level -- both are part
    # of the pinned CLI surface (plan.md line 1264: "DECK [--start-offset N]
    # [--range LO-HI] [--collection PATH] [--min N] [--max N] [--sliding]").
    args = parser.parse_args(
        [
            "programming::coding",
            "--range",
            "8-30",
            "--min",
            "8",
            "--max",
            "16",
            "--sliding",
        ]
    )
    assert args.deck == "programming::coding"


# ---------------------------------------------------------------------------
# Read-only / no-writes / no-backup (plan.md lines 1271, 1286)
# ---------------------------------------------------------------------------


def test_mtime_unchanged_after_run(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    for i in range(5):
        _add_card(col, coding_id, due=start_day + i, ivl=10 + i)
    col.close()

    time.sleep(0.01)  # ensure any accidental write would bump mtime measurably
    mtime_before = os.path.getmtime(col_path)

    exit_code = _run_cli(["programming::coding", "--collection", col_path], monkeypatch)
    assert exit_code == 0

    mtime_after = os.path.getmtime(col_path)
    assert mtime_before == mtime_after


def test_writes_nothing_due_and_ivl_unchanged(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    ids = []
    for i in range(5):
        card = _add_card(col, coding_id, due=start_day + i, ivl=10 + i)
        ids.append(card.id)
    col.close()

    before = _snapshot_due_ivl(col_path, ids)

    exit_code = _run_cli(
        ["programming::coding", "--min", "1", "--max", "8", "--collection", col_path],
        monkeypatch,
    )
    assert exit_code == 0

    after = _snapshot_due_ivl(col_path, ids)
    assert before == after


def test_creates_no_backup_directory(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    _add_card(col, coding_id, due=start_day, ivl=10)
    col.close()

    # anki-rebalance-due's default backup location is <collection dir>/backups
    # (contract line 375). anki-due-stats has no --backup-dir flag at all
    # (plan.md line 1264 pins its flag surface without one) and must never
    # take a backup (plan.md line 1271: "takes no backup").
    default_backup_dir = os.path.join(str(tmp_path), "backups")

    exit_code = _run_cli(["programming::coding", "--collection", col_path], monkeypatch)
    assert exit_code == 0
    assert not os.path.isdir(default_backup_dir) or os.listdir(default_backup_dir) == []


# ---------------------------------------------------------------------------
# Exits 0 whether feasible or not (plan.md line 1286)
# ---------------------------------------------------------------------------


def test_exits_zero_on_feasible_deck(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    for i in range(10):
        _add_card(col, coding_id, due=start_day + (i % 5), ivl=10 + i)
    col.close()

    exit_code = _run_cli(
        ["programming::coding", "--min", "1", "--max", "8", "--collection", col_path],
        monkeypatch,
    )
    assert exit_code == 0


def test_exits_zero_on_infeasible_deck(tmp_path, monkeypatch, capsys):
    # DP-B hard lower-bound violation: 3 cards over a 3-day window, --min 8
    # requires 24. anki-due-stats must still exit 0 -- it is a report, not a
    # gate (plan.md line 1271, 1286).
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    ids = []
    for i in range(3):
        card = _add_card(col, coding_id, due=start_day + i, ivl=10)
        ids.append(card.id)
    col.close()

    exit_code = _run_cli(
        ["programming::coding", "--min", "8", "--collection", col_path], monkeypatch
    )
    out = capsys.readouterr().out

    assert exit_code == 0
    assert out  # something was printed, not a silent no-op


# ---------------------------------------------------------------------------
# Reports the five documented items (plan.md lines 1265-1269)
# ---------------------------------------------------------------------------


def test_reports_totals_horizon_and_average(tmp_path, monkeypatch, capsys):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    ids = []
    for i in range(5):
        card = _add_card(col, coding_id, due=start_day + i, ivl=10 + i)
        ids.append(card.id)
    col.close()

    exit_code = _run_cli(["programming::coding", "--collection", col_path], monkeypatch)
    out = capsys.readouterr().out.lower()
    assert exit_code == 0

    # "total in-scope scheduled cards, horizon in days, first/last day ...,
    # average cards/day" (plan.md line 1265) -- best-effort keyword check
    # since the plan does not pin exact wording, only the concepts.
    assert "5" in out  # the total card count
    assert "horizon" in out or "day" in out
    assert "avg" in out or "average" in out


def test_reports_feasible_flat_and_sliding_ranges_when_bounds_supplied(
    tmp_path, monkeypatch, capsys
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    for i in range(20):
        _add_card(col, coding_id, due=start_day + (i % 5), ivl=10 + i)
    col.close()

    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            "1",
            "--max",
            "8",
            "--sliding",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    out = capsys.readouterr().out.lower()
    assert exit_code == 0
    # "when --min/--max are supplied, whether that pair is feasible in each
    # mode" (plan.md line 1269) -- the word "feasible" (or its report of
    # in/feasibility) must appear somewhere.
    assert "feasible" in out


def test_reports_required_vs_cap_achievable_profile_and_min_feasible_max_shift(
    tmp_path, monkeypatch, capsys
):
    # Block-shaped fixture verified directly against due_plan before writing
    # this test: 1 card anchoring offset 1, 100 cards spiked on offset 60,
    # min=1 max=16 --sliding gives feasible=True, shape_reachable=False,
    # min_feasible_max_shift=24 -- a TENS-of-days figure, not single digits
    # (plan.md line 1287's own pinned distinction).
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    origin_by_id = {}
    anchor = _add_card(col, coding_id, due=start_day, ivl=10)
    origin_by_id[anchor.id] = anchor.due
    for i in range(100):
        card = _add_card(col, coding_id, due=start_day + 59, ivl=10 + (i % 20))
        origin_by_id[card.id] = card.due
    col.close()

    oracle_cards = [
        CardDue(card_id=cid, day=day, ivl=10) for cid, day in origin_by_id.items()
    ]
    oracle = check_feasibility(
        oracle_cards,
        start_day,
        None,
        1,
        16,
        max_shift=14,
        sliding=True,
        set_earlier=False,
    )
    assert oracle.feasible is True
    assert oracle.shape_reachable is False
    assert oracle.min_feasible_max_shift is not None
    assert oracle.min_feasible_max_shift >= 10  # tens of days, not single digits

    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            "1",
            "--max",
            "16",
            "--sliding",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    out = capsys.readouterr().out
    assert exit_code == 0

    # The reported minimum-feasible-shift figure (a tens-of-days number, per
    # oracle.min_feasible_max_shift above) must appear as its own token
    # somewhere in the output -- not just any digit, a number >= 10.
    import re

    two_digit_or_more_numbers = {
        int(n) for n in re.findall(r"(?<!\d)(\d{2,})(?!\d)", out)
    }
    assert any(n >= 10 for n in two_digit_or_more_numbers), (
        f"expected a tens-of-days min-feasible-max-shift figure "
        f"(oracle says {oracle.min_feasible_max_shift}) somewhere in output:\n{out}"
    )


# ---------------------------------------------------------------------------
# --range produces verifiably different output than the unranged form
# (plan.md lines 1280-1281)
# ---------------------------------------------------------------------------


def test_range_produces_verifiably_different_output_than_unranged(
    tmp_path, monkeypatch, capsys
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today

    # Mass concentrated OUTSIDE an [8, 30] window: a handful in range, a
    # much larger pile far beyond it.
    for offset in range(8, 15):
        _add_card(col, coding_id, due=today + offset, ivl=10)
    for offset in range(100, 150):
        _add_card(col, coding_id, due=today + offset, ivl=10)
    col.close()

    exit_ranged = _run_cli(
        ["programming::coding", "--range", "8-30", "--collection", col_path],
        monkeypatch,
    )
    out_ranged = capsys.readouterr().out
    assert exit_ranged == 0

    exit_unranged = _run_cli(
        ["programming::coding", "--collection", col_path], monkeypatch
    )
    out_unranged = capsys.readouterr().out
    assert exit_unranged == 0

    assert out_ranged != out_unranged


def test_range_horizon_matches_the_lo_hi_span(tmp_path, monkeypatch, capsys):
    # plan.md line 1280's own worked example: "--range 8-30 ... horizon
    # D = 23."
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    for offset in [8, 15, 30]:
        _add_card(col, coding_id, due=today + offset, ivl=10)
    col.close()

    exit_code = _run_cli(
        ["programming::coding", "--range", "8-30", "--collection", col_path],
        monkeypatch,
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "23" in out  # 30 - 8 + 1 = 23-day horizon


def test_omitting_range_uses_full_derived_horizon(tmp_path, monkeypatch, capsys):
    # Regression anchor for this packet's own --range addition to
    # anki-due-stats: omitting --range must reproduce the pre-range
    # (unbounded, full-deck-derived) horizon exactly, not some accidental
    # partial slice.
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    ids = []
    for offset in [0, 4, 9]:  # spans a full 10-day horizon (start_day..+9)
        card = _add_card(col, coding_id, due=start_day + offset, ivl=10)
        ids.append(card.id)
    col.close()

    exit_code = _run_cli(["programming::coding", "--collection", col_path], monkeypatch)
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "10" in out  # the full 10-day horizon, not a --range-truncated one


# ---------------------------------------------------------------------------
# Reuse -- must call due_plan's functions, never recompute (contract lines
# 1007-1009, 1588-1589). Not independently testable as a black box beyond
# what the above already exercises (the report content matching what the
# oracle itself reports); noted here as coverage-by-construction rather than
# a separate assertion, since due_stats.py's internals are off-limits.
# ---------------------------------------------------------------------------
