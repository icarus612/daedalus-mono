"""Lane l1 e2e tail: verifies the plan's own acceptance figures for Phase 3
(subphases 3.1-3.3) end to end, across all three packets together. Not a
packet contract test -- written directly against the plan, not against any
packet's contract slice.
"""

import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from anki_tools import mutable_words_plan as plan
from anki_tools import vocabulary_source
from anki_tools.audio_naming import sanitize_word_slug

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
