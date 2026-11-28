"""Contract tests for anki_tools.new_due, on scratch collections in tmp_path."""

import datetime
import os

import pytest
from anki.collection import Collection

from anki_tools.new_due import (
    DayGroup,
    NewDueError,
    apply,
    collection_today_date,
    histogram,
    main,
    offset_for_date,
    plan,
    read_guid_list,
)

TWO_CARD = "Basic (and reversed card)"
ONE_CARD = "Basic"


@pytest.fixture
def col(tmp_path):
    collection = Collection(os.path.join(str(tmp_path), "c.anki2"))
    yield collection
    try:
        collection.close()
    except Exception:
        pass


def add_note(col, model_name, deck_id, tag):
    note = col.new_note(col.models.by_name(model_name))
    note["Front"] = f"front {tag}"
    note["Back"] = f"back {tag}"
    col.add_note(note, deck_id)
    return note


def deck(col, name="Target"):
    return col.decks.id(name, create=True)


def make_notes(col, count, model_name=TWO_CARD, deck_id=None):
    deck_id = deck_id or deck(col)
    return [add_note(col, model_name, deck_id, f"n{i}") for i in range(count)]


def ordered_cards(col, note):
    cards = [col.get_card(cid) for cid in note.card_ids()]
    return [c.id for c in sorted(cards, key=lambda c: c.ord)]


def snapshot(col):
    return sorted(col.db.all("select id, type, queue, due, ivl from cards order by id"))


def test_read_guid_list_skips_blanks_and_comments_and_strips(tmp_path):
    path = tmp_path / "g.txt"
    path.write_text("  abc  \n\n# comment\nxyz\n   \n#another\n")
    assert read_guid_list(path) == ["abc", "xyz"]


def test_read_guid_list_duplicate_raises(tmp_path):
    path = tmp_path / "g.txt"
    path.write_text("abc\nxyz\nabc\n")
    with pytest.raises(NewDueError):
        read_guid_list(path)


def test_new_due_error_is_a_value_error():
    assert issubclass(NewDueError, ValueError)


def test_day_group_is_frozen():
    group = DayGroup(day_offset=1, card_ids=(1,), note_guids=("a",))
    with pytest.raises(Exception):
        group.day_offset = 2


def test_collection_today_date_is_local_date_of_day_start(col):
    expected = datetime.datetime.fromtimestamp(col.sched.day_cutoff - 86400).date()
    assert collection_today_date(col) == expected


def test_collection_today_date_is_today_or_yesterday_never_tomorrow(col):
    now_date = datetime.datetime.now().date()
    result = collection_today_date(col)
    assert now_date - datetime.timedelta(days=1) <= result <= now_date


def test_collection_today_date_maps_to_offset_zero(col):
    today = collection_today_date(col)
    assert offset_for_date(today, today) == 0
    assert offset_for_date(today + datetime.timedelta(days=1), today) == 1


def test_offset_for_date():
    today = datetime.date(2026, 11, 26)
    assert offset_for_date(datetime.date(2026, 11, 26), today) == 0
    assert offset_for_date(datetime.date(2026, 12, 1), today) == 5


def test_offset_for_date_negative_raises():
    with pytest.raises(NewDueError):
        offset_for_date(datetime.date(2026, 11, 25), datetime.date(2026, 11, 26))


def test_date_to_offset_lands_on_collection_today(col):
    today = collection_today_date(col)
    target = today + datetime.timedelta(days=4)
    assert offset_for_date(target, today) == 4


def test_siblings_on_groups_notes_per_day_and_colocates_cards(col):
    notes = make_notes(col, 5)
    guids = [n.guid for n in notes]
    groups = plan(col, guids, first_offset=2, per_day=4)
    assert [g.day_offset for g in groups] == [2, 3, 4]
    assert [len(g.card_ids) for g in groups] == [4, 4, 2]
    assert groups[0].note_guids == (guids[0], guids[1])
    assert groups[1].note_guids == (guids[2], guids[3])
    assert groups[2].note_guids == (guids[4],)
    expected = []
    for note in notes[:2]:
        expected += ordered_cards(col, note)
    assert list(groups[0].card_ids) == expected


def test_siblings_on_follows_input_order_not_collection_order(col):
    notes = make_notes(col, 3)
    guids = [notes[2].guid, notes[0].guid, notes[1].guid]
    groups = plan(col, guids, first_offset=0, per_day=2)
    assert [g.note_guids for g in groups] == [
        (notes[2].guid,),
        (notes[0].guid,),
        (notes[1].guid,),
    ]


def test_siblings_off_flattens_in_note_then_ord_order(col):
    notes = make_notes(col, 3)
    guids = [n.guid for n in notes]
    groups = plan(col, guids, first_offset=1, per_day=4, same_day_siblings=False)
    flat = []
    for note in notes:
        flat += ordered_cards(col, note)
    assert [g.day_offset for g in groups] == [1, 2]
    assert list(groups[0].card_ids) == flat[:4]
    assert list(groups[1].card_ids) == flat[4:]


def test_siblings_off_allows_odd_per_day_and_splits_a_note(col):
    notes = make_notes(col, 2)
    guids = [n.guid for n in notes]
    groups = plan(col, guids, first_offset=0, per_day=3, same_day_siblings=False)
    assert [len(g.card_ids) for g in groups] == [3, 1]
    assert groups[0].note_guids == (notes[0].guid, notes[1].guid)
    assert groups[1].note_guids == (notes[1].guid,)


def test_siblings_off_allows_mixed_card_counts(col):
    two = add_note(col, TWO_CARD, deck(col), "two")
    one = add_note(col, ONE_CARD, deck(col), "one")
    groups = plan(
        col, [two.guid, one.guid], first_offset=0, per_day=5, same_day_siblings=False
    )
    assert sum(len(g.card_ids) for g in groups) == 3


def test_plan_is_read_only(col):
    notes = make_notes(col, 3)
    before = snapshot(col)
    plan(col, [n.guid for n in notes], first_offset=0, per_day=2)
    assert snapshot(col) == before


def test_unknown_guid_refused(col):
    notes = make_notes(col, 1)
    with pytest.raises(NewDueError):
        plan(col, [notes[0].guid, "no-such-guid"], first_offset=0, per_day=2)


@pytest.mark.parametrize("per_day", [0, -2])
def test_non_positive_per_day_refused(col, per_day):
    notes = make_notes(col, 1)
    with pytest.raises(NewDueError):
        plan(col, [notes[0].guid], first_offset=0, per_day=per_day)


def test_siblings_on_per_day_not_multiple_of_card_count_refused(col):
    notes = make_notes(col, 2)
    with pytest.raises(NewDueError):
        plan(col, [n.guid for n in notes], first_offset=0, per_day=3)


def test_siblings_on_mixed_card_counts_refused(col):
    two = add_note(col, TWO_CARD, deck(col), "two")
    one = add_note(col, ONE_CARD, deck(col), "one")
    with pytest.raises(NewDueError):
        plan(col, [two.guid, one.guid], first_offset=0, per_day=2)


def test_siblings_on_single_card_notes(col):
    notes = make_notes(col, 3, model_name=ONE_CARD)
    groups = plan(col, [n.guid for n in notes], first_offset=0, per_day=2)
    assert [len(g.card_ids) for g in groups] == [2, 1]


def test_review_card_in_list_refused_positive_control(col):
    notes = make_notes(col, 2)
    guids = [n.guid for n in notes]
    assert plan(col, guids, first_offset=0, per_day=2)
    col.sched.set_due_date(ordered_cards(col, notes[1])[:1], "3")
    assert col.get_card(ordered_cards(col, notes[1])[0]).type != 0
    with pytest.raises(NewDueError):
        plan(col, guids, first_offset=0, per_day=2)


def test_suspended_card_refused(col):
    notes = make_notes(col, 2)
    guids = [n.guid for n in notes]
    col.sched.suspend_cards(ordered_cards(col, notes[0])[:1])
    with pytest.raises(NewDueError):
        plan(col, guids, first_offset=0, per_day=2)


def test_buried_card_refused(col):
    notes = make_notes(col, 2)
    guids = [n.guid for n in notes]
    col.sched.bury_cards(ordered_cards(col, notes[0])[:1])
    with pytest.raises(NewDueError):
        plan(col, guids, first_offset=0, per_day=2)


def test_apply_sets_due_relative_to_today_and_leaves_others_untouched(col):
    notes = make_notes(col, 4)
    other_deck = deck(col, "Elsewhere")
    elsewhere = add_note(col, TWO_CARD, other_deck, "else")
    studied = add_note(col, TWO_CARD, deck(col), "studied")
    studied_card = ordered_cards(col, studied)[0]
    col.sched.set_due_date([studied_card], "9")
    bystander = add_note(col, TWO_CARD, deck(col), "bystander")

    planned_ids = {cid for n in notes for cid in n.card_ids()}
    untouched_before = [row for row in snapshot(col) if row[0] not in planned_ids]

    groups = plan(col, [n.guid for n in notes], first_offset=3, per_day=4)
    apply(col, groups)

    for group in groups:
        for cid in group.card_ids:
            assert col.get_card(cid).due == col.sched.today + group.day_offset
    untouched_after = [row for row in snapshot(col) if row[0] not in planned_ids]
    assert untouched_after == untouched_before
    assert col.get_card(ordered_cards(col, bystander)[0]).type == 0
    assert col.get_card(ordered_cards(col, elsewhere)[0]).type == 0


def test_apply_day_assignment_matches_plan(col):
    notes = make_notes(col, 3)
    groups = plan(col, [n.guid for n in notes], first_offset=0, per_day=2)
    apply(col, groups)
    today = col.sched.today
    for i, note in enumerate(notes):
        for cid in note.card_ids():
            assert col.get_card(cid).due == today + i


def test_histogram_counts_planned_plus_existing_reviews_in_target_decks(col):
    notes = make_notes(col, 2)
    other_deck = deck(col, "Elsewhere")
    studied = add_note(col, ONE_CARD, deck(col), "studied")
    stray = add_note(col, ONE_CARD, other_deck, "stray")
    today = col.sched.today
    studied_card = studied.card_ids()[0]
    col.sched.set_due_date([studied_card], "1")
    col.sched.set_due_date(stray.card_ids(), "1")
    assert col.get_card(studied_card).due == today + 1

    groups = plan(col, [n.guid for n in notes], first_offset=1, per_day=2)
    hist = histogram(col, groups)
    assert hist == {1: 2 + 1, 2: 2}


def test_histogram_covers_only_group_days(col):
    notes = make_notes(col, 2)
    groups = plan(col, [n.guid for n in notes], first_offset=2, per_day=2)
    assert set(histogram(col, groups)) == {2, 3}


def write_guids(tmp_path, notes):
    path = tmp_path / "guids.txt"
    path.write_text("\n".join(n.guid for n in notes) + "\n")
    return path


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    return tmp_path


def build_collection(tmp_path, count=2):
    path = os.path.join(str(tmp_path), "cli.anki2")
    col = Collection(path)
    notes = make_notes(col, count)
    guid_file = write_guids(tmp_path, notes)
    ids = [cid for n in notes for cid in n.card_ids()]
    col.close()
    return path, guid_file, ids


def read_rows(path):
    col = Collection(path)
    try:
        return snapshot(col), col.sched.today
    finally:
        col.close()


def test_main_dry_run_writes_nothing_and_exits_zero(cli_env, capsys):
    path, guid_file, _ = build_collection(cli_env)
    before, _ = read_rows(path)
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--start-offset",
            "1",
            "--per-day",
            "2",
            "--dry-run",
        ]
    )
    assert code == 0
    assert capsys.readouterr().out.strip()
    after, _ = read_rows(path)
    assert after == before


def test_main_yes_applies_plan(cli_env):
    path, guid_file, ids = build_collection(cli_env)
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--start-offset",
            "2",
            "--per-day",
            "2",
            "--yes",
        ]
    )
    assert code == 0
    rows, today = read_rows(path)
    dues = {row[0]: row[3] for row in rows}
    assert dues[ids[0]] == dues[ids[1]] == today + 2
    assert dues[ids[2]] == dues[ids[3]] == today + 3


def test_main_first_due_date_maps_to_offset(cli_env):
    path, guid_file, ids = build_collection(cli_env, count=1)
    col = Collection(path)
    target = collection_today_date(col) + datetime.timedelta(days=5)
    col.close()
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--first-due",
            target.isoformat(),
            "--per-day",
            "2",
            "--yes",
        ]
    )
    assert code == 0
    rows, today = read_rows(path)
    assert {row[0]: row[3] for row in rows}[ids[0]] == today + 5


def test_main_first_due_collection_today_maps_to_offset_zero(cli_env):
    path, guid_file, ids = build_collection(cli_env, count=1)
    col = Collection(path)
    target = collection_today_date(col)
    col.close()
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--first-due",
            target.isoformat(),
            "--per-day",
            "2",
            "--yes",
        ]
    )
    assert code == 0
    rows, today = read_rows(path)
    assert {row[0]: row[3] for row in rows}[ids[0]] == today


def test_main_past_first_due_exits_one_with_stderr(cli_env, capsys):
    path, guid_file, _ = build_collection(cli_env, count=1)
    before, _ = read_rows(path)
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--first-due",
            "2000-01-01",
            "--per-day",
            "2",
            "--yes",
        ]
    )
    assert code == 1
    assert capsys.readouterr().err.strip()
    assert read_rows(path)[0] == before


def test_main_refusal_exits_one_and_writes_nothing(cli_env, capsys):
    path, guid_file, _ = build_collection(cli_env)
    before, _ = read_rows(path)
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--start-offset",
            "0",
            "--per-day",
            "3",
            "--yes",
        ]
    )
    assert code == 1
    assert capsys.readouterr().err.strip()
    assert read_rows(path)[0] == before


def test_main_no_same_day_siblings_allows_odd_per_day(cli_env):
    path, guid_file, ids = build_collection(cli_env)
    code = main(
        [
            "--collection",
            path,
            "--guid-file",
            str(guid_file),
            "--start-offset",
            "0",
            "--per-day",
            "3",
            "--no-same-day-siblings",
            "--yes",
        ]
    )
    assert code == 0
    rows, today = read_rows(path)
    dues = {row[0]: row[3] for row in rows}
    assert sorted(dues[i] for i in ids) == [today] * 3 + [today + 1]


@pytest.mark.parametrize(
    "extra",
    [
        [],
        ["--first-due", "2999-01-01", "--start-offset", "1"],
    ],
)
def test_main_requires_exactly_one_of_first_due_and_start_offset(cli_env, extra):
    path, guid_file, _ = build_collection(cli_env, count=1)
    with pytest.raises(SystemExit) as exc:
        main(
            ["--collection", path, "--guid-file", str(guid_file), "--per-day", "2"]
            + extra
        )
    assert exc.value.code != 0


def test_main_requires_guid_file_and_per_day(cli_env):
    path, _, _ = build_collection(cli_env, count=1)
    with pytest.raises(SystemExit) as exc:
        main(["--collection", path, "--start-offset", "0"])
    assert exc.value.code != 0
