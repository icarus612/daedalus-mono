"""Contract tests for ``anki_tools.mutable_words_plan``, written from the
packet contract text alone. The implementation module is never read by
this file's author.
"""

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from anki.collection import Collection
from anki.utils import to_json_bytes

from anki_tools import mutable_words_plan
from anki_tools.audio_naming import build_filename, sanitize_word_slug

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
NOUNS_TSV = DATA_DIR / "nouns.tsv"
VERBS_TSV = DATA_DIR / "verbs.tsv"
ADJECTIVES_TSV = DATA_DIR / "adjectives.tsv"
ADVERBS_TSV = DATA_DIR / "adverbs.tsv"

SHEET_CARD_COUNTS = {"Nouns": 2, "Verbs": 4, "Adjectives": 2, "Adverbs": 2}


@pytest.fixture(scope="session")
def nouns():
    return mutable_words_plan.parse_nouns(str(NOUNS_TSV))


@pytest.fixture(scope="session")
def verbs():
    return mutable_words_plan.parse_verbs(str(VERBS_TSV))


@pytest.fixture(scope="session")
def adjectives():
    return mutable_words_plan.parse_adjectives(str(ADJECTIVES_TSV))


@pytest.fixture(scope="session")
def adverbs():
    return mutable_words_plan.parse_adverbs(str(ADVERBS_TSV))


def _all_sides():
    sides = []
    for sheet, count in SHEET_CARD_COUNTS.items():
        for card_index in range(count):
            qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
            sides.append((sheet, card_index, "qfmt", qfmt))
            sides.append((sheet, card_index, "afmt", afmt))
    return sides


def _joined_audio_names(word):
    return ",".join(
        build_filename(word, slot) for slot in mutable_words_plan.VOICE_SLOTS
    )


def test_row_counts(nouns, verbs, adjectives, adverbs):
    assert len(nouns) == 541
    assert len(verbs) == 179
    assert len(adjectives) == 152
    assert len(adverbs) == 132


def test_placeholder_disagreement_raises(tmp_path):
    lines = ADVERBS_TSV.read_text(encoding="utf-8").splitlines(keepends=True)
    header = lines[0]
    normal_rows = lines[1:4]

    disagreement_cols = lines[4].rstrip("\n").split("\t")
    disagreement_cols[5] = "none"
    disagreement_row = "\t".join(disagreement_cols) + "\n"

    doctored = tmp_path / "adverbs-doctored.tsv"
    doctored.write_text(
        header + "".join(normal_rows) + disagreement_row, encoding="utf-8"
    )

    with pytest.raises(Exception) as exc_info:
        mutable_words_plan.parse_adverbs(str(doctored))

    assert disagreement_cols[0] in str(exc_info.value)


def test_split_rows(adverbs):
    by_adverb = {row.adverb: row for row in adverbs}
    for word in ("направо", "справа", "налево", "слева"):
        assert word in by_adverb

    assert by_adverb["направо"].translation == "to the right"
    assert by_adverb["справа"].translation == "on the right"
    assert by_adverb["налево"].translation == "to the left"
    assert by_adverb["слева"].translation == "on the left"

    for left, right in (("направо", "справа"), ("налево", "слева")):
        row_left, row_right = by_adverb[left], by_adverb[right]
        assert row_left.from_adjective == row_right.from_adjective
        assert row_left.formation == row_right.formation
        assert row_left.comparative == row_right.comparative
        assert row_left.additional_info == row_right.additional_info


def test_no_slash_in_base_words(nouns, verbs, adjectives, adverbs):
    for rows in (nouns, verbs, adjectives, adverbs):
        for row in rows:
            for word in row.base_words:
                assert "/" not in word


def test_card_count_derivation(nouns, verbs, adjectives, adverbs):
    nouns_cards = len(nouns) * 2
    verbs_cards = len(verbs) * 4
    adjectives_cards = len(adjectives) * 2
    adverbs_cards = len(adverbs) * 2

    assert nouns_cards == 1082
    assert verbs_cards == 716
    assert adjectives_cards == 304
    assert adverbs_cards == 264
    assert nouns_cards + verbs_cards + adjectives_cards + adverbs_cards == 2366


def test_all_subdeck_names():
    names = mutable_words_plan.all_subdeck_names()
    assert names == [
        "Languages::Russian::3. Mutable Words::a. Nouns",
        "Languages::Russian::3. Mutable Words::b. Verbs",
        "Languages::Russian::3. Mutable Words::c. Adjectives",
        "Languages::Russian::3. Mutable Words::d. Adverbs",
    ]
    for name in names:
        assert ". " in name


def test_field_name_legality():
    for names in mutable_words_plan.FIELD_NAMES.values():
        for name in names:
            assert not name.startswith(("#", "^", "/"))
            assert ":" not in name
            assert '"' not in name
            assert "{" not in name
            assert "}" not in name
        assert names[-1] == "AudioRefs"


def test_no_audio_refs_placeholder_in_any_template():
    sides = _all_sides()
    assert len(sides) == 20
    for _sheet, _card_index, _side_name, content in sides:
        assert "{{AudioRefs}}" not in content


def test_no_duplicate_ids_or_addtitle_per_side():
    id_pattern = re.compile(r'id="([^"]*)"')
    for sheet, card_index, side_name, content in _all_sides():
        ids = id_pattern.findall(content)
        assert len(ids) == len(set(ids)), (sheet, card_index, side_name, ids)
        assert content.count("function addTitle") <= 1


def test_no_slug_collisions_across_all_base_words(nouns, verbs, adjectives, adverbs):
    all_words = (
        [w for row in nouns for w in row.base_words]
        + [w for row in verbs for w in row.base_words]
        + [w for row in adjectives for w in row.base_words]
        + [w for row in adverbs for w in row.base_words]
    )
    assert len(all_words) == 1183

    slugs = [sanitize_word_slug(w) for w in all_words]
    if len(set(slugs)) != len(slugs):
        dupes = {slug: c for slug, c in Counter(slugs).items() if c > 1}
        pytest.fail(f"duplicate slugs across base words: {dupes}")
    assert len(set(slugs)) == len(slugs) == 1183


def test_named_media_overlap_slugs_present(nouns, verbs, adjectives, adverbs):
    all_words = (
        [w for row in nouns for w in row.base_words]
        + [w for row in verbs for w in row.base_words]
        + [w for row in adjectives for w in row.base_words]
        + [w for row in adverbs for w in row.base_words]
    )
    slugs = {sanitize_word_slug(w) for w in all_words}
    for expected in ("кафе", "кино", "кофе", "метро", "пальто", "просто", "согласно"):
        assert expected in slugs


def test_guid_stable_across_subprocesses():
    code = (
        "from anki_tools.mutable_words_plan import parse_nouns\n"
        f"rows = parse_nouns(r'{NOUNS_TSV}')\n"
        "print(rows[0].guid)\n"
    )
    outputs = []
    for _ in range(2):
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(PACKAGE_ROOT),
        )
        outputs.append(proc.stdout.strip())

    assert outputs[0] != ""
    assert outputs[0] == outputs[1]


def test_predicted_audio_matches_build_filename(nouns, verbs, adjectives, adverbs):
    noun_idx = mutable_words_plan.FIELD_NAMES["Nouns"].index("Audio")
    row = nouns[0]
    assert row.fields()[noun_idx] == _joined_audio_names(row.russian)

    adj_idx = mutable_words_plan.FIELD_NAMES["Adjectives"].index("Audio")
    row = adjectives[0]
    assert row.fields()[adj_idx] == _joined_audio_names(row.russian_m)

    adv_idx = mutable_words_plan.FIELD_NAMES["Adverbs"].index("Audio")
    row = adverbs[0]
    assert row.fields()[adv_idx] == _joined_audio_names(row.adverb)

    imp_idx = mutable_words_plan.FIELD_NAMES["Verbs"].index("Audio Imperfective")
    perf_idx = mutable_words_plan.FIELD_NAMES["Verbs"].index("Audio Perfective")
    row = verbs[0]
    assert row.fields()[imp_idx] == _joined_audio_names(row.imperfective)
    assert row.fields()[perf_idx] == _joined_audio_names(row.perfective)


def test_dash_only_plural_survives_into_fields(nouns):
    dash_rows = [row for row in nouns if row.plural == "—"]
    assert len(dash_rows) == 107

    plural_idx = mutable_words_plan.FIELD_NAMES["Nouns"].index("Plural")
    assert dash_rows[0].fields()[plural_idx] == "—"


def test_purity_no_heavy_imports():
    code = (
        "import sys\n"
        "import anki_tools.mutable_words_plan\n"
        "banned = ('anki', 'requests', 'openpyxl')\n"
        "hits = sorted(\n"
        "    m for m in sys.modules\n"
        "    if m in banned or m.startswith(tuple(b + '.' for b in banned))\n"
        ")\n"
        "print(hits)\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
        cwd=str(PACKAGE_ROOT),
    )
    assert proc.stdout.strip() == "[]"


def test_deck_header_script_markers_in_every_qfmt():
    for sheet, card_index, side_name, content in _all_sides():
        if side_name != "qfmt":
            continue
        assert 'id="deck-header"' in content, (sheet, card_index)
        assert 'deckName.split("::")' in content, (sheet, card_index)
        assert '.split(". ")[1]' in content, (sheet, card_index)


def test_pairwise_distinct_qfmt_per_sheet():
    for sheet, count in SHEET_CARD_COUNTS.items():
        qfmts = [
            mutable_words_plan.build_template(sheet, card_index)[0]
            for card_index in range(count)
        ]
        for i in range(len(qfmts)):
            for j in range(i + 1, len(qfmts)):
                assert qfmts[i] != qfmts[j], (sheet, i, j)


def _register_note_type(col, sheet):
    note_type = col.models.new(mutable_words_plan.NOTE_TYPE_NAMES[sheet])
    for name in mutable_words_plan.FIELD_NAMES[sheet]:
        note_type["flds"].append(col.models.new_field(name))
    for card_index in range(SHEET_CARD_COUNTS[sheet]):
        qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
        template = col.models.new_template(f"Card {card_index + 1}")
        template["qfmt"] = qfmt
        template["afmt"] = afmt
        note_type["tmpls"].append(template)
    return col._backend.add_or_update_notetype(
        json=to_json_bytes(note_type),
        preserve_usn_and_mtime=True,
        skip_checks=False,
    )


@pytest.mark.parametrize("sheet", sorted(SHEET_CARD_COUNTS))
def test_note_type_registers_without_card_type_error(tmp_path, sheet):
    col = Collection(str(tmp_path / f"{sheet.lower()}.anki2"))
    try:
        _register_note_type(col, sheet)
    finally:
        col.close()
