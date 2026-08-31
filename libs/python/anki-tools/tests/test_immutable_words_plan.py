"""Contract tests for ``anki_tools.immutable_words_plan`` (lane l1, Packet A
-- pure core; lane l3 packet re-derived counts/splits per section 6b).

Written from the lane contract's "Packet A -- pure core" section
(``.workflows/russian-immutable-words/.artifacts/contracts/l1.md``), plus
the plan and ask of record it points at, and -- for the split/override/
audio-field additions -- from the AUTHORITATIVE lane l3 contract
(``.workflows/russian-immutable-words/.artifacts/contracts/l3.md``,
sections 3 and 6b), which supersedes l1's row counts and multi-form catalog
where they disagree. The implementation under test
(``anki_tools/immutable_words_plan.py``) is never read by this file's
author -- every expectation below is derived from the contract text, not
from observed behaviour. Packet B (``immutable_words.py`` /
``test_immutable_words.py``) is a separate, parallel, equally blind packet
built against the same contract text; this file never touches Anki, the
``.anki2`` snapshot, or any note type at all -- it is the pure module's
test file only.

The real source document
(``.workflows/russian-immutable-words/.artifacts/source-word-list.md``,
parent worktree's gitignored run dir) is read directly by its absolute
path below and used as fixture data for the parser tests; it is a plain
input document, not part of the implementation under test, so reading it
does not compromise the blindness this file is required to keep.
"""

import re
from itertools import groupby

import pytest

from anki_tools.audio_naming import SLOTS
from anki_tools.audio_naming import build_filename as shared_build_filename
from anki_tools.immutable_words_plan import (
    DECK_ROOT,
    FIELD_NAMES,
    POS_FIELD_VALUE,
    SUBDECK_LEAVES,
    SourceDocumentError,
    WordRow,
    all_subdeck_names,
    counts_by_deck,
    parse_word_list,
    rewrite_audio_playback,
    strip_part_of_speech,
    subdeck_name,
)

REAL_SOURCE_PATH = (
    "/home/icarus64/repos/daedalus-mono/.workflows/russian-immutable-words"
    "/.artifacts/source-word-list.md"
)

# The four sections in document order, with the exact counts the real
# document is known to contain AFTER the l3 split/transform pass (contract
# l3.md section 3, "Acceptance numbers for this section"): raw parse is
# 152 rows / 43-35-32-42, but parse_word_list applies _apply_row_transforms
# before returning, so the counts below are the POST-transform ones.
EXPECTED_SECTION_COUNTS = [
    ("Prepositions", 43),
    ("Conjunctions", 36),
    ("Particles", 32),
    ("Indeclinable Nouns", 42),
]
EXPECTED_TOTAL_ROWS = sum(count for _, count in EXPECTED_SECTION_COUNTS)

EXPECTED_SUBDECK_PATHS = {
    "Prepositions": "Languages::Russian::2. Immutable Words::a. Prepositions",
    "Conjunctions": "Languages::Russian::2. Immutable Words::b. Conjunctions",
    "Particles": "Languages::Russian::2. Immutable Words::c. Particles",
    "Indeclinable Nouns": (
        "Languages::Russian::2. Immutable Words::d. Indeclinable Nouns"
    ),
}

# The 15 multi-form rows SURVIVING the l3 split/transform pass (contract
# l3.md section 6b): the original 17-entry catalog (l1.md) had two entries
# whose source strings no longer appear verbatim in the parsed output --
# "словно / будто" (was Conjunctions rank 16, now split into a standalone
# "словно" row) and "тоже / также" (was Conjunctions rank 18, now split
# into standalone "тоже" and "также" rows) -- both removed here. Every
# Conjunctions rank at/after the old rank 18 shifts by +1 because
# "тоже / также" expanded from 1 row to 2 (see l3.md section 3 for the
# renumbering algorithm); ranks below 16, and Prepositions/Particles
# (untouched by the split), keep their original numbers.
# (pos, rank, expected verbatim `.russian` value)
MULTI_FORM_ROWS = [
    ("Prepositions", 1, "в / во"),
    ("Prepositions", 3, "с / со"),
    ("Prepositions", 5, "к / ко"),
    ("Prepositions", 10, "о / об"),
    ("Conjunctions", 8, "чтобы / чтоб"),
    ("Conjunctions", 24, "ни... ни..."),
    ("Conjunctions", 25, "то... то..."),
    ("Conjunctions", 27, "несмотря на то, что"),
    ("Conjunctions", 28, "для того, чтобы"),
    ("Conjunctions", 29, "с тех пор, как"),
    ("Conjunctions", 30, "до того, как"),
    ("Conjunctions", 31, "перед тем, как"),
    ("Particles", 16, "пусть / пускай"),
    ("Particles", 24, "-то"),
    ("Particles", 25, "-ка"),
]


def test_multi_form_catalog_has_fifteen_entries():
    """Sanity check on the test's own fixture data, not the implementation."""
    assert len(MULTI_FORM_ROWS) == 15


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
# Fixtures -- small inline markdown, deliberately smaller than the real
# 152-row document, proving the parser does not hardcode 43/35/32/42.
# ---------------------------------------------------------------------------


def _build_fixture_doc(section_word_counts):
    """Build a minimal markdown document with the same "### <name> (...)"
    heading / pipe-table shape as the real source, but arbitrary (small)
    row counts per section, in the given order.
    """
    parts = []
    for name, count in section_word_counts.items():
        lines = [
            f"### {name} (test)",
            "Intro sentence for this section.",
            "",
            "| Rank | Russian | English |",
            "|---|---|---|",
        ]
        for i in range(1, count + 1):
            lines.append(f"| {i} | слово{i} | word{i} |")
        parts.append("\n".join(lines))
    return "\n\n".join(parts) + "\n"


SMALL_FIXTURE_COUNTS = [
    ("Prepositions", 2),
    ("Conjunctions", 1),
    ("Particles", 1),
    ("Indeclinable Nouns", 1),
]
SMALL_FIXTURE = _build_fixture_doc(dict(SMALL_FIXTURE_COUNTS))


def _remove_section(text, heading_name):
    """Delete a "### <heading_name> (...)" section, heading through its
    table, up to (but not including) the next "### " heading or EOF.
    """
    pattern = re.compile(
        rf"^### {re.escape(heading_name)} \(.*?\)\n.*?(?=^### |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    new_text, count = pattern.subn("", text)
    assert count == 1, (
        f"fixture setup: expected to remove exactly one {heading_name!r} section"
    )
    return new_text


# ---------------------------------------------------------------------------
# parse_word_list -- real document
# ---------------------------------------------------------------------------


def test_parse_real_document_total_row_count(real_rows):
    assert len(real_rows) == EXPECTED_TOTAL_ROWS == 153


def test_parse_real_document_section_order_counts_and_ranks(real_rows):
    """Sections appear in document order with the exact known counts, and
    within each section rows are in rank order starting at 1.
    """
    grouped = [
        (pos, list(group)) for pos, group in groupby(real_rows, key=lambda r: r.pos)
    ]

    assert [pos for pos, _ in grouped] == [name for name, _ in EXPECTED_SECTION_COUNTS]
    for (name, expected_count), (pos, rows_in_section) in zip(
        EXPECTED_SECTION_COUNTS, grouped
    ):
        assert pos == name
        assert len(rows_in_section) == expected_count, (
            f"{name}: expected {expected_count} rows, got {len(rows_in_section)}"
        )
        assert [r.rank for r in rows_in_section] == list(range(1, expected_count + 1))


def test_parse_real_document_row_order_endpoints(real_rows):
    assert real_rows[0].pos == "Prepositions"
    assert real_rows[0].rank == 1
    assert real_rows[-1].pos == "Indeclinable Nouns"
    assert real_rows[-1].rank == 42


@pytest.mark.parametrize(
    "pos,rank,expected_russian",
    MULTI_FORM_ROWS,
    ids=[f"{pos}-{rank}" for pos, rank, _ in MULTI_FORM_ROWS],
)
def test_multi_form_row_preserved_verbatim(real_rows, pos, rank, expected_russian):
    matches = [row for row in real_rows if row.pos == pos and row.rank == rank]
    assert len(matches) == 1, f"expected exactly one row for pos={pos!r} rank={rank}"
    assert matches[0].russian == expected_russian


def test_parse_real_document_part_two_produces_no_spurious_rows(real_rows):
    """Part 2 ("Generating Russian Audio with Anki Plugins" and its
    AwesomeTTS / HyperTTS / add-on-install subsections) has no tables and
    must not contribute rows or raise.
    """
    assert len(real_rows) == 153
    assert all(row.pos in SUBDECK_LEAVES for row in real_rows)


def test_parse_missing_section_raises_on_real_document(real_source_text):
    missing_particles = _remove_section(real_source_text, "Particles")
    with pytest.raises(SourceDocumentError):
        parse_word_list(missing_particles)


# ---------------------------------------------------------------------------
# parse_word_list -- small fixtures
# ---------------------------------------------------------------------------


def test_parse_small_fixture_counts():
    rows = parse_word_list(SMALL_FIXTURE)
    assert len(rows) == sum(count for _, count in SMALL_FIXTURE_COUNTS)

    grouped = [
        (pos, len(list(group))) for pos, group in groupby(rows, key=lambda r: r.pos)
    ]
    assert grouped == SMALL_FIXTURE_COUNTS


def test_parse_missing_section_raises_on_small_fixture():
    missing_conjunctions = _remove_section(SMALL_FIXTURE, "Conjunctions")
    with pytest.raises(SourceDocumentError):
        parse_word_list(missing_conjunctions)


# ---------------------------------------------------------------------------
# subdeck_name / all_subdeck_names
# ---------------------------------------------------------------------------


def test_deck_root_constant():
    assert DECK_ROOT == "Languages::Russian::2. Immutable Words"


def test_subdeck_leaves_order():
    assert list(SUBDECK_LEAVES) == [
        "Prepositions",
        "Conjunctions",
        "Particles",
        "Indeclinable Nouns",
    ]


@pytest.mark.parametrize("pos,expected", EXPECTED_SUBDECK_PATHS.items())
def test_subdeck_name_exact_path(pos, expected):
    assert subdeck_name(pos) == expected


@pytest.mark.parametrize("pos", EXPECTED_SUBDECK_PATHS)
def test_subdeck_name_contains_dot_space(pos):
    # Load-bearing: both templates split the leaf on ". " to build the
    # card header (hard constraint 2 in the lane contract).
    assert ". " in subdeck_name(pos)


def test_all_subdeck_names_order():
    assert all_subdeck_names() == list(EXPECTED_SUBDECK_PATHS.values())


def test_subdeck_name_unknown_pos_raises():
    with pytest.raises(Exception):
        subdeck_name("Adverbs")


# ---------------------------------------------------------------------------
# strip_part_of_speech
# ---------------------------------------------------------------------------

TEMPLATE_WITH_POS_DIV = """\
<div class="card">
  <div id="russian">{{Russian}}</div>
  <div id="part-of-speech">{{Part of Speech}}</div>
  <div id="translation">{{Translation}}</div>
</div>
"""

TEMPLATE_WITHOUT_POS_DIV = """\
<div class="card">
  <div id="russian">{{Russian}}</div>
  <div id="translation">{{Translation}}</div>
</div>
"""


def test_strip_part_of_speech_removes_div():
    result = strip_part_of_speech(TEMPLATE_WITH_POS_DIV)
    assert "part-of-speech" not in result
    assert "{{Part of Speech}}" not in result


def test_strip_part_of_speech_noop_when_absent():
    assert strip_part_of_speech(TEMPLATE_WITHOUT_POS_DIV) == TEMPLATE_WITHOUT_POS_DIV


def test_strip_part_of_speech_idempotent():
    once = strip_part_of_speech(TEMPLATE_WITH_POS_DIV)
    twice = strip_part_of_speech(once)
    assert twice == once


# ---------------------------------------------------------------------------
# rewrite_audio_playback
# ---------------------------------------------------------------------------

TEMPLATE_WITH_AUDIO_DIV = """\
<div class="card">
  <div id="russian">{{Russian}}</div>
  <div id="audio">{{Audio}}</div>
  <div id="translation">{{Translation}}</div>
</div>
"""

TEMPLATE_WITHOUT_AUDIO_DIV = """\
<div class="card">
  <div id="translation">{{Translation}}</div>
</div>
"""


def test_rewrite_audio_playback_marker_vocabulary_present():
    result = rewrite_audio_playback(TEMPLATE_WITH_AUDIO_DIV)
    for marker in (
        'id="audio-data"',
        "{{Audio}}",
        'class="hidden"',
        "<script",
        "Math.random",
        "autoplay",
        "<button",
    ):
        assert marker in result, f"expected marker {marker!r} in rewritten template"


def test_rewrite_audio_playback_removes_original_literal_block():
    result = rewrite_audio_playback(TEMPLATE_WITH_AUDIO_DIV)
    assert '<div id="audio">{{Audio}}</div>' not in result


def test_rewrite_audio_playback_never_emits_sound_tag_syntax():
    result = rewrite_audio_playback(TEMPLATE_WITH_AUDIO_DIV)
    assert "[sound:" not in result


def test_rewrite_audio_playback_idempotent():
    once = rewrite_audio_playback(TEMPLATE_WITH_AUDIO_DIV)
    twice = rewrite_audio_playback(once)
    assert twice == once


def test_rewrite_audio_playback_noop_when_absent():
    result = rewrite_audio_playback(TEMPLATE_WITHOUT_AUDIO_DIV)
    assert result == TEMPLATE_WITHOUT_AUDIO_DIV


# ---------------------------------------------------------------------------
# counts_by_deck
# ---------------------------------------------------------------------------


def test_counts_by_deck_includes_all_four_decks_even_zero():
    rows = (
        [
            WordRow(pos="Prepositions", rank=i, russian=f"р{i}", english=f"e{i}")
            for i in range(1, 4)
        ]
        + [WordRow(pos="Conjunctions", rank=1, russian="x", english="y")]
        + [
            WordRow(pos="Particles", rank=i, russian=f"p{i}", english=f"q{i}")
            for i in range(1, 3)
        ]
    )

    counts = counts_by_deck(rows)

    assert counts == {
        subdeck_name("Prepositions"): 3,
        subdeck_name("Conjunctions"): 1,
        subdeck_name("Particles"): 2,
        subdeck_name("Indeclinable Nouns"): 0,
    }


# ---------------------------------------------------------------------------
# WordRow
# ---------------------------------------------------------------------------


def test_field_names_constant():
    assert FIELD_NAMES == (
        "Russian",
        "Translation",
        "Pronunciation",
        "Part of Speech",
        "Audio",
        "Additional Info",
    )


@pytest.mark.parametrize("pos", list(SUBDECK_LEAVES))
def test_word_row_fields_shape_and_values(pos):
    # NOTE: per the l3 contract (section 3b), Audio is no longer always
    # empty -- it now holds the four predicted filenames. This test was
    # updated in lane l3 (see also
    # test_word_row_fields_audio_matches_shared_build_filename below, which
    # covers the Audio slot's exact contents in more detail).
    row = WordRow(pos=pos, rank=1, russian="русский текст", english="english text")

    fields = row.fields()

    assert len(fields) == len(FIELD_NAMES) == 6
    assert fields[0] == "русский текст"  # Russian
    assert fields[1] == "english text"  # Translation
    assert fields[2] == ""  # Pronunciation
    assert fields[3] == POS_FIELD_VALUE[pos]  # Part of Speech
    assert fields[4] == ",".join(
        shared_build_filename("русский текст", slot) for slot in SLOTS
    )  # Audio -- four predicted filenames, comma-joined
    assert fields[5] == ""  # Additional Info

    # Singular label, not the plural section name verbatim.
    assert POS_FIELD_VALUE[pos] != pos


@pytest.mark.parametrize("pos", list(SUBDECK_LEAVES))
def test_word_row_deck_property_matches_subdeck_name(pos):
    row = WordRow(pos=pos, rank=1, russian="x", english="y")
    assert row.deck == subdeck_name(pos)


# ---------------------------------------------------------------------------
# ROW_SPLITS / TRANSLATION_OVERRIDES applied through parse_word_list
# (contract l3.md section 3a/6b)
# ---------------------------------------------------------------------------

# The exact override texts from l3.md section 3a's TRANSLATION_OVERRIDES /
# ROW_SPLITS tables (transcribed verbatim from the contract, not read from
# any implementation).
SLOVNO_TRANSLATION = "as if, like (literary — a poetic simile)"
TOZHE_TRANSLATION = 'also, too (same action, different subject — "me too": Я тоже иду)'
TAKZHE_TRANSLATION = (
    "also, in addition (same subject, an extra thing — Я также купил хлеб; more formal)"
)
BUDTO_TRANSLATION = (
    "as if, as though (often implies doubt — "
    'он будто не знал "as if he didn\'t know", implying he did)'
)


def test_slovno_row_present_standalone_with_literal_simile_translation(real_rows):
    matches = [
        row
        for row in real_rows
        if row.pos == "Conjunctions" and row.russian == "словно"
    ]
    assert len(matches) == 1
    assert matches[0].english == SLOVNO_TRANSLATION


def test_tozhe_row_present_standalone(real_rows):
    matches = [
        row for row in real_rows if row.pos == "Conjunctions" and row.russian == "тоже"
    ]
    assert len(matches) == 1
    assert matches[0].english == TOZHE_TRANSLATION


def test_takzhe_row_present_standalone(real_rows):
    matches = [
        row for row in real_rows if row.pos == "Conjunctions" and row.russian == "также"
    ]
    assert len(matches) == 1
    assert matches[0].english == TAKZHE_TRANSLATION


def test_original_combined_split_strings_no_longer_appear(real_rows):
    russians = {row.russian for row in real_rows}
    assert "словно / будто" not in russians
    assert "тоже / также" not in russians


def test_budto_row_overridden_translation_not_bare_as_if(real_rows):
    matches = [
        row for row in real_rows if row.pos == "Particles" and row.russian == "будто"
    ]
    assert len(matches) == 1
    assert matches[0].english == BUDTO_TRANSLATION
    # Not the source document's own bare gloss.
    assert matches[0].english != "as if"


def _parse_raw_section_glosses(text):
    """Independent oracle, built directly from the RAW markdown source (not
    from parse_word_list), mapping pos -> {russian: english} using the same
    "### <name> (...)" heading / pipe-table shape the real document uses.
    Used only to compare pre-transform glosses against post-transform ones;
    this function is test fixture logic, not a re-implementation of
    anything under test.
    """
    row_re = re.compile(r"^\| *\d+ *\| *(.+?) *\| *(.+?) *\|\s*$")
    section_re = re.compile(
        r"^### (.+?) \(.*?\)\n(.*?)(?=^### |\Z)", re.MULTILINE | re.DOTALL
    )
    result = {}
    for heading, body in section_re.findall(text):
        heading = heading.strip()
        glosses = {}
        for line in body.splitlines():
            m = row_re.match(line)
            if m:
                glosses[m.group(1).strip()] = m.group(2).strip()
        if glosses:
            result[heading] = glosses
    return result


def test_exactly_three_rows_have_an_overridden_translation(real_source_text, real_rows):
    """Aggregate check restated from l3.md section 6b: exactly the -то, -ка,
    and budto rows have a translation that differs from what parse_word_list
    would have produced pre-transform for the same `.russian` text. The two
    ROW_SPLITS-created rows (словно, тоже, также) are excluded from this
    count -- they have no pre-transform row sharing their exact `.russian`
    text (their pre-image was the combined "словно / будто" / "тоже / также"
    string, not their own text), so a pre/post comparison keyed on `.russian`
    is not meaningful for them.
    """
    raw_glosses = _parse_raw_section_glosses(real_source_text)

    split_created_russian = {"словно", "тоже", "также"}
    overridden = []
    for row in real_rows:
        if row.russian in split_created_russian:
            continue
        raw_english = raw_glosses.get(row.pos, {}).get(row.russian)
        assert raw_english is not None, (
            f"expected {row.russian!r} (pos={row.pos!r}) to exist verbatim in "
            f"the raw source document"
        )
        if row.english != raw_english:
            overridden.append(row.russian)

    assert set(overridden) == {"-то", "-ка", "будто"}
    assert len(overridden) == 3


@pytest.mark.parametrize(
    "pos,russian",
    [
        ("Prepositions", "около"),
        ("Prepositions", "в / во"),
        ("Conjunctions", "и"),
        ("Conjunctions", "чтобы / чтоб"),
        ("Particles", "не"),
        ("Indeclinable Nouns", "метро"),
    ],
)
def test_untouched_rows_keep_original_document_gloss_verbatim(
    real_source_text, real_rows, pos, russian
):
    raw_glosses = _parse_raw_section_glosses(real_source_text)
    matches = [row for row in real_rows if row.pos == pos and row.russian == russian]
    assert len(matches) == 1
    assert matches[0].english == raw_glosses[pos][russian]


# ---------------------------------------------------------------------------
# WordRow.fields() -- Audio slot (index 4), populated (contract l3.md 3b)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pos,rank,russian",
    [
        ("Prepositions", 1, "в / во"),  # real multi-form row
        ("Conjunctions", 1, "и"),
        ("Particles", 20, "да"),
        ("Indeclinable Nouns", 2, "метро"),
    ],
)
def test_word_row_fields_audio_matches_shared_build_filename(pos, rank, russian):
    row = WordRow(pos=pos, rank=rank, russian=russian, english="whatever")
    fields = row.fields()
    audio_index = FIELD_NAMES.index("Audio")
    expected = ",".join(shared_build_filename(russian, slot) for slot in SLOTS)
    assert fields[audio_index] == expected
    assert fields[audio_index] != ""
