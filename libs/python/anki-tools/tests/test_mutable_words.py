"""Contract tests for anki_tools.mutable_words, written blind from the lane
l2 packet spec alone. Every collection here is a from-scratch tmp_path file;
nothing opens ~/.local/share/Anki2/ or any real collection.
"""

import argparse
import csv
import hashlib
import os
import shutil
import sqlite3
import sys
import time

import pytest
from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageOptions, ImportAnkiPackageRequest

from anki_tools.audio_naming import get_anki_media_dir, parse_audio_filenames
from anki_tools.immutable_words import assert_unmodified
from anki_tools.mutable_words import (
    SOURCE_NOTETYPE_ID,
    TEMPLATE_COUNTS_BY_SHEET,
    attach_media,
    build_deck_tree,
    build_note_types,
    build_parser,
    export_package,
    main,
    print_deck_table,
)
from anki_tools.mutable_words_plan import (
    DECK_ROOT,
    FIELD_NAMES,
    NOTE_TYPE_NAMES,
    AdjectiveRow,
    AdverbRow,
    NounRow,
    VerbRow,
    all_subdeck_names,
    audio_names,
    build_note_type_id,
    subdeck_name,
)

_SOURCE_FIELD_NAMES = ["Word", "Meaning", "Notes"]

_FIXTURE_CSS = """\
.card {
    font-family: arial;
    font-size: 22px;
    color: navy;
}
.hidden {
    display: none !important;
}
"""


def _register_unicase_collation(conn):
    conn.create_collation(
        "unicase", lambda a, b: (a.lower() > b.lower()) - (a.lower() < b.lower())
    )


def _build_synthetic_source_collection(path):
    """Build a from-scratch source collection whose note type is forced onto
    SOURCE_NOTETYPE_ID via a raw sqlite write, mirroring
    test_immutable_words.py's fixture pattern. Shape need not match the real
    six-field source note type -- only its id and a non-trivial css matter.
    """
    col = Collection(path)
    try:
        note_type = col.models.new("Fixture Source Note Type")
        for name in _SOURCE_FIELD_NAMES:
            note_type["flds"].append(col.models.new_field(name))
        card = col.models.new_template("Card 1")
        card["qfmt"] = "{{Word}}"
        card["afmt"] = "{{FrontSide}}\n<hr id=answer>\n{{Meaning}}"
        note_type["tmpls"].append(card)
        note_type["css"] = _FIXTURE_CSS
        natural_id = col.models.add_dict(note_type).id
    finally:
        col.close()

    conn = sqlite3.connect(path)
    _register_unicase_collation(conn)
    try:
        conn.execute(
            "update notetypes set id = ? where id = ?",
            (SOURCE_NOTETYPE_ID, natural_id),
        )
        conn.execute(
            "update fields set ntid = ? where ntid = ?",
            (SOURCE_NOTETYPE_ID, natural_id),
        )
        conn.execute(
            "update templates set ntid = ? where ntid = ?",
            (SOURCE_NOTETYPE_ID, natural_id),
        )
        conn.commit()
    finally:
        conn.close()


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_fake_mp3(directory, name, content=b"fake mp3 data"):
    path = os.path.join(str(directory), name)
    with open(path, "wb") as fh:
        fh.write(content)
    return path


def _referenced_filenames(build_col):
    names = set()
    for note_id in build_col.find_notes(""):
        note = build_col.get_note(note_id)
        for field_name in note.keys():
            if field_name.startswith("Audio") and field_name != "AudioRefs":
                names.update(parse_audio_filenames(note[field_name]))
    return names


def _single_noun_referenced_names(cloned_note_types, build_col):
    """Build one noun row and return its two predicted filenames, sorted."""
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet(nouns=1, verbs=0, adjectives=0, adverbs=0)
    build_deck_tree(build_col, rows, note_types)
    names = sorted(_referenced_filenames(build_col))
    assert len(names) == 2
    return names


def _small_rows_by_sheet(nouns=3, verbs=2, adjectives=2, adverbs=2):
    noun_rows = [
        NounRow(
            rank=i + 1,
            russian=f"нос{i}",
            translation=f"noun{i}",
            stress="",
            gender="m",
            plural="",
            genitive_sg="",
            genitive_pl="",
            animate="inan",
            category="",
            additional_info="",
        )
        for i in range(nouns)
    ]
    verb_rows = [
        VerbRow(
            rank=i + 1,
            imperfective=f"делать{i}",
            perfective=f"сделать{i}",
            translation=f"verb{i}",
            stress="",
            conjugation="1",
            ya_1sg="",
            ty_2sg="",
            oni_3pl="",
            past_m_f="",
            case_preposition="",
            additional_info="",
        )
        for i in range(verbs)
    ]
    adjective_rows = [
        AdjectiveRow(
            rank=i + 1,
            russian_m=f"красный{i}",
            translation=f"adjective{i}",
            stress="",
            feminine="",
            neuter="",
            plural="",
            short_form="",
            comparative="",
            opposite="",
            stem_type="",
            additional_info="",
        )
        for i in range(adjectives)
    ]
    adverb_rows = [
        AdverbRow(
            rank=i + 1,
            adverb=f"быстро{i}",
            translation=f"adverb{i}",
            stress="",
            from_adjective="",
            formation="",
            comparative="",
            additional_info="",
        )
        for i in range(adverbs)
    ]
    return {
        "Nouns": noun_rows,
        "Verbs": verb_rows,
        "Adjectives": adjective_rows,
        "Adverbs": adverb_rows,
    }


def _write_tsv(path, header, data_rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(header)
        writer.writerows(data_rows)


def _write_nouns_tsv(path, rows):
    header = [
        "#",
        "Russian",
        "English",
        "Stress",
        "Gender",
        "Plural",
        "Genitive Sg",
        "Genitive Pl",
        "Animate",
        "Category",
        "Additional Info",
    ]
    data = [
        [
            r.rank,
            r.russian,
            r.translation,
            r.stress,
            r.gender,
            r.plural,
            r.genitive_sg,
            r.genitive_pl,
            r.animate,
            r.category,
            r.additional_info,
        ]
        for r in rows
    ]
    _write_tsv(path, header, data)


def _write_verbs_tsv(path, rows):
    header = [
        "#",
        "Imperfective",
        "Perfective",
        "English",
        "Stress",
        "Conjugation",
        "я (1sg)",
        "ты (2sg)",
        "они (3pl)",
        "Past (m / f)",
        "Case / Preposition",
        "Additional Info",
    ]
    data = [
        [
            r.rank,
            r.imperfective,
            r.perfective,
            r.translation,
            r.stress,
            r.conjugation,
            r.ya_1sg,
            r.ty_2sg,
            r.oni_3pl,
            r.past_m_f,
            r.case_preposition,
            r.additional_info,
        ]
        for r in rows
    ]
    _write_tsv(path, header, data)


def _write_adjectives_tsv(path, rows):
    header = [
        "#",
        "Russian (m)",
        "English",
        "Stress",
        "Feminine",
        "Neuter",
        "Plural",
        "Short Form",
        "Comparative",
        "Opposite",
        "Stem Type",
        "Additional Info",
    ]
    data = [
        [
            r.rank,
            r.russian_m,
            r.translation,
            r.stress,
            r.feminine,
            r.neuter,
            r.plural,
            r.short_form,
            r.comparative,
            r.opposite,
            r.stem_type,
            r.additional_info,
        ]
        for r in rows
    ]
    _write_tsv(path, header, data)


def _write_adverbs_tsv(path, rows):
    header = [
        "#",
        "Adverb",
        "English",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Status",
    ]
    data = [
        [
            r.rank,
            r.adverb,
            r.translation,
            r.stress,
            r.from_adjective,
            r.formation,
            r.comparative,
            r.additional_info,
            "confirmed",
        ]
        for r in rows
    ]
    _write_tsv(path, header, data)


def _write_source_dir(tmp_path, rows_by_sheet):
    source_dir = os.path.join(str(tmp_path), "source")
    os.makedirs(source_dir)
    _write_nouns_tsv(os.path.join(source_dir, "nouns.tsv"), rows_by_sheet["Nouns"])
    _write_verbs_tsv(os.path.join(source_dir, "verbs.tsv"), rows_by_sheet["Verbs"])
    _write_adjectives_tsv(
        os.path.join(source_dir, "adjectives.tsv"), rows_by_sheet["Adjectives"]
    )
    _write_adverbs_tsv(
        os.path.join(source_dir, "adverbs.tsv"), rows_by_sheet["Adverbs"]
    )
    return source_dir


def _build_and_export(rows_by_sheet, source_snapshot_path, out_dir, out_name):
    build_col = Collection(os.path.join(str(out_dir), f"build-{out_name}.anki2"))
    source_col = Collection(source_snapshot_path)
    try:
        note_types = build_note_types(source_col, build_col)
    finally:
        source_col.close()
    build_deck_tree(build_col, rows_by_sheet, note_types)
    out_path = os.path.join(str(out_dir), out_name)
    export_package(build_col, DECK_ROOT, out_path)
    build_col.close()
    return out_path, note_types


@pytest.fixture(scope="session")
def _synthetic_source_base(tmp_path_factory):
    base_dir = tmp_path_factory.mktemp("synthetic-source-base")
    base_path = os.path.join(str(base_dir), "synthetic-source.anki2")
    _build_synthetic_source_collection(base_path)
    return base_path


@pytest.fixture
def collection_snapshot_copy(tmp_path, _synthetic_source_base):
    copy_path = os.path.join(str(tmp_path), "snapshot-copy.anki2")
    shutil.copy2(_synthetic_source_base, copy_path)
    return copy_path


@pytest.fixture
def build_col(tmp_path):
    col = Collection(os.path.join(str(tmp_path), "build.anki2"))
    try:
        yield col
    finally:
        col.close()


@pytest.fixture
def cloned_note_types(collection_snapshot_copy, build_col):
    source_col = Collection(collection_snapshot_copy)
    try:
        source_css = source_col.models.get(SOURCE_NOTETYPE_ID)["css"]
        note_types = build_note_types(source_col, build_col)
    finally:
        source_col.close()
    return note_types, source_css


# build_note_types


def test_build_note_types_returns_all_four_sheets(cloned_note_types):
    note_types, _ = cloned_note_types
    assert set(note_types) == {"Nouns", "Verbs", "Adjectives", "Adverbs"}


def test_build_note_types_ids_match_deterministic_notetype_id(cloned_note_types):
    note_types, _ = cloned_note_types
    for sheet, note_type in note_types.items():
        assert note_type["id"] == build_note_type_id(sheet)


def test_build_note_types_ids_stable_across_two_builds(collection_snapshot_copy):
    ids_by_run = []
    for _ in range(2):
        build_col = Collection(collection_snapshot_copy + f"-build-{_}.anki2")
        source_col = Collection(collection_snapshot_copy)
        try:
            note_types = build_note_types(source_col, build_col)
        finally:
            source_col.close()
            build_col.close()
        ids_by_run.append({sheet: nt["id"] for sheet, nt in note_types.items()})
    assert ids_by_run[0] == ids_by_run[1]


def test_build_note_types_field_names_and_order_match_plan(cloned_note_types):
    note_types, _ = cloned_note_types
    for sheet, note_type in note_types.items():
        field_names = tuple(f["name"] for f in note_type["flds"])
        assert field_names == FIELD_NAMES[sheet]


def test_build_note_types_every_field_id_is_none(cloned_note_types):
    note_types, _ = cloned_note_types
    for note_type in note_types.values():
        for field in note_type["flds"]:
            assert field["id"] is None


def test_build_note_types_template_counts_and_names(cloned_note_types):
    note_types, _ = cloned_note_types
    for sheet, note_type in note_types.items():
        expected = TEMPLATE_COUNTS_BY_SHEET[sheet]
        templates = note_type["tmpls"]
        assert len(templates) == expected
        assert [t["name"] for t in templates] == [
            f"Card {i + 1}" for i in range(expected)
        ]


def test_build_note_types_verbs_have_four_templates(cloned_note_types):
    note_types, _ = cloned_note_types
    assert len(note_types["Verbs"]["tmpls"]) == 4


def test_build_note_types_css_byte_identical_to_source(cloned_note_types):
    note_types, source_css = cloned_note_types
    assert source_css
    for note_type in note_types.values():
        assert note_type["css"] == source_css


def test_build_note_types_new_note_succeeds_for_every_note_type(
    cloned_note_types, build_col
):
    note_types, _ = cloned_note_types
    for sheet, note_type in note_types.items():
        note = build_col.new_note(note_type)
        assert note is not None
        assert note.note_type()["id"] == note_type["id"]


def test_build_note_types_leaves_source_unmodified(collection_snapshot_copy, build_col):
    mtime_before = os.path.getmtime(collection_snapshot_copy)
    hash_before = _sha256(collection_snapshot_copy)

    source_col = Collection(collection_snapshot_copy)
    try:
        build_note_types(source_col, build_col)
    finally:
        source_col.close()

    assert_unmodified(collection_snapshot_copy, mtime_before)
    assert _sha256(collection_snapshot_copy) == hash_before


def test_build_note_types_missing_source_notetype_raises_value_error(tmp_path):
    bogus_source = Collection(os.path.join(str(tmp_path), "bogus-source.anki2"))
    bogus_build = Collection(os.path.join(str(tmp_path), "bogus-build.anki2"))
    try:
        with pytest.raises(ValueError):
            build_note_types(bogus_source, bogus_build)
    finally:
        bogus_source.close()
        bogus_build.close()


# build_deck_tree


def test_build_deck_tree_note_counts_all_decks_present(cloned_note_types, build_col):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet(nouns=3, verbs=2, adjectives=1, adverbs=0)

    counts = build_deck_tree(build_col, rows, note_types)

    expected = {
        subdeck_name("Nouns"): 3,
        subdeck_name("Verbs"): 2,
        subdeck_name("Adjectives"): 1,
        subdeck_name("Adverbs"): 0,
    }
    assert counts == expected
    assert list(counts.keys()) == all_subdeck_names()
    assert sum(counts.values()) == 6


def test_build_deck_tree_card_counts_use_real_template_counts_not_fixed_ratio(
    cloned_note_types, build_col
):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet(nouns=3, verbs=2, adjectives=1, adverbs=1)

    counts = build_deck_tree(build_col, rows, note_types)

    for sheet in ("Nouns", "Verbs", "Adjectives", "Adverbs"):
        deck = subdeck_name(sheet)
        template_count = len(note_types[sheet]["tmpls"])
        card_ids = build_col.find_cards(f'deck:"{deck}"')
        assert len(card_ids) == counts[deck] * template_count

    verbs_deck = subdeck_name("Verbs")
    verb_card_ids = build_col.find_cards(f'deck:"{verbs_deck}"')
    assert len(verb_card_ids) == counts[verbs_deck] * 4
    assert len(verb_card_ids) != counts[verbs_deck] * 2


def test_build_deck_tree_note_guid_matches_row_guid(cloned_note_types, build_col):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet()

    build_deck_tree(build_col, rows, note_types)

    checked = 0
    for sheet_rows in rows.values():
        for row in sheet_rows:
            note_ids = build_col.find_notes(f'deck:"{row.deck}"')
            matched = [
                nid for nid in note_ids if build_col.get_note(nid).guid == row.guid
            ]
            assert len(matched) == 1
            checked += 1
    assert checked == sum(len(v) for v in rows.values())


def test_build_deck_tree_note_fields_match_row_fields_in_order(
    cloned_note_types, build_col
):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet()

    build_deck_tree(build_col, rows, note_types)

    for sheet, sheet_rows in rows.items():
        row = sheet_rows[0]
        note_ids = [
            nid
            for nid in build_col.find_notes(f'deck:"{row.deck}"')
            if build_col.get_note(nid).guid == row.guid
        ]
        assert len(note_ids) == 1
        note = build_col.get_note(note_ids[0])
        for field_name, value in zip(FIELD_NAMES[sheet], row.fields()):
            assert note[field_name] == value


def test_build_deck_tree_two_builds_same_rows_identical_guid_set_and_notetype_ids(
    collection_snapshot_copy, tmp_path
):
    rows = _small_rows_by_sheet()

    first_col = Collection(os.path.join(str(tmp_path), "first.anki2"))
    second_col = Collection(os.path.join(str(tmp_path), "second.anki2"))
    try:
        source_col_1 = Collection(collection_snapshot_copy)
        try:
            note_types_1 = build_note_types(source_col_1, first_col)
        finally:
            source_col_1.close()

        source_col_2 = Collection(collection_snapshot_copy)
        try:
            note_types_2 = build_note_types(source_col_2, second_col)
        finally:
            source_col_2.close()

        build_deck_tree(first_col, rows, note_types_1)
        build_deck_tree(second_col, rows, note_types_2)

        first_guids = {first_col.get_note(nid).guid for nid in first_col.find_notes("")}
        second_guids = {
            second_col.get_note(nid).guid for nid in second_col.find_notes("")
        }
        assert first_guids
        assert first_guids == second_guids
        assert len(first_guids) == sum(len(v) for v in rows.values())

        ids_1 = {sheet: nt["id"] for sheet, nt in note_types_1.items()}
        ids_2 = {sheet: nt["id"] for sheet, nt in note_types_2.items()}
        assert ids_1 == ids_2
    finally:
        first_col.close()
        second_col.close()


def test_build_deck_tree_source_stays_unmodified(collection_snapshot_copy, build_col):
    mtime_before = os.path.getmtime(collection_snapshot_copy)

    source_col = Collection(collection_snapshot_copy)
    try:
        note_types = build_note_types(source_col, build_col)
    finally:
        source_col.close()
    build_deck_tree(build_col, _small_rows_by_sheet(), note_types)

    assert_unmodified(collection_snapshot_copy, mtime_before)


# attach_media


def test_attach_media_zero_notes_returns_empty_lists(build_col, tmp_path):
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)

    found, missing = attach_media(build_col, audio_dir)

    assert found == []
    assert missing == []


def test_attach_media_found_missing_split_sorted_and_bytes_copied(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet()
    build_deck_tree(build_col, rows, note_types)

    all_names = sorted(_referenced_filenames(build_col))
    assert all_names
    half = len(all_names) // 2
    assert half > 0
    present_names, absent_names = all_names[:half], all_names[half:]

    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    contents = {}
    for name in present_names:
        content = f"data for {name}".encode()
        contents[name] = content
        _write_fake_mp3(audio_dir, name, content)

    found, missing = attach_media(build_col, audio_dir)

    assert found == present_names
    assert missing == absent_names

    media_dir = build_col.media.dir()
    for name in found:
        with open(os.path.join(media_dir, name), "rb") as fh:
            assert fh.read() == contents[name]


def test_attach_media_verbs_union_of_both_audio_fields(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    rows = {
        "Nouns": [],
        "Verbs": _small_rows_by_sheet(verbs=1)["Verbs"],
        "Adjectives": [],
        "Adverbs": [],
    }
    build_deck_tree(build_col, rows, note_types)

    verb_row = rows["Verbs"][0]
    imperfective_names = audio_names(verb_row.imperfective)
    perfective_names = audio_names(verb_row.perfective)
    assert set(imperfective_names).isdisjoint(perfective_names)

    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    for name in imperfective_names + perfective_names:
        _write_fake_mp3(audio_dir, name)

    found, missing = attach_media(build_col, audio_dir)

    for name in imperfective_names + perfective_names:
        assert name in found
    assert missing == []


def test_attach_media_missing_files_reported_never_raised(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    build_deck_tree(build_col, _small_rows_by_sheet(), note_types)

    audio_dir = os.path.join(str(tmp_path), "empty-audio")
    os.makedirs(audio_dir)

    found, missing = attach_media(build_col, audio_dir)

    assert found == []
    assert missing == sorted(_referenced_filenames(build_col))
    assert missing != []


def test_attach_media_extra_dirs_resolves_name_absent_from_audio_dir(
    cloned_note_types, build_col, tmp_path
):
    target, other = _single_noun_referenced_names(cloned_note_types, build_col)

    audio_dir = os.path.join(str(tmp_path), "audio")
    extra_dir = os.path.join(str(tmp_path), "extra")
    os.makedirs(audio_dir)
    os.makedirs(extra_dir)
    _write_fake_mp3(audio_dir, other, b"audio-dir bytes")
    extra_content = b"extra-dir bytes"
    _write_fake_mp3(extra_dir, target, extra_content)

    found, missing = attach_media(build_col, audio_dir, extra_dirs=(extra_dir,))

    assert found == [target, other]
    assert missing == []
    with open(os.path.join(build_col.media.dir(), target), "rb") as fh:
        assert fh.read() == extra_content


def test_attach_media_audio_dir_wins_over_extra_dirs_on_name_collision(
    cloned_note_types, build_col, tmp_path
):
    target, _other = _single_noun_referenced_names(cloned_note_types, build_col)

    audio_dir = os.path.join(str(tmp_path), "audio")
    extra_dir = os.path.join(str(tmp_path), "extra")
    os.makedirs(audio_dir)
    os.makedirs(extra_dir)
    audio_content = b"audio-dir bytes"
    _write_fake_mp3(audio_dir, target, audio_content)
    _write_fake_mp3(extra_dir, target, b"extra-dir bytes")

    found, missing = attach_media(build_col, audio_dir, extra_dirs=(extra_dir,))

    assert target in found
    with open(os.path.join(build_col.media.dir(), target), "rb") as fh:
        assert fh.read() == audio_content


def test_attach_media_multiple_extra_dirs_walked_in_order(
    cloned_note_types, build_col, tmp_path
):
    target, _other = _single_noun_referenced_names(cloned_note_types, build_col)

    audio_dir = os.path.join(str(tmp_path), "audio")
    extra_dir_1 = os.path.join(str(tmp_path), "extra1")
    extra_dir_2 = os.path.join(str(tmp_path), "extra2")
    for directory in (audio_dir, extra_dir_1, extra_dir_2):
        os.makedirs(directory)
    second_content = b"second extra dir bytes"
    _write_fake_mp3(extra_dir_2, target, second_content)

    found, missing = attach_media(
        build_col, audio_dir, extra_dirs=(extra_dir_1, extra_dir_2)
    )

    assert target in found
    assert target not in missing
    with open(os.path.join(build_col.media.dir(), target), "rb") as fh:
        assert fh.read() == second_content


def test_attach_media_multi_dir_still_reports_genuine_absence(
    cloned_note_types, build_col, tmp_path
):
    target, _other = _single_noun_referenced_names(cloned_note_types, build_col)

    audio_dir = os.path.join(str(tmp_path), "audio")
    extra_dir_1 = os.path.join(str(tmp_path), "extra1")
    extra_dir_2 = os.path.join(str(tmp_path), "extra2")
    for directory in (audio_dir, extra_dir_1, extra_dir_2):
        os.makedirs(directory)

    found, missing = attach_media(
        build_col, audio_dir, extra_dirs=(extra_dir_1, extra_dir_2)
    )

    assert target in missing
    assert target not in found


def test_attach_media_extra_dirs_omitted_matches_single_dir_behavior(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    rows = _small_rows_by_sheet()
    build_deck_tree(build_col, rows, note_types)

    all_names = sorted(_referenced_filenames(build_col))
    half = len(all_names) // 2
    present_names, absent_names = all_names[:half], all_names[half:]

    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    for name in present_names:
        _write_fake_mp3(audio_dir, name)

    found, missing = attach_media(build_col, audio_dir)

    assert found == present_names
    assert missing == absent_names


# export_package


def test_export_package_creates_nonempty_file(cloned_note_types, build_col, tmp_path):
    note_types, _ = cloned_note_types
    build_deck_tree(build_col, _small_rows_by_sheet(), note_types)
    out_path = os.path.join(str(tmp_path), "out.apkg")

    export_package(build_col, DECK_ROOT, out_path, force=False)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_export_package_raises_file_exists_error_without_force(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    build_deck_tree(build_col, _small_rows_by_sheet(), note_types)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    export_package(build_col, DECK_ROOT, out_path, force=False)

    with pytest.raises(FileExistsError):
        export_package(build_col, DECK_ROOT, out_path, force=False)


def test_export_package_force_true_overwrites_without_raising(
    cloned_note_types, build_col, tmp_path
):
    note_types, _ = cloned_note_types
    build_deck_tree(build_col, _small_rows_by_sheet(), note_types)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    export_package(build_col, DECK_ROOT, out_path, force=False)

    export_package(build_col, DECK_ROOT, out_path, force=True)

    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0


def test_export_package_unknown_root_deck_raises_value_error(build_col, tmp_path):
    out_path = os.path.join(str(tmp_path), "out.apkg")

    with pytest.raises(ValueError):
        export_package(build_col, "Nowhere::At::All", out_path, force=False)


# Default ImportAnkiPackageOptions, never merge_notetypes=True -- that flag
# would mask an unstable notetype id instead of catching it.


def test_reimport_default_options_updates_in_place_no_duplicate_notetypes(
    tmp_path, collection_snapshot_copy
):
    rows = _small_rows_by_sheet()
    total_rows = sum(len(v) for v in rows.values())

    out1, _ = _build_and_export(rows, collection_snapshot_copy, tmp_path, "build1.apkg")

    fresh_path = os.path.join(str(tmp_path), "fresh.anki2")
    fresh_col = Collection(fresh_path)
    try:
        default_options = ImportAnkiPackageOptions()
        fresh_col.import_anki_package(
            ImportAnkiPackageRequest(package_path=out1, options=default_options)
        )
        assert fresh_col.note_count() == total_rows
        guids_after_import1 = {
            fresh_col.get_note(nid).guid for nid in fresh_col.find_notes("")
        }

        time.sleep(1.1)
        out2, _ = _build_and_export(
            rows, collection_snapshot_copy, tmp_path, "build2.apkg"
        )

        fresh_col.import_anki_package(
            ImportAnkiPackageRequest(package_path=out2, options=default_options)
        )
        fresh_col.close()
        fresh_col = Collection(fresh_path)

        assert fresh_col.note_count() == total_rows
        guids_after_import2 = {
            fresh_col.get_note(nid).guid for nid in fresh_col.find_notes("")
        }
        assert guids_after_import2 == guids_after_import1

        notetype_names = [n.name for n in fresh_col.models.all_names_and_ids()]
        for expected_name in NOTE_TYPE_NAMES.values():
            assert notetype_names.count(expected_name) == 1
    finally:
        fresh_col.close()


# print_deck_table


def test_print_deck_table_does_not_crash_with_varying_cards_per_note(capsys):
    counts = {
        subdeck_name("Nouns"): 3,
        subdeck_name("Verbs"): 2,
        subdeck_name("Adjectives"): 1,
        subdeck_name("Adverbs"): 1,
    }
    cards_per_note = {
        subdeck_name("Nouns"): 2,
        subdeck_name("Verbs"): 4,
        subdeck_name("Adjectives"): 2,
        subdeck_name("Adverbs"): 2,
    }

    print_deck_table(counts, cards_per_note)

    captured = capsys.readouterr()
    assert captured.out != ""


# build_parser / CLI


def test_build_parser_returns_argument_parser():
    parser = build_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_main_dry_run_opens_no_collection_and_writes_nothing(tmp_path, monkeypatch):
    source_dir = _write_source_dir(tmp_path, _small_rows_by_sheet())
    fake_collection_path = os.path.join(str(tmp_path), "does-not-exist.anki2")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
            "--dry-run",
            "--collection",
            fake_collection_path,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert not os.path.exists(fake_collection_path)


def test_main_requires_out_unless_dry_run(tmp_path, monkeypatch):
    source_dir = _write_source_dir(tmp_path, _small_rows_by_sheet())
    fake_collection_path = os.path.join(str(tmp_path), "does-not-exist.anki2")

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
            "--collection",
            fake_collection_path,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code != 0


def test_main_out_overwrite_refusal_prechecks_and_exits_cleanly(
    tmp_path, monkeypatch, collection_snapshot_copy, capsys
):
    source_dir = _write_source_dir(tmp_path, _small_rows_by_sheet())
    out_path = os.path.join(str(tmp_path), "existing.apkg")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("pre-existing content")
    with open(out_path, "rb") as fh:
        before = fh.read()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
            "--out",
            out_path,
            "--collection",
            collection_snapshot_copy,
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1
    with open(out_path, "rb") as fh:
        after = fh.read()
    assert after == before

    captured = capsys.readouterr()
    assert "Traceback" not in captured.err


def test_main_cli_wiring_source_dir_out_audio_dir_collection_force(
    tmp_path, monkeypatch, collection_snapshot_copy, capsys
):
    rows = _small_rows_by_sheet()
    source_dir = _write_source_dir(tmp_path, rows)
    out_path = os.path.join(str(tmp_path), "out.apkg")
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)
    collection_mtime_before = os.path.getmtime(collection_snapshot_copy)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
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
    assert os.path.exists(out_path)
    assert os.path.getsize(out_path) > 0
    assert_unmodified(collection_snapshot_copy, collection_mtime_before)

    captured = capsys.readouterr()
    assert "Attached 0 media file(s)" in captured.out
    assert "Wrote" in captured.out
    assert out_path in captured.out

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
            "--out",
            out_path,
            "--collection",
            collection_snapshot_copy,
            "--force",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert os.path.getsize(out_path) > 0


def test_main_default_fallback_passes_anki_media_dir_as_extra_dirs(
    tmp_path, monkeypatch, collection_snapshot_copy
):
    source_dir = _write_source_dir(tmp_path, _small_rows_by_sheet())
    out_path = os.path.join(str(tmp_path), "out.apkg")
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)

    captured_calls = []

    def _capturing_attach_media(build_col, audio_dir_arg, extra_dirs=()):
        captured_calls.append((build_col, audio_dir_arg, extra_dirs))
        return [], []

    monkeypatch.setattr(
        "anki_tools.mutable_words.attach_media", _capturing_attach_media
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
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
    assert len(captured_calls) == 1
    _build_col_arg, captured_audio_dir, captured_extra_dirs = captured_calls[0]
    assert captured_audio_dir == audio_dir
    assert captured_extra_dirs == (get_anki_media_dir(collection_snapshot_copy),)


def test_main_no_media_dir_fallback_flag_disables_extra_dirs(
    tmp_path, monkeypatch, collection_snapshot_copy
):
    source_dir = _write_source_dir(tmp_path, _small_rows_by_sheet())
    out_path = os.path.join(str(tmp_path), "out.apkg")
    audio_dir = os.path.join(str(tmp_path), "audio")
    os.makedirs(audio_dir)

    captured_calls = []

    def _capturing_attach_media(build_col, audio_dir_arg, extra_dirs=()):
        captured_calls.append((build_col, audio_dir_arg, extra_dirs))
        return [], []

    monkeypatch.setattr(
        "anki_tools.mutable_words.attach_media", _capturing_attach_media
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mutable-words",
            "--source-dir",
            source_dir,
            "--out",
            out_path,
            "--collection",
            collection_snapshot_copy,
            "--audio-dir",
            audio_dir,
            "--no-media-dir-fallback",
        ],
    )

    with pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 0
    assert len(captured_calls) == 1
    _build_col_arg, captured_audio_dir, captured_extra_dirs = captured_calls[0]
    assert captured_audio_dir == audio_dir
    assert captured_extra_dirs == ()
