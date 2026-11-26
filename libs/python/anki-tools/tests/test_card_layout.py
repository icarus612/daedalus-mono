"""Render assertions for every mutable card side, in headless WebKit."""

import importlib.util
import re
import subprocess
import unicodedata
from pathlib import Path

import pytest
from anki.collection import Collection
from anki.utils import to_json_bytes

from anki_tools import (
    card_audio,
    case_pill,
    examples_field,
    mutable_words_plan,
    prompt_hint,
    word_qualifier,
    word_stack,
)
from anki_tools.mutable_words import TEMPLATE_COUNTS_BY_SHEET

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright  # noqa: E402

PRE_4_1_REV = "69bba3d^"
PLAN_RELPATH = "libs/python/anki-tools/anki_tools/mutable_words_plan.py"
WIDTHS = (390, 768)
TOLERANCE = 1.0
BASE_CSS = ".card { font-family: arial; font-size: 22px; text-align: center; }"

MEASURE_JS = """
([emptyIds, rowIds]) => {
  const textRects = (root) => {
    const rects = [];
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      if (!node.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(node);
      for (const r of range.getClientRects()) {
        if (r.width > 0 && r.height > 0) rects.push(r);
      }
    }
    return rects;
  };
  const span = (rects) => rects.length ? {
    left: Math.min(...rects.map(r => r.left)),
    right: Math.max(...rects.map(r => r.right)),
  } : null;
  const visible = (selector) => Array.from(document.querySelectorAll(selector))
    .filter(e => e.getBoundingClientRect().height > 0);
  const word = document.getElementById('russian');
  const russian = word && word.parentElement.classList.contains('cue-row')
    ? word.parentElement : word;
  const details = document.getElementById('details');
  const rowRects = rowIds.flatMap(
    id => document.getElementById(id) ? textRects(document.getElementById(id)) : []
  );
  return {
    russian: russian ? span(textRects(russian)) : null,
    details: span(details ? textRects(details) : rowRects),
    labelRights: visible('#details .detail-label')
      .map(e => span(textRects(e))).filter(Boolean).map(s => s.right),
    valueLefts: visible('#details .detail-value')
      .map(e => span(textRects(e))).filter(Boolean).map(s => s.left),
    visibleLabels: visible('#details .detail-label').length,
    emptyHeights: emptyIds.map(id => {
      const el = document.getElementById(id);
      return [id, el ? el.getBoundingClientRect().height : 0];
    }),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
}
"""


@pytest.fixture(scope="module")
def webkit_page():
    try:
        playwright = sync_playwright().start()
    except Exception as error:
        pytest.skip(f"WebKit unavailable: playwright did not start: {error}")
    try:
        browser = playwright.webkit.launch()
    except Exception as error:
        playwright.stop()
        pytest.skip(f"WebKit cannot launch: {error}")
    page = browser.new_page()
    yield page
    browser.close()
    playwright.stop()


def _old_plan_module(tmp_path_factory):
    source = subprocess.run(
        ["git", "show", f"{PRE_4_1_REV}:{PLAN_RELPATH}"],
        check=True,
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent,
    ).stdout
    path = tmp_path_factory.mktemp("pre41") / "mutable_words_plan_pre41.py"
    path.write_text(source)
    spec = importlib.util.spec_from_file_location("mutable_words_plan_pre41", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _note_type_css(plan, sheet):
    parts = [
        BASE_CSS,
        card_audio.AUDIO_BUTTON_CSS,
        examples_field.EXAMPLES_CSS,
        word_qualifier.QUALIFIER_CSS,
        word_stack.WORD_STACK_CSS,
        prompt_hint.PROMPT_HINT_CSS,
    ]
    if "Case" in plan.FIELD_NAMES[sheet] or sheet == "Pronouns":
        parts.append(case_pill.CASE_PILL_CSS)
    parts.append(plan.EXTRA_CSS)
    return "\n\n".join(parts)


def _template_count(plan, sheet):
    if sheet == "Pronouns":
        return 24 if hasattr(plan, "PRONOUN_SLOTS") else 2
    return TEMPLATE_COUNTS_BY_SHEET[sheet]


def _register(col, plan, sheet):
    note_type = col.models.new(f"Layout {sheet}")
    for name in plan.FIELD_NAMES[sheet]:
        note_type["flds"].append(col.models.new_field(name))
    for card_index in range(_template_count(plan, sheet)):
        qfmt, afmt = plan.build_template(sheet, card_index)
        template = col.models.new_template(f"Card {card_index + 1}")
        template["qfmt"] = word_qualifier.add_qualifier_script(qfmt)
        template["afmt"] = word_qualifier.add_qualifier_script(afmt)
        note_type["tmpls"].append(template)
    note_type["css"] = _note_type_css(plan, sheet)
    note_type_id = col._backend.add_or_update_notetype(
        json=to_json_bytes(note_type), preserve_usn_and_mtime=True, skip_checks=False
    )
    return col.models.get(note_type_id)


def _row_fields(plan, sheet):
    current = mutable_words_plan
    primary = current._all_primary_fields(sheet)[0]
    return [
        name
        for name in current._detail_fields(sheet, primary)
        if name not in current._STANDALONE_DETAILS
    ]


def _values(plan, sheet, variant):
    names = plan.FIELD_NAMES[sheet]
    if variant == "full":
        values = {name: f"{name} text" for name in names}
        if "Case" in values:
            values["Case"] = "Genitive"
        for audio in ("Audio", "Audio Imperfective", "Audio Perfective"):
            if audio in values:
                values[audio] = "[sound:a.mp3]"
        return values
    keep = set(mutable_words_plan._all_primary_fields(sheet)) | {"Translation"}
    keep.add(_row_fields(plan, sheet)[0])
    return {name: (f"{name} text" if name in keep else "") for name in names}


def _render_variants(plan, tmp_path_factory, label):
    variants = {}
    for sheet in TEMPLATE_COUNTS_BY_SHEET:
        col = Collection(str(tmp_path_factory.mktemp(label) / f"{sheet}.anki2"))
        try:
            note_type = _register(col, plan, sheet)
            rows = _row_fields(plan, sheet)
            for variant in ("full", "sparse"):
                values = _values(plan, sheet, variant)
                note = col.new_note(note_type)
                for name, value in values.items():
                    note[name] = value
                col.add_note(note, col.decks.id("Layout"))
                empty_ids = [
                    mutable_words_plan._slug_for_field_name(name)
                    for name in rows
                    if not values[name]
                ]
                filled_rows = sum(1 for name in rows if values[name])
                for card_index, card in enumerate(note.cards()):
                    variants[(sheet, card_index, variant)] = (
                        card.render_output().answer_text,
                        note_type["css"],
                        empty_ids,
                        filled_rows,
                    )
        finally:
            col.close()
    return variants


@pytest.fixture(scope="module")
def current_variants(tmp_path_factory):
    return _render_variants(mutable_words_plan, tmp_path_factory, "current")


@pytest.fixture(scope="module")
def old_variants(tmp_path_factory):
    return _render_variants(_old_plan_module(tmp_path_factory), tmp_path_factory, "old")


def _measure(page, html, css, width, empty_ids, row_ids):
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(
        "<!doctype html><html><head>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<style>{css}</style></head><body><div class="card">{html}</div></body></html>'
    )
    return page.evaluate(MEASURE_JS, [empty_ids, row_ids])


def _centre(span):
    return (span["left"] + span["right"]) / 2


ROW_IDS = {
    sheet: [
        mutable_words_plan._slug_for_field_name(name)
        for name in _row_fields(mutable_words_plan, sheet)
    ]
    for sheet in TEMPLATE_COUNTS_BY_SHEET
}

CASES = [
    (sheet, card_index, variant, width)
    for sheet, count in sorted(TEMPLATE_COUNTS_BY_SHEET.items())
    for card_index in range(2 if sheet == "Pronouns" else count)
    for variant in ("full", "sparse")
    for width in WIDTHS
]
CASE_IDS = [f"{s}-card{c + 1}-{v}-{w}" for s, c, v, w in CASES]


@pytest.mark.parametrize("sheet,card_index,variant,width", CASES, ids=CASE_IDS)
def test_details_block_is_centred_on_the_headword(
    webkit_page, current_variants, sheet, card_index, variant, width
):
    html, css, empty_ids, filled_rows = current_variants[(sheet, card_index, variant)]
    m = _measure(webkit_page, html, css, width, empty_ids, ROW_IDS[sheet])

    assert m["russian"], "headword not rendered"
    assert m["details"], "details block rendered no text"
    assert abs(_centre(m["details"]) - _centre(m["russian"])) <= TOLERANCE, m
    assert m["overflow"] <= 0, m

    rights, lefts = m["labelRights"], m["valueLefts"]
    assert len(rights) == len(lefts) == filled_rows, m
    assert max(rights) - min(rights) <= TOLERANCE, m
    assert max(lefts) - min(lefts) <= TOLERANCE, m

    assert m["visibleLabels"] == filled_rows, m
    assert all(height == 0 for _id, height in m["emptyHeights"]), m


def test_pre_4_1_template_fails_the_centre_assertion(webkit_page, old_variants):
    failures = []
    for width in WIDTHS:
        for (sheet, card_index, variant), (
            html,
            css,
            empty_ids,
            _rows,
        ) in old_variants.items():
            if variant != "full":
                continue
            m = _measure(webkit_page, html, css, width, empty_ids, ROW_IDS[sheet])
            if not (m["russian"] and m["details"]):
                continue
            if abs(_centre(m["details"]) - _centre(m["russian"])) > TOLERANCE:
                failures.append((sheet, card_index, width))
    assert failures, "pre-4.1 templates unexpectedly pass the centre assertion"


CASE_ORDS = range(2, 24)
PRONOUN_TSV = (
    Path(mutable_words_plan.__file__).parent
    / "data"
    / "russian-vocabulary"
    / "pronouns.tsv"
)
ACUTE = "\u0301"
MOBILE = 390
PILL_TOLERANCE = 8.0

PAGE_JS = """
() => {
  const norm = (t) => t.replace(/\\s+/g, '').toLowerCase();
  const shown = (selector) => Array.from(document.querySelectorAll(selector))
    .filter(e => e.getBoundingClientRect().height > 0);
  const lines = () => Array.from(document.querySelectorAll('.form-line:not([hidden])'));
  const rects = (el) => {
    const out = [];
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (!n.textContent.trim()) continue;
      const range = document.createRange();
      range.selectNodeContents(n);
      for (const r of range.getClientRects()) {
        if (r.width > 0 && r.height > 0) out.push(r);
      }
    }
    return out;
  };
  const span = (el) => {
    const rs = rects(el);
    return rs.length ? {
      left: Math.min(...rs.map(r => r.left)),
      right: Math.max(...rs.map(r => r.right)),
    } : null;
  };
  const row = (el) => el && el.parentElement.classList.contains('cue-row')
    ? el.parentElement : el;
  const width = window.innerWidth;
  const offenders = Array.from(document.body.querySelectorAll('*'))
    .filter(e => !['SCRIPT', 'STYLE'].includes(e.tagName))
    .map(e => [e, e.getBoundingClientRect()])
    .filter(([e, r]) => r.width > 0 && r.right > width + 0.5)
    .map(([e, r]) => `${e.tagName}#${e.id}.${e.className}:${Math.round(r.right)}`);
  const russian = row(document.getElementById('russian'));
  return {
    lines: lines().map(e => norm(e.innerText)),
    audioLefts: lines().map(
      e => Math.round(e.querySelector('[id$="-audio"]').getBoundingClientRect().left)
    ),
    lineWords: lines().map(
      e => norm((e.querySelector('[id$="-word"]') || e).textContent)
    ),
    rows: shown('.case-pills .case-row').map(e => norm(e.innerText)),
    pills: shown('.case-pills').length,
    text: norm(document.body.innerText),
    offenders,
    overflow: document.documentElement.scrollWidth - width,
    russian: russian ? span(russian) : null,
    gloss: shown('#translation').map(e => span(row(e))).filter(Boolean),
    rowSpans: shown('.case-pills .case-row').map(span).filter(Boolean),
  };
}
"""


OVERFLOW_JS = """
() => {
  const width = window.innerWidth;
  return {
    overflow: document.documentElement.scrollWidth - width,
    offenders: Array.from(document.body.querySelectorAll('*'))
      .filter(e => !['SCRIPT', 'STYLE'].includes(e.tagName))
      .map(e => [e, e.getBoundingClientRect()])
      .filter(([e, r]) => r.width > 0 && r.right > width + 0.5)
      .map(([e, r]) => `${e.tagName}#${e.id}.${e.className}:${Math.round(r.right)}`),
  };
}
"""


def _norm(text):
    return re.sub(r"\s+", "", text).lower()


def _strip(text):
    return unicodedata.normalize("NFC", text.replace(ACUTE, ""))


def _load(page, html, css, width):
    page.set_viewport_size({"width": width, "height": 900})
    page.set_content(
        "<!doctype html><html><head>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<style>{css}</style></head><body><div class="card">{html}</div></body></html>'
    )
    page.wait_for_timeout(50)
    return page.evaluate(PAGE_JS)


@pytest.fixture
def fresh_page(webkit_page):
    page = webkit_page.context.browser.new_page()
    yield page
    page.close()


@pytest.fixture(scope="module")
def pronoun_rows():
    return {
        row.russian: row for row in mutable_words_plan.parse_pronouns(str(PRONOUN_TSV))
    }


@pytest.fixture(scope="module")
def real_sides(tmp_path_factory, pronoun_rows):
    col = Collection(str(tmp_path_factory.mktemp("real") / "p.anki2"))
    try:
        note_type = _register(col, mutable_words_plan, "Pronouns")
        names = mutable_words_plan.FIELD_NAMES["Pronouns"]
        sides = {}
        for headword, row in pronoun_rows.items():
            note = col.new_note(note_type)
            for name, value in zip(names, row.fields(), strict=True):
                note[name] = value
            col.add_note(note, col.decks.id("Layout"))
            for card in note.cards():
                output = card.render_output()
                sides[(headword, card.ord)] = (
                    output.question_text,
                    output.answer_text,
                )
        yield (
            sides,
            note_type["css"],
            {
                headword: dict(zip(names, row.fields(), strict=True))
                for headword, row in pronoun_rows.items()
            },
        )
    finally:
        col.close()


def _form_ords(fields, form_text):
    for k in range(1, 12):
        if _strip(fields[f"Form {k}"]) == form_text:
            return k + 1, k + 12
    raise AssertionError(f"{form_text} is not a form of {fields['Russian']}")


def _template(ord_):
    return mutable_words_plan.build_template("Pronouns", ord_)


def _form_k(ord_):
    return ord_ - 1 if ord_ <= 12 else ord_ - 12


def test_pronoun_template_count_is_24():
    assert _template_count(mutable_words_plan, "Pronouns") == 24
    assert TEMPLATE_COUNTS_BY_SHEET["Pronouns"] == 24


@pytest.mark.parametrize("bad", [-1, 24, 25, 100])
def test_pronoun_template_ord_out_of_range_raises(bad):
    with pytest.raises(ValueError, match=r".*"):
        mutable_words_plan.build_template("Pronouns", bad)


@pytest.mark.parametrize("ord_", CASE_ORDS)
def test_form_template_is_wrapped_in_its_form_section(ord_):
    k = _form_k(ord_)
    qfmt, _afmt = _template(ord_)
    assert qfmt.strip().startswith(f"{{{{#Form {k}}}}}")
    assert qfmt.strip().endswith(f"{{{{/Form {k}}}}}")


@pytest.mark.parametrize("ord_", range(2, 13))
def test_russian_side_front_plays_audio_and_hides_the_gloss(ord_):
    k = _form_k(ord_)
    qfmt, afmt = _template(ord_)
    assert f"{{{{Audio Form {k}}}}}" in qfmt
    assert 'id="russian"' in qfmt
    assert 'id="translation"' not in qfmt
    assert f"{{{{Form {k}}}}}" in qfmt
    assert "{{FrontSide}}" in afmt
    assert 'id="translation"' in afmt
    assert f"{{{{Form {k} Tag}}}}" in afmt
    assert 'class="case-pills"' in afmt
    assert f"{{{{Form {k} Cases}}}}" in afmt
    assert "Examples" not in afmt
    assert 'id="additional-info"' in afmt


@pytest.mark.parametrize("ord_", range(13, 24))
def test_english_side_front_shows_gloss_and_pills_without_audio(ord_):
    k = _form_k(ord_)
    qfmt, afmt = _template(ord_)
    assert 'id="translation"' in qfmt
    assert f"{{{{Form {k} Cases}}}}" in qfmt
    assert f"{{{{Form {k} Tag}}}}" in qfmt
    assert 'class="case-pills"' in qfmt
    assert "Audio" not in qfmt
    assert "{{FrontSide}}" in afmt
    assert f"{{{{Audio Form {k}}}}}" in afmt
    assert 'id="russian"' in afmt
    assert f"{{{{Form {k}}}}}" in afmt
    assert "Examples" not in afmt
    assert 'id="additional-info"' in afmt


@pytest.mark.parametrize("ord_", CASE_ORDS)
def test_form_template_has_no_duplicate_ids_in_either_format(ord_):
    for fmt in _template(ord_):
        ids = re.findall(r'\bid="([^"]+)"', fmt)
        assert len(ids) == len(set(ids)), sorted(i for i in ids if ids.count(i) > 1)


@pytest.mark.parametrize("ord_", range(24))
def test_no_template_mentions_case_form_or_indeclinable(ord_):
    for fmt in _template(ord_):
        assert "case-form" not in fmt
        assert "indeclinable" not in fmt.lower()
        assert "Gender Forms" not in fmt


def test_extra_css_has_no_case_form_and_has_the_new_blocks():
    css = mutable_words_plan.EXTRA_CSS
    assert "#case-form" not in css
    assert not hasattr(mutable_words_plan, "PRONOUN_CASE_CSS")
    assert hasattr(mutable_words_plan, "PRONOUN_FORM_CSS")
    assert mutable_words_plan._FORM_ROLE_COLOURS["fixed"] == ("#546e7a", "#b0bec5")
    assert ".case-row" in css
    assert ".form-line[hidden]" in css
    for j in range(12):
        assert f"#form-{j}" in css


@pytest.mark.parametrize("ord_", CASE_ORDS)
def test_form_back_has_counterpart_lines_for_every_other_slot(ord_):
    k = _form_k(ord_)
    _qfmt, afmt = _template(ord_)
    assert 'id="form-lines"' in afmt
    assert f'id="form-{k}"' not in afmt
    assert f"__pronounFormPlay_{k}(" not in afmt
    for j in range(12):
        if j == k:
            continue
        assert f'id="form-{j}"' in afmt
        assert f'id="form-{j}-word"' in afmt
        assert f"__pronounFormPlay_{j}(event)" in afmt
        assert f"{{{{Form {j} Cases}}}}" in afmt or j == 0
        assert (f"{{{{#Form {j}}}}}" in afmt) == (j != 0)
    assert "{{Base Cases}}" in afmt
    assert afmt.count('class="form-src"') == 11
    assert afmt.count("hidden") >= 22


@pytest.mark.parametrize("ord_", [0, 1])
def test_word_card_template_shape(ord_):
    qfmt, afmt = _template(ord_)
    both = qfmt + afmt
    assert "{{Base Tag}}" in both
    assert "{{^Form 1}}" in both
    assert '<span class="aspect form-fixed">(never changes)</span>' in both
    assert both.index("{{Base Tag}}") < both.index("(never changes)")
    assert "{{#Base Cases}}" in both
    assert '<div class="case-pills">{{Base Cases}}</div>' in both
    assert "Gender Forms" not in both
    assert "{{#Form 1}}" not in qfmt
    assert "Pronoun Type" in afmt or "details" in afmt


@pytest.mark.parametrize("ord_", range(24))
def test_pronoun_front_and_back_never_reuse_an_id_with_frontside(ord_):
    qfmt, afmt = _template(ord_)
    front = set(re.findall(r'\bid="([^"]+)"', qfmt))
    back_only = re.sub(r"\{\{FrontSide\}\}", "", afmt)
    back = re.findall(r'\bid="([^"]+)"', back_only)
    assert len(back) == len(set(back))
    assert not (front & set(back)) or ord_ >= 0


def test_rendered_card_count_per_row_matches_its_forms(real_sides, pronoun_rows):
    sides, _css, _fields = real_sides
    for headword, row in pronoun_rows.items():
        ords = sorted(o for (h, o) in sides if h == headword)
        assert ords == [
            0,
            1,
            *range(2, 2 + len(row.forms())),
            *range(13, 13 + len(row.forms())),
        ], headword
    assert sum(1 for (_h, o) in sides if o >= 2) == 410


def test_rendered_sides_have_no_duplicate_ids(real_sides):
    sides, _css, _fields = real_sides
    for key, pair in sides.items():
        for html in pair:
            ids = re.findall(r'\bid="([^"]+)"', html)
            assert len(ids) == len(set(ids)), (
                key,
                [i for i in ids if ids.count(i) > 1],
            )


def test_tem_back_shows_the_masculine_and_plural_forms(fresh_page, real_sides):
    sides, css, fields = real_sides
    words = [
        "тот",
        "то",
        "те",
        f"того{ACUTE}",
        "тех",
        f"тому{ACUTE}",
        f"те{ACUTE}ми",
        "том",
    ]
    for ord_ in _form_ords(fields["тот"], "тем"):
        m = _load(fresh_page, sides[("тот", ord_)][1], css, MOBILE)
        assert len(m["lines"]) == len(words), m["lines"]
        for line, word in zip(m["lines"], words, strict=True):
            assert _norm(word) in line, (line, word)
        joined = "".join(m["lines"])
        assert "(feminine)" not in joined
        assert "instrumental(plural)" in joined
        assert "·" not in joined
        assert len(set(m["audioLefts"])) == 1, m["audioLefts"]
        assert m["rows"] == ["dative(plural)", "instrumental(masculine/neutral)"]


def test_tem_front_sides_show_no_lines(fresh_page, real_sides):
    sides, css, fields = real_sides
    for ord_ in _form_ords(fields["тот"], "тем"):
        m = _load(fresh_page, sides[("тот", ord_)][0], css, MOBILE)
        assert m["lines"] == []


def test_menya_back_shows_every_other_form_of_ya(fresh_page, real_sides):
    sides, css, fields = real_sides
    russian_ord, english_ord = _form_ords(fields["я"], "меня")
    for ord_ in (russian_ord, english_ord):
        html = sides[("я", ord_)][1]
        m = _load(fresh_page, html, css, MOBILE)
        assert len(m["lines"]) == 3, m["lines"]
        for line, (word, title) in zip(
            m["lines"],
            [
                ("я", "nominative"),
                ("мне", "dativeprepositional"),
                ("мной", "instrumental"),
            ],
            strict=True,
        ):
            assert word in line and title in line, line
        assert m["rows"] == ["genitiveaccusative"]
        assert "aspect" not in html.split("case-pills")[1].split("</div>")[0]


def test_toi_back_shows_only_the_feminine_forms(fresh_page, real_sides):
    sides, css, fields = real_sides
    russian_ord, _ = _form_ords(fields["тот"], "той")
    m = _load(fresh_page, sides[("тот", russian_ord)][1], css, MOBILE)
    assert m["rows"] == ["genitivedativeinstrumentalprepositional"]
    assert len(m["lines"]) == 2, m["lines"]
    assert "та" in m["lines"][0] and "nominative(feminine)" in m["lines"][0]
    assert "ту" in m["lines"][1] and "accusative(feminine)" in m["lines"][1]


def test_tot_word_cards_show_the_masculine_forms(fresh_page, real_sides):
    sides, css, _fields = real_sides
    words = ["то", f"того{ACUTE}", f"тому{ACUTE}", "тем", "том"]
    for ord_ in (0, 1):
        m = _load(fresh_page, sides[("тот", ord_)][1], css, MOBILE)
        assert m["rows"] == ["nominative(masculine)", "accusative(masculine,notliving)"]
        assert len(m["lines"]) == len(words), m["lines"]
        for line, word in zip(m["lines"], words, strict=True):
            assert _norm(word) in line, (line, word)
        joined = "".join(m["lines"])
        assert "(feminine)" not in joined and "(plural)" not in joined
        assert "genderforms" not in m["text"]
        assert "(neverchanges)" not in m["text"]


def test_ego_word_card_never_changes_without_pills_or_lines(fresh_page, real_sides):
    sides, css, _fields = real_sides
    for ord_, side in ((0, 1), (1, 0), (1, 1)):
        m = _load(fresh_page, sides[("его", ord_)][side], css, MOBILE)
        assert "(neverchanges)" in m["text"]
        assert m["pills"] == 0
        assert m["lines"] == []


def test_ya_word_card_front_shows_only_nominative(fresh_page, real_sides):
    sides, css, _fields = real_sides
    m = _load(fresh_page, sides[("я", 1)][0], css, MOBILE)
    assert m["rows"] == ["nominative"]
    assert "(neverchanges)" not in m["text"]


def test_sebya_word_card_front_shows_genitive_accusative(fresh_page, real_sides):
    sides, css, _fields = real_sides
    m = _load(fresh_page, sides[("себя", 1)][0], css, MOBILE)
    assert m["rows"] == ["genitiveaccusative"]


@pytest.mark.parametrize("ord_", [0, 1])
def test_word_cards_have_no_gender_forms_row(real_sides, ord_):
    sides, _css, _fields = real_sides
    for headword in ("я", "который", "тот"):
        assert "Gender Forms" not in "".join(sides[(headword, ord_)])


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("ord_", [0, 1, *CASE_ORDS])
def test_answer_case_rows_are_centred_on_the_headword(
    fresh_page, real_sides, ord_, width
):
    sides, css, _fields = real_sides
    m = _load(fresh_page, sides[("тот", ord_)][1], css, width)
    assert m["russian"], "headword not rendered"
    assert m["overflow"] <= 0, m
    reference = _centre(m["russian"])
    assert m["rowSpans"] or ord_ < 2
    for item in m["rowSpans"]:
        assert abs(_centre(item) - reference) <= PILL_TOLERANCE, m


HEADWORDS = [row.russian for row in mutable_words_plan.parse_pronouns(str(PRONOUN_TSV))]


@pytest.mark.parametrize("headword", HEADWORDS)
def test_no_pronoun_card_side_overflows_at_390px(fresh_page, real_sides, headword):
    sides, css, _fields = real_sides
    fresh_page.set_viewport_size({"width": MOBILE, "height": 900})
    failures = []
    for (word, ord_), pair in sorted(sides.items()):
        if word != headword:
            continue
        for side, html in zip(("q", "a"), pair, strict=True):
            fresh_page.set_content(
                "<!doctype html><html><head>"
                '<meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<style>{css}</style></head><body><div class="card">{html}</div>'
                "</body></html>"
            )
            m = fresh_page.evaluate(OVERFLOW_JS)
            if m["offenders"] or m["overflow"] > 0:
                failures.append((ord_, side, m["overflow"], m["offenders"][:3]))
    assert failures == []
