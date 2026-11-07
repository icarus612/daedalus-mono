import argparse

import pytest

from anki_tools import flagged_audio
from anki_tools.flagged_audio_cli import HEADWORD_FIELDS, SLOTS, build_parser, main

MUTABLE_NOUNS = "Russian - Mutable Nouns (Ellis Version)"
IMMUTABLE = flagged_audio.IMMUTABLE_NOTE_TYPE


def test_build_parser_returns_argument_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_parser_prog_name():
    assert build_parser().prog == "anki-flagged-audio"


def test_reporting_is_the_default():
    assert build_parser().parse_args([]).fix is False


def test_flag_is_repeatable_and_collects_colours():
    args = build_parser().parse_args(["--flag", "1", "--flag", "4"])
    assert args.flags == [1, 4]


def test_flag_defaults_to_none_meaning_every_colour():
    assert build_parser().parse_args([]).flags is None


@pytest.mark.parametrize("bad", ["0", "8", "-1"])
def test_parser_rejects_a_colour_anki_has_no_flag_for(bad):
    with pytest.raises(SystemExit) as exc:
        build_parser().parse_args(["--flag", bad])
    assert exc.value.code != 0


def test_slots_match_the_voice_counts_the_two_families_use():
    assert SLOTS[flagged_audio.MODE_SINGLE] == ("f1", "m2")
    assert SLOTS[flagged_audio.MODE_DOUBLE] == ("f1", "f2", "m1", "m2")
    assert set(SLOTS) == {flagged_audio.MODE_SINGLE, flagged_audio.MODE_DOUBLE}


def test_headword_fields_cover_both_families_and_verb_aspects():
    assert "Russian" in HEADWORD_FIELDS
    assert "Imperfective" in HEADWORD_FIELDS and "Perfective" in HEADWORD_FIELDS


def test_main_reports_nothing_to_do_on_an_unflagged_collection(monkeypatch, capsys):
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: _FakeCollection([])
    )
    assert main(["--collection", "ignored"]) == 0
    assert "no flagged cards" in capsys.readouterr().out


def test_main_reports_without_regenerating(monkeypatch, capsys):
    rows = [(4, MUTABLE_NOUNS, ["школа"]), (1, IMMUTABLE, ["как (conjunction)"])]
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: _FakeCollection(rows)
    )
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.regenerate", _forbidden_regenerate
    )
    assert main(["--collection", "ignored"]) == 0
    out = capsys.readouterr().out
    assert "Blue" in out and "Red" in out
    assert "школа" in out and "как (conjunction)" in out
    assert "6 file(s)" in out
    assert "report only" in out


def test_main_with_fix_drives_word_audio_once_per_mode(monkeypatch, capsys):
    rows = [(4, MUTABLE_NOUNS, ["школа"]), (1, IMMUTABLE, ["как (conjunction)"])]
    calls = []
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: _FakeCollection(rows)
    )
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.regenerate",
        lambda mode, words: calls.append((mode, words)) or 0,
    )
    assert main(["--collection", "ignored", "--fix"]) == 0
    assert dict(calls) == {
        flagged_audio.MODE_SINGLE: ["школа"],
        flagged_audio.MODE_DOUBLE: ["как (conjunction)"],
    }
    assert "cleared the flag on 2 regenerated card(s)" in capsys.readouterr().out


def test_main_returns_nonzero_when_a_regeneration_fails(monkeypatch):
    rows = [(4, MUTABLE_NOUNS, ["школа"])]
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: _FakeCollection(rows)
    )
    monkeypatch.setattr("anki_tools.flagged_audio_cli.regenerate", lambda m, w: 1)
    assert main(["--collection", "ignored", "--fix"]) == 1


def test_fix_clears_only_the_picked_flags_after_success(monkeypatch):
    rows = [(4, MUTABLE_NOUNS, ["школа"]), (1, IMMUTABLE, ["как (conjunction)"])]
    collection = _FakeCollection(rows)
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: collection
    )
    monkeypatch.setattr("anki_tools.flagged_audio_cli.regenerate", lambda m, w: 0)
    assert main(["--collection", "ignored", "--fix", "--flag", "4"]) == 0
    assert collection.cleared == (0, [0])


def test_failed_regeneration_leaves_flags(monkeypatch):
    collection = _FakeCollection([(4, MUTABLE_NOUNS, ["школа"])])
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: collection
    )
    monkeypatch.setattr("anki_tools.flagged_audio_cli.regenerate", lambda m, w: 1)
    assert main(["--collection", "ignored", "--fix"]) == 1
    assert not hasattr(collection, "cleared")


def test_main_closes_the_collection_even_when_the_scan_raises(monkeypatch):
    collection = _FakeCollection([(4, MUTABLE_NOUNS, ["школа"])], raise_on_scan=True)
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection", lambda path: collection
    )
    with pytest.raises(RuntimeError):
        main(["--collection", "ignored"])
    assert collection.closed


def test_the_fix_path_check_catches_the_shape_it_guards(monkeypatch):
    """Positive control: --fix must actually reach regenerate, or the
    forbidden-call assertion in the report test proves nothing."""
    reached = []
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.Collection",
        lambda path: _FakeCollection([(4, MUTABLE_NOUNS, ["школа"])]),
    )
    monkeypatch.setattr(
        "anki_tools.flagged_audio_cli.regenerate",
        lambda mode, words: reached.append(mode) or 0,
    )
    main(["--collection", "ignored", "--fix"])
    assert reached == [flagged_audio.MODE_SINGLE]


def _forbidden_regenerate(mode, words):
    raise AssertionError(f"regenerate called without --fix: {mode} {words}")


class _FakeNote:
    def __init__(self, note_type_name, headwords):
        names = [n for n in HEADWORD_FIELDS if n == "Russian"] or []
        if note_type_name.endswith("Verbs (Ellis Version)"):
            names = ["Imperfective", "Perfective"]
        else:
            names = ["Russian"]
        self._names = names[: len(headwords)] or ["Russian"]
        self.fields = list(headwords)
        self._type = {
            "name": note_type_name,
            "flds": [{"name": n} for n in self._names],
        }

    def note_type(self):
        return self._type


class _FakeCard:
    def __init__(self, card_id, flags, note):
        self.id = card_id
        self.flags = flags
        self._note = note

    def note(self):
        return self._note


class _FakeDb:
    def __init__(self, card_ids):
        self._ids = card_ids

    def list(self, _query):
        return list(self._ids)


class _FakeCollection:
    def __init__(self, rows, raise_on_scan=False):
        self._rows = list(rows)
        self._raise = raise_on_scan
        self.closed = False
        self.db = _FakeDb(range(len(self._rows)))

    def get_card(self, card_id):
        if self._raise:
            raise RuntimeError("scan blew up")
        flags, note_type, headwords = self._rows[card_id]
        return _FakeCard(card_id, flags, _FakeNote(note_type, headwords))

    def set_user_flag_for_cards(self, flag, card_ids):
        self.cleared = (flag, list(card_ids))

    def close(self):
        self.closed = True
