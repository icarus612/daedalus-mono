import argparse

import pytest

from anki_tools import phrase_words as pw
from anki_tools.phrase_words_cli import build_parser, main

PHRASE_TYPE = "Russian - Common Words (Ellis Version) "
VERB_TYPE = "Russian - Mutable Verbs (Ellis Version)"
NOUN_TYPE = "Russian - Mutable Nouns (Ellis Version)"
IMMUTABLE_TYPE = "Russian - Immutable Words (Ellis Version)"
FOREIGN_TYPE = "LlamaNote"

FIELDS = {
    PHRASE_TYPE: ["Russian", "Translation", "Pronunciation", "Part of Speech"],
    VERB_TYPE: ["Imperfective", "Perfective", "Translation", "я (1sg)"],
    NOUN_TYPE: ["Russian", "Translation", "Plural"],
    IMMUTABLE_TYPE: ["Russian", "Translation"],
    FOREIGN_TYPE: ["Russian", "English"],
}

PHRASES = [
    (100, ["Говорю по-русски", "I speak Russian", "", ""]),
    (101, ["Добро пожаловать", "Welcome", "", ""]),
    (102, ["Встреча", "A meeting", "", ""]),
]
TAUGHT = [
    (200, VERB_TYPE, ["говорить", "сказать", "speak", ""]),
    (201, NOUN_TYPE, ["встреча", "meeting", "встречи"]),
    (202, NOUN_TYPE, ["добро", "goodness", ""]),
    (203, IMMUTABLE_TYPE, ["по-русски (adverb)", "in Russian"]),
]
FOREIGN = [(300, FOREIGN_TYPE, ["пожаловать", "to welcome"])]
CARDS = {
    200: [(2, 2), (2, 2)],
    201: [(2, 2)],
    202: [(0, 0), (0, 0)],
    203: [(0, -1)],
    300: [(2, 2)],
}


def collection(phrases=PHRASES, taught=TAUGHT, foreign=FOREIGN, cards=None):
    notes = [(nid, PHRASE_TYPE, fields) for nid, fields in phrases]
    notes += list(taught) + list(foreign)
    return _FakeCollection(notes, CARDS if cards is None else cards)


def patch(monkeypatch, col):
    monkeypatch.setattr("anki_tools.phrase_words_cli.Collection", lambda path: col)
    return col


def test_build_parser_returns_argument_parser():
    assert isinstance(build_parser(), argparse.ArgumentParser)


def test_parser_prog_name():
    assert build_parser().prog == "anki-phrase-words"


def test_lemma_resolution_is_the_default():
    args = build_parser().parse_args([])
    assert args.no_lemma is False and args.headwords_only is False


def test_parser_defaults_to_the_phrase_note_type():
    assert build_parser().parse_args([]).note_type == pw.PHRASE_NOTE_TYPE


def test_parser_defaults_to_plain_text_output():
    assert build_parser().parse_args([]).format == "text"


def test_parser_accepts_markdown_output():
    assert build_parser().parse_args(["--format", "markdown"]).format == "markdown"


@pytest.mark.parametrize("flag", ["--no-lemma", "--headwords-only"])
def test_parser_accepts_the_narrower_resolution_modes(flag):
    assert build_parser().parse_args([flag])


def test_parser_rejects_an_unknown_output_format():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["--format", "yaml"])


def test_main_counts_every_distinct_token_once(monkeypatch, capsys):
    patch(monkeypatch, collection())
    assert main(["--collection", "ignored"]) == 0
    assert "5 distinct word token(s)" in capsys.readouterr().out


def test_main_reports_a_genuinely_untaught_word_as_missing(monkeypatch, capsys):
    """Positive control: the only word no taught note covers is
    `пожаловать`, and a run that reported zero missing would be wrong."""
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    out = capsys.readouterr().out
    assert "missing" in out and "пожаловать" in out


def test_main_does_not_count_a_foreign_note_type_as_teaching_a_word(
    monkeypatch, capsys
):
    """`пожаловать` exists only on a third-party note type, which is out of
    scope -- if that type leaked into the index the word would resolve."""
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    assert "пожаловать" in capsys.readouterr().out


def test_main_lemmatizes_a_conjugated_verb_rather_than_calling_it_missing(
    monkeypatch, capsys
):
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    out = capsys.readouterr().out
    assert "говорю" in out and "говорить / сказать" in out


def test_without_lemmatization_the_same_verb_is_reported_missing(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored", "--no-lemma"])
    lines = capsys.readouterr().out.splitlines()
    missing = _section(lines, "missing")
    assert any("говорю" in line for line in missing)


def test_lemmatization_changes_the_answer(monkeypatch, capsys):
    """Positive control for `--no-lemma`: if both modes agreed, neither the
    default nor the comparison would be measuring anything."""
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    with_lemma = _count(capsys.readouterr().out, "missing")
    patch(monkeypatch, collection())
    main(["--collection", "ignored", "--no-lemma"])
    assert _count(capsys.readouterr().out, "missing") > with_lemma


def test_headwords_only_ignores_a_stored_inflection(monkeypatch, capsys):
    patch(monkeypatch, collection(phrases=[(100, ["Встречи", "", "", ""])]))
    main(["--collection", "ignored", "--headwords-only", "--no-lemma"])
    lines = _section(capsys.readouterr().out.splitlines(), "missing")
    assert any("встречи" in line for line in lines)


def test_a_stored_inflection_resolves_when_headwords_are_not_the_only_source(
    monkeypatch, capsys
):
    patch(monkeypatch, collection(phrases=[(100, ["Встречи", "", "", ""])]))
    main(["--collection", "ignored", "--no-lemma"])
    out = capsys.readouterr().out
    assert _count(out, "missing") == 0
    assert "встреча" in out


def test_main_buckets_card_states(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    out = capsys.readouterr().out
    assert _count(out, "studied") == 2
    assert _count(out, "all-new") == 1
    assert _count(out, "suspended") == 1
    assert _count(out, "missing") == 1


def test_main_prints_the_phrase_each_word_came_from(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    out = capsys.readouterr().out
    assert "Добро пожаловать" in out
    assert "Говорю по-русски" in out


def test_main_treats_a_single_word_entry_like_a_phrase(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    out = capsys.readouterr().out
    assert "встреча" in out and "Встреча" in out


def test_markdown_output_carries_a_heading_per_bucket(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored", "--format", "markdown"])
    out = capsys.readouterr().out
    assert "## missing" in out and "## studied" in out
    assert out.startswith("# ")


def test_main_reports_the_size_of_the_taught_index(monkeypatch, capsys):
    patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    assert "taught index" in capsys.readouterr().out


def test_main_errors_when_the_note_type_is_absent(monkeypatch, capsys):
    patch(monkeypatch, collection())
    assert main(["--collection", "ignored", "--note-type", "No Such Type"]) == 1
    assert "No Such Type" in capsys.readouterr().err


def test_main_closes_the_collection_even_when_a_read_raises(monkeypatch):
    col = patch(monkeypatch, collection())
    col.raise_on_read = True
    with pytest.raises(RuntimeError):
        main(["--collection", "ignored"])
    assert col.closed


def test_main_closes_the_collection_on_a_clean_run(monkeypatch):
    col = patch(monkeypatch, collection())
    main(["--collection", "ignored"])
    assert col.closed


def test_main_returns_two_when_the_collection_will_not_open(monkeypatch, capsys):
    def explode(path):
        raise _FakeDBError("locked")

    monkeypatch.setattr("anki_tools.phrase_words_cli.Collection", explode)
    monkeypatch.setattr("anki_tools.phrase_words_cli.DBError", _FakeDBError)
    assert main(["--collection", "ignored"]) == 2
    assert "locked" in capsys.readouterr().err


def _section(lines, state):
    out, inside = [], False
    for line in lines:
        if line.startswith(("== ", "## ")):
            inside = line.split()[1].strip() == state
            continue
        if inside and line.strip():
            out.append(line)
    return out


def _count(out, state):
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0] == state:
            return int(parts[1])
    raise AssertionError(f"no count line for {state!r} in:\n{out}")


class _FakeDBError(Exception):
    pass


class _NameAndId:
    def __init__(self, ntid, name):
        self.id = ntid
        self.name = name


class _FakeModels:
    def __init__(self, names):
        self._names = list(names)

    def all_names_and_ids(self):
        return [_NameAndId(i, name) for i, name in enumerate(self._names)]

    def get(self, ntid):
        name = self._names[ntid]
        return {"name": name, "flds": [{"name": n} for n in FIELDS[name]]}


class _FakeDb:
    def __init__(self, collection):
        self._collection = collection

    def all(self, query, *args):
        if self._collection.raise_on_read:
            raise RuntimeError("read blew up")
        if "from notes" in query:
            wanted = self._collection.models._names[args[0]]
            return [
                (nid, "\x1f".join(fields))
                for nid, name, fields in self._collection.notes
                if name == wanted
            ]
        if "from cards" in query:
            return [
                (nid, card_type, queue)
                for nid, rows in self._collection.cards.items()
                for card_type, queue in rows
            ]
        raise AssertionError(f"unexpected query: {query}")


class _FakeCollection:
    def __init__(self, notes, cards):
        self.notes = list(notes)
        self.cards = dict(cards)
        self.closed = False
        self.raise_on_read = False
        self.models = _FakeModels(sorted({name for _, name, _ in self.notes}))
        self.db = _FakeDb(self)

    def close(self):
        self.closed = True
