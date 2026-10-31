"""Tests for the aspect-rule command, driven against a fake collection."""

import argparse

import pytest

from anki_tools.aspect_due import (
    NEW_TYPE,
    REVIEW_TYPE,
    RULE_GATE,
    RULE_SPACE,
    SUSPENDED_QUEUE,
    VERB_NOTE_TYPE,
)
from anki_tools.aspect_due_cli import build_parser, main, scan

TODAY = 1885

NEW = (NEW_TYPE, 0, 500)
DUE = (REVIEW_TYPE, 2, TODAY - 1)
SUSPENDED_DUE = (REVIEW_TYPE, SUSPENDED_QUEUE, TODAY - 1)

BOTH_PERFECTIVE_DUE = (1001, "делать", "сделать", [DUE, DUE, DUE, DUE])
ALL_FOUR_NEW = (1002, "стоить", "—", [NEW, NEW, NEW, NEW])
PERFECTIVE_AHEAD = (1003, "знать", "узнать", [NEW, NEW, DUE, DUE])
SUSPENDED_PERFECTIVE = (1004, "идти", "пойти", [NEW, NEW, DUE, SUSPENDED_DUE])


def test_build_parser_returns_argument_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_parser_prog_name():
    assert build_parser().prog == "anki-aspect-due"


def test_the_rule_must_be_named_explicitly():
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args([])
    assert exc.value.code != 0


@pytest.mark.parametrize("bad", ["Gate", "both", "spacing", ""])
def test_parser_rejects_a_rule_it_does_not_implement(bad):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--rule", bad])
    assert exc.value.code != 0


@pytest.mark.parametrize("rule", [RULE_GATE, RULE_SPACE])
def test_parser_accepts_both_rules(rule):
    assert build_parser().parse_args(["--rule", rule]).rule == rule


def test_reporting_is_the_default():
    args = build_parser().parse_args(["--rule", RULE_SPACE])
    assert args.fix is False
    assert args.include_new is False


def test_a_single_day_is_the_default_deferral():
    assert build_parser().parse_args(["--rule", RULE_SPACE]).days == 1


@pytest.mark.parametrize("bad", ["0", "-3"])
def test_parser_rejects_a_deferral_that_would_not_move_the_card(bad):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--rule", RULE_SPACE, "--days", bad])
    assert exc.value.code != 0


def test_scan_reads_only_the_verb_note_type():
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE, ALL_FOUR_NEW])
    rows = scan(collection)
    assert len(rows) == 8
    assert collection.db.queries
    sql, params = collection.db.queries[-1]
    assert params == [collection.models.by_name(VERB_NOTE_TYPE)["id"]]
    assert "notes" in sql and "cards" in sql


def test_scan_refuses_a_collection_without_the_verb_note_type():
    with pytest.raises(LookupError):
        scan(_FakeCollection([], note_type=None))


def test_report_mode_never_reschedules_anything(monkeypatch, capsys):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE, PERFECTIVE_AHEAD])
    _use(monkeypatch, collection)
    assert main(["--rule", RULE_SPACE, "--collection", "ignored"]) == 0
    assert collection.sched.due_calls == []
    assert collection.sched.reposition_calls == []
    out = capsys.readouterr().out
    assert "report only" in out
    assert "--fix" in out


def test_the_report_names_the_rule_it_applied(capsys, monkeypatch):
    _use(monkeypatch, _FakeCollection([BOTH_PERFECTIVE_DUE]))
    main(["--rule", RULE_GATE, "--collection", "ignored"])
    assert f"rule: {RULE_GATE}" in capsys.readouterr().out


def test_the_report_names_both_aspects_of_an_offending_note(monkeypatch, capsys):
    _use(monkeypatch, _FakeCollection([PERFECTIVE_AHEAD]))
    main(["--rule", RULE_GATE, "--collection", "ignored"])
    out = capsys.readouterr().out
    assert "знать" in out and "узнать" in out


def test_gate_and_space_select_differently_on_the_same_collection(monkeypatch, capsys):
    rows = [BOTH_PERFECTIVE_DUE]
    _use(monkeypatch, _FakeCollection(rows))
    main(["--rule", RULE_GATE, "--collection", "ignored"])
    gate_out = capsys.readouterr().out
    _use(monkeypatch, _FakeCollection(rows))
    main(["--rule", RULE_SPACE, "--collection", "ignored"])
    space_out = capsys.readouterr().out
    assert "0 perfective card(s)" in gate_out
    assert "1 perfective card(s)" in space_out


def test_fix_defers_with_the_plain_form_so_the_interval_survives(monkeypatch):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE])
    _use(monkeypatch, collection)
    assert main(["--rule", RULE_SPACE, "--collection", "ignored", "--fix"]) == 0
    assert len(collection.sched.due_calls) == 1
    card_ids, days = collection.sched.due_calls[0]
    assert days == "1"
    assert "!" not in days
    assert card_ids == [1001 * 10 + 3]


def test_fix_honours_a_longer_deferral(monkeypatch):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE])
    _use(monkeypatch, collection)
    main(["--rule", RULE_SPACE, "--collection", "ignored", "--fix", "--days", "4"])
    assert collection.sched.due_calls[0][1] == "4"


def test_fix_leaves_a_suspended_perfective_alone_and_says_so(monkeypatch, capsys):
    collection = _FakeCollection([SUSPENDED_PERFECTIVE])
    _use(monkeypatch, collection)
    main(["--rule", RULE_GATE, "--collection", "ignored", "--fix"])
    deferred = collection.sched.due_calls[0][0]
    assert deferred == [1004 * 10 + 2]
    assert collection.row_for(1004 * 10 + 3)[4] == SUSPENDED_QUEUE
    assert "suspended" in capsys.readouterr().out


def test_fix_converges_so_the_rule_holds_afterwards(monkeypatch, capsys):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE, PERFECTIVE_AHEAD])
    _use(monkeypatch, collection)
    assert main(["--rule", RULE_SPACE, "--collection", "ignored", "--fix"]) == 0
    assert "still breaking the rule: 0" in capsys.readouterr().out


def test_fix_never_turns_a_new_card_into_a_review_card(monkeypatch):
    collection = _FakeCollection([ALL_FOUR_NEW])
    _use(monkeypatch, collection)
    main(["--rule", RULE_GATE, "--collection", "ignored", "--fix"])
    assert collection.sched.due_calls == []
    for row in collection.rows:
        assert row[3] == NEW_TYPE


def test_new_cards_are_reported_but_left_in_place_without_include_new(
    monkeypatch, capsys
):
    collection = _FakeCollection([ALL_FOUR_NEW])
    _use(monkeypatch, collection)
    main(["--rule", RULE_GATE, "--collection", "ignored", "--fix"])
    assert collection.sched.reposition_calls == []
    assert "--include-new" in capsys.readouterr().out


def test_include_new_moves_them_to_the_back_without_shifting_the_queue(monkeypatch):
    collection = _FakeCollection([ALL_FOUR_NEW])
    _use(monkeypatch, collection)
    main(
        [
            "--rule",
            RULE_GATE,
            "--collection",
            "ignored",
            "--fix",
            "--include-new",
        ]
    )
    assert len(collection.sched.reposition_calls) == 1
    call = collection.sched.reposition_calls[0]
    assert call["card_ids"] == [1002 * 10 + 2, 1002 * 10 + 3]
    assert call["starting_from"] == collection.highest_new_position + 1
    assert call["randomize"] is False
    assert call["shift_existing"] is False


def test_include_new_without_fix_still_changes_nothing(monkeypatch):
    collection = _FakeCollection([ALL_FOUR_NEW])
    _use(monkeypatch, collection)
    main(["--rule", RULE_GATE, "--collection", "ignored", "--include-new"])
    assert collection.sched.reposition_calls == []


def test_nothing_to_do_on_a_collection_the_rule_already_holds_for(monkeypatch, capsys):
    collection = _FakeCollection([(1005, "жить", "пожить", [DUE, DUE, NEW, NEW])])
    _use(monkeypatch, collection)
    assert main(["--rule", RULE_GATE, "--collection", "ignored"]) == 0
    assert "Nothing to do" in capsys.readouterr().out


def test_the_fix_path_reaches_the_scheduler(monkeypatch):
    """Positive control: the report-mode assertions above are worthless if
    --fix cannot reach set_due_date at all."""
    collection = _FakeCollection([PERFECTIVE_AHEAD])
    _use(monkeypatch, collection)
    main(["--rule", RULE_GATE, "--collection", "ignored", "--fix"])
    assert collection.sched.due_calls != []


def test_the_collection_is_closed_even_when_the_scan_raises(monkeypatch):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE], raise_on_scan=True)
    _use(monkeypatch, collection)
    with pytest.raises(RuntimeError):
        main(["--rule", RULE_SPACE, "--collection", "ignored"])
    assert collection.closed


def test_the_collection_is_closed_after_a_normal_run(monkeypatch):
    collection = _FakeCollection([BOTH_PERFECTIVE_DUE])
    _use(monkeypatch, collection)
    main(["--rule", RULE_SPACE, "--collection", "ignored"])
    assert collection.closed


def test_a_collection_without_the_verb_note_type_exits_nonzero(monkeypatch, capsys):
    collection = _FakeCollection([], note_type=None)
    _use(monkeypatch, collection)
    assert main(["--rule", RULE_SPACE, "--collection", "ignored"]) == 2
    assert collection.closed


def _use(monkeypatch, collection):
    monkeypatch.setattr("anki_tools.aspect_due_cli.Collection", lambda path: collection)


class _FakeNote:
    def __init__(self, imperfective, perfective):
        self.fields = [imperfective, perfective]


class _FakeDb:
    def __init__(self, collection):
        self._collection = collection
        self.queries = []

    def all(self, sql, *params):
        self.queries.append((sql, list(params)))
        if self._collection.raise_on_scan:
            raise RuntimeError("scan blew up")
        return [tuple(row) for row in self._collection.rows]

    def scalar(self, sql, *params):
        self.queries.append((sql, list(params)))
        return self._collection.highest_new_position


class _FakeModels:
    def __init__(self, note_type):
        self._note_type = note_type

    def by_name(self, name):
        if name != VERB_NOTE_TYPE:
            return None
        return self._note_type


class _FakeScheduler:
    def __init__(self, collection):
        self._collection = collection
        self.today = TODAY
        self.due_calls = []
        self.reposition_calls = []

    def set_due_date(self, card_ids, days):
        self.due_calls.append((list(card_ids), days))
        if "!" in days:
            raise AssertionError("the interval-rewriting form must never be used")
        offset = int(days)
        for card_id in card_ids:
            row = self._collection.row_for(card_id)
            row[3] = REVIEW_TYPE
            row[5] = self.today + offset

    def reposition_new_cards(
        self, card_ids, starting_from, step_size, randomize, shift_existing
    ):
        self.reposition_calls.append(
            {
                "card_ids": list(card_ids),
                "starting_from": starting_from,
                "step_size": step_size,
                "randomize": randomize,
                "shift_existing": shift_existing,
            }
        )
        for index, card_id in enumerate(card_ids):
            self._collection.row_for(card_id)[5] = starting_from + index * step_size


class _FakeCollection:
    def __init__(self, notes, note_type=None, raise_on_scan=False):
        self.raise_on_scan = raise_on_scan
        self.closed = False
        self.highest_new_position = 900
        self.rows = []
        self._notes = {}
        for note_id, imperfective, perfective, states in notes:
            self._notes[note_id] = _FakeNote(imperfective, perfective)
            for card_ord, (card_type, queue, due) in enumerate(states):
                self.rows.append(
                    [note_id * 10 + card_ord, note_id, card_ord, card_type, queue, due]
                )
        if note_type is None and notes:
            note_type = {"id": 2868982455410308617, "name": VERB_NOTE_TYPE}
        self.models = _FakeModels(note_type)
        self.db = _FakeDb(self)
        self.sched = _FakeScheduler(self)

    def row_for(self, card_id):
        for row in self.rows:
            if row[0] == card_id:
                return row
        raise KeyError(card_id)

    def get_note(self, note_id):
        return self._notes[note_id]

    def close(self):
        self.closed = True
