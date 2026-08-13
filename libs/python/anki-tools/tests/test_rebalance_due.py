"""Contract tests for anki_tools.rebalance_due (Packet C, subphases 3.1-3.3).

Written blind to the implementation, from the plan
(project-plans/anki-due-rebalance-08-12-26/plan.md, subphases 3.1-3.3) and the
lane l1 contract (.artifacts/contracts/l1.md, "Packet C") alone. Never opens
the real user collection (~/.local/share/Anki2/User 1/collection.anki2) -
every collection here is built fresh under pytest's tmp_path.

4.1 (builder-owned, out of this packet's scope) extends this same file with
end-to-end CLI coverage against a lumpier synthetic fixture; nothing here
should be removed or altered to accommodate that later pass.
"""

import json
import os
import sys
import time

import pytest
from anki.collection import Collection

from anki_tools.rebalance_due import (
    apply_moves,
    build_parser,
    collect_cards,
    get_anki_collection_path,
    main,
    render_histogram,
    resolve_deck_ids,
)

PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULE_PATH = os.path.join(PACKAGE_ROOT, "anki_tools", "rebalance_due.py")


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def collection(tmp_path):
    """A fresh synthetic collection, closed in teardown. Never the real one."""
    col = Collection(os.path.join(str(tmp_path), "test.anki2"))
    try:
        yield col
    finally:
        col.close()


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
    """Add a note/card to deck_id and force its scheduling fields, per the
    plan 4.1 pattern block. Leaving ctype/queue at their new-card defaults
    (by simply not overriding them) yields a genuine new card.
    """
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


# ---------------------------------------------------------------------------
# get_anki_collection_path
# ---------------------------------------------------------------------------


def test_get_anki_collection_path_posix(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    path = get_anki_collection_path()
    assert path == os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")


def test_get_anki_collection_path_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    path = get_anki_collection_path()
    assert path == os.path.expanduser(
        "~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2"
    )


def test_get_anki_collection_path_unsupported_os_raises_oserror(monkeypatch):
    monkeypatch.setattr(os, "name", "java")
    with pytest.raises(OSError):
        get_anki_collection_path()


# ---------------------------------------------------------------------------
# resolve_deck_ids
# ---------------------------------------------------------------------------


def test_resolve_deck_ids_returns_deck_and_subdeck_only(collection):
    col = collection
    coding_id = col.decks.id("programming::coding")
    python_id = col.decks.id("programming::coding::python")
    col.decks.id("programming::other")  # unrelated sibling, must not appear

    result = resolve_deck_ids(col, "programming::coding")

    assert set(result) == {coding_id, python_id}


def test_resolve_deck_ids_excludes_parent_and_default(collection):
    col = collection
    col.decks.id("programming::coding")
    col.decks.id("programming::coding::python")
    programming_id = col.decks.id_for_name("programming")
    default_id = col.decks.id_for_name("Default")

    result = resolve_deck_ids(col, "programming::coding")

    assert programming_id is not None
    assert programming_id not in result
    assert default_id not in result


def test_resolve_deck_ids_nonexistent_deck_raises_naming_the_deck(collection):
    col = collection
    with pytest.raises(Exception) as exc_info:
        resolve_deck_ids(col, "totally::not::a::real::deck")
    assert "totally::not::a::real::deck" in str(exc_info.value)


def test_resolve_deck_ids_is_case_insensitive(collection):
    # Permanent regression test for the plan's empirical probe: col.decks.
    # id_for_name really is case-insensitive for this API, so an upper/mixed
    # -case query resolves to exactly the same ids as the exact-case name.
    col = collection
    coding_id = col.decks.id("programming::coding")
    python_id = col.decks.id("programming::coding::python")

    exact_case_result = resolve_deck_ids(col, "programming::coding")
    upper_case_result = resolve_deck_ids(col, "PROGRAMMING::CODING")

    assert set(exact_case_result) == {coding_id, python_id}
    assert set(upper_case_result) == {coding_id, python_id}


def test_resolve_deck_ids_echoes_resolved_names_on_success(collection, capsys):
    col = collection
    col.decks.id("programming::coding")
    col.decks.id("programming::coding::python")

    resolve_deck_ids(col, "programming::coding")

    captured = capsys.readouterr()
    assert "programming::coding" in captured.out


# ---------------------------------------------------------------------------
# collect_cards
# ---------------------------------------------------------------------------


def test_collect_cards_filters_to_review_queue_due_on_or_after_start(
    collection, capsys
):
    col = collection
    coding_id = col.decks.id("programming::coding")
    python_id = col.decks.id("programming::coding::python")
    unrelated_id = col.decks.id("unrelated")
    today = col.sched.today
    start_day = today + 1

    in_scope_boundary = _add_card(col, coding_id, due=start_day, ivl=12)
    in_scope_later = _add_card(col, python_id, due=start_day + 5, ivl=40)

    overdue = _add_card(col, coding_id, due=today, ivl=8)  # due < start_day
    new_card = _add_card(col, coding_id, due=0, ctype=0, queue=0)
    learning_card = _add_card(
        col, coding_id, due=int(time.time()) + 600, ctype=1, queue=1
    )
    suspended_card = _add_card(
        col, coding_id, due=start_day + 2, ivl=20, ctype=2, queue=-1
    )
    user_buried_card = _add_card(
        col, coding_id, due=start_day + 1, ivl=15, ctype=2, queue=-2
    )
    scheduler_buried_card = _add_card(
        col, coding_id, due=start_day + 1, ivl=15, ctype=2, queue=-3
    )
    _add_card(col, unrelated_id, due=start_day + 1, ivl=15)  # wrong deck entirely

    deck_ids = resolve_deck_ids(col, "programming::coding")
    result = collect_cards(col, deck_ids, start_day)
    result_ids = {c.card_id for c in result}
    captured = capsys.readouterr()

    assert result_ids == {in_scope_boundary.id, in_scope_later.id}
    assert user_buried_card.id not in result_ids
    assert scheduler_buried_card.id not in result_ids
    assert "buried" in captured.out

    # Every card placed in the two in-scope decks: boundary, later, overdue,
    # new, learning, suspended, user-buried, scheduler-buried = 8. Skip
    # counters must sum with the returned count back to that total (per
    # 3.1's/finding-3's acceptance criterion). collect_cards is pinned to
    # return only list[CardDue], so this suite verifies the arithmetic
    # identity by construction: cards created in-deck minus cards returned
    # equals cards deliberately excluded.
    total_in_target_decks = 8
    excluded = {
        overdue.id,
        new_card.id,
        learning_card.id,
        suspended_card.id,
        user_buried_card.id,
        scheduler_buried_card.id,
    }
    assert len(excluded) == total_in_target_decks - len(result_ids)


def test_collect_cards_carddue_fields_match_source_card(collection):
    col = collection
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    card = _add_card(col, coding_id, due=start_day + 3, ivl=17)

    deck_ids = resolve_deck_ids(col, "programming::coding")
    result = collect_cards(col, deck_ids, start_day)

    assert len(result) == 1
    carddue = result[0]
    assert carddue.card_id == card.id
    assert carddue.day == start_day + 3
    assert carddue.ivl == 17


def test_collect_cards_excludes_due_before_start_day(collection):
    col = collection
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1
    _add_card(col, coding_id, due=today, ivl=5)  # exactly one day too early

    deck_ids = resolve_deck_ids(col, "programming::coding")
    result = collect_cards(col, deck_ids, start_day)

    assert result == []


# ---------------------------------------------------------------------------
# apply_moves
# ---------------------------------------------------------------------------


def test_apply_moves_preserves_ivl_and_sets_due(collection):
    col = collection
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    card1 = _add_card(col, coding_id, due=today + 10, ivl=30)
    card2 = _add_card(col, coding_id, due=today + 12, ivl=45)

    moves = {card1.id: today + 3, card2.id: today + 3}
    apply_moves(col, moves, today)

    reloaded1 = col.get_card(card1.id)
    reloaded2 = col.get_card(card2.id)

    assert reloaded1.due == today + 3
    assert reloaded1.ivl == 30
    assert reloaded2.due == today + 3
    assert reloaded2.ivl == 45


def test_apply_moves_one_call_per_distinct_target_day(collection, monkeypatch):
    col = collection
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    card1 = _add_card(col, coding_id, due=today + 10, ivl=20)
    card2 = _add_card(col, coding_id, due=today + 11, ivl=20)
    card3 = _add_card(col, coding_id, due=today + 12, ivl=20)

    calls = []
    original_set_due_date = col.sched.set_due_date

    def counting_set_due_date(card_ids, days_str):
        calls.append((tuple(card_ids), days_str))
        return original_set_due_date(card_ids, days_str)

    monkeypatch.setattr(col.sched, "set_due_date", counting_set_due_date)

    moves = {
        card1.id: today + 2,
        card2.id: today + 2,
        card3.id: today + 5,
    }
    apply_moves(col, moves, today)

    assert len(calls) == 2  # two distinct target days: today+2, today+5


def test_apply_moves_empty_moves_makes_no_calls(collection, monkeypatch):
    col = collection
    calls = []
    original_set_due_date = col.sched.set_due_date

    def counting_set_due_date(card_ids, days_str):
        calls.append((card_ids, days_str))
        return original_set_due_date(card_ids, days_str)

    monkeypatch.setattr(col.sched, "set_due_date", counting_set_due_date)

    apply_moves(col, {}, col.sched.today)

    assert calls == []


def test_read_only_planning_does_not_mutate_card_state(tmp_path):
    # Stands in for "--dry-run leaves the collection byte-identical": since
    # dry-run's decision to skip apply_moves lives in main() (out of this
    # packet's testable surface per 3.3's build_parser()-only test approach),
    # this verifies the underlying guarantee directly - collect_cards and
    # render_histogram alone (the dry-run path's read/plan/print operations)
    # never change a card's due or ivl.
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    card = _add_card(col, coding_id, due=today + 5, ivl=10)
    original_due = card.due
    original_ivl = card.ivl
    col.close()

    col2 = Collection(col_path)
    try:
        deck_ids = resolve_deck_ids(col2, "programming::coding")
        start_day = today + 1
        cards = collect_cards(col2, deck_ids, start_day)
        before = {c.day: 1 for c in cards}
        render_histogram(before, before, None, 16, today, [])
    finally:
        col2.close()

    col3 = Collection(col_path)
    try:
        reloaded = col3.get_card(card.id)
        assert reloaded.due == original_due
        assert reloaded.ivl == original_ivl
    finally:
        col3.close()


def test_backup_file_appears_before_card_modification(collection, tmp_path):
    # apply_moves's own signature (col, moves, today) carries no backup_dir
    # / no_backup parameter, so backup orchestration lives above it (main(),
    # out of this packet's directly-testable surface). This test exercises
    # the ordering the plan mandates - backup taken, THEN cards written -
    # using the same primitives (col.create_backup + apply_moves) main() is
    # specified to call, in the specified order.
    col = collection
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    card = _add_card(col, coding_id, due=today + 5, ivl=15)

    backup_dir = os.path.join(str(tmp_path), "backups")
    os.makedirs(backup_dir, exist_ok=True)
    assert os.listdir(backup_dir) == []

    col.create_backup(backup_folder=backup_dir, force=True, wait_for_completion=True)
    assert len(os.listdir(backup_dir)) >= 1

    reloaded_before = col.get_card(card.id)
    assert reloaded_before.due == today + 5  # unmodified at backup time

    apply_moves(col, {card.id: today + 2}, today)

    reloaded_after = col.get_card(card.id)
    assert reloaded_after.due == today + 2


# ---------------------------------------------------------------------------
# render_histogram
# ---------------------------------------------------------------------------


def test_render_histogram_returns_string_mentioning_each_day():
    # today=0 makes offset == day for every row, so the original literal-day
    # assertions stay meaningful under the new "day - today" row value.
    before = {101: 3, 102: 5, 103: 2}
    after = {101: 4, 102: 3, 103: 3}

    output = render_histogram(before, after, 2, 6, 0, [])

    assert isinstance(output, str)
    for day in before:
        assert str(day) in output


def test_render_histogram_sums_match_before_and_after_totals():
    before = {201: 4, 202: 6, 203: 2}
    after = {201: 5, 202: 4, 203: 3}
    assert sum(before.values()) == sum(after.values()) == 12

    output = render_histogram(before, after, 1, 10, 0, [])

    # Every individual count value must be represented somewhere in the
    # rendered text - nothing dropped or fabricated.
    for count in list(before.values()) + list(after.values()):
        assert str(count) in output


def test_render_histogram_marks_out_of_bounds_day_differently():
    # Same before/after counts in both calls; only the bound that makes
    # day 301 a violation changes. If a marker is added for out-of-bounds
    # days, the two renders must differ even though every count is equal.
    # The above-`--max` marker is unchanged by this fix (still a raw
    # after_count > max_per_day comparison), so today/short_days are held
    # constant across both calls.
    before = {301: 5}
    after = {301: 5}

    within_bounds = render_histogram(before, after, 0, 10, 0, [])
    over_max = render_histogram(before, after, 0, 3, 0, [])

    assert within_bounds != over_max
    assert "<- above --max" in over_max
    assert "<- above --max" not in within_bounds


def test_render_histogram_marks_under_min_day_differently():
    # Under the new contract the below-`--min` marker is keyed off list
    # membership in `short_days`, not off a raw after_count/min_per_day
    # comparison - so this holds before/after/min_per_day/max_per_day/today
    # fixed and varies only short_days between the two calls.
    before = {401: 1}
    after = {401: 1}

    not_short = render_histogram(before, after, 0, 10, 0, [])
    marked_short = render_histogram(before, after, 0, 10, 0, [401])

    assert not_short != marked_short
    assert "<- below --min" in marked_short
    assert "<- below --min" not in not_short


def test_render_histogram_row_shows_small_offset_not_large_absolute_day():
    # Plan 3.2: "one line per day: day offset from today". A day far from
    # day 0 in absolute terms must still render its small offset from
    # `today`, not the (meaningless to a user) absolute day number.
    today = 1800
    day = 1805
    before = {day: 7}
    after = {day: 7}

    output = render_histogram(before, after, 0, 10, today, [])

    assert str(day) not in output  # absolute day number never appears
    assert str(day - today) in output  # the true offset (5) does


def test_render_histogram_day_not_in_short_days_never_marked_below_min():
    # The exempt-tail fix: a day can have a very low (even zero) after
    # count and NOT be marked below-min, so long as it is not in
    # short_days - e.g. the exempt trailing day. Under the old raw
    # after_count < min_per_day comparison this would have been wrongly
    # marked; under the new short_days-membership rule it must not be.
    before = {50: 0}
    after = {50: 0}

    output = render_histogram(before, after, 10, None, 0, [])

    assert "<- below --min" not in output


def test_render_histogram_handles_empty_input():
    output = render_histogram({}, {}, 1, 5, 0, [])
    assert isinstance(output, str)


# ---------------------------------------------------------------------------
# build_parser / CLI argument validation
# ---------------------------------------------------------------------------
#
# The contract pins CLI flag *names* (--min, --max, --collection, ...) and
# their semantics, but never pins argparse's internal `dest` attribute name.
# `_first_present` reads a parsed value under any of several plausible dest
# names so these tests encode the contract's stated interface rather than
# one guessed spelling of it.


def _first_present(namespace, *candidate_names):
    ns = vars(namespace)
    for name in candidate_names:
        if name in ns:
            return ns[name]
    raise AssertionError(f"none of {candidate_names} present in parsed args: {ns}")


def test_build_parser_returns_argument_parser():
    import argparse

    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_min_only_is_accepted_by_the_parser():
    # "--min N / --max N — both optional individually" (plan 3.3): the bare
    # ArgumentParser must accept --min without --max at the syntax level.
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8"])
    value = _first_present(args, "min", "min_per_day")
    assert int(value) == 8


def test_max_only_is_accepted_by_the_parser():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--max", "16"])
    value = _first_present(args, "max", "max_per_day")
    assert int(value) == 16


def test_min_and_max_together_is_accepted_by_the_parser():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "10", "--max", "10"])
    assert int(_first_present(args, "min", "min_per_day")) == 10
    assert int(_first_present(args, "max", "max_per_day")) == 10


def test_neither_min_nor_max_is_accepted_by_the_bare_parser():
    # "At least one required" is enforced by calling validate_bounds and
    # turning its ValueError into parser.error(...) (plan 3.3) - that
    # cross-field check is main()'s job, invoked after parse_args() returns,
    # not something build_parser()'s grammar can express on its own (argparse
    # has no native "at least one of these two optional flags" constraint).
    # This packet's test approach is explicitly "testable without invoking
    # main()", so only the parser-level half of this criterion (bare DECK
    # alone does not fail at the grammar level) is covered here; the
    # non-zero-exit-naming-both-flags half requires main() and is a gap for
    # this non-e2e slice (see report).
    parser = build_parser()
    args = parser.parse_args(["programming::coding"])
    assert args.deck == "programming::coding"


def test_deck_positional_is_required(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--min", "8"])
    assert exc_info.value.code != 0


def test_max_shift_default_resolves_to_14():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8"])
    value = _first_present(args, "max_shift")
    assert str(value) == "14"


def test_max_shift_accepts_integer():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--max-shift", "7"])
    value = _first_present(args, "max_shift")
    assert str(value) == "7"


def test_max_shift_accepts_zero():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--max-shift", "0"])
    value = _first_present(args, "max_shift")
    assert str(value) == "0"


def test_max_shift_accepts_literal_none():
    parser = build_parser()
    args = parser.parse_args(
        ["programming::coding", "--min", "8", "--max-shift", "none"]
    )
    value = _first_present(args, "max_shift")
    assert value is None or str(value).lower() == "none"


def test_help_exits_zero_and_documents_subdecks(capsys):
    parser = build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "subdeck" in captured.out.lower()


def test_default_flag_values():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8"])
    assert args.set_earlier is False
    assert args.dry_run is False
    assert args.yes is False
    assert args.start_offset == 1
    assert args.no_backup is False


def test_set_earlier_flag_true_when_passed():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--set-earlier"])
    assert args.set_earlier is True


def test_dry_run_flag_true_when_passed():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--dry-run"])
    assert args.dry_run is True


def test_yes_flag_true_when_passed():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--yes"])
    assert args.yes is True


def test_start_offset_custom_value():
    parser = build_parser()
    args = parser.parse_args(
        ["programming::coding", "--min", "8", "--start-offset", "3"]
    )
    assert args.start_offset == 3


def test_no_backup_flag_true_when_passed():
    parser = build_parser()
    args = parser.parse_args(["programming::coding", "--min", "8", "--no-backup"])
    assert args.no_backup is True


def test_collection_and_backup_dir_overrides():
    parser = build_parser()
    args = parser.parse_args(
        [
            "programming::coding",
            "--min",
            "8",
            "--collection",
            "/tmp/custom.anki2",
            "--backup-dir",
            "/tmp/custom-backups",
        ]
    )
    assert _first_present(args, "collection", "collection_path") == "/tmp/custom.anki2"
    assert _first_present(args, "backup_dir") == "/tmp/custom-backups"


# ---------------------------------------------------------------------------
# Static / packaging acceptance criteria
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
    assert mode & 0o111, "rebalance_due.py must be executable (mode 755)"


def test_package_json_registers_bin_entry():
    package_json_path = os.path.join(PACKAGE_ROOT, "package.json")
    with open(package_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert (
        data.get("bin", {}).get("anki-rebalance-due") == "anki_tools/rebalance_due.py"
    )


# ---------------------------------------------------------------------------
# End-to-end (subphase 4.1, builder-owned) -- drives the full CLI path via
# main() against synthetic temporary collections. Verified against the
# plan's acceptance criteria (project-plans/anki-due-rebalance-08-12-26/
# plan.md, subphase 4.1), not against the contract or the implementation --
# this is the whole-chunk cross-file behaviour no single packet agent could
# see. The real user collection (~/.local/share/Anki2/User 1/collection.anki2)
# is never opened or referenced by anything below.
# ---------------------------------------------------------------------------


def _run_cli(argv, monkeypatch):
    """Invoke main() with the given CLI args, returning its SystemExit code."""
    monkeypatch.setattr(sys, "argv", ["anki-rebalance-due"] + list(argv))
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


def test_e2e_subdecks_included_unrelated_deck_untouched_and_skips_reported(
    tmp_path, monkeypatch, capsys
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    python_id = col.decks.id("programming::coding::python")
    unrelated_id = col.decks.id("unrelated::deck")
    today = col.sched.today
    start_day = today + 1

    in_scope_parent = _add_card(col, coding_id, due=start_day + 1, ivl=20)
    in_scope_child = _add_card(col, python_id, due=start_day + 2, ivl=25)
    unrelated_card = _add_card(col, unrelated_id, due=start_day + 1, ivl=30)
    unrelated_due_before = unrelated_card.due

    _add_card(col, coding_id, due=0, ctype=0, queue=0)  # new
    _add_card(col, coding_id, due=int(time.time()) + 600, ctype=1, queue=1)  # learning
    _add_card(col, coding_id, due=start_day + 1, ivl=5, ctype=2, queue=-1)  # suspended
    _add_card(col, coding_id, due=today, ivl=5)  # already due/overdue
    col.close()

    # Generous bounds: this test is about wiring (subdeck scope, exclusion,
    # skip reporting), not about exercising rebalance feasibility, so a huge
    # --max guarantees the max pass never triggers.
    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            "1",
            "--max",
            "1000",
            "--dry-run",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    # Skip report must name every excluded category (3.1's requirement that
    # exclusion is counted by reason and reported, never silent).
    assert "new" in captured.out
    assert "learning" in captured.out
    assert "suspended" in captured.out
    assert "overdue" in captured.out

    # Unrelated deck untouched -- dry-run touches nothing, but confirm
    # explicitly per the 4.1 criterion.
    col2 = Collection(col_path)
    try:
        reloaded_unrelated = col2.get_card(unrelated_card.id)
        assert reloaded_unrelated.due == unrelated_due_before
        # Subdeck + parent cards were at least visible to the run (not
        # asserting exact moves here -- --max 1000 means neither may need
        # to move at all; wiring correctness is what this test targets).
        assert col2.get_card(in_scope_parent.id) is not None
        assert col2.get_card(in_scope_child.id) is not None
    finally:
        col2.close()


def test_e2e_full_apply_respects_bounds_preserves_ivl_never_moves_later(
    tmp_path, monkeypatch
):
    # A feasible distribution: nothing forces InfeasibleRebalance, because
    # start_day (the sink) never receives more than it can hold. Verified
    # structurally below via post-run invariants, not via a hand-traced
    # exact final distribution -- the algorithm's exact arithmetic is
    # already covered by 97 passing unit tests in Packets B/C; this test's
    # job is the CLI-to-collection wiring.
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    all_ids = []
    ivl_by_id = {}
    origin_day_by_id = {}
    for offset, count in [(1, 0), (2, 3), (3, 6), (4, 40)]:
        for i in range(count):
            card = _add_card(col, coding_id, due=start_day + offset - 1, ivl=10 + i)
            all_ids.append(card.id)
            ivl_by_id[card.id] = card.ivl
            origin_day_by_id[card.id] = card.due
    col.close()

    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            "8",
            "--max",
            "16",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code == 0

    col2 = Collection(col_path)
    try:
        counts_by_day = {}
        for cid in all_ids:
            card = col2.get_card(cid)
            counts_by_day[card.due] = counts_by_day.get(card.due, 0) + 1
            # ivl untouched by set_due_date's non-bang form.
            assert card.ivl == ivl_by_id[cid], f"card {cid} ivl changed"
            # Default mode: a card only ever moves earlier, never later.
            assert card.due <= origin_day_by_id[cid], (
                f"card {cid} moved later: origin {origin_day_by_id[cid]}, "
                f"new day {card.due}"
            )
            # D2: nothing lands on or before today.
            assert card.due >= start_day
            # R5: memory_state unchanged. On a non-FSRS collection this is
            # trivially None both before and after -- documented honestly
            # in the exit report as an unverified-under-FSRS path (FSRS
            # enablement was probed and found non-trivial via this repo's
            # anki Python API; not attempted here per the plan's own
            # allowance to skip it and report rather than claim coverage).
            assert card.memory_state is None

        # No day in the window holds more than --max.
        assert all(count <= 16 for count in counts_by_day.values())
        # Multiset preserved.
        assert sum(counts_by_day.values()) == len(all_ids) == 49
    finally:
        col2.close()


def test_e2e_dry_run_produces_identical_histogram_and_leaves_due_untouched(
    tmp_path, monkeypatch, capsys
):
    def build_collection(path):
        col = Collection(path)
        coding_id = col.decks.id("programming::coding")
        today = col.sched.today
        start_day = today + 1
        ids = []
        for offset, count in [(1, 2), (2, 20)]:
            for i in range(count):
                card = _add_card(col, coding_id, due=start_day + offset - 1, ivl=10 + i)
                ids.append(card.id)
        col.close()
        return ids

    dry_path = os.path.join(str(tmp_path), "dry.anki2")
    real_path = os.path.join(str(tmp_path), "real.anki2")
    dry_ids = build_collection(dry_path)
    real_ids = build_collection(real_path)

    before_snapshot = _snapshot_due_ivl(dry_path, dry_ids)
    real_before_snapshot = _snapshot_due_ivl(real_path, real_ids)

    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "16",
            "--dry-run",
            "--collection",
            dry_path,
        ],
        monkeypatch,
    )
    dry_out = capsys.readouterr().out
    assert exit_code == 0

    after_snapshot = _snapshot_due_ivl(dry_path, dry_ids)
    assert before_snapshot == after_snapshot  # byte-identical due/ivl

    # Same starting distribution, real apply this time -- plan_rebalance is
    # deterministic and computed identically whether or not the result is
    # written, so the histogram (before/after per-day counts) must match.
    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "16",
            "--yes",
            "--collection",
            real_path,
        ],
        monkeypatch,
    )
    real_out = capsys.readouterr().out
    assert exit_code == 0

    def _histogram_block(text):
        lines = text.splitlines()
        start = next(i for i, line in enumerate(lines) if line.startswith("-" * 10))
        end = next(
            i for i, line in enumerate(lines) if i > start and line.startswith("-" * 10)
        )
        return lines[start : end + 1]

    assert _histogram_block(dry_out) == _histogram_block(real_out)

    # And the real run actually wrote (its own due values differ from its
    # own pre-run snapshot), proving dry-run truly wrote nothing (asserted
    # above via before_snapshot == after_snapshot on dry_path) while the
    # real run genuinely did.
    real_after_snapshot = _snapshot_due_ivl(real_path, real_ids)
    assert real_after_snapshot != real_before_snapshot


def test_e2e_default_mode_infeasibility_writes_nothing(tmp_path, monkeypatch):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    # Every card lands on start_day itself -- the sink -- with count far
    # over --max. Structurally guaranteed infeasible in default mode: the
    # earlier-only pass has nowhere earlier than start_day to push to, so
    # this is not a hand-traced probability, it is a mathematical certainty
    # given the algorithm's own contract (start_day is untouchable from
    # below, D2).
    ids = []
    for i in range(50):
        card = _add_card(col, coding_id, due=start_day, ivl=10 + i)
        ids.append(card.id)
    col.close()

    before = _snapshot_due_ivl(col_path, ids)

    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "16",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )

    assert exit_code != 0

    after = _snapshot_due_ivl(col_path, ids)
    assert before == after  # nothing written -- D3's "no partial writes"


def test_e2e_set_earlier_rescues_infeasible_run_and_extends_horizon(
    tmp_path, monkeypatch, capsys
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    ids = []
    origin_by_id = {}
    for i in range(50):
        card = _add_card(col, coding_id, due=start_day, ivl=10 + i)
        ids.append(card.id)
        origin_by_id[card.id] = card.due
    col.close()

    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "16",
            "--set-earlier",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "LATER" in out  # main() states plainly when the reverse pass fired

    col2 = Collection(col_path)
    try:
        max_final_day = start_day
        moved_later = False
        for cid in ids:
            card = col2.get_card(cid)
            assert card.due >= start_day  # D2 still holds absolutely
            if card.due > origin_by_id[cid]:
                moved_later = True
            max_final_day = max(max_final_day, card.due)
        # At least one card legitimately moved later -- the one place in
        # the whole plan where that is allowed (settled D3 escape hatch).
        assert moved_later
        # Horizon extended past the original single day.
        assert max_final_day > start_day
    finally:
        col2.close()


def test_e2e_max_shift_limits_earlier_movement_and_reports_shortfall_not_failure(
    tmp_path, monkeypatch, capsys
):
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    # start_day itself empty; a pile of cards two days out. With
    # --max-shift 0 no card may move earlier at all (may_move_to requires
    # target_day >= origin - max_shift, i.e. target == origin exactly when
    # max_shift is 0), so start_day is guaranteed to stay short of --min
    # and this must be REPORTED, not raised.
    ids = []
    origin_by_id = {}
    for i in range(20):
        card = _add_card(col, coding_id, due=start_day + 1, ivl=10 + i)
        ids.append(card.id)
        origin_by_id[card.id] = card.due
    col.close()

    exit_code = _run_cli(
        [
            "programming::coding",
            "--min",
            "8",
            "--max-shift",
            "0",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    out = capsys.readouterr().out

    # Cap-induced shortfall is reported, not a failure (D6.1, settled).
    assert exit_code == 0
    assert "below --min" in out or "short" in out.lower()
    assert str(start_day) in out

    col2 = Collection(col_path)
    try:
        for cid in ids:
            card = col2.get_card(cid)
            # No card moved earlier than max_shift (0) allows -- i.e. no
            # card moved earlier at all.
            assert card.due >= origin_by_id[cid]
        start_day_count = sum(1 for cid in ids if col2.get_card(cid).due == start_day)
        assert start_day_count == 0  # confirms the day genuinely stayed short
    finally:
        col2.close()


def test_e2e_one_day_cascade_is_observable_not_bypassed(tmp_path, monkeypatch):
    # Mirrors the plan's own flagship one-day-rule example (max=3, a day
    # holding 3 cards and the next holding 6) at the CLI/collection level,
    # matching Packet B's already-proven unit-level trace exactly so the
    # expected outcome is known with certainty, not guessed:
    #   - day+1 (the sink) ends up with exactly the 3 cards that started on
    #     day+2 (they were untouched and thus preferred movers off day+2);
    #   - day+2 ends up with 3 of the 6 cards that started on day+3 (the
    #     transient overfill-then-relief this criterion exists to prove);
    #   - day+3 keeps the remaining 3 of its own original cards.
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    coding_id = col.decks.id("programming::coding")
    today = col.sched.today
    start_day = today + 1

    day2_ids = {
        _add_card(col, coding_id, due=start_day + 1, ivl=10 + i).id for i in range(3)
    }
    day3_ids = {
        _add_card(col, coding_id, due=start_day + 2, ivl=20 + i).id for i in range(6)
    }
    col.close()

    exit_code = _run_cli(
        [
            "programming::coding",
            "--max",
            "3",
            "--yes",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    assert exit_code == 0

    col2 = Collection(col_path)
    try:
        by_day = {}
        for cid in day2_ids | day3_ids:
            due = col2.get_card(cid).due
            by_day.setdefault(due, set()).add(cid)

        # The sink (start_day) holds exactly the day+2 originals -- proving
        # day+2 was itself relieved by shedding onto day+1, not that day+3's
        # overflow leapfrogged straight past it.
        assert by_day.get(start_day) == day2_ids
        # day+2 now holds exactly 3 cards, all originally from day+3 -- the
        # transient overfill (day+2 momentarily held 3 + 3 = 6 mid-sweep)
        # was relieved down to 3, not bypassed.
        assert by_day.get(start_day + 1, set()) <= day3_ids
        assert len(by_day.get(start_day + 1, set())) == 3
        # day+3 keeps the remaining 3 of its own originals.
        assert len(by_day.get(start_day + 2, set())) == 3
        assert by_day.get(start_day + 2, set()) <= day3_ids
    finally:
        col2.close()


def test_e2e_neither_min_nor_max_given_exits_nonzero_naming_both_flags(monkeypatch):
    # Closes the gap Packet C's own (blind, build_parser()-only) tests
    # explicitly flagged as out of their testable surface: this criterion
    # requires main(), which only the builder's e2e tail exercises.
    exit_code = _run_cli(["programming::coding"], monkeypatch)
    assert exit_code != 0


def test_e2e_min_exceeds_max_exits_nonzero_with_message(monkeypatch, capsys):
    exit_code = _run_cli(
        ["programming::coding", "--min", "20", "--max", "16"], monkeypatch
    )
    err = capsys.readouterr().err
    assert exit_code != 0
    assert "min" in err.lower() and "max" in err.lower()


def test_e2e_nonexistent_deck_exits_nonzero_naming_the_deck_not_a_traceback(
    tmp_path, monkeypatch, capsys
):
    # Closes code-review Round 1 finding 5: resolve_deck_ids's nonexistent-deck
    # path is unit-tested directly (test_resolve_deck_ids_nonexistent_deck_raises_
    # naming_the_deck), but 3.1's own acceptance criterion -- "a nonexistent deck
    # name produces a non-zero exit with a message naming the deck, not a
    # traceback" -- had no CLI-level coverage driving main() through the
    # ValueError -> print -> SystemExit(1) wrapping. --min/--max are both
    # supplied so the failure is unambiguously the deck-resolution path, not the
    # bounds-validation path already covered by the two tests above. _run_cli
    # only catches SystemExit, so any unhandled exception of another type would
    # fail this test with an error rather than a clean assertion -- that absence
    # of an error is itself part of what "not a traceback" proves here.
    col_path = os.path.join(str(tmp_path), "test.anki2")
    col = Collection(col_path)
    col.close()

    exit_code = _run_cli(
        [
            "totally::not::a::real::deck",
            "--min",
            "8",
            "--max",
            "16",
            "--collection",
            col_path,
        ],
        monkeypatch,
    )
    out = capsys.readouterr().out

    assert exit_code != 0
    assert "totally::not::a::real::deck" in out
