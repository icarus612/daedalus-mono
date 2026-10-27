import pytest

from anki_tools import audio_naming, flagged_audio

MUTABLE_NOUNS = "Russian - Mutable Nouns (Ellis Version)"
MUTABLE_VERBS = "Russian - Mutable Verbs (Ellis Version)"
IMMUTABLE = flagged_audio.IMMUTABLE_NOTE_TYPE


@pytest.mark.parametrize(
    "stored,expected",
    [(0, 0), (1, 1), (4, 4), (7, 7), (8, 0), (9, 1), (4 | 8, 4), (1 | 16, 1)],
)
def test_flag_of_reads_only_the_low_three_bits(stored, expected):
    assert flagged_audio.flag_of(stored) == expected


def test_flag_names_cover_every_colour_anki_offers():
    assert sorted(flagged_audio.FLAG_NAMES) == [1, 2, 3, 4, 5, 6, 7]
    assert flagged_audio.UNFLAGGED not in flagged_audio.FLAG_NAMES


@pytest.mark.parametrize(
    "note_type,expected",
    [
        (IMMUTABLE, flagged_audio.MODE_DOUBLE),
        (MUTABLE_NOUNS, flagged_audio.MODE_SINGLE),
        (MUTABLE_VERBS, flagged_audio.MODE_SINGLE),
        ("Russian - Mutable Pronouns (Ellis Version)", flagged_audio.MODE_SINGLE),
    ],
)
def test_mode_follows_the_deck_family(note_type, expected):
    assert flagged_audio.mode_for_note_type(note_type) == expected


@pytest.mark.parametrize(
    "headwords,expected",
    [
        (["школа"], ["школа"]),
        (["повторять", "повторить"], ["повторять", "повторить"]),
        (["заблуждаться", "—"], ["заблуждаться"]),
        (["иметь", ""], ["иметь"]),
        (["брать", "-"], ["брать"]),
        (["  школа  "], ["школа"]),
        (["значить", "значить"], ["значить"]),
        (["как (conjunction)"], ["как (conjunction)"]),
    ],
)
def test_clean_headwords_drops_placeholders_and_repeats(headwords, expected):
    assert flagged_audio.clean_headwords(headwords) == expected


def test_clean_headwords_keeps_field_order():
    assert flagged_audio.clean_headwords(["возить", "везти"]) == ["возить", "везти"]


def test_unflagged_cards_are_never_picked_up():
    rows = [(0, MUTABLE_NOUNS, ["школа"]), (8, MUTABLE_NOUNS, ["дом"])]
    assert flagged_audio.words_to_regenerate(rows) == {}


def test_words_group_by_mode():
    rows = [
        (4, MUTABLE_NOUNS, ["школа"]),
        (1, IMMUTABLE, ["как (conjunction)"]),
    ]
    assert flagged_audio.words_to_regenerate(rows) == {
        flagged_audio.MODE_SINGLE: ["школа"],
        flagged_audio.MODE_DOUBLE: ["как (conjunction)"],
    }


def test_two_cards_of_one_note_voice_the_word_once():
    rows = [(4, MUTABLE_NOUNS, ["школа"]), (4, MUTABLE_NOUNS, ["школа"])]
    assert flagged_audio.words_to_regenerate(rows) == {
        flagged_audio.MODE_SINGLE: ["школа"]
    }


def test_a_flagged_verb_yields_both_aspects():
    rows = [(2, MUTABLE_VERBS, ["повторять", "повторить"])]
    assert flagged_audio.words_to_regenerate(rows) == {
        flagged_audio.MODE_SINGLE: ["повторить", "повторять"]
    }


def test_flags_wanted_restricts_to_those_colours():
    rows = [
        (1, MUTABLE_NOUNS, ["дом"]),
        (4, MUTABLE_NOUNS, ["школа"]),
        (7, MUTABLE_NOUNS, ["город"]),
    ]
    assert flagged_audio.words_to_regenerate(rows, flags_wanted=[4]) == {
        flagged_audio.MODE_SINGLE: ["школа"]
    }
    assert flagged_audio.words_to_regenerate(rows, flags_wanted=[1, 7]) == {
        flagged_audio.MODE_SINGLE: ["город", "дом"]
    }
    assert flagged_audio.words_to_regenerate(rows, flags_wanted=[3]) == {}


def test_flags_wanted_none_takes_every_colour():
    rows = [(c, MUTABLE_NOUNS, [f"w{c}"]) for c in range(1, 8)]
    picked = flagged_audio.words_to_regenerate(rows, flags_wanted=None)
    assert picked[flagged_audio.MODE_SINGLE] == [f"w{c}" for c in range(1, 8)]


def test_count_by_flag_reports_cards_not_words():
    rows = [
        (4, MUTABLE_NOUNS, ["школа"]),
        (4, MUTABLE_NOUNS, ["школа"]),
        (1, IMMUTABLE, ["как (conjunction)"]),
        (0, MUTABLE_NOUNS, ["дом"]),
    ]
    assert flagged_audio.count_by_flag(rows) == {1: 1, 4: 2}


def test_every_selected_word_resolves_to_a_filename():
    rows = [
        (4, MUTABLE_NOUNS, ["школа"]),
        (1, IMMUTABLE, ["как (conjunction)", "в / во"]),
    ]
    picked = flagged_audio.words_to_regenerate(rows)
    slots = {
        flagged_audio.MODE_SINGLE: ("f1", "m2"),
        flagged_audio.MODE_DOUBLE: ("f1", "f2", "m1", "m2"),
    }
    built = [
        audio_naming.build_filename(word, slot)
        for mode, words in picked.items()
        for word in words
        for slot in slots[mode]
    ]
    assert len(built) == 2 + 4 + 4
    assert all(name.endswith(".mp3") and " " not in name for name in built)
    assert "как_f1.mp3" in built and "в-во_m2.mp3" in built


def test_the_selection_check_catches_the_shape_it_guards():
    """Positive control: a flagged row must be able to produce a hit, or the
    negative assertions above prove nothing."""
    rows = [(4, MUTABLE_NOUNS, ["школа"])]
    assert flagged_audio.words_to_regenerate(rows)
    assert flagged_audio.count_by_flag(rows)
