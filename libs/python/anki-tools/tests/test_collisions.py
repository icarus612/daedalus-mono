import dataclasses
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from anki_tools import case_field, collisions, mutable_words_plan
from anki_tools.case_field import CaseGovernment
from anki_tools.collisions import Note
from anki_tools.distinction import ENGLISH_DISTINCTIONS, qualifier_of

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
SOURCE_LIST = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"
COMMITTED_TSV = DATA_DIR / "qualifier-classification.tsv"

IMMUTABLE_TYPE = "Russian - Immutable Words (Ellis Version)"
NOUNS = "Languages::Russian::1. Mutable Words::a. Nouns"
ADJECTIVES = "Languages::Russian::1. Mutable Words::c. Adjectives"
VERBS = "Languages::Russian::1. Mutable Words::b. Verbs"
NUMERALS = "Languages::Russian::1. Mutable Words::f. Numerals"
CONJUNCTIONS = "Languages::Russian::2. Immutable Words::g. Conjunctions"
PREPOSITIONS = "Languages::Russian::2. Immutable Words::e. Prepositions"
DERIVED_ADVERBS = "Languages::Russian::2. Immutable Words::f. Derived Adverbs"


def make_note(
    headword: str = "w",
    *,
    translation: str = "",
    deck: str = NOUNS,
    guid: str = "",
    english_distinction: str = "",
    russian_distinction: str = "",
    additional_info: str = "",
    cases: tuple[str, ...] = (),
) -> Note:
    immutable = "Immutable" in deck
    return Note(
        family="immutable" if immutable else "mutable",
        note_type=IMMUTABLE_TYPE if immutable else "Russian - Test",
        section=collisions.deck_label(deck),
        deck=deck,
        headword=headword,
        guid=guid or f"g-{headword}",
        translation=translation,
        russian_distinction=russian_distinction,
        english_distinction=english_distinction,
        additional_info=additional_info,
        cases=frozenset(cases),
    )


@pytest.fixture(scope="module")
def notes() -> list[Note]:
    return collisions.load_notes(SOURCE_LIST, DATA_DIR)


@pytest.fixture(scope="module")
def governed_notes() -> list[Note]:
    return collisions.load_notes(SOURCE_LIST, DATA_DIR, case_field.default_government())


@pytest.fixture(scope="module")
def groups(notes: list[Note]) -> list[collisions.CollisionGroup]:
    return collisions.find_collisions(notes)


@pytest.fixture(scope="module")
def rows(notes: list[Note]) -> list[collisions.ClassificationRow]:
    return collisions.classify(notes)


def rows_of(
    rows: list[collisions.ClassificationRow],
    headword: str,
    source_field: str,
) -> list[collisions.ClassificationRow]:
    return [
        row
        for row in rows
        if row.headword == headword and row.source_field == source_field
    ]


def classify_one(
    note: Note, *others: Note
) -> dict[str, list[collisions.ClassificationRow]]:
    result = collisions.classify([note, *others])
    by_field: dict[str, list[collisions.ClassificationRow]] = {}
    for row in result:
        if row.guid == note.guid:
            by_field.setdefault(row.source_field, []).append(row)
    return by_field


@pytest.mark.parametrize(
    ("translation", "expected"),
    [
        (
            "in / at (where)<br>into (where/what)",
            ("in", "at (where)", "into (where/what)"),
        ),
        ("a, b", ("a", "b")),
        ("earth; land", ("earth", "land")),
        ("a (x / y) / b", ("a (x / y)", "b")),
        ("<div>a</div><div>b</div>", ("a", "b")),
        ("a<br/>b", ("a", "b")),
        ("a <br> b", ("a", "b")),
        ("a<br><br>b", ("a", "b")),
        ("<b>a</b>", ("a",)),
        ("a &amp; b", ("a & b",)),
        ("a    b", ("a b",)),
        ("single", ("single",)),
        ("", ()),
    ],
)
def test_gloss_segments(translation: str, expected: tuple[str, ...]) -> None:
    assert collisions.gloss_segments(translation) == expected


@pytest.mark.parametrize(
    ("segment", "expected"),
    [
        ("At (Where)", "at"),
        ("a (b (c)) d", "a d"),
        ("x (y) (z)", "x"),
        ("  Hello.. ", "hello"),
        ("Hello;: ", "hello"),
        ("a   b", "a b"),
        ("(only)", ""),
        ("plain", "plain"),
    ],
)
def test_sense_key(segment: str, expected: str) -> None:
    assert collisions.sense_key(segment) == expected


@pytest.mark.parametrize(
    ("translation", "expected"),
    [
        ("in / at (where)<br>into (where/what)", ("in", "at", "into")),
        ("Bank / bank (a)", ("bank",)),
        ("(x) / y", ("y",)),
        ("b / a / b", ("b", "a")),
        ("solo", ("solo",)),
    ],
)
def test_senses(translation: str, expected: tuple[str, ...]) -> None:
    assert collisions.senses(translation) == expected


@pytest.mark.parametrize(
    ("deck", "expected"),
    [
        (
            "Languages::Russian::2. Immutable Words::f. Derived Adverbs",
            "Derived Adverbs",
        ),
        ("Languages::Russian::1. Mutable Words::a. Nouns", "Nouns"),
        ("Languages::Russian::Plain", "Plain"),
    ],
)
def test_deck_label(deck: str, expected: str) -> None:
    assert collisions.deck_label(deck) == expected


@pytest.mark.parametrize(
    ("cue", "deck", "expected"),
    [
        ("adj.", ADJECTIVES, True),
        ("Adjective", ADJECTIVES, True),
        ("adj.", NOUNS, False),
        ("adj. (weather)", ADJECTIVES, False),
        ("noun", NOUNS, True),
        ("verb.", VERBS, True),
        ("verb", NOUNS, False),
        ("adv.", DERIVED_ADVERBS, True),
        ("numeral", NUMERALS, True),
        ("prep.", PREPOSITIONS, True),
        ("conj.", CONJUNCTIONS, True),
        ("conj.", PREPOSITIONS, False),
        ("the postal kind", NOUNS, False),
    ],
)
def test_is_bare_pos_cue(cue: str, deck: str, expected: bool) -> None:
    assert collisions.is_bare_pos_cue(cue, deck) is expected


@pytest.mark.parametrize(
    ("cue", "deck", "counts"),
    [
        ("adj.", ADJECTIVES, (1, 1, 1, 0, 0)),
        ("adjective", ADJECTIVES, (1, 1, 0, 0, 0)),
        ("numeral", NUMERALS, (1, 1, 0, 0, 0)),
        ("noun", NOUNS, (1, 1, 1, 0, 0)),
        ("adj. (weather)", ADJECTIVES, (1, 0, 0, 1, 0)),
        ("conjunction: that", CONJUNCTIONS, (1, 0, 0, 1, 0)),
        ("adj.", NOUNS, (1, 0, 0, 0, 0)),
        ("a bus stop (noun)", NOUNS, (0, 0, 0, 0, 1)),
        ("a bus stop (noun)", VERBS, (0, 0, 0, 0, 1)),
        ("adjacent", ADJECTIVES, (0, 0, 0, 0, 0)),
        ("the postal kind", NOUNS, (0, 0, 0, 0, 0)),
        ("", NOUNS, (0, 0, 0, 0, 0)),
    ],
)
def test_pos_cue_counts_classification(
    cue: str, deck: str, counts: tuple[int, int, int, int, int]
) -> None:
    result = collisions.pos_cue_counts([make_note(deck=deck, english_distinction=cue)])
    assert (
        result.leading,
        result.bare,
        result.bare_abbreviated,
        result.qualified,
        result.trailing,
    ) == counts


def test_pos_cue_counts_sums_over_notes() -> None:
    result = collisions.pos_cue_counts(
        [
            make_note("a", deck=ADJECTIVES, english_distinction="adj."),
            make_note("b", deck=ADJECTIVES, english_distinction="adj."),
            make_note("c", deck=NOUNS, english_distinction="a bus stop (noun)"),
        ]
    )
    assert (result.leading, result.bare, result.trailing) == (2, 2, 1)


@pytest.mark.parametrize(
    ("cue", "deck", "expected"),
    [
        ("adj. (weather)", ADJECTIVES, "weather"),
        ("adj.", ADJECTIVES, ""),
        ("conjunction: that", CONJUNCTIONS, "that"),
        ("a bus stop (noun)", NOUNS, "a bus stop"),
        ("the postal kind", NOUNS, None),
        ("adj. (weather)", NOUNS, None),
        ("a bus stop (noun)", VERBS, None),
    ],
)
def test_leading_pos_residual(cue: str, deck: str, expected: str | None) -> None:
    assert collisions.leading_pos_residual(cue, deck) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Genitive", {"Genitive"}),
        ("genitive or DATIVE", {"Genitive", "Dative"}),
        ("Nominative, Accusative, Instrumental, Prepositional", None),
        ("acc.", {"Accusative"}),
        ("gen.", {"Genitive"}),
        ("dat.", {"Dative"}),
        ("instr.", {"Instrumental"}),
        ("prep.", {"Prepositional"}),
        ("в/на + acc. (destination)", {"Accusative"}),
        ("acc", set()),
        ("xacc.", set()),
        ("preposition", set()),
        ("the postal kind", set()),
    ],
)
def test_cases_in(text: str, expected: set[str] | None) -> None:
    result = collisions.cases_in(text)
    if expected is None:
        expected = {"Nominative", "Accusative", "Instrumental", "Prepositional"}
    assert result == frozenset(expected)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Genitive", True),
        ("acc.", True),
        ("which case", True),
        ("governs the next noun", True),
        ("government", True),
        ("the postal kind", False),
        ("regular", False),
    ],
)
def test_has_case_text(text: str, expected: bool) -> None:
    assert collisions.has_case_text(text) is expected


@pytest.mark.parametrize(
    ("cue", "expected"),
    [
        ("в/на + acc. (destination)", "destination"),
        ("Genitive; right beside", "right beside"),
        ("Accusative or Instrumental", ""),
        ("not much; takes Genitive", "not much"),
        ("Dative: it pleases you", "it pleases you"),
        ("Dative; also along / around", "also along / around"),
        ("the postal kind", "the postal kind"),
    ],
)
def test_strip_case_part(cue: str, expected: str) -> None:
    assert collisions.strip_case_part(cue) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("The running dogs", {"runn", "dog"}),
        ("walked", {"walk"}),
        ("boxes", {"box"}),
        ("cat", {"cat"}),
        ("wonderful", {"wonde"}),
        ("<b>cat</b>", {"cat"}),
        ("A cat. Cat!", {"cat"}),
        ("the to of a", set()),
        ("", set()),
    ],
)
def test_stems(text: str, expected: set[str]) -> None:
    assert collisions.stems(text) == frozenset(expected)


@pytest.mark.parametrize(
    ("small", "big", "expected"),
    [
        ("cold", "cold weather", True),
        ("dog", "dogs", True),
        ("weather", "cold", False),
        ("cold weather", "cold", False),
        ("", "anything", False),
        ("the", "the cat", False),
    ],
)
def test_restates(small: str, big: str, expected: bool) -> None:
    assert collisions.restates(small, big) is expected


@pytest.mark.parametrize(
    ("translation", "expected"),
    [
        (
            "in / at (where)<br>into (where/what)",
            [("where", 2, 3), ("where/what", 3, 3)],
        ),
        ("carrot(s)", [("s", 1, 1)]),
        ("a (b (c)) d", [("b (c)", 1, 1)]),
        ("a (x) b (y)", [("x", 1, 1), ("y", 1, 1)]),
        ("bank ( the financial one )", [("the financial one", 1, 1)]),
        ("a (b", []),
        ("plain", []),
    ],
)
def test_translation_qualifiers(
    translation: str, expected: list[tuple[str, int, int]]
) -> None:
    result = collisions.translation_qualifiers(translation)
    assert [(q.text, q.segment, q.segments) for q in result] == expected


@pytest.mark.parametrize(
    ("translation", "indexes", "expected"),
    [
        ("bank (a) tail (b)", {0}, "bank tail (b)"),
        ("bank (a) tail (b)", {1}, "bank (a) tail"),
        ("bank (a) tail (b)", {0, 1}, "bank tail"),
        ("bank (a) tail (b)", set(), "bank (a) tail (b)"),
        ("(a) bank", {0}, "bank"),
        ("x (a)<br>y", {0}, "x<br>y"),
        ("x (a)<br>y (b)", {1}, "x (a)<br>y"),
    ],
)
def test_remove_parentheticals(
    translation: str, indexes: set[int], expected: str
) -> None:
    assert collisions.remove_parentheticals(translation, indexes) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("bank (the financial one)", "bank"),
        ("<b>bank</b> (a)<br>tail (b)", "bank tail"),
        ("plain  text", "plain text"),
    ],
)
def test_outside_parentheses(text: str, expected: str) -> None:
    assert collisions.outside_parentheses(text) == expected


GEN = ("Genitive",)
DAT = ("Dative",)


@pytest.mark.parametrize(
    ("first", "second", "expected"),
    [
        (
            make_note("a", deck=ADJECTIVES, cases=GEN),
            make_note("b", deck=NOUNS, cases=DAT),
            "header",
        ),
        (
            make_note("a", deck=ADJECTIVES),
            make_note("b", deck=NOUNS),
            "header",
        ),
        (
            make_note("a", deck=PREPOSITIONS, cases=GEN),
            make_note("b", deck=PREPOSITIONS, cases=DAT),
            "pill",
        ),
        (
            make_note("a", deck=PREPOSITIONS, cases=GEN),
            make_note("b", deck=PREPOSITIONS, cases=GEN),
            "none",
        ),
        (
            make_note("a", deck=PREPOSITIONS, cases=GEN),
            make_note("b", deck=PREPOSITIONS),
            "none",
        ),
        (make_note("a", deck=NOUNS), make_note("b", deck=NOUNS), "none"),
    ],
)
def test_pair_separator(first: Note, second: Note, expected: str) -> None:
    assert collisions.pair_separator(first, second) == expected


def test_find_collisions_header_only_group() -> None:
    first = make_note("a", translation="cold", deck=ADJECTIVES)
    second = make_note("b", translation="cold", deck=NOUNS)
    [group] = collisions.find_collisions([first, second])
    assert group.sense == "cold"
    assert group.mechanism == "header"
    assert group.members == (first, second)
    assert group.unseparated == ()


def test_find_collisions_pill_only_group() -> None:
    first = make_note("a", translation="near", deck=PREPOSITIONS, cases=GEN)
    second = make_note("b", translation="near", deck=PREPOSITIONS, cases=DAT)
    [group] = collisions.find_collisions([first, second])
    assert group.mechanism == "pill"
    assert group.unseparated == ()


def test_find_collisions_mixed_group() -> None:
    first = make_note("a", translation="near", deck=PREPOSITIONS, cases=GEN)
    second = make_note("b", translation="near", deck=PREPOSITIONS, cases=DAT)
    third = make_note("c", translation="near", deck=CONJUNCTIONS)
    [group] = collisions.find_collisions([first, second, third])
    assert group.mechanism == "header+pill"
    assert group.unseparated == ()


def test_find_collisions_cue_group_lists_unseparated_pairs() -> None:
    first = make_note("a", translation="shore", guid="g1")
    second = make_note("b", translation="shore", guid="g2")
    third = make_note("c", translation="shore", guid="g3", deck=ADJECTIVES)
    [group] = collisions.find_collisions([first, second, third])
    assert group.mechanism == "cue"
    assert group.unseparated == (("g1", "g2"),)


def test_find_collisions_cue_wins_over_other_pairs() -> None:
    notes = [
        make_note("a", translation="x", deck=PREPOSITIONS, cases=GEN, guid="g1"),
        make_note("b", translation="x", deck=PREPOSITIONS, cases=DAT, guid="g2"),
        make_note("c", translation="x", deck=PREPOSITIONS, cases=DAT, guid="g3"),
        make_note("d", translation="x", deck=CONJUNCTIONS, guid="g4"),
    ]
    [group] = collisions.find_collisions(notes)
    assert group.mechanism == "cue"
    assert group.unseparated == (("g2", "g3"),)


def test_find_collisions_indexes_each_sense_and_sorts() -> None:
    first = make_note("a", translation="in / at (where)")
    second = make_note("b", translation="at")
    third = make_note("c", translation="in", deck=ADJECTIVES)
    result = collisions.find_collisions([first, second, third])
    assert [g.sense for g in result] == ["at", "in"]
    assert result[0].members == (first, second)
    assert result[1].members == (first, third)


def test_find_collisions_ignores_single_holders() -> None:
    lone = make_note("a", translation="x / x")
    other = make_note("b", translation="y")
    assert collisions.find_collisions([lone, other]) == []


def test_find_collisions_positive_control_for_repeated_sense() -> None:
    assert collisions.find_collisions([make_note("a", translation="x / X")]) == []
    pair = [make_note("a", translation="x"), make_note("b", translation="x")]
    assert len(collisions.find_collisions(pair)) == 1


def test_format_groups_table_layout() -> None:
    first = make_note("а", translation="near", deck=PREPOSITIONS, cases=GEN)
    second = make_note("б", translation="near", deck=CONJUNCTIONS)
    table = collisions.format_groups_table(collisions.find_collisions([first, second]))
    lines = table.splitlines()
    assert lines[0].split("\t")[:3] == ["sense", "mechanism", "members"]
    assert len(lines) == 2
    assert lines[1].split("\t") == [
        "near",
        "header",
        "а [Prepositions; Genitive] | б [Conjunctions; -]",
    ]


def test_format_groups_table_empty_has_header_only() -> None:
    assert len(collisions.format_groups_table([]).splitlines()) == 1


def test_load_notes_counts_and_order(notes: list[Note]) -> None:
    assert len(notes) == 1469
    assert [n.family for n in notes[:233]] == ["immutable"] * 233
    assert {n.family for n in notes[233:]} == {"mutable"}
    mutable_sections = list(dict.fromkeys(n.section for n in notes[233:]))
    assert mutable_sections == [
        "Nouns",
        "Verbs",
        "Adjectives",
        "Adverbs",
        "Pronouns",
        "Numerals",
    ]
    counts = Counter(n.section for n in notes[233:])
    assert [counts[s] for s in mutable_sections] == [631, 215, 172, 134, 29, 55]


def test_load_notes_fields(notes: list[Note]) -> None:
    assert {n.note_type for n in notes if n.family == "immutable"} == {IMMUTABLE_TYPE}
    for note in notes:
        assert note.russian_distinction == qualifier_of(note.headword)
        assert note.english_distinction == ENGLISH_DISTINCTIONS.get(note.headword, "")
        if note.family == "mutable":
            assert note.note_type == mutable_words_plan.NOTE_TYPE_NAMES[note.section]
    assert len({n.guid for n in notes}) == 1469


def test_every_english_distinction_key_matches_a_headword(notes: list[Note]) -> None:
    headwords = {n.headword for n in notes}
    assert len(ENGLISH_DISTINCTIONS) == 194
    assert set(ENGLISH_DISTINCTIONS) <= headwords
    assert sum(1 for n in notes if n.english_distinction) == 194


def test_provisional_cases(notes: list[Note], governed_notes: list[Note]) -> None:
    by_headword = {n.headword: n for n in notes if n.section == "Prepositions"}
    assert by_headword["через"].cases == frozenset({"Accusative"})
    assert by_headword["сквозь"].cases == frozenset({"Accusative"})
    assert any(n.cases for n in notes if n.section == "Prepositions")
    assert all(not n.cases for n in notes if n.section == "Nouns")
    verb_rows = {
        row.guid: row for row in mutable_words_plan.parse_verbs(DATA_DIR / "verbs.tsv")
    }
    verbs = [n for n in governed_notes if n.section == "Verbs"]
    assert any(n.cases for n in verbs)
    for note in verbs:
        expected = collisions.cases_in(verb_rows[note.guid].case)
        assert note.cases == expected


def test_government_overrides_cases_for_any_section(notes: list[Note]) -> None:
    noun = next(n for n in notes if n.section == "Nouns")
    preposition = next(
        n for n in notes if n.section == "Prepositions" and n.headword == "через"
    )
    government = {
        noun.guid: CaseGovernment(cases=("Genitive",), line_cases={}),
        preposition.guid: CaseGovernment(cases=("Dative", "Genitive"), line_cases={}),
    }
    overridden = {
        n.guid: n for n in collisions.load_notes(SOURCE_LIST, DATA_DIR, government)
    }
    assert overridden[noun.guid].cases == frozenset({"Genitive"})
    assert overridden[preposition.guid].cases == frozenset({"Dative", "Genitive"})
    untouched = next(n for n in notes if n.section == "Verbs")
    assert overridden[untouched.guid].cases == untouched.cases


def test_collision_totals(groups: list[collisions.CollisionGroup]) -> None:
    assert len(groups) == 202
    assert sum(len(g.members) for g in groups) == 443
    assert len({m.guid for g in groups for m in g.members}) == 368
    assert Counter(g.mechanism for g in groups) == {
        "cue": 115,
        "header": 79,
        "pill": 7,
        "header+pill": 1,
    }
    assert [g.sense for g in groups] == sorted(g.sense for g in groups)


def test_immutable_only_collisions(notes: list[Note]) -> None:
    immutable = [n for n in notes if n.family == "immutable"]
    assert len(immutable) == 233
    result = collisions.find_collisions(immutable)
    assert len(result) == 55
    assert len({m.guid for g in result for m in g.members}) == 97
    assert sum(1 for g in result if g.mechanism == "pill") == 7


def group_for(
    groups: list[collisions.CollisionGroup], sense: str
) -> collisions.CollisionGroup:
    return next(g for g in groups if g.sense == sense)


def test_spot_check_through(groups: list[collisions.CollisionGroup]) -> None:
    group = group_for(groups, "through")
    heads = {m.headword for m in group.members}
    assert {"через", "сквозь"} <= heads
    assert all(
        m.cases == frozenset({"Accusative"})
        for m in group.members
        if m.headword in {"через", "сквозь"}
    )
    assert group.mechanism == "cue"


def test_spot_check_near_and_from(groups: list[collisions.CollisionGroup]) -> None:
    near = group_for(groups, "near")
    assert {"около", "возле"} <= {m.headword for m in near.members}
    assert near.mechanism == "cue"
    origin = group_for(groups, "from")
    assert {"из", "от"} <= {m.headword for m in origin.members}
    assert origin.mechanism == "cue"


def test_spot_check_according_to(groups: list[collisions.CollisionGroup]) -> None:
    group = group_for(groups, "according to")
    heads = {m.headword for m in group.members}
    assert {"по", "согласно (preposition)", "согласно (adverb)"} <= heads


def test_real_pos_cue_counts(notes: list[Note]) -> None:
    result = collisions.pos_cue_counts(notes)
    assert result.leading == 0
    assert result.bare == 0
    assert result.bare_abbreviated == 0
    assert result.qualified == 0
    assert result.trailing == 0


def test_real_case_bearing_cues(notes: list[Note]) -> None:
    bearing = {
        n.headword
        for n in notes
        if n.english_distinction and collisions.has_case_text(n.english_distinction)
    }
    assert bearing == set()


def test_map_cues_roles_and_separation() -> None:
    needed_a = make_note("a", translation="shore", english_distinction="river")
    needed_b = make_note("b", translation="shore", english_distinction="sea")
    same_a = make_note("c", translation="isle", english_distinction="adj. (x)")
    same_b = make_note("d", translation="isle", english_distinction="adj. (x)")
    covered_a = make_note(
        "e", translation="cold", deck=ADJECTIVES, english_distinction="weather"
    )
    covered_b = make_note("f", translation="cold", deck=NOUNS)
    lone = make_note("g", translation="solo", english_distinction="the only one")
    no_cue = make_note("h", translation="solo2")
    everything = [
        needed_a,
        needed_b,
        same_a,
        same_b,
        covered_a,
        covered_b,
        lone,
        no_cue,
    ]
    found = collisions.find_collisions(everything)
    uses = {u.headword: u for u in collisions.map_cues(everything, found)}
    assert list(uses) == ["a", "b", "c", "d", "e", "g"]
    assert uses["a"].role == "needed"
    assert uses["a"].separates is True
    assert uses["a"].groups == ("shore",)
    assert uses["a"].cue == "river"
    assert uses["a"].guid == needed_a.guid
    assert uses["c"].role == "needed"
    assert uses["c"].separates is False
    assert uses["e"].role == "covered"
    assert uses["e"].separates is False
    assert uses["g"].role == "none"
    assert uses["g"].groups == ()
    assert uses["g"].separates is False


def test_map_cues_separates_needs_one_side_nonempty() -> None:
    cued = make_note("a", translation="shore", english_distinction="river")
    bare = make_note("b", translation="shore")
    uses = collisions.map_cues([cued, bare], collisions.find_collisions([cued, bare]))
    assert [u.headword for u in uses] == ["a"]
    assert uses[0].separates is True


def test_map_cues_real_entry_count(
    notes: list[Note], groups: list[collisions.CollisionGroup]
) -> None:
    assert len(collisions.map_cues(notes, groups)) == 194


def test_classify_row_columns_are_declared() -> None:
    assert collisions.COLUMNS == (
        "family",
        "note type",
        "headword (keyed)",
        "guid",
        "source field",
        "qualifier text",
        "applies to",
        "action",
        "resulting Translation",
        "resulting English Distinction",
        "resulting Additional Info",
        "reason",
        "decision",
    )
    assert collisions.ACTIONS == (
        "move-to-distinction",
        "keep-inline",
        "drop-duplicate",
        "drop-header-duplicate",
        "drop-case",
        "rewrite-cue-non-case",
        "keep",
    )
    assert [f.name for f in dataclasses.fields(collisions.ClassificationRow)] == [
        "family",
        "note_type",
        "headword",
        "guid",
        "source_field",
        "qualifier_text",
        "applies_to",
        "action",
        "resulting_translation",
        "resulting_english_distinction",
        "resulting_additional_info",
        "reason",
        "decision",
    ]


def test_russian_distinction_row_names_siblings() -> None:
    shared = make_note(
        "согласно (preposition)", russian_distinction="preposition", guid="g1"
    )
    sibling = make_note("согласно (adverb)", russian_distinction="adverb", guid="g2")
    lone = make_note("уникальный", russian_distinction="odd", guid="g3")
    by_field = classify_one(shared, sibling, lone)
    [row] = by_field["Russian Distinction"]
    assert (row.applies_to, row.action) == ("whole word", "keep")
    assert "согласно (adverb)" in row.reason
    [lone_row] = classify_one(lone, shared, sibling)["Russian Distinction"]
    assert lone_row.action == "keep"
    assert "(adverb)" not in lone_row.reason


def test_no_russian_distinction_row_when_empty() -> None:
    assert "Russian Distinction" not in classify_one(make_note("a", translation="x"))


@pytest.mark.parametrize(
    ("translation", "deck", "text", "action", "applies"),
    [
        (
            "about (takes Genitive)",
            PREPOSITIONS,
            "takes Genitive",
            "drop-case",
            "whole word",
        ),
        ("big (adj.)", ADJECTIVES, "adj.", "drop-header-duplicate", "whole word"),
        ("big (noun)", ADJECTIVES, "noun", "move-to-distinction", "whole word"),
        ("carrot(s)", NOUNS, "s", "keep", "whole word"),
        ("run (to)", VERBS, "to", "keep", "whole word"),
        ("tool (one)", NOUNS, "one", "keep", "whole word"),
        ("about (whom/what)", PREPOSITIONS, "whom/what", "keep-inline", "sense 1 of 1"),
        (
            "bank (the financial one)",
            NOUNS,
            "the financial one",
            "move-to-distinction",
            "whole word",
        ),
        ("a (red one)<br>b", NOUNS, "red one", "keep-inline", "sense 1 of 2"),
        ("x / y (kind)", NOUNS, "kind", "keep-inline", "sense 2 of 2"),
    ],
)
def test_translation_parenthetical_rules(
    translation: str, deck: str, text: str, action: str, applies: str | None
) -> None:
    note = make_note("w", translation=translation, deck=deck)
    matching = [
        r for r in classify_one(note)["Translation"] if r.qualifier_text == text
    ]
    assert len(matching) == 1
    row = matching[0]
    assert row.action == action
    assert row.source_field == "Translation"
    if applies is not None:
        assert row.applies_to == applies


def test_translation_rows_in_order_and_one_each() -> None:
    note = make_note("w", translation="a (first) / b<br>c (whom)")
    rows_ = classify_one(note)["Translation"]
    assert [r.qualifier_text for r in rows_] == ["first", "whom"]


def test_slash_synonym_attachment_reason_mentions_position() -> None:
    attached = make_note("w", translation="x / y (kind)")
    [row] = classify_one(attached)["Translation"]
    split_lines = make_note("v", translation="x (kind)<br>y")
    [other] = classify_one(split_lines)["Translation"]
    assert "position" in row.reason
    assert "position" not in other.reason


def test_translation_without_parentheticals_has_no_translation_rows() -> None:
    assert "Translation" not in classify_one(make_note("w", translation="plain"))


def test_english_distinction_case_not_needed_is_dropped() -> None:
    note = make_note(
        "w", translation="near", english_distinction="Genitive; right beside"
    )
    [row] = classify_one(note)["English Distinction"]
    assert row.action == "drop-case"
    assert row.applies_to == "whole word"
    assert row.resulting_english_distinction == ""


def test_english_distinction_case_needed_is_rewritten() -> None:
    first = make_note(
        "a",
        translation="near",
        deck=PREPOSITIONS,
        english_distinction="Genitive; right beside",
    )
    second = make_note(
        "b", translation="near", deck=PREPOSITIONS, english_distinction="very close"
    )
    [row] = classify_one(first, second)["English Distinction"]
    assert row.action == "rewrite-cue-non-case"
    assert row.resulting_english_distinction == "right beside"


def test_english_distinction_case_needed_without_residual_asks_for_editorial_cue() -> (
    None
):
    first = make_note(
        "a",
        translation="near",
        deck=PREPOSITIONS,
        english_distinction="Accusative or Instrumental",
    )
    second = make_note("b", translation="near", deck=PREPOSITIONS)
    [row] = classify_one(first, second)["English Distinction"]
    assert row.action == "rewrite-cue-non-case"
    assert row.resulting_english_distinction == ""
    assert row.reason.startswith("needs editorial cue:")


def test_english_distinction_case_residual_restating_translation_is_dropped() -> None:
    first = make_note(
        "a",
        translation="right beside",
        deck=PREPOSITIONS,
        english_distinction="Genitive; right beside",
    )
    second = make_note("b", translation="right beside", deck=PREPOSITIONS)
    [row] = classify_one(first, second)["English Distinction"]
    assert row.action == "drop-case"
    assert row.resulting_english_distinction == ""


@pytest.mark.parametrize(
    ("cue", "translation", "expected_cue"),
    [
        ("adj. (weather)", "cold", "weather"),
        ("adj.", "cold", ""),
        ("adj. (cold)", "cold", ""),
    ],
)
def test_english_distinction_leading_label_is_header_duplicate(
    cue: str, translation: str, expected_cue: str
) -> None:
    note = make_note(
        "w", translation=translation, deck=ADJECTIVES, english_distinction=cue
    )
    [row] = classify_one(note)["English Distinction"]
    assert row.action == "drop-header-duplicate"
    assert row.resulting_english_distinction == expected_cue


def test_english_distinction_restating_translation_is_dropped() -> None:
    note = make_note("w", translation="cold (weather)", english_distinction="cold")
    [row] = classify_one(note)["English Distinction"]
    assert row.action == "drop-duplicate"


def test_english_distinction_unrelated_cue_is_kept() -> None:
    lone = make_note("w", translation="mail", english_distinction="the postal kind")
    [row] = classify_one(lone)["English Distinction"]
    assert row.action == "keep"
    assert row.resulting_english_distinction == "the postal kind"


def test_english_distinction_row_absent_without_cue() -> None:
    assert "English Distinction" not in classify_one(make_note("w", translation="mail"))


def test_additional_info_restating_qualifiers_is_dropped() -> None:
    note = make_note(
        "w",
        translation="cold",
        english_distinction="weather related",
        additional_info="weather related",
    )
    by_field = classify_one(note)
    [row] = by_field["Additional Info"]
    assert row.action == "drop-duplicate"
    assert row.applies_to == "whole word"
    assert row.resulting_additional_info == ""


@pytest.mark.parametrize(
    "info",
    ["completely unrelated words here", "weather", "weather plus lots of other words"],
)
def test_additional_info_not_restating_qualifiers_is_untouched(info: str) -> None:
    note = make_note(
        "w",
        translation="cold",
        english_distinction="weather related",
        additional_info=info,
    )
    by_field = classify_one(note)
    assert "Additional Info" not in by_field
    assert all(
        r.resulting_additional_info == info for r in by_field["English Distinction"]
    )


def test_additional_info_uses_translation_qualifiers_and_russian_distinction() -> None:
    from_translation = make_note(
        "a", translation="cold (winter weather)", additional_info="winter weather"
    )
    from_russian = make_note(
        "b",
        translation="cold",
        russian_distinction="winter weather",
        additional_info="winter weather",
    )
    assert "Additional Info" in classify_one(from_translation)
    assert "Additional Info" in classify_one(from_russian)


def test_note_level_results_move_and_dedupe() -> None:
    note = make_note(
        "банк",
        translation="bank (the financial one)",
        english_distinction="the financial one",
    )
    result = collisions.classify([note])
    assert {r.resulting_translation for r in result} == {"bank"}
    assert {r.resulting_english_distinction for r in result} == {"the financial one"}


def test_note_level_results_join_moved_text_and_cue() -> None:
    note = make_note(
        "w",
        translation="cold (weather) / chill (inline one)<br>frost",
        english_distinction="mail kind",
        additional_info="keep me",
    )
    result = collisions.classify([note])
    assert len({r.resulting_translation for r in result}) == 1
    assert len({r.resulting_english_distinction for r in result}) == 1
    first = result[0]
    assert first.resulting_additional_info == "keep me"
    assert first.resulting_english_distinction.endswith("mail kind")


def test_note_level_results_drop_case_and_header_duplicates_from_translation() -> None:
    note = make_note(
        "w", translation="big (adj.) / large (takes Genitive)", deck=ADJECTIVES
    )
    result = collisions.classify([note])
    assert {r.resulting_translation for r in result} == {"big / large"}


def test_classify_emits_all_rows_with_empty_decision() -> None:
    note = make_note(
        "w",
        translation="cold (weather)",
        english_distinction="cold",
        russian_distinction="x",
        additional_info="cold weather",
    )
    result = collisions.classify([note])
    assert [r.source_field for r in result][:1] == ["Russian Distinction"]
    assert {r.decision for r in result} == {""}
    assert {r.family for r in result} == {"mutable"}
    assert {r.headword for r in result} == {"w"}
    assert all(r.action in collisions.ACTIONS for r in result)


def test_classify_accepts_explicit_groups() -> None:
    first = make_note(
        "a",
        translation="near",
        deck=PREPOSITIONS,
        english_distinction="Genitive; right beside",
    )
    second = make_note("b", translation="near", deck=PREPOSITIONS)
    implicit = collisions.classify([first, second])
    explicit = collisions.classify(
        [first, second], collisions.find_collisions([first, second])
    )
    assert implicit == explicit
    assert collisions.classify([first, second], []) != implicit


def test_tsv_round_trip_and_sanitising() -> None:
    row = collisions.ClassificationRow(
        family="mutable",
        note_type="t",
        headword="w",
        guid="g",
        source_field="Translation",
        qualifier_text="a\tb",
        applies_to="whole word",
        action="keep",
        resulting_translation="x\ny",
        resulting_english_distinction="",
        resulting_additional_info="",
        reason="r",
        decision="",
    )
    text = collisions.format_classification_tsv([row])
    lines = text.split("\n")
    assert text.endswith("\n")
    assert lines[0] == "\t".join(collisions.COLUMNS)
    assert len(lines) == 3
    assert lines[1].count("\t") == len(collisions.COLUMNS) - 1
    [parsed] = collisions.parse_classification_tsv(text)
    assert parsed == dataclasses.replace(
        row, qualifier_text="a b", resulting_translation="x y"
    )


def test_tsv_round_trip_of_classify_output() -> None:
    note = make_note("w", translation="cold (weather)", english_distinction="cold")
    result = collisions.classify([note])
    text = collisions.format_classification_tsv(result)
    assert collisions.parse_classification_tsv(text) == result


def test_check_rows_clean_run_reports_nothing() -> None:
    notes_ = [
        make_note("a", translation="cold (weather)", english_distinction="cold"),
        make_note(
            "b",
            translation="near",
            deck=PREPOSITIONS,
            english_distinction="Genitive; right beside",
        ),
    ]
    assert collisions.check_rows(collisions.classify(notes_), notes_) == []


def tamperable() -> tuple[list[Note], list[collisions.ClassificationRow]]:
    notes_ = [
        make_note("a", translation="cold (weather)", english_distinction="mail kind"),
    ]
    return notes_, collisions.classify(notes_)


def test_check_rows_reports_changed_translation_word() -> None:
    notes_, result = tamperable()
    tampered = [dataclasses.replace(result[0], resulting_translation="warm")] + result[
        1:
    ]
    assert collisions.check_rows(tampered, notes_)


def test_check_rows_tolerates_parenthetical_only_changes() -> None:
    notes_, result = tamperable()
    changed = [dataclasses.replace(r, resulting_translation="cold") for r in result]
    assert collisions.check_rows(changed, notes_) == []


def test_check_rows_reports_unknown_action() -> None:
    notes_, result = tamperable()
    tampered = [dataclasses.replace(result[0], action="bogus")] + result[1:]
    assert collisions.check_rows(tampered, notes_)


@pytest.mark.parametrize(
    "field", ["resulting_translation", "resulting_english_distinction"]
)
def test_check_rows_reports_case_text_in_results(field: str) -> None:
    notes_, result = tamperable()
    tampered = [dataclasses.replace(r, **{field: "cold Genitive"}) for r in result]
    assert collisions.check_rows(tampered, notes_)


def test_check_rows_reports_missing_cue_row() -> None:
    notes_, result = tamperable()
    without_cue = [r for r in result if r.source_field != "English Distinction"]
    assert len(without_cue) < len(result)
    assert collisions.check_rows(without_cue, notes_)


def test_check_rows_reports_missing_parenthetical_row() -> None:
    notes_, result = tamperable()
    without_paren = [r for r in result if r.source_field != "Translation"]
    assert len(without_paren) < len(result)
    assert collisions.check_rows(without_paren, notes_)


def test_real_every_cue_has_exactly_one_row(
    notes: list[Note], rows: list[collisions.ClassificationRow]
) -> None:
    for note in notes:
        matching = [
            r
            for r in rows
            if r.guid == note.guid and r.source_field == "English Distinction"
        ]
        assert len(matching) == (1 if note.english_distinction else 0)


def test_real_no_cue_row_names_a_case(rows: list[collisions.ClassificationRow]) -> None:
    assert not [
        r
        for r in rows
        if r.source_field == "English Distinction"
        and collisions.has_case_text(r.qualifier_text)
    ]


def test_real_screenshot_cases(rows: list[collisions.ClassificationRow]) -> None:
    still = rows_of(rows, "ещё", "Translation")
    actions = {r.qualifier_text: r.action for r in still}
    assert actions["ongoing"] == "keep-inline"
    assert actions["asking for more"] == "keep-inline"
    assert rows_of(rows, "ещё", "English Distinction") == []
    assert rows_of(rows, "ещё", "Additional Info") == []
    assert rows_of(rows, "до", "English Distinction") == []

    everything = {
        r.qualifier_text: r.action for r in rows_of(rows, "всё", "Translation")
    }
    assert everything["keeps on"] == "keep-inline"
    assert rows_of(rows, "всё", "English Distinction") == []

    assert rows_of(rows, "банк", "Translation") == []
    [bank] = rows_of(rows, "банк", "English Distinction")
    assert bank.qualifier_text == "the financial one"
    assert bank.action == "keep"


def test_real_rows_pass_check(
    notes: list[Note], rows: list[collisions.ClassificationRow]
) -> None:
    assert collisions.check_rows(rows, notes) == []
    assert {r.decision for r in rows} == {""}
    assert {r.action for r in rows} <= set(collisions.ACTIONS)


def test_committed_tsv_parses_and_has_no_pending_decisions() -> None:
    parsed = collisions.parse_classification_tsv(
        COMMITTED_TSV.read_text(encoding="utf-8")
    )
    assert parsed
    assert {r.decision for r in parsed} == {""}
    assert {r.action for r in parsed} <= set(collisions.ACTIONS)


def test_cli_groups_prints_table(capsys: pytest.CaptureFixture[str]) -> None:
    code = collisions.main(["--groups"])
    out = capsys.readouterr().out
    assert code == 0
    assert out.splitlines()[0].split("\t")[:3] == ["sense", "mechanism", "members"]
    assert len(out.splitlines()) == 203


def test_cli_pos_counts_prints_fields(capsys: pytest.CaptureFixture[str]) -> None:
    assert collisions.main(["--pos-counts"]) == 0
    out = capsys.readouterr().out
    for name in ("leading", "bare", "bare_abbreviated", "qualified", "trailing"):
        assert name in out
    assert "leading: 0" in out


def test_cli_write_then_check_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "classification.tsv"
    assert collisions.main(["--write-classification", str(target)]) == 0
    assert target.read_text(encoding="utf-8").startswith("family\t")
    assert collisions.main(["--check-classification", str(target)]) == 0


def test_cli_check_rejects_stale_file(tmp_path: Path) -> None:
    target = tmp_path / "classification.tsv"
    collisions.main(["--write-classification", str(target)])
    text = target.read_text(encoding="utf-8")
    lines = text.splitlines()
    target.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    assert collisions.main(["--check-classification", str(target)]) == 1


def test_core_imports_no_anki_module() -> None:
    script = (
        "import sys, anki_tools.collisions\n"
        "names = ('anki', 'aqt')\n"
        "bad = [m for m in sys.modules if m.split('.')[0] in names]\n"
        "print(bad)\n"
        "sys.exit(1 if bad else 0)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=PACKAGE_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
