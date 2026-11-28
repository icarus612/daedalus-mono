import dataclasses
from pathlib import Path

import pytest

from anki_tools import immutable_words_plan as iwp
from anki_tools import mutable_words_plan as mwp
from anki_tools import variant_pairs
from anki_tools.anki_identity import guid_for_row
from anki_tools.audio_naming import (
    STRESS_MARK,
    build_filename,
    parse_audio_filenames,
    spoken_text_for,
    stressed_headword,
    strip_qualifier,
    strip_stress,
)
from anki_tools.flagged_audio import clean_headwords

PACKAGE = Path(__file__).resolve().parents[1]
VOCABULARY = PACKAGE / "anki_tools" / "data" / "russian-vocabulary"
SOURCE_MD = PACKAGE / "tests" / "data" / "source-word-list.md"

MUTABLE_SHEETS = {
    "Nouns": ("nouns.tsv", mwp.parse_nouns, ("Russian",)),
    "Verbs": ("verbs.tsv", mwp.parse_verbs, ("Imperfective", "Perfective")),
    "Adjectives": ("adjectives.tsv", mwp.parse_adjectives, ("Russian (m)",)),
    "Adverbs": ("adverbs.tsv", mwp.parse_adverbs, ("Adverb",)),
    "Pronouns": ("pronouns.tsv", mwp.parse_pronouns, ("Russian",)),
    "Numerals": ("numerals.tsv", mwp.parse_numerals, ("Russian",)),
}


def _mutable_rows(sheet):
    file_name, parse, _ = MUTABLE_SHEETS[sheet]
    return parse(str(VOCABULARY / file_name))


def _immutable_rows():
    return iwp.parse_word_list(SOURCE_MD.read_text(encoding="utf-8"))


def _assert_only_stress_differs(names, before, after, headword_fields):
    for name, old, new in zip(names, before, after, strict=True):
        if name == "Stress":
            continue
        if name in headword_fields:
            plain = clean_headwords([new])
            assert (plain[0] if plain else strip_stress(new)) == old, name
        else:
            assert new == old, name


def test_strip_stress_removes_only_the_acute():
    assert strip_stress("больно́й (adjective)") == "больной (adjective)"
    assert strip_stress("учёный") == "учёный"


def test_stressed_headword_keeps_the_qualifier():
    assert stressed_headword("больной (adjective)", "больно́й") == (
        "больно́й (adjective)"
    )


def test_a_homograph_shows_both_stresses():
    assert stressed_headword("замок", "за́мок / замо́к") == "за́мок / замо́к"
    assert clean_headwords(["за́мок / замо́к"]) == ["замок"]


@pytest.mark.parametrize("stressed", ["", "  ", "за́мок (castle) / замо́к (lock)"])
def test_stressed_headword_falls_back_to_plain(stressed):
    assert stressed_headword("замок", stressed) == "замок"


@pytest.mark.parametrize("sheet", list(MUTABLE_SHEETS))
def test_mutable_identity_is_byte_identical(sheet):
    _, _, headword_fields = MUTABLE_SHEETS[sheet]
    names = mwp.FIELD_NAMES[sheet]
    for row in _mutable_rows(sheet):
        plain_row = dataclasses.replace(row, stress="")
        before, after = plain_row.fields(), row.fields()
        _assert_only_stress_differs(names, before, after, headword_fields)
        source = row.base_words[0]
        assert row.guid == plain_row.guid
        assert row.guid == (
            mwp.GUID_PINS.get((sheet, source)) or guid_for_row(source, sheet)
        )
        for field in headword_fields:
            displayed = after[names.index(field)]
            if not displayed:
                continue
            displayed = clean_headwords([displayed])[0]
            for slot in mwp.VOICE_SLOTS:
                assert build_filename(displayed, slot) == (
                    build_filename(before[names.index(field)], slot)
                )
            assert spoken_text_for(displayed) == spoken_text_for(
                strip_qualifier(before[names.index(field)])
            )


def test_immutable_identity_is_byte_identical():
    names = iwp.FIELD_NAMES
    for row in _immutable_rows():
        before = row.fields(stress={})
        after = row.fields()
        _assert_only_stress_differs(names, before, after, ("Russian",))
        displayed = after[names.index("Russian")]
        audio = parse_audio_filenames(after[names.index("Audio")])
        assert audio == [
            build_filename(strip_stress(displayed), slot) for slot in iwp.SLOTS
        ]
        assert row.guid == (
            iwp.GUID_PINS.get((row.pos, row.russian))
            or guid_for_row(row.russian, row.pos)
        )


def test_variant_pair_identity_is_byte_identical():
    names = variant_pairs.FIELD_NAMES
    for pair in variant_pairs.load_pairs():
        plain_pair = dataclasses.replace(pair, russian_stressed="", variant_stressed="")
        _assert_only_stress_differs(
            names, plain_pair.fields(), pair.fields(), ("Russian", "Variant")
        )


def test_mutable_headwords_carry_the_stress_cell():
    for sheet in MUTABLE_SHEETS:
        _, _, headword_fields = MUTABLE_SHEETS[sheet]
        names = mwp.FIELD_NAMES[sheet]
        for row in _mutable_rows(sheet):
            fields = row.fields()
            for field in headword_fields:
                displayed = fields[names.index(field)]
                stressed = [
                    part.strip()
                    for part in row.stress.split(" / ")
                    if strip_stress(part.strip()) == displayed.replace(STRESS_MARK, "")
                ]
                if displayed and stressed:
                    assert displayed == stressed[0], (sheet, displayed)


def test_a_missing_immutable_stress_row_falls_back_to_plain():
    row = _immutable_rows()[0]
    assert row.fields(stress={})[0] == strip_qualifier(row.russian)


def test_immutable_stress_file_matches_the_word_list():
    rows = {(row.pos, row.russian) for row in _immutable_rows()}
    stress = iwp.load_stress()
    stale = sorted(key for key in stress if key not in rows)
    mismatched = sorted(
        key
        for key, stressed in stress.items()
        if strip_stress(stressed) != strip_qualifier(key[1])
    )
    print(f"\nimmutable stress coverage: {len(rows & set(stress))}/{len(rows)} rows")
    assert not stale
    assert not mismatched


def test_variant_pair_stress_coverage():
    pairs = variant_pairs.load_pairs()
    words = [
        (word, stressed)
        for pair in pairs
        for word, stressed in (
            (pair.russian, pair.russian_stressed),
            (pair.variant, pair.variant_stressed),
        )
    ]
    covered = [word for word, stressed in words if stressed]
    print(f"\nvariant pair stress coverage: {len(covered)}/{len(words)} words")
    assert all(strip_stress(stressed) == word for word, stressed in words if stressed)


def test_live_stressed_headwords_resolve_to_plain_audio_words():
    assert clean_headwords(["де́лать", "сде́лать", "—"]) == ["делать", "сделать"]
    assert mwp.pronoun_audio_word("са́мый", "са́мого") == "самого-самый"
