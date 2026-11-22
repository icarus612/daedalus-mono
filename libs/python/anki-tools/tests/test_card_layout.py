"""Centre-line render assertion for every mutable answer side, in headless WebKit."""

import importlib.util
import subprocess
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

CASE_MEASURE_JS = """
() => {
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
  const ids = (selector) => Array.from(document.querySelectorAll(selector))
    .filter(e => e.getBoundingClientRect().height > 0)
    .map(span).filter(Boolean);
  const row = (el) => el && el.parentElement.classList.contains('cue-row')
    ? el.parentElement : el;
  const rows = (selector) => Array.from(document.querySelectorAll(selector))
    .filter(e => e.getBoundingClientRect().height > 0)
    .map(row).map(span).filter(Boolean);
  const head = row(document.getElementById('russian'));
  return {
    russian: head ? span(head) : null,
    form: rows('#case-form'),
    lines: ids('.form-line'),
    gloss: rows('#translation'),
    overflow: document.documentElement.scrollWidth - window.innerWidth,
  };
}
"""


@pytest.fixture(scope="module")
def case_answers(tmp_path_factory):
    col = Collection(str(tmp_path_factory.mktemp("case") / "p.anki2"))
    try:
        note_type = _register(col, mutable_words_plan, "Pronouns")
        note = col.new_note(note_type)
        for name in mutable_words_plan.FIELD_NAMES["Pronouns"]:
            note[name] = "[sound:a.mp3]" if name.startswith("Audio") else f"{name} text"
        col.add_note(note, col.decks.id("Layout"))
        cards = {card.ord: card for card in note.cards()}
        assert sorted(cards) == list(range(24))
        yield {
            ord_: (cards[ord_].render_output().answer_text, note_type["css"])
            for ord_ in CASE_ORDS
        }
    finally:
        col.close()


def test_pronoun_template_count_is_24():
    assert _template_count(mutable_words_plan, "Pronouns") == 24


@pytest.mark.parametrize("width", WIDTHS)
@pytest.mark.parametrize("ord_", CASE_ORDS)
def test_case_answer_form_lines_and_gloss_are_centred(
    webkit_page, case_answers, ord_, width
):
    html, css = case_answers[ord_]
    webkit_page.set_viewport_size({"width": width, "height": 900})
    webkit_page.set_content(
        "<!doctype html><html><head>"
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<style>{css}</style></head><body><div class="card">{html}</div></body></html>'
    )
    m = webkit_page.evaluate(CASE_MEASURE_JS)
    assert m["russian"], "headword not rendered"
    assert m["form"], "case form not rendered"
    assert m["gloss"], "gloss not rendered"
    assert m["overflow"] <= 0, m
    reference = _centre(m["russian"])
    for item in m["form"] + m["lines"] + m["gloss"]:
        assert abs(_centre(item) - reference) <= TOLERANCE, m


def _question(col, note_type, filled, ord_):
    note = col.new_note(note_type)
    for name in mutable_words_plan.FIELD_NAMES["Pronouns"]:
        note[name] = (
            "" if name in mutable_words_plan.PRONOUN_CARD_SLOTS else f"{name} text"
        )
        if name.startswith("Audio "):
            note[name] = ""
    for name in filled:
        note[name] = f"{name} text"
    col.add_note(note, col.decks.id("Layout"))
    cards = {card.ord: card for card in note.cards()}
    return cards[ord_].render_output().question_text


@pytest.fixture(scope="module")
def case_col(tmp_path_factory):
    col = Collection(str(tmp_path_factory.mktemp("question") / "q.anki2"))
    try:
        yield col, _register(col, mutable_words_plan, "Pronouns")
    finally:
        col.close()


def test_single_form_cell_renders_the_pill_and_no_qualifier(case_col):
    col, note_type = case_col
    html = _question(col, note_type, ["Prepositional"], 6)
    assert 'data-case="Prepositional"' in html
    assert "aspect" not in html


def test_primary_qualifier_appears_only_when_a_sibling_slot_is_filled(case_col):
    col, note_type = case_col
    plain = _question(col, note_type, ["Genitive"], 2)
    gendered = _question(col, note_type, ["Genitive", "Genitive f."], 2)
    prep = _question(col, note_type, ["Genitive", "Genitive (н-)"], 2)
    assert "aspect" not in plain
    assert "(masculine / neuter)" in gendered
    assert "(without a preposition)" in prep
    assert "(masculine / neuter)" not in prep


def test_accusative_primary_says_not_living_only_with_the_living_form(case_col):
    col, note_type = case_col
    html = _question(col, note_type, ["Accusative", "Accusative m. living"], 4)
    assert "(masculine, not living)" in html
    assert "(masculine, not living)" not in _question(col, note_type, ["Accusative"], 4)


def test_non_primary_front_shows_pill_before_its_fixed_qualifier(case_col):
    col, note_type = case_col
    html = _question(col, note_type, ["Genitive f."], 7)
    assert html.index('data-case="Genitive"') < html.index("(feminine)")
