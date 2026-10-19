"""Contract tests for ``anki_tools.mutable_words_plan``, written from the
packet contract text alone. The implementation module is never read by
this file's author.
"""

import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest
from anki.collection import Collection
from anki.utils import to_json_bytes

from anki_tools import card_audio, examples_field, mutable_words_plan
from anki_tools.audio_naming import (
    build_filename,
    get_anki_collection_path,
    sanitize_word_slug,
)
from anki_tools.mutable_words import SOURCE_NOTETYPE_ID

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "anki_tools" / "data" / "russian-vocabulary"
NOUNS_TSV = DATA_DIR / "nouns.tsv"
VERBS_TSV = DATA_DIR / "verbs.tsv"
ADJECTIVES_TSV = DATA_DIR / "adjectives.tsv"
ADVERBS_TSV = DATA_DIR / "adverbs.tsv"
PRONOUNS_TSV = DATA_DIR / "pronouns.tsv"
NUMERALS_TSV = DATA_DIR / "numerals.tsv"

SHEET_CARD_COUNTS = {
    "Nouns": 2,
    "Verbs": 4,
    "Adjectives": 2,
    "Adverbs": 2,
    "Pronouns": 2,
    "Numerals": 2,
}


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


@pytest.fixture(scope="session")
def pronouns():
    return mutable_words_plan.parse_pronouns(str(PRONOUNS_TSV))


@pytest.fixture(scope="session")
def numerals():
    return mutable_words_plan.parse_numerals(str(NUMERALS_TSV))


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


def test_row_counts(nouns, verbs, adjectives, adverbs, pronouns, numerals):
    assert len(nouns) == 624
    assert len(verbs) == 209
    assert len(adjectives) == 172
    assert len(adverbs) == 132
    assert len(pronouns) == 29
    assert len(numerals) == 55


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


def test_card_count_derivation(nouns, verbs, adjectives, adverbs, pronouns, numerals):
    nouns_cards = len(nouns) * 2
    verbs_cards = len(verbs) * 4
    adjectives_cards = len(adjectives) * 2
    adverbs_cards = len(adverbs) * 2
    pronouns_cards = len(pronouns) * 2
    numerals_cards = len(numerals) * 2

    assert nouns_cards == 1248
    assert verbs_cards == 836
    assert adjectives_cards == 344
    assert adverbs_cards == 264
    assert pronouns_cards == 58
    assert numerals_cards == 110
    assert (
        nouns_cards
        + verbs_cards
        + adjectives_cards
        + adverbs_cards
        + pronouns_cards
        + numerals_cards
        == 2860
    )


def test_all_subdeck_names():
    names = mutable_words_plan.all_subdeck_names()
    assert names == [
        "Languages::Russian::3. Mutable Words::a. Nouns",
        "Languages::Russian::3. Mutable Words::b. Verbs",
        "Languages::Russian::3. Mutable Words::c. Adjectives",
        "Languages::Russian::2. Immutable Words::f. Derived Adverbs",
        "Languages::Russian::3. Mutable Words::d. Pronouns",
        "Languages::Russian::3. Mutable Words::e. Numerals",
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
    assert len(sides) == 28
    for _sheet, _card_index, _side_name, content in sides:
        assert "{{AudioRefs}}" not in content


def test_no_duplicate_ids_or_addtitle_per_side():
    id_pattern = re.compile(r'id="([^"]*)"')
    for sheet, card_index, side_name, content in _all_sides():
        ids = id_pattern.findall(content)
        assert len(ids) == len(set(ids)), (sheet, card_index, side_name, ids)
        assert content.count("function addTitle") <= 1


# Legitimate shared-audio slugs: same real word reused across rows/decks,
# not a collision. See each row's Additional Info for why.
_EXPECTED_DUPLICATE_SLUGS = {"побежать", "поехать", "значить", "иметь", "первый"}


def test_no_slug_collisions_across_all_base_words(
    nouns, verbs, adjectives, adverbs, pronouns, numerals
):
    all_words = (
        [w for row in nouns for w in row.base_words]
        + [w for row in verbs for w in row.base_words]
        + [w for row in adjectives for w in row.base_words]
        + [w for row in adverbs for w in row.base_words]
        + [w for row in pronouns for w in row.base_words]
        + [w for row in numerals for w in row.base_words]
    )
    assert len(all_words) == 1428

    slugs = [sanitize_word_slug(w) for w in all_words]
    dupes = {slug: c for slug, c in Counter(slugs).items() if c > 1}
    assert set(dupes) == _EXPECTED_DUPLICATE_SLUGS, dupes
    assert len(set(slugs)) == 1423


def test_named_media_overlap_slugs_present(nouns, verbs, adjectives, adverbs):
    all_words = (
        [w for row in nouns for w in row.base_words]
        + [w for row in verbs for w in row.base_words]
        + [w for row in adjectives for w in row.base_words]
        + [w for row in adverbs for w in row.base_words]
    )
    slugs = {sanitize_word_slug(w) for w in all_words}
    for expected in ("просто", "согласно"):
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
    assert len(dash_rows) == 131

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
        assert 'id="path"' in content, (sheet, card_index)
        assert 'id="deck"' in content, (sheet, card_index)
        assert "Russian - " in content, (sheet, card_index)
        assert '.split("::")' in content, (sheet, card_index)
        assert '.split(". ")[1]' in content, (sheet, card_index)
        assert '.join(" > ")' in content, (sheet, card_index)


def _copy_real_collection(tmp_path):
    real_path = get_anki_collection_path()
    if not os.path.isfile(real_path):
        pytest.skip("no real Anki collection on this machine")
    copy_path = os.path.join(str(tmp_path), "source-snapshot.anki2")
    shutil.copy2(real_path, copy_path)
    return real_path, copy_path


def _real_source_qfmt_and_css(tmp_path):
    real_path, copy_path = _copy_real_collection(tmp_path)
    mtime_before = os.path.getmtime(real_path)
    col = Collection(copy_path)
    try:
        notetype = col.models.get(SOURCE_NOTETYPE_ID)
        qfmt = notetype["tmpls"][0]["qfmt"]
        css = notetype["css"]
    finally:
        col.close()
    assert os.path.getmtime(real_path) == mtime_before
    return qfmt, css


def _extract_header_and_script(qfmt):
    header_match = re.search(
        r'<div id="path">.*?<div id="deck">.*?</div>', qfmt, re.DOTALL
    )
    script_match = re.search(r"<script>.*?</script>", qfmt, re.DOTALL)
    assert header_match, "no #path/#deck header found in real qfmt"
    assert script_match, "no <script> block found in real qfmt"
    return header_match.group(0), script_match.group(0)


def _normalize_fragment(text):
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)


def test_deck_header_matches_real_note_type_verbatim(tmp_path):
    qfmt, _css = _real_source_qfmt_and_css(tmp_path)
    real_header, real_script = _extract_header_and_script(qfmt)

    assert _normalize_fragment(real_header) == _normalize_fragment(
        mutable_words_plan._DECK_HEADER_HTML
    )
    assert _normalize_fragment(real_script) == _normalize_fragment(
        mutable_words_plan._DECK_HEADER_SCRIPT
    )


def test_deck_header_ids_all_have_css_rules(tmp_path):
    _qfmt, css = _real_source_qfmt_and_css(tmp_path)

    css_ids = re.findall(r"#([A-Za-z][\w-]*)", css)
    markup_ids = re.findall(r'id="([^"]+)"', mutable_words_plan._DECK_HEADER_HTML)

    assert set(markup_ids) - set(css_ids) == set()


# card_audio.py's own bookkeeping ids; the reference's own such ids
# carry no CSS rule either.
_AUDIO_BOOKKEEPING_SUFFIXES = ("-data", "-controls")


def _ids_and_classes(html):
    ids = set(re.findall(r'id="([^"]+)"', html))
    ids = {i for i in ids if not i.endswith(_AUDIO_BOOKKEEPING_SUFFIXES)}
    classes: set[str] = set()
    for value in re.findall(r'class="([^"]+)"', html):
        classes.update(value.split())
    # The replay button sets its class from JS, not static markup.
    for value in re.findall(r'\.className\s*=\s*"([^"]+)"', html):
        classes.update(value.split())
    for value in re.findall(r"\.classList\.add\(([^)]*)\)", html):
        classes.update(re.findall(r'"([^"]+)"', value))
    return ids | classes


def _css_selector_tokens(css):
    ids = re.findall(r"#([^\W\d][\w-]*)", css)
    classes = re.findall(r"\.([^\W\d][\w-]*)", css)
    return set(ids) | set(classes)


def test_every_template_id_and_class_has_a_css_rule(tmp_path):
    """The defect this module was rewritten to fix: CSS cloned from the
    reference note type is inert unless the templates actually emit the
    ids/classes it styles. Proves the set difference is empty for every
    side of every sheet/card, over the CSS the built note types will
    actually ship (`source_css + EXTRA_CSS`).
    """
    _qfmt, source_css = _real_source_qfmt_and_css(tmp_path)
    css_tokens = _css_selector_tokens(
        source_css
        + "\n\n"
        + card_audio.AUDIO_BUTTON_CSS
        + "\n\n"
        + examples_field.EXAMPLES_CSS
        + "\n\n"
        + mutable_words_plan.EXTRA_CSS
    )

    for sheet, card_index, side_name, content in _all_sides():
        missing = _ids_and_classes(content) - css_tokens
        assert not missing, (sheet, card_index, side_name, missing)


def _real_source_afmt(tmp_path):
    real_path, copy_path = _copy_real_collection(tmp_path)
    mtime_before = os.path.getmtime(real_path)
    col = Collection(copy_path)
    try:
        afmt = col.models.get(SOURCE_NOTETYPE_ID)["tmpls"][0]["afmt"]
    finally:
        col.close()
    assert os.path.getmtime(real_path) == mtime_before
    return afmt


def test_structure_mirrors_reference_wrapper_divs_and_addtitle(tmp_path):
    """Structural comparison against the reference: same `#front`/`#back`
    wrapper idiom, same `addTitle` mechanism, same ordering (wrapper divs
    close, THEN the `<script>` with the function and its calls).
    """
    real_afmt = _real_source_afmt(tmp_path)
    assert re.search(r'<div id="back">.*?</div>\s*<script>', real_afmt, re.S)
    assert 'classList.add("title")' in real_afmt
    assert 'classList.add("body")' in real_afmt

    assert 'classList.add("title")' in mutable_words_plan._ADD_TITLE_FUNCTION
    assert 'classList.add("body")' in mutable_words_plan._ADD_TITLE_FUNCTION

    for sheet, card_index, side_name, content in _all_sides():
        if side_name == "qfmt":
            assert content.startswith('<div id="front">'), (sheet, card_index)
        else:
            assert re.search(r'<div id="back">.*?</div>\s*<script>', content, re.S), (
                sheet,
                card_index,
            )
            assert content.count("function addTitle") == 1, (sheet, card_index)


def test_pairwise_distinct_qfmt_per_sheet():
    for sheet, count in SHEET_CARD_COUNTS.items():
        qfmts = [
            mutable_words_plan.build_template(sheet, card_index)[0]
            for card_index in range(count)
        ]
        for i in range(len(qfmts)):
            for j in range(i + 1, len(qfmts)):
                assert qfmts[i] != qfmts[j], (sheet, i, j)


def test_verbs_reverse_front_carries_inline_aspect_qualifier():
    for card_index, aspect in ((1, "imperfective"), (3, "perfective")):
        qfmt = mutable_words_plan.build_template("Verbs", card_index)[0]
        expected = (
            '<div id="translation">{{Translation}}'
            f' <span class="aspect aspect-{aspect}">({aspect})</span></div>'
        )
        assert expected in qfmt, (card_index, qfmt)


def test_reverse_verb_fronts_carry_distinct_aspect_colour_classes():
    classes = {}
    for card_index, aspect in ((1, "imperfective"), (3, "perfective")):
        qfmt = mutable_words_plan.build_template("Verbs", card_index)[0]
        assert f'class="aspect aspect-{aspect}"' in qfmt, (card_index, qfmt)
        classes[aspect] = mutable_words_plan.ASPECT_COLOURS[aspect]
    assert classes["imperfective"] != classes["perfective"]


def test_aspect_colours_override_the_grey_detail_rule():
    css = mutable_words_plan.EXTRA_CSS
    grey = css.index("#additional-info") if "#additional-info" in css else 0
    for aspect, colour in mutable_words_plan.ASPECT_COLOURS.items():
        rule = f"#{aspect} .title, #{aspect} .body, .aspect-{aspect} {{"
        assert rule in css, aspect
        assert css.index(rule) > grey
        assert colour in css
        # the generic grey rule must come first, or the colour never wins
        assert css.index(rule) > css.index(".aspect {")


def test_no_standalone_title_div_in_any_template():
    for sheet, card_index, side_name, content in _all_sides():
        assert '<div class="title">' not in content, (sheet, card_index, side_name)


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


def test_every_verb_card_carries_its_counterpart_aspect_on_the_answer_side():
    for card_index, counterpart in (
        (0, "Perfective"),
        (1, "Perfective"),
        (2, "Imperfective"),
        (3, "Imperfective"),
    ):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        assert f"{{{{{counterpart}}}}}" in afmt, card_index
        assert f"{{{{Audio {counterpart}}}}}" in afmt, card_index


def test_verb_counterpart_aspect_never_appears_on_the_question_side():
    for card_index, counterpart in (
        (0, "Perfective"),
        (1, "Perfective"),
        (2, "Imperfective"),
        (3, "Imperfective"),
    ):
        qfmt, _afmt = mutable_words_plan.build_template("Verbs", card_index)
        assert f"{{{{{counterpart}}}}}" not in qfmt, card_index


def test_verb_counterpart_aspect_is_not_also_a_grey_detail_row():
    for card_index in range(4):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        assert (
            afmt.count('<div id="perfective"') + afmt.count('<div id="imperfective"')
            == 1
        ), card_index


def test_verb_counterpart_line_gets_its_own_title_row():
    for card_index, slug, title in (
        (0, "perfective", "Perfective"),
        (2, "imperfective", "Imperfective"),
    ):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        assert f'addTitle("{slug}-word", "{title}");' in afmt, card_index


def test_non_verb_sheets_have_no_aspect_line():
    for sheet in ("Nouns", "Adjectives", "Pronouns", "Numerals"):
        for card_index in (0, 1):
            _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
            assert mutable_words_plan.ASPECT_AUDIO_SLOT_ID not in afmt, sheet


def test_aspect_line_is_centred_rather_than_a_left_aligned_detail_row():
    css = mutable_words_plan.EXTRA_CSS
    rule = css.split("#imperfective, #perfective {")[1].split("}")[0]
    assert "justify-content: center" in rule
    assert "text-align: center" in rule
    assert "#perfective" not in css.split("{")[0]


def test_aspect_colours_still_win_over_the_aspect_line_layout():
    css = mutable_words_plan.EXTRA_CSS
    layout = css.index("#imperfective .title, #perfective .title {")
    for aspect in mutable_words_plan.ASPECT_COLOURS:
        colour = css.index(f"#{aspect} .title, #{aspect} .body, .aspect-{aspect} {{")
        assert colour > layout, aspect


def test_verb_counterpart_play_button_precedes_the_word():
    for card_index, slug, counterpart in (
        (0, "perfective", "Perfective"),
        (1, "perfective", "Perfective"),
        (2, "imperfective", "Imperfective"),
        (3, "imperfective", "Imperfective"),
    ):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        row = afmt.split(f'<div id="{slug}" ')[1]
        slot = row.index(f'id="{mutable_words_plan.ASPECT_AUDIO_SLOT_ID}"')
        word = row.index(f"{{{{{counterpart}}}}}")
        assert slot < word, card_index


def test_verb_counterpart_row_is_tappable_on_ankimobile():
    fn = mutable_words_plan.ASPECT_PLAY_FN
    for card_index, slug in (
        (0, "perfective"),
        (1, "perfective"),
        (2, "imperfective"),
        (3, "imperfective"),
    ):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        open_tag = afmt.split(f'<div id="{slug}" ')[1].split(">")[0]
        assert f'class="{card_audio.TAPPABLE_CLASS}"' in open_tag, card_index
        assert f'onclick="{fn}(event)"' in open_tag, card_index
        assert f"window.{fn} = function (event)" in afmt, card_index
        row = afmt.split(f'<div id="{slug}" ')[1].split("</script>")[0]
        assert "addEventListener" not in row, card_index


def test_verb_counterpart_play_button_opens_the_line_before_the_label():
    for card_index, slug in (
        (0, "perfective"),
        (1, "perfective"),
        (2, "imperfective"),
        (3, "imperfective"),
    ):
        _qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        row = afmt.split(f'<div id="{slug}" ')[1]
        slot = row.index(f'id="{mutable_words_plan.ASPECT_AUDIO_SLOT_ID}"')
        label = row.index(f'<div id="{slug}-word">')
        assert slot < label, card_index


def test_every_verb_card_names_the_headwords_own_aspect():
    for card_index, aspect in (
        (0, "imperfective"),
        (1, "imperfective"),
        (2, "perfective"),
        (3, "perfective"),
    ):
        qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        side = qfmt if 'id="translation"' in qfmt else afmt
        assert f'<span class="aspect aspect-{aspect}">({aspect})</span>' in side, (
            card_index
        )


def test_the_headword_aspect_never_contradicts_the_counterpart_line():
    for card_index, own, other in (
        (0, "imperfective", "perfective"),
        (2, "perfective", "imperfective"),
    ):
        qfmt, afmt = mutable_words_plan.build_template("Verbs", card_index)
        whole = qfmt + afmt
        assert f'aspect-{own}">({own})</span>' in whole, card_index
        assert f'aspect-{other}">({other})</span>' not in whole, card_index
        assert f'<div id="{other}" ' in afmt, card_index


def test_non_verb_sheets_keep_a_bare_translation():
    for sheet in ("Nouns", "Adjectives", "Pronouns", "Numerals", "Adverbs"):
        for card_index in (0, 1):
            qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
            assert '<div id="translation">{{Translation}}</div>' in qfmt + afmt, sheet
            assert 'class="aspect' not in qfmt + afmt, sheet
