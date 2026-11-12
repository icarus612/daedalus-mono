"""Rendered-card duplicate check across all seven note types, every template.

Every note of the real sources is rendered (question and answer side of every
card) and each side must hold every piece of information once. Three groups of
data steer the verdict and are all listed here, none hidden in the helper:

- STRUCTURAL: what the check never compares (headwords, labels, examples,
  inflection cells, stop words, gloss-internal repeats).
- ALLOWED: note-level pairs that overlap by approved decision or because one
  segment elaborates the other. Each carries its reason.
- OPEN: real repeats not yet resolved. A guard test fails when an entry
  stops reproducing so the list cannot rot.
"""

import dataclasses
import os
import re
import sqlite3
from pathlib import Path

import pytest
from anki.collection import Collection

from anki_tools import card_dedup as dedup
from anki_tools import (
    distinction,
    immutable_words,
    immutable_words_plan,
    mutable_words,
    mutable_words_plan,
    phrase_words,
)

_PACKAGE = Path(__file__).resolve().parents[1]
_VOCAB_DIR = _PACKAGE / "anki_tools" / "data" / "russian-vocabulary"
_WORD_LIST = _PACKAGE / "tests" / "data" / "source-word-list.md"

STRUCTURAL = dedup.Exemptions(
    ignored_labels=frozenset(phrase_words.INFLECTION_FIELDS),
    equal_skip_kinds=frozenset({dedup.HEADWORD, dedup.LABEL, dedup.EXAMPLES}),
    equal_skip_labels=frozenset({"Stem Type"}),
    equal_skip_kind_pairs=frozenset(
        {(dedup.SENSE, dedup.SENSE), (dedup.PAREN, dedup.PAREN)}
    ),
    stopwords=frozenset(
        "a an the to of or and for in on at by with as be is it its s".split()
    ),
)

STRUCTURAL_REASONS = {
    "headword/label/examples kinds are never compared for equality": (
        "a headword is the question, a label names a row, examples quote usage"
    ),
    "inflection cells (phrase_words.INFLECTION_FIELDS) are dropped entirely": (
        "forms legitimately coincide (Plural == Genitive Sg) "
        "and are filled concurrently"
    ),
    "Stem Type is not compared for equality": (
        "'hard' there is a grammar class, not the gloss 'hard'"
    ),
    "sense/sense and paren/paren pairs inside one gloss are not compared": (
        "two senses may share a head word or qualifier: 'take (exam) / pass (exam)'"
    ),
    "stop words are ignored when comparing content words": (
        "grammar words carry no information"
    ),
}

_APPROVED_KEEP = (
    "approved qualifier-classification.tsv decision (keep / move-to-distinction)"
)
_ELABORATES = (
    "the longer segment adds content beyond the short label, "
    "so the label is not the same information"
)

_CATEGORY_LABEL = "Category is a classification label"

ALLOWED = {
    (
        "Immutable Words",
        "просто",
        dedup.RULE_CONTAINED,
        ("plays it down", "plays it down it s just that"),
    ): _ELABORATES,
    (
        "Immutable Words",
        "здравствуйте",
        dedup.RULE_CONTAINED,
        ("formal", "formal plural greeting lit imperative be healthy"),
    ): _ELABORATES,
    (
        "Immutable Words",
        "это",
        dedup.RULE_CONTAINED,
        (
            "this is linking word",
            (
                "subject less linking word это книга this is a book invariable "
                "unlike the pronoun этот эта это эти which agrees with its noun"
            ),
        ),
    ): _ELABORATES,
    (
        "Immutable Words",
        "правда",
        dedup.RULE_CONTAINED,
        (
            "asserts the whole clause",
            (
                "asserts the truth of the whole clause not the manner of the verb "
                "also a noun правда truth"
            ),
        ),
    ): _ELABORATES,
    (
        "Mutable Adjectives",
        "жаркий",
        dedup.RULE_CONTAINED,
        ("weather", "weather climate горячии hot to the touch"),
    ): _ELABORATES,
    (
        "Mutable Adjectives",
        "горячий",
        dedup.RULE_CONTAINED,
        ("to the touch", "hot to the touch жаркии hot weather"),
    ): _ELABORATES,
    ("Mutable Nouns", "время", dedup.RULE_EQUAL, ("time", "time")): _CATEGORY_LABEL,
    (
        "Mutable Nouns",
        "люди",
        dedup.RULE_EQUAL,
        ("people", "people"),
    ): _CATEGORY_LABEL,
    (
        "Mutable Nouns",
        "семья",
        dedup.RULE_EQUAL,
        ("family", "family"),
    ): _CATEGORY_LABEL,
    ("Mutable Nouns", "тело", dedup.RULE_EQUAL, ("body", "body")): _CATEGORY_LABEL,
    (
        "Mutable Nouns",
        "здоровье",
        dedup.RULE_EQUAL,
        ("health", "health"),
    ): _CATEGORY_LABEL,
    ("Mutable Nouns", "раз", dedup.RULE_EQUAL, ("time", "time")): _CATEGORY_LABEL,
    (
        "Immutable Words",
        "привет",
        dedup.RULE_CONTAINED,
        (
            "informal",
            "informal only do not use with strangers or superiors",
        ),
    ): _ELABORATES,
    (
        "Mutable Verbs",
        "приходиться",
        dedup.RULE_CONTAINED,
        (
            "impersonal",
            (
                "irregular impersonal used only in 3sg neuter "
                "придется пришлось and the infinitive"
            ),
        ),
    ): _ELABORATES,
}

OPEN: dict = {}

_SOURCE_FIELDS = [
    "Russian",
    "Translation",
    "Pronunciation",
    "Part of Speech",
    "Audio",
    "Additional Info",
]
_CARD1_QFMT = (
    '<div id="deck-header"></div>\n<div id="part-of-speech">{{Part of Speech}}</div>\n'
    '<div id="russian">{{Russian}}</div>'
)
_CARD1_AFMT = (
    '{{FrontSide}}\n<hr id=answer>\n<div id="translation">{{Translation}}</div>\n'
    '<div id="audio">{{Audio}}</div>\n{{Pronunciation}}'
)
_CARD2_QFMT = (
    '<div id="audio">{{Audio}}</div>\n<div id="translation">{{Translation}}</div>'
)
_CARD2_AFMT = (
    '{{FrontSide}}\n<hr id=answer>\n<div id="part-of-speech">{{Part of Speech}}</div>\n'
    '<div id="russian">{{Russian}}</div>\n'
    '<div id="additional-info">{{Additional Info}}</div>\n'
    '<script>\naddTitle("additional-info", "&#9432;");\n</script>'
)


def _make_source(path):
    col = Collection(path)
    try:
        note_type = col.models.new("Fixture Source ")
        for name in _SOURCE_FIELDS:
            note_type["flds"].append(col.models.new_field(name))
        for name, qfmt, afmt in (
            ("Card 1", _CARD1_QFMT, _CARD1_AFMT),
            ("Card 2", _CARD2_QFMT, _CARD2_AFMT),
        ):
            template = col.models.new_template(name)
            template["qfmt"], template["afmt"] = qfmt, afmt
            note_type["tmpls"].append(template)
        note_type["css"] = ".card { color: black; }"
        natural_id = col.models.add_dict(note_type).id
    finally:
        col.close()
    conn = sqlite3.connect(path)
    conn.create_collation(
        "unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower())
    )
    try:
        for table, column in (
            ("notetypes", "id"),
            ("fields", "ntid"),
            ("templates", "ntid"),
        ):
            conn.execute(
                f"update {table} set {column} = ? where {column} = ?",
                (immutable_words.SOURCE_NOTETYPE_ID, natural_id),
            )
        conn.commit()
    finally:
        conn.close()


class Bench:
    """A build collection holding the Immutable note type and the six Mutable ones."""

    def __init__(self, directory):
        source_path = os.path.join(directory, "source.anki2")
        _make_source(source_path)
        source = Collection(source_path)
        self.col = Collection(os.path.join(directory, "build.anki2"))
        try:
            self.immutable = immutable_words.clone_note_type(
                source, self.col, immutable_words.NEW_NOTE_TYPE_NAME
            )
            self.mutable = mutable_words.build_note_types(source, self.col)
        finally:
            source.close()
        self.deck = self.col.decks.id("Dedup", create=True)

    def close(self):
        self.col.close()

    def add_immutable(self, row, overrides=None):
        values = dict(zip(immutable_words_plan.FIELD_NAMES, row.fields()))
        values.update(overrides or {})
        note = self.col.new_note(self.immutable)
        note.guid = row.guid
        for name, value in values.items():
            note[name] = value
        self.col.add_note(note, self.deck)

    def add_all_current(self):
        for row in current_immutable_rows():
            self.add_immutable(row)
        mutable_words.build_deck_tree(self.col, current_mutable_rows(), self.mutable)

    def sides(self):
        out = []
        for note_id in self.col.find_notes(""):
            note = self.col.get_note(note_id)
            name = note.note_type()["name"]
            name = name.removeprefix("Russian - ").removesuffix(" (Ellis Version)")
            headword = re.sub(r"<[^>]*>", "", note.fields[0]).strip()
            for card in note.cards():
                output = card.render_output()
                for side, html in (
                    ("q", output.question_text),
                    ("a", output.answer_text),
                ):
                    out.append((name, headword, f"card{card.ord + 1}/{side}", html))
        return out


def current_immutable_rows():
    return immutable_words_plan.parse_word_list(_WORD_LIST.read_text(encoding="utf-8"))


def current_mutable_rows():
    return {
        "Nouns": mutable_words_plan.parse_nouns(str(_VOCAB_DIR / "nouns.tsv")),
        "Verbs": mutable_words_plan.parse_verbs(str(_VOCAB_DIR / "verbs.tsv")),
        "Adjectives": mutable_words_plan.parse_adjectives(
            str(_VOCAB_DIR / "adjectives.tsv")
        ),
        "Adverbs": mutable_words_plan.parse_adverbs(str(_VOCAB_DIR / "adverbs.tsv")),
        "Pronouns": mutable_words_plan.parse_pronouns(str(_VOCAB_DIR / "pronouns.tsv")),
        "Numerals": mutable_words_plan.parse_numerals(str(_VOCAB_DIR / "numerals.tsv")),
    }


def _key(name, headword, violation):
    return (
        name,
        headword,
        violation.rule,
        tuple(dedup.normalize(text) for text in violation.texts),
    )


@pytest.fixture(scope="module")
def all_current_keys(tmp_path_factory):
    bench = Bench(str(tmp_path_factory.mktemp("dedup-all")))
    try:
        bench.add_all_current()
        sides = bench.sides()
    finally:
        bench.close()
    keys = {}
    for name, headword, where, html in sides:
        for violation in dedup.violations(html, STRUCTURAL):
            keys.setdefault(_key(name, headword, violation), []).append(where)
    return len(sides), keys


def test_every_note_type_and_template_is_rendered(all_current_keys):
    rendered, _ = all_current_keys
    expected = 0
    immutable_count = len(current_immutable_rows())
    expected += immutable_count * 2 * 2
    templates = mutable_words.TEMPLATE_COUNTS_BY_SHEET
    for sheet, rows in current_mutable_rows().items():
        expected += len(rows) * templates[sheet] * 2
        if sheet == "Verbs":
            expected -= sum(1 for r in rows if not r.perfective.strip()) * 2 * 2
            expected -= sum(1 for r in rows if not r.imperfective.strip()) * 2 * 2
    assert rendered == expected


def test_no_rendered_side_repeats_information(all_current_keys):
    _, keys = all_current_keys
    unexplained = sorted(set(keys) - set(ALLOWED) - set(OPEN))
    assert unexplained == []


def test_open_findings_still_reproduce_so_the_list_cannot_rot(all_current_keys):
    _, keys = all_current_keys
    assert sorted(set(OPEN) - set(keys)) == []


def test_allowed_pairs_still_reproduce_so_the_list_cannot_rot(all_current_keys):
    _, keys = all_current_keys
    assert sorted(set(ALLOWED) - set(keys)) == []


def test_allowed_and_open_are_disjoint_and_every_entry_has_a_reason():
    assert set(ALLOWED).isdisjoint(OPEN)
    assert all(reason for reason in {**ALLOWED, **OPEN}.values())
    assert all(STRUCTURAL_REASONS.values())


def test_inflection_cells_play_no_part_in_the_verdict():
    html = (
        '<div id="translation">house</div>'
        '<div class="detail-label">Plural</div><div class="detail-value">дома</div>'
        '<div class="detail-label">Genitive Sg</div>'
        '<div class="detail-value">дома</div>'
    )
    assert dedup.violations(html, STRUCTURAL) == []
    assert dedup.violations(
        html, dataclasses.replace(STRUCTURAL, ignored_labels=frozenset())
    )


SEEDED_CASES = {
    "ещё": {
        "row": "ещё",
        "overrides": {
            "English Distinction": "ongoing, or asking for more",
            "Additional Info": "Marks an ongoing status or asks for more",
        },
        "rules": {dedup.RULE_UNION},
    },
    "до": {
        "row": "до",
        "overrides": {"English Distinction": "Genitive", "Additional Info": "Genitive"},
        "rules": {dedup.RULE_CASE, dedup.RULE_CONTAINED},
    },
    "всё": {
        "row": "всё",
        "overrides": {
            "Translation": "still / all / constantly (keeps on)",
            "English Distinction": "keeps on",
        },
        "rules": {dedup.RULE_EQUAL, dedup.RULE_CONTAINED},
    },
}


def _rows_by_russian():
    return {row.russian: row for row in current_immutable_rows()}


def _violation_rules(bench, headword):
    rules = set()
    for _, noted, _, html in bench.sides():
        if noted == headword:
            rules.update(v.rule for v in dedup.violations(html, STRUCTURAL))
    return rules


@pytest.mark.parametrize("case", sorted(SEEDED_CASES))
def test_the_screenshot_cases_pass_as_shipped(case, tmp_path):
    spec = SEEDED_CASES[case]
    bench = Bench(str(tmp_path))
    try:
        bench.add_immutable(_rows_by_russian()[spec["row"]])
        assert _violation_rules(bench, spec["row"]) == set()
    finally:
        bench.close()


@pytest.mark.parametrize("case", sorted(SEEDED_CASES))
def test_the_screenshot_cases_fail_when_their_old_duplicate_is_restored(case, tmp_path):
    spec = SEEDED_CASES[case]
    bench = Bench(str(tmp_path))
    try:
        bench.add_immutable(_rows_by_russian()[spec["row"]], spec["overrides"])
        rules = _violation_rules(bench, spec["row"])
    finally:
        bench.close()
    assert spec["rules"] <= rules


def test_a_seeded_second_case_name_is_caught_on_a_case_pill_card(tmp_path):
    bench = Bench(str(tmp_path))
    try:
        row = _rows_by_russian()["до"]
        bench.add_immutable(row, {"Additional Info": "takes the Genitive"})
        rules = _violation_rules(bench, "до")
    finally:
        bench.close()
    assert dedup.RULE_CASE in rules


def test_the_distinction_table_is_untouched_by_the_seeded_runs():
    assert distinction.english_distinction("до") != "Genitive"


_PILLS = (
    '<div class="case-pills" data-case="Accusative, Prepositional">'
    '<span class="case-pill">Accusative</span></div>'
)


@pytest.mark.parametrize(
    "html,rules",
    [
        ('<div id="translation">hot</div>', []),
        (
            '<div id="translation">hot (weather)</div>'
            '<div id="prompt-hint">(weather)</div>',
            ["equal", "contained"],
        ),
        (
            '<div id="translation">still / yet (ongoing)'
            "<br>more (asking for more)</div>"
            '<div id="prompt-hint">(ongoing, or asking for more)</div>',
            ["union"],
        ),
        ('<div id="translation">stay</div>' + _PILLS, []),
        (
            '<div id="translation">stay</div>' + _PILLS + _PILLS,
            ["equal", "equal", "case-name", "case-name"],
        ),
        (
            '<div id="translation">stay</div>'
            '<div id="additional-info">takes accusative</div>' + _PILLS,
            ["case-name"],
        ),
        (
            '<div id="translation">hot</div><script>var x = "hot";</script>'
            '<span class="hidden">hot</span>',
            [],
        ),
        ('<div id="translation">hot</div><div id="examples">hot hot</div>', []),
    ],
)
def test_rules_on_small_sides(html, rules):
    assert [v.rule for v in dedup.violations(html, STRUCTURAL)] == rules


def test_segments_split_gloss_into_senses_parentheticals_and_the_whole():
    found = dedup.segments('<div id="translation">still / yet (ongoing)<br>more</div>')
    assert [(s.kind, s.text) for s in found] == [
        (dedup.GLOSS_ALL, "still / yet (ongoing)"),
        (dedup.PAREN, "ongoing"),
        (dedup.SENSE, "still"),
        (dedup.SENSE, "yet"),
        (dedup.GLOSS_ALL, "more"),
        (dedup.SENSE, "more"),
    ]
