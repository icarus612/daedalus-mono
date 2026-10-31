"""Tests for the phrase-sourced set-due command, against a fake collection."""

import argparse
from collections import namedtuple
from copy import deepcopy

import pytest
from anki.collection import Collection

from anki_tools.phrase_due_cli import (
    DUE_TODAY,
    PHRASE_DECK,
    build_parser,
    main,
    phrase_texts,
    scan,
    taught_notes,
)

NOUNS = "Russian - Mutable Nouns (Ellis Version)"
VERBS = "Russian - Mutable Verbs (Ellis Version)"
IMMUTABLE = "Russian - Immutable Words (Ellis Version)"
COMMON = "Russian - Common Words (Ellis Version) "
JAPANESE = "Japanese - Common Words (Ellis Version)"

NEW = 0
REVIEW = 2
NEW_QUEUE = 0
REVIEW_QUEUE = 2
SUSPENDED = -1


def test_build_parser_returns_argument_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_parser_prog_name():
    assert build_parser().prog == "anki-phrase-due"


def test_reporting_is_the_default():
    assert build_parser().parse_args([]).fix is False


def test_phrase_deck_defaults_to_the_consolidated_deck():
    assert build_parser().parse_args([]).deck == PHRASE_DECK
    assert PHRASE_DECK == "Languages::Russian::5. Russian Phrases"


def test_due_today_keeps_the_interval_and_never_rewrites_it():
    """`set_due_date("0!")` overwrites the interval -- a prior run used that
    form and rewrote 138 intervals. Only the plain form is allowed."""
    assert DUE_TODAY == "0"
    assert "!" not in DUE_TODAY


def test_taught_notes_reads_both_verb_aspects_and_skips_other_languages():
    col = _collection(
        taught=[
            (1, NOUNS, ["туалет", "toilet"]),
            (2, VERBS, ["фотографировать", "сфотографировать", "to photograph"]),
            (3, IMMUTABLE, ["в / во", "in"]),
        ],
        other_notes=[(4, JAPANESE, ["ねこ", "cat"]), (5, COMMON, ["Чек", "check"])],
    )
    assert dict(taught_notes(col)) == {
        1: ["туалет"],
        2: ["фотографировать", "сфотографировать"],
        3: ["в / во"],
    }


def test_phrase_texts_reads_the_headword_field_of_the_deck():
    col = _collection(phrase=["Можно сфотографировать?", "Чек, пожалуйста"])
    assert phrase_texts(col, [PHRASE_DECK_ID]) == [
        "Можно сфотографировать?",
        "Чек, пожалуйста",
    ]


def test_scan_reads_every_card_of_the_notes_it_is_given():
    col = _collection(cards=[(1, 10, NEW, NEW_QUEUE), (2, 11, REVIEW, REVIEW_QUEUE)])
    assert scan(col, [10]) == [(1, 10, NEW, NEW_QUEUE)]


def test_main_reports_nothing_to_do_on_a_fully_studied_collection(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, REVIEW, REVIEW_QUEUE), (2, 10, REVIEW, REVIEW_QUEUE)],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored"]) == 0
    assert "Nothing to do" in capsys.readouterr().out
    assert col.closed


def test_main_reports_an_all_new_phrase_word_without_fixing_it(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"]), (11, NOUNS, ["дом", "house"])],
        phrase=["Где туалет?"],
        cards=[
            (1, 10, NEW, NEW_QUEUE),
            (2, 10, NEW, NEW_QUEUE),
            (3, 11, NEW, NEW_QUEUE),
        ],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored"]) == 0
    out = capsys.readouterr().out
    assert "туалет" in out
    assert "дом" not in out
    assert "2 card(s)" in out
    assert "--fix" in out
    assert col.due_calls == []


def test_main_with_fix_sets_them_due_today_with_the_plain_form(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, NEW, NEW_QUEUE), (2, 10, NEW, NEW_QUEUE)],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored", "--fix"]) == 0
    assert col.due_calls == [([1, 2], "0")]
    assert "Made 2 card(s) due today" in capsys.readouterr().out


def test_main_rerun_after_a_fix_finds_nothing_left(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, NEW, NEW_QUEUE), (2, 10, NEW, NEW_QUEUE)],
    )
    _install(monkeypatch, col)
    main(["--collection", "ignored", "--fix"])
    out = capsys.readouterr().out
    assert "Still all-new afterwards: 0" in out


def test_main_never_sets_a_suspended_card_due_and_says_how_many(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, NEW, NEW_QUEUE), (2, 10, NEW, SUSPENDED)],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored", "--fix"]) == 0
    assert col.due_calls == [([1], "0")]
    assert 2 not in col.due_calls[0][0]
    assert (
        "1 more card(s) left alone because they are suspended"
        in capsys.readouterr().out
    )


def test_the_unsuspended_path_is_reachable_so_the_exclusion_proves_something(
    monkeypatch, capsys
):
    """Positive control: an all-new UNSUSPENDED word must reach set_due_date,
    or the suspended-exclusion assertions above pass vacuously."""
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, NEW, NEW_QUEUE), (2, 10, NEW, NEW_QUEUE)],
    )
    _install(monkeypatch, col)
    main(["--collection", "ignored", "--fix"])
    assert col.due_calls and sorted(col.due_calls[0][0]) == [1, 2]


def test_a_word_with_one_studied_card_is_left_for_counterpart_due(monkeypatch, capsys):
    col = _collection(
        taught=[(10, NOUNS, ["туалет", "toilet"])],
        phrase=["Где туалет?"],
        cards=[(1, 10, REVIEW, REVIEW_QUEUE), (2, 10, NEW, NEW_QUEUE)],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored", "--fix"]) == 0
    assert col.due_calls == []


def test_main_resolves_a_verb_by_its_perfective_aspect(monkeypatch, capsys):
    col = _collection(
        taught=[(10, VERBS, ["фотографировать", "сфотографировать", "photograph"])],
        phrase=["Можно сфотографировать?"],
        cards=[(i, 10, NEW, NEW_QUEUE) for i in (1, 2, 3, 4)],
    )
    _install(monkeypatch, col)
    assert main(["--collection", "ignored", "--fix"]) == 0
    assert col.due_calls == [([1, 2, 3, 4], "0")]


def test_main_returns_nonzero_for_a_deck_that_does_not_exist(monkeypatch, capsys):
    col = _collection()
    _install(monkeypatch, col)
    assert main(["--collection", "ignored", "--deck", "No::Such::Deck"]) == 1
    assert col.closed


def test_main_closes_the_collection_even_when_the_scan_raises(monkeypatch):
    col = _collection(raise_on_query=True)
    _install(monkeypatch, col)
    with pytest.raises(RuntimeError):
        main(["--collection", "ignored"])
    assert col.closed


PHRASE_DECK_ID = 1790710159549

_NameId = namedtuple("_NameId", "id name")


def _install(monkeypatch, col):
    monkeypatch.setattr("anki_tools.phrase_due_cli.Collection", lambda path: col)


def _collection(taught=(), other_notes=(), phrase=(), cards=(), raise_on_query=False):
    return _FakeCollection(taught, other_notes, phrase, cards, raise_on_query)


class _FakeDb:
    def __init__(self, collection):
        self._col = collection

    def all(self, sql, *params):
        if self._col.raise_on_query:
            raise RuntimeError("query blew up")
        if "from notes where mid in" in sql:
            wanted = set(params)
            return [
                (note_id, self._col.mid_of[name], "\x1f".join(fields))
                for note_id, name, fields in self._col.all_notes
                if self._col.mid_of[name] in wanted
            ]
        if "join cards" in sql:
            assert set(params) == {PHRASE_DECK_ID}
            return [(f"{text}\x1fgloss",) for text in self._col.phrase]
        if "from cards where nid in" in sql:
            wanted = set(params)
            return [row for row in self._col.cards if row[1] in wanted]
        raise AssertionError(f"unexpected query: {sql}")


class _FakeDecks:
    def id_for_name(self, name):
        return PHRASE_DECK_ID if name == PHRASE_DECK else None

    def deck_and_child_ids(self, deck_id):
        return [deck_id]

    def name(self, deck_id):
        return PHRASE_DECK


class _FakeModels:
    def __init__(self, mid_of):
        self._mid_of = mid_of

    def all_names_and_ids(self):
        return [_NameId(mid, name) for name, mid in self._mid_of.items()]


class _FakeSched:
    def __init__(self, collection):
        self._col = collection

    def set_due_date(self, card_ids, spec):
        self._col.due_calls.append((list(card_ids), spec))
        self._col.cards = [
            (cid, nid, 2 if cid in card_ids else card_type, queue)
            for cid, nid, card_type, queue in self._col.cards
        ]


class _FakeCollection:
    def __init__(self, taught, other_notes, phrase, cards, raise_on_query):
        self.all_notes = list(taught) + list(other_notes)
        self.phrase = list(phrase)
        self.cards = list(cards)
        self.raise_on_query = raise_on_query
        self.due_calls = []
        self.closed = False
        names = sorted({name for _, name, _ in self.all_notes} | {COMMON})
        self.mid_of = {name: index + 1 for index, name in enumerate(names)}
        self.db = _FakeDb(self)
        self.decks = _FakeDecks()
        self.models = _FakeModels(self.mid_of)
        self.sched = _FakeSched(self)

    def close(self):
        self.closed = True


def _taught_model(col, name):
    model = deepcopy(col.models.by_name("Basic (and reversed card)"))
    model["id"] = 0
    model["name"] = name
    col.models.add_dict(model)
    return col.models.by_name(name)


def _add(col, model, deck_id, front, back):
    note = col.new_note(model)
    note["Front"] = front
    note["Back"] = back
    col.add_note(note, deck_id)
    return note


def test_end_to_end_against_a_real_collection(tmp_path, monkeypatch, capsys):
    """The sweep over Anki's own tables, then the fix, then re-running it.

    Each `main` opens and closes the collection exactly as a real run does.
    The pre-fix assertion is the positive control: a scan that silently
    returned nothing would be indistinguishable from a clean collection,
    and the suspended and interval assertions would prove nothing.
    """
    path = str(tmp_path / "c.anki2")
    monkeypatch.setattr(
        "anki_tools.phrase_due_cli.Collection", lambda _ignored: Collection(path)
    )

    col = Collection(path)
    try:
        taught_model = _taught_model(col, NOUNS)
        basic = col.models.by_name("Basic")
        phrase_deck = col.decks.id(PHRASE_DECK, create=True)
        taught_deck = col.decks.id("Languages::Russian::3. Mutable Words", create=True)

        _add(col, basic, phrase_deck, "Где туалет?", "Where is the bathroom?")
        _add(col, basic, phrase_deck, "Чек, пожалуйста", "The check, please")
        _add(col, basic, phrase_deck, "Можно сфотографировать?", "May I photograph?")

        all_new = _add(col, taught_model, taught_deck, "туалет", "toilet")
        half_suspended = _add(col, taught_model, taught_deck, "чек", "check")
        started = _add(col, taught_model, taught_deck, "можно", "one may")
        untouched = _add(col, taught_model, taught_deck, "дом", "house")

        suspended_card = half_suspended.card_ids()[1]
        col.sched.suspend_cards([suspended_card])
        col.sched.set_due_date([started.card_ids()[0]], "5")
        col.sched.set_due_date(untouched.card_ids(), "7")
        untouched_before = {
            card_id: (col.get_card(card_id).ivl, col.get_card(card_id).due)
            for card_id in untouched.card_ids()
        }
        all_new_ids = all_new.card_ids()
        started_new_sibling = started.card_ids()[1]
        unsuspended_sibling = half_suspended.card_ids()[0]
    finally:
        col.close()

    assert main(["--collection", path]) == 0
    report = capsys.readouterr().out
    assert "туалет" in report and "чек" in report
    assert "можно" not in report
    assert "дом" not in report
    assert "1 more card(s) left alone because they are suspended" in report

    assert main(["--collection", path, "--fix"]) == 0
    assert "Still all-new afterwards: 0" in capsys.readouterr().out

    col = Collection(path)
    try:
        for card_id in all_new_ids:
            card = col.get_card(card_id)
            assert card.type != NEW
            assert card.due == col.sched.today

        assert col.get_card(suspended_card).queue == SUSPENDED
        assert col.get_card(suspended_card).type == NEW
        sibling = col.get_card(unsuspended_sibling)
        assert sibling.type != NEW
        assert sibling.due == col.sched.today

        assert col.get_card(started_new_sibling).type == NEW
        for card_id, before in untouched_before.items():
            card = col.get_card(card_id)
            assert (card.ivl, card.due) == before
    finally:
        col.close()


def test_anki_unsuspends_a_card_set_due_and_the_bang_form_rewrites_the_interval(
    tmp_path,
):
    """Why the exclusion and the plain `DUE_TODAY` form exist, asserted
    against Anki itself: without this the guards above are untestable
    claims about a library the tests never exercise.
    """
    col = Collection(str(tmp_path / "c.anki2"))
    try:
        basic = col.models.by_name("Basic")
        deck_id = col.decks.id("Hazard", create=True)
        suspended = _add(col, basic, deck_id, "x", "y").card_ids()[0]
        col.sched.suspend_cards([suspended])
        assert col.get_card(suspended).queue == SUSPENDED

        col.sched.set_due_date([suspended], DUE_TODAY)
        assert col.get_card(suspended).queue != SUSPENDED

        scheduled = _add(col, basic, deck_id, "a", "b").card_ids()[0]
        col.sched.set_due_date([scheduled], "1")
        interval = col.get_card(scheduled).ivl
        col.sched.set_due_date([scheduled], DUE_TODAY)
        assert col.get_card(scheduled).ivl == interval
        col.sched.set_due_date([scheduled], "690!")
        assert col.get_card(scheduled).ivl == 690
    finally:
        col.close()
