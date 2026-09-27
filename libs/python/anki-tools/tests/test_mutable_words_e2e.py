"""Lane l1 e2e tail: verifies the plan's own acceptance figures for Phase 3
(subphases 3.1-3.3) end to end, across all three packets together. Not a
packet contract test -- written directly against the plan, not against any
packet's contract slice.

Extended by lane l6 (subphase 7.2) with the full deck-package chain and the
audio dry run, both over the real committed data -- the pre-spend gate for
Phase 8.
"""

import os
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import pytest
import requests
from anki.collection import Collection
from anki.import_export_pb2 import ImportAnkiPackageOptions, ImportAnkiPackageRequest

from anki_tools import (
    elevenlabs_tts,
    mutable_words,
    mutable_words_audio,
    vocabulary_source,
)
from anki_tools import mutable_words_plan as plan
from anki_tools.audio_naming import (
    get_anki_collection_path,
    get_anki_media_dir,
    sanitize_word_slug,
)
from anki_tools.immutable_words import assert_unmodified

_DATA_DIR = (
    Path(__file__).resolve().parents[1] / "anki_tools" / "data" / "russian-vocabulary"
)
_REAL_WORKBOOK = Path("~/Downloads/russian_vocabulary.xlsx").expanduser()

_KNOWN_OVERLAP_SLUGS = {
    "кафе",
    "кино",
    "кофе",
    "метро",
    "пальто",
    "просто",
    "согласно",
}

_PER_DECK_NOTES = {
    "Nouns": 541,
    "Verbs": 179,
    "Adjectives": 152,
    "Adverbs": 132,
}
_PER_DECK_CARDS = {
    "Nouns": 1082,
    "Verbs": 716,
    "Adjectives": 304,
    "Adverbs": 264,
}
_FILENAME_RE = re.compile(r"^[^/]+_(?:f1|m2)\.mp3$")


def _parse_all_rows():
    nouns = plan.parse_nouns(str(_DATA_DIR / "nouns.tsv"))
    verbs = plan.parse_verbs(str(_DATA_DIR / "verbs.tsv"))
    adjectives = plan.parse_adjectives(str(_DATA_DIR / "adjectives.tsv"))
    adverbs = plan.parse_adverbs(str(_DATA_DIR / "adverbs.tsv"))
    return nouns, verbs, adjectives, adverbs


def test_full_pipeline_regenerates_byte_identical_tsvs(tmp_path):
    if not _REAL_WORKBOOK.exists():
        pytest.skip("real workbook absent on this machine")
    for sheet in vocabulary_source.SHEETS:
        rows = vocabulary_source.read_sheet(str(_REAL_WORKBOOK), sheet)
        out_path = tmp_path / f"{sheet.lower()}.tsv"
        vocabulary_source.write_tsv(
            rows, vocabulary_source.EXPECTED_HEADERS[sheet], str(out_path)
        )
        committed = (_DATA_DIR / f"{sheet.lower()}.tsv").read_bytes()
        assert out_path.read_bytes() == committed


def test_full_pipeline_note_and_card_totals():
    nouns, verbs, adjectives, adverbs = _parse_all_rows()

    assert len(nouns) == 541
    assert len(verbs) == 179
    assert len(adjectives) == 152
    assert len(adverbs) == 132

    total_notes = len(nouns) + len(verbs) + len(adjectives) + len(adverbs)
    assert total_notes == 1004

    cards_by_sheet = {
        "Nouns": len(nouns) * 2,
        "Verbs": len(verbs) * 4,
        "Adjectives": len(adjectives) * 2,
        "Adverbs": len(adverbs) * 2,
    }
    assert cards_by_sheet == {
        "Nouns": 1082,
        "Verbs": 716,
        "Adjectives": 304,
        "Adverbs": 264,
    }
    assert sum(cards_by_sheet.values()) == 2366


def test_full_pipeline_base_word_and_slug_totals():
    nouns, verbs, adjectives, adverbs = _parse_all_rows()

    all_base_words: list[str] = []
    for row in (*nouns, *verbs, *adjectives, *adverbs):
        all_base_words.extend(row.base_words)

    assert len(all_base_words) == 1183

    slugs = [sanitize_word_slug(word) for word in all_base_words]
    if len(set(slugs)) != len(slugs):
        dupes = {s: c for s, c in Counter(slugs).items() if c > 1}
        offending = {
            s: [w for w in all_base_words if sanitize_word_slug(w) == s] for s in dupes
        }
        pytest.fail(f"slug collisions found: {offending}")
    assert len(set(slugs)) == 1183

    assert _KNOWN_OVERLAP_SLUGS <= set(slugs)


def test_no_audio_refs_in_any_real_built_template():
    card_counts = {"Nouns": 2, "Verbs": 4, "Adjectives": 2, "Adverbs": 2}
    for sheet, count in card_counts.items():
        for card_index in range(count):
            qfmt, afmt = plan.build_template(sheet, card_index)
            assert "{{AudioRefs}}" not in qfmt
            assert "{{AudioRefs}}" not in afmt


def test_guid_for_row_argument_order_matches_shipped_signature():
    import inspect

    from anki_tools.anki_identity import guid_for_row

    assert list(inspect.signature(guid_for_row).parameters) == ["russian", "pos"]

    nouns, *_ = _parse_all_rows()
    row = nouns[0]
    assert row.guid == guid_for_row(row.russian, row.SHEET)


def test_module_purity_no_anki_requests_openpyxl():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import anki_tools.mutable_words_plan; "
            "hits = [m for m in sys.modules "
            "if m in ('anki', 'requests', 'openpyxl') "
            "or m.startswith(('anki.', 'requests.', 'openpyxl.'))]; "
            "print(sorted(hits))",
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(Path(__file__).resolve().parents[1]),
    )
    assert result.stdout.strip() == "[]"


def _copy_real_collection(tmp_path):
    real_path = get_anki_collection_path()
    if not os.path.isfile(real_path):
        pytest.skip("no real Anki collection on this machine")
    copy_path = os.path.join(str(tmp_path), "source-snapshot.anki2")
    shutil.copy2(real_path, copy_path)
    return real_path, copy_path


def _run_build(argv, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["anki-mutable-words", *argv])
    try:
        mutable_words.main()
    except SystemExit as exc:
        return exc.code
    return 0  # pragma: no cover - main() always raises SystemExit


def test_real_source_builds_the_exact_deck_and_card_counts_unmodified(
    tmp_path, monkeypatch
):
    real_path, copy_path = _copy_real_collection(tmp_path)
    mtime_before = os.path.getmtime(real_path)

    out_path = os.path.join(str(tmp_path), "mutable-words.apkg")
    exit_code = _run_build(["--collection", copy_path, "--out", out_path], monkeypatch)
    assert exit_code == 0
    assert_unmodified(real_path, mtime_before)

    fresh_path = os.path.join(str(tmp_path), "fresh.anki2")
    fresh_col = Collection(fresh_path)
    try:
        fresh_col.import_anki_package(
            ImportAnkiPackageRequest(
                package_path=out_path, options=ImportAnkiPackageOptions()
            )
        )
        assert fresh_col.note_count() == 1004

        for sheet, expected_notes in _PER_DECK_NOTES.items():
            deck_name = plan.subdeck_name(sheet)
            note_ids = fresh_col.find_notes(f'deck:"{deck_name}"')
            card_ids = fresh_col.find_cards(f'deck:"{deck_name}"')
            assert len(note_ids) == expected_notes
            assert len(card_ids) == _PER_DECK_CARDS[sheet]

        for sheet, name in plan.NOTE_TYPE_NAMES.items():
            notetype = fresh_col.models.by_name(name)
            assert notetype is not None
            assert notetype["id"] == plan.build_note_type_id(sheet)
    finally:
        fresh_col.close()


def test_real_source_reimport_is_idempotent_no_duplicate_notetypes(
    tmp_path, monkeypatch
):
    _, copy_path = _copy_real_collection(tmp_path)

    out1 = os.path.join(str(tmp_path), "build1.apkg")
    assert _run_build(["--collection", copy_path, "--out", out1], monkeypatch) == 0

    fresh_path = os.path.join(str(tmp_path), "fresh.anki2")
    fresh_col = Collection(fresh_path)
    options = ImportAnkiPackageOptions()
    fresh_col.import_anki_package(
        ImportAnkiPackageRequest(package_path=out1, options=options)
    )
    guids_after_first = {
        fresh_col.get_note(nid).guid for nid in fresh_col.find_notes("")
    }
    fresh_col.close()

    time.sleep(1.1)
    out2 = os.path.join(str(tmp_path), "build2.apkg")
    assert _run_build(["--collection", copy_path, "--out", out2], monkeypatch) == 0

    fresh_col = Collection(fresh_path)
    try:
        fresh_col.import_anki_package(
            ImportAnkiPackageRequest(package_path=out2, options=options)
        )
        assert fresh_col.note_count() == 1004
        guids_after_second = {
            fresh_col.get_note(nid).guid for nid in fresh_col.find_notes("")
        }
        assert guids_after_second == guids_after_first

        notetype_names = [n.name for n in fresh_col.models.all_names_and_ids()]
        for name in plan.NOTE_TYPE_NAMES.values():
            assert notetype_names.count(name) == 1
        duplicates = [n for n in notetype_names if n.startswith("Russian - Mutable")]
        assert sorted(duplicates) == sorted(plan.NOTE_TYPE_NAMES.values())
    finally:
        fresh_col.close()


def test_real_source_predicted_audio_filenames_well_formed_and_number_2366():
    nouns, verbs, adjectives, adverbs = _parse_all_rows()

    filenames: set[str] = set()
    for row in (*nouns, *verbs, *adjectives, *adverbs):
        for base_word in row.base_words:
            filenames.update(plan.audio_names(base_word))

    assert len(filenames) == 2366
    malformed = [name for name in filenames if not _FILENAME_RE.match(name)]
    assert malformed == []


def test_audio_dry_run_over_real_media_dir_reports_exact_pending_count(
    monkeypatch, capsys, tmp_path
):
    real_media_dir = get_anki_media_dir()
    if not os.path.isdir(real_media_dir):
        pytest.skip("no real Anki media directory on this machine")

    def _boom(*_args, **_kwargs):
        raise AssertionError("dry run must never issue a real HTTP request")

    def _boom_api_key():
        raise AssertionError("dry run must never read the ElevenLabs API key")

    monkeypatch.setattr(requests, "post", _boom)
    monkeypatch.setattr(requests.Session, "post", _boom)
    monkeypatch.setattr(elevenlabs_tts, "get_api_key", _boom_api_key)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "anki-mutable-words-audio",
            "--dry-run",
            "--anki-media-dir",
            real_media_dir,
        ],
    )
    exit_code = mutable_words_audio.main()
    assert exit_code == 0

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    match = re.match(r"total (\d+) / present (\d+) / pending (\d+)$", lines[0])
    assert match is not None
    total, present, pending = (int(g) for g in match.groups())
    assert total == 2366
    assert present + pending == total
    assert (
        lines[1]
        == "voices: Alisa - Natural Russian Female, Nester Surovy - Gravely yet Refined"
    )

    owned_media_dir = tmp_path / "media"
    owned_media_dir.mkdir()
    owned_mtime_before = os.path.getmtime(owned_media_dir)
    owned_listing_before = sorted(os.listdir(owned_media_dir))

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "anki-mutable-words-audio",
            "--dry-run",
            "--anki-media-dir",
            str(owned_media_dir),
        ],
    )
    assert mutable_words_audio.main() == 0
    capsys.readouterr()

    # Backdated snapshot makes the external-writer race deterministic.
    concurrent_writer_dir = tmp_path / "concurrent-writer-stand-in"
    concurrent_writer_dir.mkdir()
    stand_in_mtime_before = time.time() - 5
    os.utime(concurrent_writer_dir, (stand_in_mtime_before, stand_in_mtime_before))
    (concurrent_writer_dir / "unrelated-write.tmp").write_bytes(b"")
    with pytest.raises(AssertionError):
        assert os.path.getmtime(concurrent_writer_dir) == stand_in_mtime_before

    assert os.path.getmtime(owned_media_dir) == owned_mtime_before
    assert sorted(os.listdir(owned_media_dir)) == owned_listing_before
