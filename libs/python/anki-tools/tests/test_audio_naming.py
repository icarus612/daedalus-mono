"""Contract tests for ``anki_tools.audio_naming`` (lane l3 packet, section 6a;
``parse_audio_filenames`` added by lane l4, section 1).

Written from the lane contract alone
(``.workflows/russian-immutable-words/.artifacts/contracts/l3.md``, section 1
"``anki_tools/audio_naming.py`` -- the ONE shared module" plus section 6a
"NEW ``tests/test_audio_naming.py``"; ``parse_audio_filenames`` from
``.artifacts/contracts/l4.md``, section 1). The implementation
(``anki_tools/audio_naming.py``, and the two modules that import from it,
``anki_tools/immutable_words_plan.py`` / ``anki_tools/elevenlabs_tts.py``) is
never read by this file's author -- every expectation below comes from the
contract text, not from observed behaviour.

The real source document
(``.workflows/russian-immutable-words/.artifacts/source-word-list.md``,
parent worktree's gitignored run dir) is read directly by its absolute path
below and used as fixture data for the parser-agreement test; it is a plain
input document, not part of the implementation under test, so reading it
does not compromise the blindness this file is required to keep.
"""

import os

import pytest

from anki_tools.audio_naming import (
    SLOTS,
    SPOKEN_TEXT_OVERRIDES,
    build_filename,
    get_anki_collection_path,
    get_anki_media_dir,
    parse_audio_filenames,
    sanitize_word_slug,
    spoken_text_for,
)
from anki_tools.elevenlabs_tts import VOICES
from anki_tools.elevenlabs_tts import build_filename as tts_build_filename
from anki_tools.immutable_words_plan import FIELD_NAMES, parse_word_list

REAL_SOURCE_PATH = (
    "/home/icarus64/repos/daedalus-mono/.workflows/russian-immutable-words"
    "/.artifacts/source-word-list.md"
)

_SOURCE_MISSING_REASON = (
    "source-word-list.md lives in the parent worktree's gitignored run dir "
    "(.artifacts/), which is destroyed with that worktree once this run's "
    "lanes merge and closeout runs -- this test verifies against the REAL "
    "word list while the run is in flight and skips once the artifact is "
    "gone, rather than becoming a permanently broken/false-failing test "
    "long after the data it checks stopped existing."
)


# ---------------------------------------------------------------------------
# SLOTS
# ---------------------------------------------------------------------------


def test_slots_constant():
    assert SLOTS == ("f1", "f2", "m1", "m2")


# ---------------------------------------------------------------------------
# sanitize_word_slug / build_filename -- moved-verbatim spot checks
# ---------------------------------------------------------------------------


def test_build_filename_bare_no_dir_name():
    # Docstring's own example (contract section 1).
    assert build_filename("около", "f1") == "около_f1.mp3"


def test_build_filename_with_dir_name_uses_os_path_join():
    assert build_filename("около", "f1", dir_name="x") == os.path.join(
        "x", "около_f1.mp3"
    )


def test_build_filename_none_dir_name_returns_bare_name_explicitly():
    # None must behave identically to omitting the argument.
    assert build_filename("около", "f1", dir_name=None) == "около_f1.mp3"


@pytest.mark.parametrize("slot", list(SLOTS))
def test_build_filename_uses_word_slug_underscore_slot_dot_mp3(slot):
    assert build_filename("на", slot) == f"{sanitize_word_slug('на')}_{slot}.mp3"


def test_sanitize_word_slug_never_empty_and_no_hostile_chars():
    for word in ["в / во", "-то", "-ка", "ни... ни...", "простой"]:
        slug = sanitize_word_slug(word)
        assert slug
        for bad_char in ("/", "\\", "\0"):
            assert bad_char not in slug


def test_sanitize_word_slug_empty_input_falls_back_to_word():
    assert sanitize_word_slug("") == "word"


def test_sanitize_word_slug_deterministic():
    for word in ["около", "в / во", "-то"]:
        assert sanitize_word_slug(word) == sanitize_word_slug(word)


# ---------------------------------------------------------------------------
# spoken_text_for / SPOKEN_TEXT_OVERRIDES
# ---------------------------------------------------------------------------


def test_spoken_text_overrides_table_contents():
    assert SPOKEN_TEXT_OVERRIDES == {
        "в / во": "во",
        "с / со": "со",
        "к / ко": "ко",
        "о / об": "об",
        "-то": "то",
        "-ка": "ка",
        "чтобы / чтоб": "чтобы",
        "пусть / пускай": "пусть",
        "ни... ни...": "ни, ни",
        "то... то...": "то, то",
    }


@pytest.mark.parametrize("source,expected", list(SPOKEN_TEXT_OVERRIDES.items()))
def test_spoken_text_for_returns_override_for_every_table_key(source, expected):
    assert spoken_text_for(source) == expected


def test_spoken_text_for_clitic_particles_do_not_collapse_with_their_examples():
    # The exact hazard named in the contract: "-то"/"-ка" must speak as
    # bare "то"/"ка", never as some example word the particle attaches to.
    assert spoken_text_for("-то") == "то"
    assert spoken_text_for("-то") != "-то"
    assert "кто" not in spoken_text_for("-то")
    assert spoken_text_for("-ка") == "ка"
    assert spoken_text_for("-ка") != "-ка"
    assert "скажи" not in spoken_text_for("-ка")


@pytest.mark.parametrize("word", ["около", "словно", "будто", "тоже", "также"])
def test_spoken_text_for_passthrough_for_unlisted_words(word):
    # словно/будто/тоже/также are split into standalone single-word rows
    # upstream and therefore never appear as combined strings here -- each
    # speaks itself.
    assert spoken_text_for(word) == word


# ---------------------------------------------------------------------------
# THE load-bearing divergence test: filename derives from the source text,
# spoken text differs -- for all four preposition pairs plus both clitics.
# ---------------------------------------------------------------------------

DIVERGENT_PAIRS = [
    ("в / во", "во"),
    ("с / со", "со"),
    ("к / ко", "ко"),
    ("о / об", "об"),
    ("-то", "то"),
    ("-ка", "ка"),
]


@pytest.mark.parametrize(
    "source,expected_spoken", DIVERGENT_PAIRS, ids=[p[0] for p in DIVERGENT_PAIRS]
)
def test_filename_and_spoken_text_diverge_for_documented_pairs(source, expected_spoken):
    filename = build_filename(source, "f1")
    spoken = spoken_text_for(source)

    # Filename is built from the SOURCE text's own slug -- never the spoken
    # form's slug.
    assert filename == f"{sanitize_word_slug(source)}_f1.mp3"
    assert spoken == expected_spoken

    # The two must be different strings for every one of these six pairs.
    assert filename != spoken

    # Fails loudly if filename and spoken text were ever swapped or unified:
    # a "backwards" implementation that named the file after the SPOKEN form
    # would produce this value instead -- assert we did NOT produce it. (Not
    # meaningful for the two clitics, where sanitizing the bare spoken form
    # happens to coincide with sanitizing the hyphen-prefixed source -- the
    # `filename != spoken` assertion above is what carries the divergence
    # check for those two.)
    if sanitize_word_slug(source) != sanitize_word_slug(expected_spoken):
        wrong_filename = f"{sanitize_word_slug(expected_spoken)}_f1.mp3"
        assert filename != wrong_filename


# ---------------------------------------------------------------------------
# get_anki_media_dir
# ---------------------------------------------------------------------------


def test_get_anki_media_dir_derives_from_get_anki_collection_path():
    expected = os.path.join(
        os.path.dirname(get_anki_collection_path()), "collection.media"
    )
    assert get_anki_media_dir() == expected


def test_get_anki_media_dir_accepts_explicit_collection_path_override(tmp_path):
    fake_collection = os.path.join(str(tmp_path), "User 1", "collection.anki2")
    expected = os.path.join(str(tmp_path), "User 1", "collection.media")
    assert get_anki_media_dir(fake_collection) == expected


def test_get_anki_media_dir_override_does_not_call_get_anki_collection_path(
    monkeypatch, tmp_path
):
    import anki_tools.audio_naming as audio_naming_module

    def _boom():
        raise AssertionError(
            "get_anki_collection_path() must not be called when an explicit "
            "collection_path override is given"
        )

    monkeypatch.setattr(audio_naming_module, "get_anki_collection_path", _boom)

    fake_collection = os.path.join(str(tmp_path), "User 1", "collection.anki2")
    expected = os.path.join(str(tmp_path), "User 1", "collection.media")
    assert get_anki_media_dir(fake_collection) == expected


# ---------------------------------------------------------------------------
# Fixtures -- real document
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_source_text():
    with open(REAL_SOURCE_PATH, encoding="utf-8") as fh:
        return fh.read()


@pytest.fixture(scope="module")
def real_rows(real_source_text):
    return parse_word_list(real_source_text)


# ---------------------------------------------------------------------------
# THE full 153x4 agreement test -- the single most important test in this
# lane: the deck builder's predicted Audio field and the TTS tool's own
# build_filename must agree byte-for-byte, for every row and every slot, on
# the full real document, never a sample.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not os.path.isfile(REAL_SOURCE_PATH), reason=_SOURCE_MISSING_REASON)
def test_deck_audio_field_agrees_with_tts_build_filename_for_every_row_and_slot(
    real_rows,
):
    assert len(real_rows) == 153  # positive control: don't trivially pass on 0 rows

    audio_index = FIELD_NAMES.index("Audio")
    slot_to_voice = {voice.slot: voice for voice in VOICES}
    assert set(slot_to_voice) == set(SLOTS)  # all four slots represented

    checked = 0
    for row in real_rows:
        fields = row.fields()
        audio_names = fields[audio_index].split(",")
        assert len(audio_names) == len(SLOTS)

        for slot, predicted_name in zip(SLOTS, audio_names):
            voice = slot_to_voice[slot]
            # dir_name=None explicitly: the Audio field holds bare
            # filenames only (contract section 3b), so the TTS side's own
            # build_filename must be asked for the same bare form to agree
            # byte-for-byte.
            expected_name = tts_build_filename(row.russian, voice, dir_name=None)
            assert predicted_name == expected_name, (
                f"row pos={row.pos!r} rank={row.rank!r} russian={row.russian!r} "
                f"slot={slot!r}: deck predicted {predicted_name!r}, TTS side "
                f"produced {expected_name!r}"
            )
            checked += 1

    assert checked == 153 * 4 == 612


# ---------------------------------------------------------------------------
# Collision/uniqueness check restated at the module level
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not os.path.isfile(REAL_SOURCE_PATH), reason=_SOURCE_MISSING_REASON)
def test_153_rows_152_distinct_slugs_sole_repeat_is_da(real_rows):
    assert len(real_rows) == 153

    slugs = [sanitize_word_slug(row.russian) for row in real_rows]
    slug_to_words = {}
    for row, slug in zip(real_rows, slugs):
        slug_to_words.setdefault(slug, []).append(row.russian)
    collisions = {
        slug: words for slug, words in slug_to_words.items() if len(words) > 1
    }

    da_slug = sanitize_word_slug("да")
    assert list(collisions.keys()) == [da_slug], (
        f"expected exactly one repeated slug (the legitimate 'да' "
        f"duplicate); found instead: {collisions}"
    )
    assert collisions[da_slug] == ["да", "да"]

    assert len(set(slugs)) == 152

    # The split rule was corrected specifically to avoid manufacturing a
    # "будто" duplicate -- assert it explicitly is not one.
    budto_slug = sanitize_word_slug("будто")
    assert budto_slug != da_slug
    assert len(slug_to_words.get(budto_slug, [])) == 1


# ---------------------------------------------------------------------------
# parse_audio_filenames (lane l4, contract section 1) -- the Python-side
# mirror of the card template's own JS split (`/[,\n]+/` in
# rewrite_audio_playback), so attach_media (immutable_words.py) looks up
# on disk exactly the filenames the browser will try to play.
# ---------------------------------------------------------------------------


def test_parse_audio_filenames_comma_separated():
    assert parse_audio_filenames("a.mp3,b.mp3") == ["a.mp3", "b.mp3"]


def test_parse_audio_filenames_newline_and_comma_both_split():
    assert parse_audio_filenames("a.mp3\nb.mp3,c.mp3") == [
        "a.mp3",
        "b.mp3",
        "c.mp3",
    ]


def test_parse_audio_filenames_empty_string_yields_empty_list():
    assert parse_audio_filenames("") == []


def test_parse_audio_filenames_whitespace_only_string_yields_empty_list():
    assert parse_audio_filenames("  ") == []


def test_parse_audio_filenames_strips_incidental_whitespace():
    assert parse_audio_filenames("a.mp3, b.mp3") == ["a.mp3", "b.mp3"]


def test_parse_audio_filenames_never_yields_a_lone_empty_string_entry():
    # An empty/whitespace-only value must yield [], never [""].
    assert parse_audio_filenames("") != [""]
    assert parse_audio_filenames("   ") != [""]


def test_parse_audio_filenames_real_four_slot_value_round_trips():
    # The shape attach_media will actually see: build_filename's own CSV
    # output for a real word, all four slots.
    names = [build_filename("около", slot) for slot in SLOTS]
    csv_value = ",".join(names)
    assert parse_audio_filenames(csv_value) == names


def test_parse_audio_filenames_mixed_newline_comma_runs_collapse():
    # Consecutive separators (a run of commas/newlines) must not produce
    # empty entries in between -- mirrors the JS regex's `+` quantifier.
    assert parse_audio_filenames("a.mp3,,\n\nb.mp3") == ["a.mp3", "b.mp3"]
