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

from anki_tools import (
    card_audio,
    case_field,
    case_pill,
    distinction,
    examples_field,
    mutable_words_plan,
    prompt_hint,
)
from anki_tools.audio_naming import (
    audio_field_value,
    build_filename,
    get_anki_collection_path,
    sanitize_word_slug,
    strip_qualifier,
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

CASE_SHEETS = ("Verbs", "Adverbs")

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


def _audio_field_for(word):
    return audio_field_value(
        build_filename(word, slot) for slot in mutable_words_plan.VOICE_SLOTS
    )


def test_row_counts(nouns, verbs, adjectives, adverbs, pronouns, numerals):
    assert len(nouns) == 631
    assert len(verbs) == 223
    assert len(adjectives) == 172
    assert len(adverbs) == 134
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
    verbs_cards = sum(4 if v.perfective.strip() else 2 for v in verbs)
    adjectives_cards = len(adjectives) * 2
    adverbs_cards = len(adverbs) * 2
    pronouns_cards = len(pronouns) * 2
    numerals_cards = len(numerals) * 2

    assert nouns_cards == 1262
    assert verbs_cards == 856
    assert adjectives_cards == 344
    assert adverbs_cards == 268
    assert pronouns_cards == 58
    assert numerals_cards == 110
    assert (
        nouns_cards
        + verbs_cards
        + adjectives_cards
        + adverbs_cards
        + pronouns_cards
        + numerals_cards
        == 2898
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
    tail = ("Russian Distinction", "English Distinction")
    for sheet, names in mutable_words_plan.FIELD_NAMES.items():
        if sheet in CASE_SHEETS:
            assert tuple(names[-3:]) == (*tail, "Case"), sheet
            assert names[-4].startswith("Audio"), sheet
        else:
            assert tuple(names[-2:]) == tail, sheet
            assert names[-3].startswith("Audio"), sheet
            assert "Case" not in names, sheet


def test_no_av_tag_in_any_template():
    sides = _all_sides()
    assert len(sides) == 28
    for _sheet, _card_index, _side_name, content in sides:
        assert "[sound:" not in content
        assert "[anki:tts" not in content


def test_no_duplicate_ids_or_addtitle_per_side():
    id_pattern = re.compile(r'id="([^"]*)"')
    for sheet, card_index, side_name, content in _all_sides():
        ids = id_pattern.findall(content)
        assert len(ids) == len(set(ids)), (sheet, card_index, side_name, ids)
        assert content.count("function addTitle") <= 1


# Legitimate shared-audio slugs: same real word reused across rows/decks,
# not a collision. See each row's Additional Info for why.
_EXPECTED_DUPLICATE_SLUGS = {"первый"}


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
    assert len(all_words) == 1449

    slugs = [sanitize_word_slug(w) for w in all_words]
    dupes = {slug: c for slug, c in Counter(slugs).items() if c > 1}
    assert set(dupes) == _EXPECTED_DUPLICATE_SLUGS, dupes
    assert len(set(slugs)) == 1448


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
    assert row.fields()[noun_idx] == _audio_field_for(row.russian)

    adj_idx = mutable_words_plan.FIELD_NAMES["Adjectives"].index("Audio")
    row = adjectives[0]
    assert row.fields()[adj_idx] == _audio_field_for(row.russian_m)

    adv_idx = mutable_words_plan.FIELD_NAMES["Adverbs"].index("Audio")
    row = adverbs[0]
    assert row.fields()[adv_idx] == _audio_field_for(row.adverb)

    imp_idx = mutable_words_plan.FIELD_NAMES["Verbs"].index("Audio Imperfective")
    perf_idx = mutable_words_plan.FIELD_NAMES["Verbs"].index("Audio Perfective")
    row = verbs[0]
    assert row.fields()[imp_idx] == _audio_field_for(row.imperfective)
    assert row.fields()[perf_idx] == _audio_field_for(row.perfective)


def test_dash_only_plural_survives_into_fields(nouns):
    dash_rows = [row for row in nouns if row.plural == "—"]
    assert len(dash_rows) == 134

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
        + prompt_hint.PROMPT_HINT_CSS
        + "\n\n"
        + case_pill.CASE_PILL_CSS
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
            if sheet == "Verbs" and card_index >= 2:
                assert content.startswith('{{#Perfective}}<div id="front">')
                assert content.endswith("{{/Perfective}}")
            else:
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


_HEADWORD_SIDES = [
    (sheet, card_index)
    for sheet in mutable_words_plan.FIELD_NAMES
    for card_index in range(SHEET_CARD_COUNTS[sheet])
]

RUSSIAN_CUE = prompt_hint.hint_div(
    distinction.RUSSIAN_FIELD, prompt_hint.RUSSIAN_HINT_ID
)


@pytest.mark.parametrize("sheet,card_index", _HEADWORD_SIDES)
def test_a_question_showing_the_headword_cues_it(sheet, card_index):
    qfmt, _afmt = mutable_words_plan.build_template(sheet, card_index)
    assert ('id="russian"' in qfmt) == (RUSSIAN_CUE in qfmt), (sheet, card_index)
    if RUSSIAN_CUE not in qfmt:
        return
    assert re.search(
        r'<div id="russian">\{\{[^{}]+\}\}</div>\n' + re.escape(RUSSIAN_CUE), qfmt
    ), (sheet, card_index)
    field = distinction.RUSSIAN_FIELD
    assert f"{{{{#{field}}}}}" in qfmt
    assert f"{{{{/{field}}}}}" in qfmt


@pytest.mark.parametrize("sheet", list(mutable_words_plan.FIELD_NAMES))
def test_every_sheet_cues_the_headword_on_at_least_one_question(sheet):
    cued = [
        card_index
        for card_index in range(SHEET_CARD_COUNTS[sheet])
        if RUSSIAN_CUE in mutable_words_plan.build_template(sheet, card_index)[0]
    ]
    assert cued == [
        card_index
        for card_index in range(SHEET_CARD_COUNTS[sheet])
        if 'id="russian"' in mutable_words_plan.build_template(sheet, card_index)[0]
    ]
    assert cued


@pytest.mark.parametrize("sheet,card_index", _HEADWORD_SIDES)
def test_the_answer_has_no_labelled_russian_distinction_row(sheet, card_index):
    _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    field = distinction.RUSSIAN_FIELD
    assert "detail-russian-distinction" not in afmt, (sheet, card_index)
    assert f'"{field}"' not in afmt, (sheet, card_index)
    assert re.search(rf"\{{\{{{re.escape(field)}\}}\}}", _details_block(afmt)) is None


@pytest.mark.parametrize("sheet,card_index", _HEADWORD_SIDES)
def test_no_duplicate_ids_once_frontside_expands(sheet, card_index):
    qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    assert afmt.startswith("{{FrontSide}}")
    rendered = qfmt + "\n" + afmt[len("{{FrontSide}}") :]
    ids = re.findall(r'id="([^"]*)"', rendered)
    assert len(ids) == len(set(ids)), (sheet, card_index, ids)


# Pinned as literals: `guid_for_row` hashes the QUALIFIED text, so a change
# here means every one of these notes re-imports as a duplicate instead of
# updating, losing its scheduling.
_QUALIFIED_HEADWORD_GUIDS = {
    ("Nouns", "правда (noun)"): "OMBx{Do|O@",
    ("Adjectives", "первый (adjective)"): "fX3LIC8l!>",
    ("Adverbs", "просто (adverb)"): "v*^Y^8o93j",
    ("Adverbs", "согласно (adverb)"): "tL.M_0|Uet",
    ("Numerals", "первый (numeral)"): "B.OZ`5x]dH",
}


def test_qualified_headwords_keep_their_guids_and_drop_the_inline_qualifier(
    nouns, verbs, adjectives, adverbs, pronouns, numerals
):
    by_sheet = {
        "Nouns": nouns,
        "Verbs": verbs,
        "Adjectives": adjectives,
        "Adverbs": adverbs,
        "Pronouns": pronouns,
        "Numerals": numerals,
    }
    found = {}
    for sheet, rows in by_sheet.items():
        field_names = mutable_words_plan.FIELD_NAMES[sheet]
        for row in rows:
            fields = dict(zip(field_names, row.fields()))
            for stored in row.base_words:
                if strip_qualifier(stored) == stored:
                    continue
                found[(sheet, stored)] = row.guid
                assert fields[field_names[0]] == strip_qualifier(stored)
                assert "(" not in fields[field_names[0]]
                assert fields[distinction.RUSSIAN_FIELD] == distinction.qualifier_of(
                    stored
                )
    assert found == _QUALIFIED_HEADWORD_GUIDS


def test_audio_filenames_ignore_the_qualifier(adjectives, numerals):
    for rows, sheet, attr in (
        (adjectives, "Adjectives", "russian_m"),
        (numerals, "Numerals", "russian"),
    ):
        audio_idx = mutable_words_plan.FIELD_NAMES[sheet].index("Audio")
        row = next(r for r in rows if getattr(r, attr).startswith("первый ("))
        assert row.fields()[audio_idx] == _audio_field_for(getattr(row, attr))
        assert "(" not in row.fields()[audio_idx]
        assert "первый_f1.mp3" in row.fields()[audio_idx]


_RENDERED_CUE = re.compile(
    rf'<div id="{prompt_hint.RUSSIAN_HINT_ID}">(.*?)</div>', re.S
)
_WRAPPED_CUE = re.compile(
    rf"\{{\{{#({re.escape(distinction.RUSSIAN_FIELD)})\}}\}}"
    r"\(\{\{\1\}\}\)"
    r"\{\{/\1\}\}"
)


def _rendered_cues(col):
    cues = {}
    for note_id in col.find_notes(""):
        note = col.get_note(note_id)
        found = cues.setdefault(note["Russian"], set())
        for card in note.cards():
            output = card.render_output()
            for text in (output.question_text, output.answer_text):
                found.update(_RENDERED_CUE.findall(text))
    return cues


def test_an_empty_cue_renders_nothing_and_the_check_fails_without_the_wrapper(tmp_path):
    """Positive control for `{{#Russian Distinction}}`: an unpopulated cue
    renders no stray parentheses, and the same assertion DOES fail once the
    wrapper is stripped, so it cannot pass vacuously.
    """
    col = Collection(str(tmp_path / "cue.anki2"))
    try:
        _register_note_type(col, "Nouns")
        note_type = col.models.by_name(mutable_words_plan.NOTE_TYPE_NAMES["Nouns"])
        for russian, cue in (("правда", "noun"), ("дом", "")):
            note = col.new_note(note_type)
            note["Russian"] = russian
            note["Translation"] = "truth"
            note[distinction.RUSSIAN_FIELD] = cue
            col.add_note(note, col.decks.id("Cue"))

        cues = _rendered_cues(col)
        assert cues["правда"] == {"(noun)"}
        assert "()" not in cues["дом"]
        assert cues["дом"] == {""}

        stripped = col.models.get(note_type["id"])
        substitutions = 0
        for template in stripped["tmpls"]:
            for side in ("qfmt", "afmt"):
                template[side], count = _WRAPPED_CUE.subn(r"({{\1}})", template[side])
                substitutions += count
        assert substitutions == 2
        col.models.update_dict(stripped)

        assert "()" in _rendered_cues(col)["дом"]
    finally:
        col.close()


HEADWORD_FRONT = {
    sheet: (0, 2) if sheet == "Verbs" else (0,) for sheet in SHEET_CARD_COUNTS
}
GLOSS_FRONT = {
    sheet: (1, 3) if sheet == "Verbs" else (1,) for sheet in SHEET_CARD_COUNTS
}
_ENGLISH_CUE = prompt_hint.hint_div(distinction.ENGLISH_FIELD)
_PILLS = case_pill.pill_block()
_CARDS = [
    (sheet, card_index)
    for sheet, count in SHEET_CARD_COUNTS.items()
    for card_index in range(count)
]
_SECTION = re.compile(r"\{\{([#^])([^{}]+)\}\}((?:(?!\{\{[#^]).)*?)\{\{/\2\}\}", re.S)
_TOKEN = re.compile(r"\{\{(?:text:)?([^{}#^/]+)\}\}")


def _render(template, fields, front_side=""):
    def section(match):
        present = bool(fields.get(match.group(2), "").strip())
        return match.group(3) if present == (match.group(1) == "#") else ""

    template = re.sub(r"<!--.*?-->", "", template, flags=re.DOTALL)
    previous = None
    while previous != template:
        previous = template
        template = _SECTION.sub(section, template)
    return _TOKEN.sub(
        lambda m: (
            front_side if m.group(1) == "FrontSide" else fields.get(m.group(1), "")
        ),
        template,
    )


def _full_fields(sheet, **overrides):
    fields = {
        name: "v-" + name.replace(" ", "-")
        for name in mutable_words_plan.FIELD_NAMES[sheet]
    }
    fields["Case"] = "Accusative"
    fields.update(overrides)
    return fields


def _question_and_answer(sheet, card_index, fields):
    qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    question = _render(qfmt, fields)
    return question, _render(afmt, fields, front_side=question)


def _details_block(html):
    start = html.index('<div id="details">')
    depth = 0
    for match in re.finditer(r"<div\b|</div>", html[start:]):
        depth += 1 if match.group(0) == "<div" else -1
        if depth == 0:
            return html[start : start + match.end()]
    raise AssertionError("unbalanced #details")


def _ids(html):
    return re.findall(r'id="([^"]*)"', html)


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_details_is_one_container_after_the_aspect_line_before_standalone_rows(
    sheet, card_index
):
    _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    assert afmt.count('<div id="details">') == 1
    block = _details_block(afmt)
    start = afmt.index(block)
    end = start + len(block)
    assert "{{Additional Info}}" not in block
    assert "{{Examples}}" not in block
    assert afmt.index("{{Additional Info}}") > end
    assert afmt.find("{{Examples}}", end) != -1 or "{{Examples}}" not in afmt
    if sheet == "Verbs":
        slug = "perfective" if card_index in (0, 1) else "imperfective"
        assert afmt.index(f'<div id="{slug}" ') < start


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_details_rows_are_conditional_static_labelled_and_exclude_cues(
    sheet, card_index
):
    _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    block = _details_block(afmt)
    for excluded in (distinction.RUSSIAN_FIELD, distinction.ENGLISH_FIELD, "Case"):
        assert f"{{{{{excluded}}}}}" not in block, (sheet, excluded)
    assert "addTitle" not in block
    fields_in_block = re.findall(r"\{\{#([^{}]+)\}\}", block)
    assert fields_in_block
    for field in fields_in_block:
        assert f"{{{{/{field}}}}}" in block
        assert f"{{{{{field}}}}}" in block.split(f"{{{{#{field}}}}}")[1]
        opener = f"{{{{#{field}}}}}"
        assert block[block.index(opener) + len(opener) :].lstrip().startswith("<")


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_add_title_is_only_called_for_rows_outside_the_details_block(sheet, card_index):
    _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    detail_ids = set(_ids(_details_block(afmt)))
    called = re.findall(r'addTitle\("([^"]+)"', afmt)
    assert called
    assert not detail_ids & set(called)
    assert afmt.count("function addTitle") == 1


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_empty_detail_fields_leave_no_element_behind(sheet, card_index):
    _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    full = _details_block(_render(afmt, _full_fields(sheet)))
    detail_fields = re.findall(r"\{\{#([^{}]+)\}\}", _details_block(afmt))
    for field in detail_fields:
        reduced = _details_block(_render(afmt, _full_fields(sheet, **{field: ""})))
        assert len(_ids(reduced)) < len(_ids(full)), (sheet, field)
        assert f"v-{field.replace(' ', '-')}" not in reduced
    blank = {name: "" for name in detail_fields}
    emptied = _details_block(_render(afmt, _full_fields(sheet, **blank)))
    assert _ids(emptied) == ["details"]


def test_a_noun_with_empty_genitives_renders_no_genitive_rows():
    sheet = "Nouns"
    for card_index in HEADWORD_FRONT[sheet] + GLOSS_FRONT[sheet]:
        _qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
        full = _details_block(_render(afmt, _full_fields(sheet)))
        sparse = _details_block(
            _render(afmt, _full_fields(sheet, **{"Genitive Sg": "", "Genitive Pl": ""}))
        )
        assert len(_ids(full)) - len(_ids(sparse)) == 2
        assert "v-Genitive-Sg" in full and "v-Genitive-Sg" not in sparse
        assert "v-Genitive-Pl" in full and "v-Genitive-Pl" not in sparse
        assert "v-Plural" in sparse


def test_details_css_is_a_centred_two_column_grid():
    css = re.sub(r"\s+", " ", mutable_words_plan.EXTRA_CSS)
    rule = re.search(r"#details \{([^}]*)\}", css)
    assert rule, "no #details rule"
    body = rule.group(1)
    for declaration in (
        "display: grid",
        "grid-template-columns: max-content max-content",
        "width: max-content",
        "margin: 0 auto",
    ):
        assert declaration in body, declaration
    assert "display: contents" in css
    assert "text-align: right" in css
    assert "text-align: left" in css


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_english_cue_follows_the_translation_on_headword_front_back(sheet, card_index):
    if card_index not in HEADWORD_FRONT[sheet]:
        pytest.skip("gloss-front card")
    qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    assert _ENGLISH_CUE not in qfmt
    assert afmt.startswith("{{FrontSide}}")
    assert re.search(
        r'<div id="translation">.*?</div>\s*' + re.escape(_ENGLISH_CUE), afmt, re.S
    )


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_gloss_front_has_the_english_cue_on_the_question_and_russian_cue_on_the_back(
    sheet, card_index
):
    if card_index not in GLOSS_FRONT[sheet]:
        pytest.skip("headword-front card")
    qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    assert re.search(
        r'<div id="translation">.*?</div>\s*' + re.escape(_ENGLISH_CUE), qfmt, re.S
    )
    assert _ENGLISH_CUE not in afmt
    assert RUSSIAN_CUE not in qfmt
    assert re.search(r'<div id="russian">[^<]*</div>\s*' + re.escape(RUSSIAN_CUE), afmt)


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_pill_placement_in_the_raw_templates(sheet, card_index):
    qfmt, afmt = mutable_words_plan.build_template(sheet, card_index)
    if sheet not in CASE_SHEETS:
        assert 'class="case-pills"' not in qfmt + afmt
        return
    if card_index in HEADWORD_FRONT[sheet]:
        assert 'class="case-pills"' not in qfmt
        assert afmt.count(_PILLS) == 1
        assert re.search(re.escape(_ENGLISH_CUE) + r"\s*" + re.escape(_PILLS), afmt)
        if sheet == "Verbs":
            slug = "perfective" if card_index == 0 else "imperfective"
            assert afmt.index(_PILLS) < afmt.index(f'<div id="{slug}" ')
        assert afmt.index(_PILLS) < afmt.index('<div id="details">')
    else:
        assert qfmt.count(_PILLS) == 1
        assert re.search(re.escape(_ENGLISH_CUE) + r"\s*" + re.escape(_PILLS), qfmt)
        assert 'class="case-pills"' not in afmt


def test_pill_positive_and_negative_controls():
    question, _answer = _question_and_answer("Verbs", 1, _full_fields("Verbs"))
    assert 'class="case-pills"' in question
    question, _answer = _question_and_answer(
        "Adverbs", 1, _full_fields("Adverbs", Case="")
    )
    assert 'class="case-pills"' not in question
    for card_index in (0, 1):
        question, answer = _question_and_answer(
            "Nouns", card_index, _full_fields("Nouns")
        )
        assert "case-pills" not in question + answer


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_cues_and_pills_render_exactly_once_on_the_answer_side(sheet, card_index):
    question, answer = _question_and_answer(sheet, card_index, _full_fields(sheet))
    assert answer.count('id="prompt-hint"') == 1, (sheet, card_index)
    assert answer.count('id="russian-distinction"') == 1, (sheet, card_index)
    expected_pills = 1 if sheet in CASE_SHEETS else 0
    assert answer.count('class="case-pills"') == expected_pills, (sheet, card_index)
    ids = _ids(answer)
    assert len(ids) == len(set(ids)), (sheet, card_index, ids)
    if card_index in HEADWORD_FRONT[sheet]:
        assert 'class="case-pills"' not in question
        assert 'id="prompt-hint"' not in question
        assert question.count('id="russian-distinction"') == 1
    else:
        assert question.count('id="prompt-hint"') == 1
        assert 'id="russian-distinction"' not in question
        assert question.count('class="case-pills"') == expected_pills


@pytest.mark.parametrize("sheet,card_index", _CARDS)
def test_ids_stay_unique_with_every_field_empty_or_full(sheet, card_index):
    for fields in (
        _full_fields(sheet),
        {name: "" for name in mutable_words_plan.FIELD_NAMES[sheet]},
    ):
        _question, answer = _question_and_answer(sheet, card_index, fields)
        ids = _ids(answer)
        assert len(ids) == len(set(ids)), (sheet, card_index)


def _tsv_lines(path):
    return path.read_text(encoding="utf-8").split("\n")


@pytest.mark.parametrize("path", [VERBS_TSV, ADVERBS_TSV])
def test_case_column_is_the_final_column_of_every_row(path):
    lines = _tsv_lines(path)
    assert lines[-1] == ""
    header, *rows = lines[:-1]
    assert header.endswith("\tCase")
    width = len(header.split("\t"))
    assert rows
    for row in rows:
        cells = row.split("\t")
        assert len(cells) == width, row[:40]


@pytest.mark.parametrize("path", [VERBS_TSV, ADVERBS_TSV])
def test_removing_the_case_column_reproduces_the_original(path):
    show = subprocess.run(
        ["git", "show", f"HEAD:./anki_tools/data/russian-vocabulary/{path.name}"],
        capture_output=True,
        text=True,
        cwd=str(PACKAGE_ROOT),
    )
    if show.returncode != 0:
        pytest.skip("no git HEAD copy")
    original = show.stdout
    if original.split("\n", 1)[0].endswith("\tCase"):
        pytest.skip("HEAD already carries the Case column")
    stripped = "\n".join(
        line.rsplit("\t", 1)[0] if line else line for line in _tsv_lines(path)
    )
    assert stripped == original


@pytest.mark.parametrize(
    "path", [NOUNS_TSV, ADJECTIVES_TSV, PRONOUNS_TSV, NUMERALS_TSV]
)
def test_other_sheets_gain_no_case_column(path):
    header = _tsv_lines(path)[0]
    assert not header.endswith("\tCase")


def _tsv_with_case(path, tmp_path, value):
    lines = _tsv_lines(path)
    out = [lines[0]] + [line.rsplit("\t", 1)[0] + "\t" + value for line in lines[1:-1]]
    doctored = tmp_path / path.name
    doctored.write_text("\n".join(out) + "\n", encoding="utf-8")
    return str(doctored)


def test_parse_verbs_reads_the_case_column(verbs, tmp_path):
    government = case_field.default_government()
    assert any(row.case for row in verbs)
    for row in verbs:
        assert row.case == case_field.case_value(government, row.guid)
        assert row.fields()[-1] == row.case
    parsed = mutable_words_plan.parse_verbs(
        _tsv_with_case(VERBS_TSV, tmp_path, "Accusative")
    )
    assert len(parsed) == len(verbs)
    assert {row.case for row in parsed} == {"Accusative"}
    assert all(row.fields()[-1] == "Accusative" for row in parsed)


def test_parse_adverbs_reads_the_case_column_including_split_rows(adverbs, tmp_path):
    government = case_field.default_government()
    assert any(row.case for row in adverbs)
    for row in adverbs:
        assert row.case == case_field.case_value(government, row.guid)
    parsed = mutable_words_plan.parse_adverbs(
        _tsv_with_case(ADVERBS_TSV, tmp_path, "Genitive")
    )
    assert len(parsed) == len(adverbs) == 134
    assert {row.case for row in parsed} == {"Genitive"}
    by_adverb = {row.adverb: row for row in parsed}
    for word in ("направо", "справа", "налево", "слева"):
        assert by_adverb[word].case == "Genitive"
    assert [row.rank for row in parsed] == [row.rank for row in adverbs]


@pytest.mark.parametrize("sheet", ["Verbs", "Adverbs"])
def test_case_is_the_last_field_and_changes_nothing_else(sheet, verbs, adverbs):
    import dataclasses

    row = (verbs if sheet == "Verbs" else adverbs)[0]
    other = dataclasses.replace(row, case="Dative")
    assert len(row.fields()) == len(mutable_words_plan.FIELD_NAMES[sheet])
    assert other.fields()[-1] == "Dative"
    assert other.fields()[:-1] == row.fields()[:-1]
    assert other.guid == row.guid


def test_rows_without_a_case_argument_still_construct():
    row = mutable_words_plan.AdverbRow(
        rank=1,
        adverb="быстро",
        translation="quickly",
        stress="",
        from_adjective="",
        formation="",
        comparative="",
        additional_info="",
        examples="",
    )
    assert row.case == ""
    assert row.fields()[-1] == ""


def _pronoun_row(russian, pronoun_type):
    return mutable_words_plan.PronounRow(
        rank=1,
        russian=russian,
        translation="x",
        stress=russian,
        pronoun_type=pronoun_type,
        gender_forms="",
        oblique_forms="",
        additional_info="",
        examples="",
    )


PRONOUN_TYPE_FIELD = mutable_words_plan.FIELD_NAMES["Pronouns"].index("Pronoun Type")


@pytest.mark.parametrize(
    "russian,pronoun_type",
    [
        ("кто", "interrogative / relative"),
        ("себя", "reflexive"),
        ("ты", "personal (2nd sg.)"),
        ("вы", "personal (2nd pl./formal)"),
    ],
)
def test_pronoun_type_row_is_empty_when_the_cue_says_it(russian, pronoun_type):
    fields = _pronoun_row(russian, pronoun_type).fields()
    assert fields[PRONOUN_TYPE_FIELD] == ""
    assert fields[-1] != ""


def test_pronoun_type_row_is_kept_when_the_cue_adds_to_it():
    fields = _pronoun_row("ничто", "negative").fields()
    assert fields[PRONOUN_TYPE_FIELD] == "negative"


def test_pronoun_type_row_is_kept_when_there_is_no_cue():
    fields = _pronoun_row("я", "personal (1st sg.)").fields()
    assert fields[-1] == ""
    assert fields[PRONOUN_TYPE_FIELD] == "personal (1st sg.)"


def test_exactly_the_eleven_restating_pronouns_lose_their_type_row(pronouns):
    emptied = sorted(
        row.russian
        for row in pronouns
        if row.pronoun_type and row.fields()[PRONOUN_TYPE_FIELD] == ""
    )
    assert emptied == sorted(
        "ты вы кто себя тот какой который весь твой ваш свой".split()
    )
