"""Contract tests for anki_tools.immutable_words (Packet B, subphases 2.1-2.3;
``attach_media`` and the ``--audio-dir`` CLI flag added by lane l4).

Written blind to the implementation, from the plan and the lane l1 contract
(.artifacts/contracts/l1.md, "Packet B -- Anki plumbing") alone, plus the
lane l4 contract (.artifacts/contracts/l4.md, section 3, "New function
attach_media" and "CLI wiring in main()") for the media-attachment
additions -- never read anki_tools/immutable_words.py itself, only the
contract text describing it.

Every test that needs the source note type works against a tmp_path COPY of
the real snapshot collection
(.workflows/russian-immutable-words/.artifacts/col-snapshot.anki2), made
*before* that copy is ever opened. The real snapshot path itself is never
opened directly, anywhere in this file. Fixture ".mp3" files used to test
attach_media / --audio-dir are tiny fabricated byte strings written into
tmp_path -- never real audio, never anything read from
~/Desktop/russian-audio/, and no network access anywhere in this file.

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
    attach_media,
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


def _write_fake_mp3(directory, name, content=b"fake mp3 data"):
    """A tiny fabricated ``.mp3`` -- never real audio, never network. Used
    to test attach_media / --audio-dir without touching
    ~/Desktop/russian-audio/ or any real recording.
    """
    path = os.path.join(str(directory), name)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


def _referenced_filenames(build_col):
    """Independent oracle: every filename referenced by any note's Audio
    field, parsed the same way the card template's own JS does (comma/
    newline split) -- built directly here rather than importing
    attach_media's own parsing helper, so this doesn't just restate the
    implementation under test.
    """
    names = set()
    for note_id in build_col.find_notes(""):
        note = build_col.get_note(note_id)
        for entry in re.split(r"[,\n]+", note["Audio"]):
            entry = entry.strip()
            if entry:
                names.add(entry)
    return names


def _fixture_word_audio_filenames():
    """The predicted filenames for every word in _FIXTURE_SOURCE_DOC (one
    per section: Prepositions "в", Conjunctions "и", Particles "же",
    Indeclinable Nouns "метро"), keyed by word, four filenames each. Used
    by the --audio-dir CLI tests to build a fixture audio directory whose
    contents are known in advance.
    """
    from anki_tools.audio_naming import SLOTS, build_filename

    words = ["в", "и", "же", "метро"]
    return {word: [build_filename(word, slot) for slot in SLOTS] for word in words}


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
        "AudioRefs",
    ]

    # AudioRefs exists solely for Anki's media-usage scan (export/import/
    # Check Media) -- it must never be rendered by any template side, or it
    # would autoplay all four [sound:...] tags back to back (contract
    # l4.md section 2).
    for side in _template_sides(note_type):
        assert "{{AudioRefs}}" not in side


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
# attach_media (lane l4 contract, section 3 "New function attach_media")
# ---------------------------------------------------------------------------


def test_attach_media_zero_notes_returns_empty_lists_and_touches_nothing(
    build_col, tmp_path
):
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)

    found, missing = attach_media(build_col, audio_dir)

    assert found == []
    assert missing == []


def test_attach_media_found_missing_split_sorted_and_byte_identical_copy(
    cloned, build_col, tmp_path
):
    note_type, _ = cloned
    rows = _fixture_rows()
    build_deck_tree(build_col, rows, note_type)

    all_names = sorted(_referenced_filenames(build_col))
    assert all_names  # sanity: some filenames are actually referenced

    # Fixture bytes for roughly half of the referenced filenames; the rest
    # are deliberately absent from disk.
    half = len(all_names) // 2
    assert half > 0  # sanity: split is meaningful, not degenerate
    present_names = all_names[:half]
    absent_names = all_names[half:]

    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    contents = {}
    for name in present_names:
        content = f"fake mp3 data for {name}".encode("utf-8")
        contents[name] = content
        _write_fake_mp3(audio_dir, name, content)

    found, missing = attach_media(build_col, audio_dir)

    assert found == sorted(present_names)
    assert missing == sorted(absent_names)
    assert found == present_names  # already sorted -- confirms sort, not luck
    assert missing == absent_names

    media_dir = build_col.media.dir()
    for name in found:
        media_path = os.path.join(media_dir, name)
        assert os.path.isfile(media_path)
        with open(media_path, "rb") as fh:
            assert fh.read() == contents[name]


def test_attach_media_duplicate_filename_across_two_notes_deduplicated(
    cloned, build_col, tmp_path
):
    """The da/da fixture rows (Conjunctions rank 2, Particles rank 1) share
    identical .russian text and therefore identical predicted filenames --
    attach_media must copy each shared filename once (present exactly once
    in `found`, not twice) and must not raise a duplicate-add error.
    """
    from anki_tools.audio_naming import SLOTS, build_filename

    note_type, _ = cloned
    rows = _fixture_rows()
    build_deck_tree(build_col, rows, note_type)

    da_names = [build_filename("да", slot) for slot in SLOTS]
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    for name in da_names:
        _write_fake_mp3(audio_dir, name)

    found, missing = attach_media(build_col, audio_dir)  # must not raise

    for name in da_names:
        assert found.count(name) == 1
        assert name not in missing
    assert len(found) == len(set(found))  # no duplicates anywhere in found
    assert found == da_names  # only the да filenames were provided on disk


def test_attach_media_missing_source_file_is_never_raised_as_an_error(
    cloned, build_col, tmp_path
):
    """deck-before-audio: a note whose recordings do not exist yet must
    still let attach_media complete cleanly -- missing files are reported,
    never raised.
    """
    note_type, _ = cloned
    build_deck_tree(build_col, _fixture_rows(), note_type)

    audio_dir = os.path.join(str(tmp_path), "empty-audio")
    os.makedirs(audio_dir)

    found, missing = attach_media(build_col, audio_dir)  # must not raise

    assert found == []
    assert missing == sorted(_referenced_filenames(build_col))
    assert missing != []


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
# --audio-dir CLI wiring (lane l4 contract, section 3 "CLI wiring in main()")
# ---------------------------------------------------------------------------


def test_main_audio_dir_omitted_never_calls_attach_media(
    tmp_path, monkeypatch, collection_snapshot_copy, capsys
):
    """--audio-dir omitted: byte-for-byte identical to today -- no call to
    attach_media, export proceeds as before (contract l4.md section 3).
    """
    source_path = _write_fixture_source(tmp_path)
    out_path = os.path.join(str(tmp_path), "out.apkg")

    calls = []
    monkeypatch.setattr(
        "anki_tools.immutable_words.attach_media",
        lambda *a, **k: calls.append((a, k)) or ([], []),
    )

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

    assert exc_info.value.code == 0
    assert calls == []  # attach_media never invoked without --audio-dir
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0

    captured = capsys.readouterr()
    assert "Attached" not in captured.out
    assert "WARNING" not in captured.out


def test_main_audio_dir_some_files_present_attaches_and_warns_on_rest(
    tmp_path, monkeypatch, collection_snapshot_copy, capsys
):
    source_path = _write_fixture_source(tmp_path)
    out_path = os.path.join(str(tmp_path), "with-audio.apkg")
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)

    word_filenames = _fixture_word_audio_filenames()
    present_names = word_filenames["в"] + word_filenames["и"]
    missing_names = word_filenames["же"] + word_filenames["метро"]
    for name in present_names:
        _write_fake_mp3(audio_dir, name)

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
            "--audio-dir",
            audio_dir,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert f"Attached {len(present_names)} media file(s)" in captured.out
    assert "WARNING" in captured.out
    for name in missing_names:
        assert name in captured.out
    for name in present_names:
        # Only the ones genuinely missing should appear in the warning.
        assert f"missing: {name}" not in captured.out

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_main_audio_dir_no_matching_files_completes_and_warns_all(
    tmp_path, monkeypatch, collection_snapshot_copy, capsys
):
    """--audio-dir pointing at a directory with none of the referenced
    filenames: main() must still complete (never raise), report zero
    attached, and warn on every referenced filename.
    """
    source_path = _write_fixture_source(tmp_path)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    audio_dir = os.path.join(str(tmp_path), "empty-audio")
    os.makedirs(audio_dir)
    _write_fake_mp3(audio_dir, "unrelated-file.mp3")  # present, never referenced

    word_filenames = _fixture_word_audio_filenames()
    all_names = [name for names in word_filenames.values() for name in names]

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
            "--audio-dir",
            audio_dir,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Attached 0 media file(s)" in captured.out
    assert "WARNING" in captured.out
    for name in all_names:
        assert name in captured.out
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_main_audio_dir_export_measurably_larger_than_without(
    tmp_path, monkeypatch, collection_snapshot_copy
):
    source_path = _write_fixture_source(tmp_path)

    out_without = os.path.join(str(tmp_path), "without-audio.apkg")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "immutable-words",
            "--source",
            source_path,
            "--out",
            out_without,
            "--collection",
            collection_snapshot_copy,
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    audio_dir = os.path.join(str(tmp_path), "audio-full")
    os.makedirs(audio_dir)
    word_filenames = _fixture_word_audio_filenames()
    all_names = [name for names in word_filenames.values() for name in names]
    for name in all_names:
        # Sizeable, distinct-enough content per file so a naive "same
        # bytes reused" bug would still measurably grow the export.
        _write_fake_mp3(audio_dir, name, content=os.urandom(2048))

    out_with = os.path.join(str(tmp_path), "with-audio.apkg")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "immutable-words",
            "--source",
            source_path,
            "--out",
            out_with,
            "--collection",
            collection_snapshot_copy,
            "--audio-dir",
            audio_dir,
        ],
    )
    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0

    assert os.path.getsize(out_with) > os.path.getsize(out_without)


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


# ---------------------------------------------------------------------------
# Lane l4 -- builder-authored e2e: real media attachment, Anki's own
# media-usage scan, and a real fresh-collection import with real bytes.
#
# NOT blind, NOT a contract test: written by the builder against the PLAN'S
# acceptance criteria (the-ask.md / the l4 dispatch), after the l4 packet
# (AudioRefs field, attach_media, --audio-dir) went green above. Verifies the
# actual defect this lane fixes -- that Anki's media-usage scan (export
# bundling, import, Tools -> Check Media) sees the shipped audio as USED, not
# merely present on disk -- by calling Anki's own `col.media.check()` API,
# never by reasoning about what the scanner "should" do.
#
# Uses the REAL 608 mp3s at ~/Desktop/russian-audio/ (never regenerated, no
# ElevenLabs calls anywhere in this file) and a tmp_path COPY of the real
# snapshot collection, exactly like the rest of this file. Every collection
# opened here is either that copy or a from-scratch temp collection --
# ~/.local/share/Anki2/User 1/collection.anki2 is never opened.
# ---------------------------------------------------------------------------

REAL_AUDIO_DIR = os.path.expanduser("~/Desktop/russian-audio")

_real_audio_missing_reason = (
    f"real audio directory not found or incomplete: {REAL_AUDIO_DIR!r} "
    "(expects the 608 real .mp3 files generated for this run; this test "
    "verifies the actual shipped audio, not a fixture, so it skips rather "
    "than false-failing on a machine that never had them)"
)


def _real_audio_dir_ready():
    if not os.path.isdir(REAL_AUDIO_DIR):
        return False
    return len([f for f in os.listdir(REAL_AUDIO_DIR) if f.endswith(".mp3")]) >= 608


@pytest.mark.skipif(not _real_audio_dir_ready(), reason=_real_audio_missing_reason)
def test_e2e_real_media_is_marked_used_not_merely_present(
    tmp_path, collection_snapshot_copy
):
    """The lane's central claim, proven with Anki's own scanner.

    Builds the real 153-note deck, attaches the real 608 mp3s via
    `attach_media`, and calls `build_col.media.check()` -- the exact API
    Tools -> Check Media uses -- BEFORE ever exporting. Asserts zero unused
    and zero missing.

    Includes a POSITIVE CONTROL (verify-dont-assume: a bare "0 unused" is
    not evidence on its own -- prove the check could have failed): with
    `AudioRefs` blanked back out on every note (leaving the plain-filename
    `Audio` field untouched, exactly the pre-fix shape), the SAME files on
    the SAME disk are reported unused by the SAME `check()` call. That is
    the actual defect this lane fixes, demonstrated instead of argued.
    """
    from anki_tools.immutable_words_plan import parse_word_list

    with open(SOURCE_DOC_PATH, encoding="utf-8") as fh:
        rows = parse_word_list(fh.read())
    assert len(rows) == 153

    build_col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    source_col = Collection(collection_snapshot_copy)
    try:
        note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    finally:
        source_col.close()

    build_deck_tree(build_col, rows, note_type)

    found, missing = attach_media(build_col, REAL_AUDIO_DIR)
    assert missing == [], f"real audio files not found on disk: {missing}"
    assert len(found) == 608

    check = build_col.media.check()
    assert list(check.missing) == []
    assert list(check.unused) == [], (
        "Check Media would report these as unused -- i.e. deletable -- "
        f"despite being real, referenced audio: {list(check.unused)[:10]}"
    )

    # Positive control: blank AudioRefs (the pre-fix shape -- Audio's plain
    # filenames alone) and prove the SAME scan now flags the SAME files.
    note_ids = build_col.find_notes("")
    for note_id in note_ids:
        note = build_col.get_note(note_id)
        note["AudioRefs"] = ""
        build_col.update_note(note)

    control_check = build_col.media.check()
    assert len(control_check.unused) == 608, (
        "control failed: blanking AudioRefs should reproduce the original "
        "defect (all 608 real files reported unused) -- if it doesn't, "
        "this test's '0 unused' result above is not proof of anything"
    )

    build_col.close()


@pytest.mark.skipif(not _real_audio_dir_ready(), reason=_real_audio_missing_reason)
def test_e2e_real_media_export_is_full_size_not_empty_manifest(
    tmp_path, collection_snapshot_copy
):
    """The exported `.apkg` actually carries the 608 files' bytes.

    Asserts real size (~8+ MB, not the ~76 KB / 9-byte-manifest shape of the
    original defect) AND inspects the zip directly (never trusting size
    alone) for 608 media entries distinct from the package's own
    `meta`/`media`/`collection.anki2*` bookkeeping entries.
    """
    import zipfile

    from anki_tools.immutable_words_plan import parse_word_list

    with open(SOURCE_DOC_PATH, encoding="utf-8") as fh:
        rows = parse_word_list(fh.read())

    build_col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    source_col = Collection(collection_snapshot_copy)
    try:
        note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    finally:
        source_col.close()

    build_deck_tree(build_col, rows, note_type)
    found, missing = attach_media(build_col, REAL_AUDIO_DIR)
    assert missing == []

    out_path = os.path.join(str(tmp_path), "immutable-words-with-media.apkg")
    export_package(build_col, DECK_ROOT, out_path)
    build_col.close()

    size = os.path.getsize(out_path)
    assert size > 8 * 1024 * 1024, (
        f"expected a real media payload (~8+ MB), got {size} bytes -- this "
        "is the exact 76 KB/empty-manifest shape of the original defect"
    )

    with zipfile.ZipFile(out_path) as zf:
        names = set(zf.namelist())
    bookkeeping = {"meta", "media", "collection.anki2", "collection.anki21b"}
    media_entries = names - bookkeeping
    assert len(media_entries) == 608, (
        f"expected 608 media entries in the package, got {len(media_entries)}"
    )


@pytest.mark.skipif(not _real_audio_dir_ready(), reason=_real_audio_missing_reason)
def test_e2e_real_media_fresh_import_delivers_608_files_zero_missing(
    tmp_path, collection_snapshot_copy
):
    """The strongest evidence available: import the real package into a
    collection that never existed before, and assert entirely against what
    THAT import produced -- 153 notes, 306 cards, 608 media files actually
    present in the new collection's OWN media directory, and every filename
    in every note's `Audio` field resolving on disk (zero
    referenced-but-missing). Also re-runs `media.check()` on the imported
    collection itself, and confirms `{{AudioRefs}}` renders on neither
    template while `{{Audio}}` still renders on at least one.
    """
    from anki.import_export_pb2 import (
        ImportAnkiPackageOptions,
        ImportAnkiPackageRequest,
    )

    from anki_tools.audio_naming import parse_audio_filenames
    from anki_tools.immutable_words_plan import parse_word_list

    with open(SOURCE_DOC_PATH, encoding="utf-8") as fh:
        rows = parse_word_list(fh.read())

    build_col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    source_col = Collection(collection_snapshot_copy)
    try:
        note_type = clone_note_type(source_col, build_col, NEW_NOTE_TYPE_NAME)
    finally:
        source_col.close()

    build_deck_tree(build_col, rows, note_type)
    found, missing = attach_media(build_col, REAL_AUDIO_DIR)
    assert missing == []
    assert len(found) == 608

    out_path = os.path.join(str(tmp_path), "immutable-words.apkg")
    export_package(build_col, DECK_ROOT, out_path)
    build_col.close()

    fresh_path = os.path.join(str(tmp_path), "fresh-import-target.anki2")
    assert not os.path.exists(fresh_path)
    fresh_col = Collection(fresh_path)
    try:
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

        total_notes = 0
        total_cards = 0
        for name in all_subdeck_names():
            card_ids = fresh_col.find_cards(f'deck:"{name}"')
            note_ids = {fresh_col.get_card(cid).nid for cid in card_ids}
            total_notes += len(note_ids)
            total_cards += len(card_ids)
        assert total_notes == 153
        assert total_cards == 306

        media_files_on_disk = set(os.listdir(fresh_col.media.dir()))
        assert len(media_files_on_disk) == 608

        all_note_ids = fresh_col.find_notes(f'note:"{NEW_NOTE_TYPE_NAME}"')
        assert len(all_note_ids) == 153
        missing_refs = []
        for note_id in all_note_ids:
            note = fresh_col.get_note(note_id)
            names = parse_audio_filenames(note["Audio"])
            assert len(names) == 4, (note["Russian"], names)
            for name in names:
                if name not in media_files_on_disk:
                    missing_refs.append((note["Russian"], name))
        assert missing_refs == [], (
            f"referenced-but-missing after import: {missing_refs[:10]} "
            f"(+{max(0, len(missing_refs) - 10)} more)"
        )

        fresh_check = fresh_col.media.check()
        assert list(fresh_check.missing) == []
        assert list(fresh_check.unused) == []

        imported_note_type = fresh_col.models.by_name(NEW_NOTE_TYPE_NAME)
        sides = _template_sides(imported_note_type)
        assert not any("{{AudioRefs}}" in side for side in sides), (
            "a template renders {{AudioRefs}} -- this would autoplay all "
            "four recordings back to back, the exact bug the Audio/"
            "random-JS split exists to avoid"
        )
        assert any("{{Audio}}" in side for side in sides)
    finally:
        fresh_col.close()


def test_audio_refs_never_rendered_by_any_template_side(cloned):
    """Narrow, fast, fixture-only regression guard for the same invariant
    the real-import e2e test above proves at full scale: fails immediately
    if anyone later "helpfully" wires `{{AudioRefs}}` into a template.
    Does not need real audio or the real snapshot's live state beyond the
    already-shared `cloned` fixture.
    """
    note_type, _ = cloned
    sides = _template_sides(note_type)
    assert not any("{{AudioRefs}}" in side for side in sides)
    assert any("{{Audio}}" in side for side in sides)


def test_random_pick_js_and_empty_audio_render_cleanly(cloned, build_col):
    """`rewrite_audio_playback`'s JS still drives the `Audio` field (never
    `AudioRefs`) and a note with an empty `Audio` field still renders
    without error on every card side -- the defensive fallback documented
    in `rewrite_audio_playback` must still hold now that a 7th field exists.
    """
    note_type, _ = cloned
    deck_id = build_col.decks.id("Lane l4 render check", create=True)

    with_audio = build_col.new_note(note_type)
    with_audio["Russian"] = "около"
    with_audio["Translation"] = "near"
    with_audio["Audio"] = "около_f1.mp3,около_f2.mp3,около_m1.mp3,около_m2.mp3"
    with_audio["AudioRefs"] = (
        "[sound:около_f1.mp3][sound:около_f2.mp3]"
        "[sound:около_m1.mp3][sound:около_m2.mp3]"
    )
    build_col.add_note(with_audio, deck_id)

    empty_audio = build_col.new_note(note_type)
    empty_audio["Russian"] = "тест"
    empty_audio["Translation"] = "test"
    # Audio and AudioRefs both left at their default empty string.
    build_col.add_note(empty_audio, deck_id)

    saw_audio_data_span = False
    for note in (with_audio, empty_audio):
        for card in note.cards():
            output = card.render_output()  # must not raise
            question = output.question_text
            assert "{{AudioRefs}}" not in question
            if 'id="audio-data"' in question:
                saw_audio_data_span = True
                assert "Math.random" in question
                assert "<script" in question

    # At least one of the two notes' rendered sides actually exercised the
    # audio div (some sides legitimately don't render Audio at all -- see
    # rewrite_audio_playback's docstring).
    assert saw_audio_data_span
