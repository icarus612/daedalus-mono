"""Contract tests for anki_tools.immutable_words (Packet B, subphases 2.1-2.3).

Written blind to the implementation, from the plan and the lane l1 contract
(.artifacts/contracts/l1.md, "Packet B -- Anki plumbing") alone -- never read
anki_tools/immutable_words.py itself, only the contract text describing it.

Every test that needs the source note type works against a tmp_path COPY of
the real snapshot collection
(.workflows/russian-immutable-words/.artifacts/col-snapshot.anki2), made
*before* that copy is ever opened. The real snapshot path itself is never
opened directly, anywhere in this file.

Subphase 3.1 (builder-owned, out of this packet's scope) appends a full
build -> export -> import round-trip end-to-end test to this same file after
this packet goes green; nothing here should be removed or altered to
accommodate that later pass.
"""

import argparse
import hashlib
import os
import re
import shutil
import sys

import pytest
from anki.collection import Collection

from anki_tools.immutable_words import (
    NEW_NOTE_TYPE_NAME,
    SOURCE_NOTETYPE_ID,
    assert_unmodified,
    build_deck_tree,
    build_parser,
    clone_note_type,
    export_package,
    get_anki_collection_path,
    main,
    print_deck_table,
)
from anki_tools.immutable_words_plan import (
    DECK_ROOT,
    FIELD_NAMES,
    WordRow,
    all_subdeck_names,
    subdeck_name,
)

SNAPSHOT_PATH = (
    "/home/icarus64/repos/daedalus-mono/.workflows/russian-immutable-words"
    "/.artifacts/col-snapshot.anki2"
)

# Shared marker vocabulary from Packet A's contract (rewrite_audio_playback):
# both packets' blind testers assert against this exact set so they stay
# consistent without reading each other's code.
AUDIO_MARKERS = (
    'id="audio-data"',
    "{{Audio}}",
    'class="hidden"',
    "<script",
    "Math.random",
    "autoplay",
    "<button",
)

# A deliberately small, synthetic word-list document -- just enough for
# parse_word_list to accept (all four named sections present, each with a
# header + separator + at least one data row). Not the real 152-row
# document, which subphase 3.1's e2e test owns.
_FIXTURE_SOURCE_DOC = """# Fixture Word List

## Part 1: Russian Invariable Word Lists

### Prepositions (Test)
desc

| Rank | Russian | English |
|---|---|---|
| 1 | в | in |

### Conjunctions (Test)
desc

| Rank | Russian | English |
|---|---|---|
| 1 | и | and |

### Particles (Test)
desc

| Rank | Russian | English |
|---|---|---|
| 1 | же | emphasis |

### Indeclinable Nouns (Test)
desc

| Rank | Russian | English |
|---|---|---|
| 1 | метро | metro |
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _template_sides(note_type):
    """All 4 qfmt/afmt template strings, in tmpls order."""
    sides = []
    for tmpl in note_type["tmpls"]:
        sides.append(tmpl["qfmt"])
        sides.append(tmpl["afmt"])
    return sides


def _fixture_rows():
    """7 WordRows across all 4 decks, uneven counts, including the
    real document's "two da notes, both intended" case: one Conjunctions
    row and one Particles row sharing identical .russian text.
    """
    return [
        WordRow(pos="Prepositions", rank=1, russian="в", english="in"),
        WordRow(pos="Prepositions", rank=2, russian="на", english="on"),
        WordRow(pos="Prepositions", rank=3, russian="с", english="with"),
        WordRow(pos="Conjunctions", rank=1, russian="и", english="and"),
        WordRow(pos="Conjunctions", rank=2, russian="да", english="and, but"),
        WordRow(pos="Particles", rank=1, russian="да", english="yes"),
        WordRow(pos="Indeclinable Nouns", rank=1, russian="метро", english="metro"),
    ]


def _write_fixture_source(tmp_path, name="source.md"):
    path = os.path.join(str(tmp_path), name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(_FIXTURE_SOURCE_DOC)
    return path


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def collection_snapshot_copy(tmp_path):
    """Copy the real snapshot into tmp_path BEFORE ever opening it. Every
    test needing the source note type opens this copy, never the original.
    """
    copy_path = os.path.join(str(tmp_path), "snapshot-copy.anki2")
    shutil.copy2(SNAPSHOT_PATH, copy_path)
    return copy_path


@pytest.fixture
def build_col(tmp_path):
    """A fresh synthetic build collection, closed in teardown."""
    col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    try:
        yield col
    finally:
        col.close()


@pytest.fixture
def cloned(collection_snapshot_copy, build_col):
    """A real clone_note_type() result registered into build_col, plus the
    source note type's own css for byte-identical comparison. Shared by
    every test that just needs *a* cloned note type and doesn't care about
    timing the clone call itself (that's test_clone_note_type_leaves_
    source_unmodified_mtime_and_hash's job, which manages this by hand).
    """
    source_col = Collection(collection_snapshot_copy)
    try:
        source_css = source_col.models.get(SOURCE_NOTETYPE_ID)["css"]
        note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    finally:
        source_col.close()
    return note_type, source_css


# ---------------------------------------------------------------------------
# get_anki_collection_path
# ---------------------------------------------------------------------------


def test_get_anki_collection_path_posix(monkeypatch):
    monkeypatch.setattr(os, "name", "posix")
    path = get_anki_collection_path()
    assert path == os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")


def test_get_anki_collection_path_windows(monkeypatch):
    monkeypatch.setattr(os, "name", "nt")
    path = get_anki_collection_path()
    assert path == os.path.expanduser(
        "~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2"
    )


def test_get_anki_collection_path_unsupported_os_raises_oserror(monkeypatch):
    monkeypatch.setattr(os, "name", "java")
    with pytest.raises(OSError):
        get_anki_collection_path()


# ---------------------------------------------------------------------------
# clone_note_type
# ---------------------------------------------------------------------------


def test_clone_note_type_leaves_source_unmodified_mtime_and_hash(
    collection_snapshot_copy, build_col
):
    copy_path = collection_snapshot_copy
    source_col = Collection(copy_path)

    mtime_before = os.path.getmtime(copy_path)
    hash_before = _sha256(copy_path)

    clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    source_col.close()

    mtime_after = os.path.getmtime(copy_path)
    hash_after = _sha256(copy_path)

    assert mtime_after == mtime_before
    assert hash_after == hash_before


def test_clone_note_type_renamed_with_no_trailing_space(cloned):
    note_type, _ = cloned
    assert note_type["name"] == NEW_NOTE_TYPE_NAME
    assert not note_type["name"].endswith(" ")


def test_clone_note_type_field_list_matches_field_names_in_order(cloned):
    note_type, _ = cloned
    field_names = [f["name"] for f in note_type["flds"]]
    assert field_names == list(FIELD_NAMES)
    assert field_names == [
        "Russian",
        "Translation",
        "Pronunciation",
        "Part of Speech",
        "Audio",
        "Additional Info",
    ]


def test_clone_note_type_css_byte_identical_to_source(cloned):
    note_type, source_css = cloned
    assert note_type["css"] == source_css


def test_clone_note_type_strips_part_of_speech_from_every_template_side(cloned):
    note_type, _ = cloned
    for side in _template_sides(note_type):
        assert "{{Part of Speech}}" not in side


def test_clone_note_type_audio_markers_present_across_templates(cloned):
    note_type, _ = cloned
    combined = "\n".join(_template_sides(note_type))
    for marker in AUDIO_MARKERS:
        assert marker in combined, f"missing audio marker: {marker!r}"


def test_clone_note_type_never_contains_sound_tag(cloned):
    note_type, _ = cloned
    combined = "\n".join(_template_sides(note_type))
    assert "[sound:" not in combined


def test_clone_note_type_preserves_russian_and_translation_fields(cloned):
    note_type, _ = cloned
    combined = "\n".join(_template_sides(note_type))
    assert "{{Russian}}" in combined
    assert "{{Translation}}" in combined


def test_clone_note_type_missing_source_notetype_raises_value_error(tmp_path):
    # A fresh, empty collection genuinely has no note type with this id --
    # it's a real timestamp-derived id from the source account, effectively
    # impossible to collide with a brand-new tmp_path collection's defaults.
    bogus_source_col = Collection(os.path.join(str(tmp_path), "bogus-source.anki2"))
    bogus_build_col = Collection(os.path.join(str(tmp_path), "bogus-build.anki2"))
    try:
        with pytest.raises(ValueError):
            clone_note_type(bogus_source_col, bogus_build_col, NEW_NOTE_TYPE_NAME)
    finally:
        bogus_source_col.close()
        bogus_build_col.close()


# ---------------------------------------------------------------------------
# assert_unmodified
# ---------------------------------------------------------------------------


def test_assert_unmodified_same_mtime_does_not_raise(tmp_path):
    target = os.path.join(str(tmp_path), "tracked.txt")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("hello")
    mtime_before = os.path.getmtime(target)

    assert_unmodified(target, mtime_before)  # must not raise


def test_assert_unmodified_changed_mtime_raises_assertion_error(tmp_path):
    target = os.path.join(str(tmp_path), "tracked.txt")
    with open(target, "w", encoding="utf-8") as fh:
        fh.write("hello")
    mtime_before = os.path.getmtime(target)

    new_time = mtime_before + 1000  # comfortably past any FS mtime resolution
    os.utime(target, (new_time, new_time))

    with pytest.raises(AssertionError):
        assert_unmodified(target, mtime_before)


# ---------------------------------------------------------------------------
# build_deck_tree
# ---------------------------------------------------------------------------


def test_build_deck_tree_counts_match_all_subdeck_names_order(cloned, build_col):
    note_type, _ = cloned
    rows = _fixture_rows()

    counts = build_deck_tree(build_col, rows, note_type)

    expected = {
        subdeck_name("Prepositions"): 3,
        subdeck_name("Conjunctions"): 2,
        subdeck_name("Particles"): 1,
        subdeck_name("Indeclinable Nouns"): 1,
    }
    assert counts == expected
    assert list(counts.keys()) == all_subdeck_names()
    assert sum(counts.values()) == len(rows) == 7


def test_build_deck_tree_every_note_has_exactly_two_cards(cloned, build_col):
    note_type, _ = cloned
    rows = _fixture_rows()

    build_deck_tree(build_col, rows, note_type)

    assert build_col.card_count() == 2 * len(rows)
    for note_id in build_col.find_notes(""):
        assert len(build_col.get_note(note_id).cards()) == 2


def test_build_deck_tree_duplicate_russian_text_both_notes_exist_in_own_decks(
    cloned, build_col
):
    note_type, _ = cloned
    rows = _fixture_rows()

    build_deck_tree(build_col, rows, note_type)

    conjunctions_deck = subdeck_name("Conjunctions")
    particles_deck = subdeck_name("Particles")
    conjunctions_da = build_col.find_notes('deck:"%s" Russian:да' % conjunctions_deck)
    particles_da = build_col.find_notes('deck:"%s" Russian:да' % particles_deck)

    # Both notes exist, one per deck, and they are not the same note --
    # this is the real document's "da appears once under Conjunctions and
    # once under Particles" case: two intended notes, not a duplicate bug.
    assert len(conjunctions_da) == 1
    assert len(particles_da) == 1
    assert conjunctions_da[0] != particles_da[0]


def test_build_deck_tree_audio_field_predicts_four_filenames(cloned, build_col):
    """Per the l3 contract (audio_naming.py / immutable_words_plan.py
    section 3b), the Audio field is no longer always empty: it holds the
    four predicted filenames for the note's own Russian field, derived via
    anki_tools.audio_naming's build_filename/SLOTS -- the same shared
    function the deck builder and the TTS tool both rely on to agree
    byte-for-byte before any audio file exists.
    """
    from anki_tools.audio_naming import SLOTS, build_filename

    note_type, _ = cloned
    rows = _fixture_rows()

    build_deck_tree(build_col, rows, note_type)

    note_ids = build_col.find_notes("")
    assert len(note_ids) == len(rows)
    for note_id in note_ids:
        note = build_col.get_note(note_id)
        russian = note["Russian"]
        expected_audio = ",".join(build_filename(russian, slot) for slot in SLOTS)
        assert note["Audio"] == expected_audio
        assert note["Audio"] != ""


# ---------------------------------------------------------------------------
# export_package
# ---------------------------------------------------------------------------


def _build_small_tree(cloned_bundle, build_col):
    note_type, _ = cloned_bundle
    build_deck_tree(build_col, _fixture_rows()[:2], note_type)


def test_export_package_creates_nonempty_file(cloned, build_col, tmp_path):
    _build_small_tree(cloned, build_col)
    out_path = os.path.join(str(tmp_path), "out.apkg")

    export_package(build_col, DECK_ROOT, out_path, force=False)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_export_package_raises_file_exists_error_without_force(
    cloned, build_col, tmp_path
):
    _build_small_tree(cloned, build_col)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    export_package(build_col, DECK_ROOT, out_path, force=False)

    with pytest.raises(FileExistsError):
        export_package(build_col, DECK_ROOT, out_path, force=False)


def test_export_package_force_true_overwrites_without_raising(
    cloned, build_col, tmp_path
):
    _build_small_tree(cloned, build_col)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    export_package(build_col, DECK_ROOT, out_path, force=False)

    export_package(build_col, DECK_ROOT, out_path, force=True)  # must not raise

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_export_package_unknown_root_deck_raises_value_error(build_col, tmp_path):
    out_path = os.path.join(str(tmp_path), "out.apkg")

    with pytest.raises(ValueError):
        export_package(build_col, "Nowhere::At::All", out_path, force=False)


# ---------------------------------------------------------------------------
# print_deck_table (CLI-only, contract requires no more than "doesn't crash")
# ---------------------------------------------------------------------------


def test_print_deck_table_does_not_crash(capsys):
    counts = {
        subdeck_name("Prepositions"): 3,
        subdeck_name("Conjunctions"): 2,
        subdeck_name("Particles"): 1,
        subdeck_name("Indeclinable Nouns"): 1,
    }

    print_deck_table(counts)  # must not raise

    captured = capsys.readouterr()
    assert captured.out != ""


# ---------------------------------------------------------------------------
# build_parser / CLI
# ---------------------------------------------------------------------------


def test_build_parser_returns_argument_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_main_dry_run_writes_no_file_and_never_opens_a_collection(
    tmp_path, monkeypatch
):
    source_path = _write_fixture_source(tmp_path)
    fake_collection_path = os.path.join(str(tmp_path), "does-not-exist.anki2")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "immutable-words",
            "--source",
            source_path,
            "--dry-run",
            "--collection",
            fake_collection_path,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    # Dry-run must never open (and thereby create) a live collection.
    assert not os.path.exists(fake_collection_path)


def test_main_out_overwrite_refusal_end_to_end(
    tmp_path, monkeypatch, collection_snapshot_copy
):
    source_path = _write_fixture_source(tmp_path)
    out_path = os.path.join(str(tmp_path), "existing.apkg")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("pre-existing content")
    with open(out_path, "rb") as fh:
        before = fh.read()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "immutable-words",
            "--source",
            source_path,
            "--out",
            out_path,
            "--collection",
            collection_snapshot_copy,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code != 0
    with open(out_path, "rb") as fh:
        after = fh.read()
    assert after == before  # never overwritten without --force


def test_main_requires_out_unless_dry_run(tmp_path, monkeypatch):
    source_path = _write_fixture_source(tmp_path)
    fake_collection_path = os.path.join(str(tmp_path), "does-not-exist.anki2")

    # Neither --out nor --dry-run supplied.
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "immutable-words",
            "--source",
            source_path,
            "--collection",
            fake_collection_path,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code != 0


# ---------------------------------------------------------------------------
# Subphase 3.1 -- builder-authored e2e round trip (NOT part of Packet B; the
# builder writes this directly, after Packet B went green, per the lane
# contract's "3.1 is the load-bearing evidence" requirement). Full flow:
# parse the REAL source document -> clone_note_type against a copy of the
# REAL snapshot -> build_deck_tree all 153 rows -> export_package -> import
# the resulting .apkg into a brand-new collection that never existed before
# -> assert against the IMPORTED collection's own decks/notes/models, never
# against this test's own in-memory rows/build_col state.
#
# Updated by lane 3 (integration, `.artifacts/contracts/l3.md`): the source
# document still has 152 raw rows, but `parse_word_list` now applies a
# table-driven split/override transform (see `ROW_SPLITS`/
# `TRANSLATION_OVERRIDES` in `immutable_words_plan.py`) that yields 153
# final rows (43/36/32/42 by section), and `build_deck_tree` -> `WordRow.
# fields()` now populates every note's Audio field with four PREDICTED
# filenames instead of leaving it empty -- lane 3's central "deck before
# audio" claim.
# ---------------------------------------------------------------------------

SOURCE_DOC_PATH = (
    "/home/icarus64/repos/daedalus-mono/.workflows/russian-immutable-words"
    "/.artifacts/source-word-list.md"
)


def test_e2e_real_document_round_trip_import_asserts_on_imported_result(
    tmp_path, collection_snapshot_copy
):
    """The plan's load-bearing acceptance evidence.

    Builds the real 153-row .apkg from the real source document and a copy
    of the real note-type snapshot, imports it into a fresh empty
    collection, and asserts entirely against what THAT import produced.

    Also covers lane 3's central "deck-before-audio" claim end-to-end: no
    audio bytes are ever written or read anywhere in this test -- every
    note's Audio field is a comma-separated list of PREDICTED filenames for
    files that do not exist on this machine, and the export/import round
    trip must still succeed and preserve those four names byte-for-byte,
    matching `elevenlabs_tts.build_filename`'s own predictions for the same
    (word, slot) pairs -- proving the deck builder and the TTS tool agree
    on names before either of them ever touches a real audio file.
    """
    from anki_tools.audio_naming import SLOTS, build_filename
    from anki_tools.immutable_words_plan import counts_by_deck, parse_word_list

    with open(SOURCE_DOC_PATH, encoding="utf-8") as fh:
        source_text = fh.read()
    rows = parse_word_list(source_text)
    assert len(rows) == 153
    expected_counts = counts_by_deck(rows)
    assert expected_counts == {
        subdeck_name("Prepositions"): 43,
        subdeck_name("Conjunctions"): 36,
        subdeck_name("Particles"): 32,
        subdeck_name("Indeclinable Nouns"): 42,
    }

    snapshot_mtime_before = os.path.getmtime(collection_snapshot_copy)
    snapshot_hash_before = _sha256(collection_snapshot_copy)

    build_col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    source_col = Collection(collection_snapshot_copy)
    try:
        note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    finally:
        source_col.close()

    # The clone read must never touch the source file.
    assert os.path.getmtime(collection_snapshot_copy) == snapshot_mtime_before
    assert _sha256(collection_snapshot_copy) == snapshot_hash_before

    built_counts = build_deck_tree(build_col, rows, note_type)
    assert built_counts == expected_counts

    # Every note's Audio field is already populated by build_deck_tree
    # itself now -- no manual override needed (unlike this test's
    # pre-lane-3 shape, when Audio was always empty). Spot-check a handful
    # directly against build_col before export, including the load-bearing
    # multi-form case: the filename must derive from the SOURCE text
    # "в / во", never from the spoken form "во" (lane 3's central hazard).
    russian_to_audio = {}
    for note_id in build_col.find_notes(""):
        note = build_col.get_note(note_id)
        russian_to_audio[note["Russian"]] = note["Audio"]

    for russian in ("в / во", "словно", "будто", "-то", "-ка", "да"):
        assert russian in russian_to_audio, f"missing note for {russian!r}"
        expected_names = [build_filename(russian, slot) for slot in SLOTS]
        assert russian_to_audio[russian] == ",".join(expected_names)

    out_path = os.path.join(str(tmp_path), "immutable-words.apkg")
    export_package(build_col, DECK_ROOT, out_path)
    build_col.close()
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    # A collection at a path that has never existed before -- the strongest
    # available proof this is a real import, not a re-read of build_col.
    fresh_path = os.path.join(str(tmp_path), "fresh-import-target.anki2")
    assert not os.path.exists(fresh_path)
    fresh_col = Collection(fresh_path)
    try:
        from anki.import_export_pb2 import (
            ImportAnkiPackageOptions,
            ImportAnkiPackageRequest,
        )

        fresh_col.import_anki_package(
            ImportAnkiPackageRequest(
                package_path=out_path,
                options=ImportAnkiPackageOptions(
                    merge_notetypes=True,
                    with_scheduling=False,
                    with_deck_configs=False,
                ),
            )
        )

        # Deck tree, on the IMPORTED collection.
        for name in all_subdeck_names():
            deck_id = fresh_col.decks.id(name, create=False)
            assert deck_id is not None, f"deck missing after import: {name}"
            leaf = name.rsplit("::", 1)[-1]
            assert ". " in leaf  # the load-bearing <letter>. prefix

        # Per-deck note/card counts, all measured against the imported
        # collection's own cards -- never against built_counts or rows.
        total_notes = 0
        total_cards = 0
        for name in all_subdeck_names():
            card_ids = fresh_col.find_cards(f'deck:"{name}"')
            note_ids = {fresh_col.get_card(cid).nid for cid in card_ids}
            assert len(card_ids) == expected_counts[name] * 2, name
            assert len(note_ids) == expected_counts[name], name
            total_notes += len(note_ids)
            total_cards += len(card_ids)
        assert total_notes == 153
        assert total_cards == 306

        # Note type present, Part of Speech rendered nowhere.
        imported_note_type = fresh_col.models.by_name(NEW_NOTE_TYPE_NAME)
        assert imported_note_type is not None
        for side in _template_sides(imported_note_type):
            assert "{{Part of Speech}}" not in side

        # Spot-checked note, verbatim against the real document.
        last_indeclinable = [r for r in rows if r.pos == "Indeclinable Nouns"][-1]
        spot_note_ids = fresh_col.find_notes(
            f'deck:"{subdeck_name("Indeclinable Nouns")}" '
            f'Russian:"{last_indeclinable.russian}"'
        )
        assert spot_note_ids
        spot_note = fresh_col.get_note(spot_note_ids[0])
        assert spot_note["Russian"] == last_indeclinable.russian
        assert spot_note["Translation"] == last_indeclinable.english

        # Audio field: the central "deck-before-audio" claim, on the
        # IMPORTED collection -- every one of the 153 notes carries its
        # four predicted filenames, byte-for-byte identical to what
        # build_col had before export (`russian_to_audio`), and to what
        # `elevenlabs_tts.build_filename` predicts for the same (word,
        # slot) pairs. No audio file referenced here exists anywhere on
        # this machine -- the deck exports/imports cleanly on field-level
        # filename references alone.
        all_note_ids = fresh_col.find_notes(f'note:"{NEW_NOTE_TYPE_NAME}"')
        assert len(all_note_ids) == 153
        mismatches = []
        for note_id in all_note_ids:
            note = fresh_col.get_note(note_id)
            audio_value = note["Audio"]
            russian = note["Russian"]

            # Every entry parses as exactly 4 filenames -- the same split
            # the card template's own JS performs (`/[,\n]+/`), proving the
            # template will see four real entries, not one blob or a
            # trailing empty string.
            entries = [e for e in re.split(r"[,\n]+", audio_value) if e.strip()]
            if len(entries) != 4:
                mismatches.append((russian, "entry-count", entries))
                continue
            for entry in entries:
                if not entry.endswith(".mp3") or "," in entry or entry != entry.strip():
                    mismatches.append((russian, "malformed-entry", entry))

            if audio_value != russian_to_audio[russian]:
                mismatches.append(
                    (
                        russian,
                        "round-trip-mismatch",
                        audio_value,
                        russian_to_audio[russian],
                    )
                )

        assert not mismatches, f"Audio field problems after import: {mismatches}"
    finally:
        fresh_col.close()
