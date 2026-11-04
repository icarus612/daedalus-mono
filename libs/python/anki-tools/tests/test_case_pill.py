import itertools
import re

import pytest
from anki.collection import Collection

from anki_tools import case_pill
from anki_tools.case_field import CASE_NAMES

CANONICAL = (
    "Nominative",
    "Genitive",
    "Dative",
    "Accusative",
    "Instrumental",
    "Prepositional",
)
LIGHT_TEXT = dict(
    zip(
        CANONICAL,
        ("#616161", "#c62828", "#2e7d32", "#1565c0", "#c43e00", "#6a1b9a"),
        strict=True,
    )
)
DARK_TEXT = dict(
    zip(
        CANONICAL,
        ("#bdbdbd", "#ef9a9a", "#a5d6a7", "#90caf9", "#ffb74d", "#ce93d8"),
        strict=True,
    )
)
LIGHT_BG = dict(
    zip(
        CANONICAL,
        ("#eeeeee", "#fdecea", "#e8f5e9", "#e3f2fd", "#fff3e0", "#f3e5f5"),
        strict=True,
    )
)
DARK_BG = dict(
    zip(
        CANONICAL,
        ("#3a3a3a", "#4a2c2c", "#2c4030", "#2a3a4d", "#4d3a1f", "#40304a"),
        strict=True,
    )
)
_COLLECTION_IDS = itertools.count()
PAGE_LIGHT = "#ffffff"
PAGE_DARK = "#2c2c2c"
MIN_CONTRAST = 4.5

RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
COLOR = re.compile(r"(?<![-\w])color\s*:\s*(#[0-9a-fA-F]{6})")
BACKGROUND = re.compile(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})")


def _linear(channel):
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def _luminance(hex_colour):
    red, green, blue = (int(hex_colour[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _linear(red) + 0.7152 * _linear(green) + 0.0722 * _linear(blue)


def contrast(foreground, background):
    lighter, darker = sorted(
        (_luminance(foreground), _luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def _rules():
    rules = []
    for selectors, body in RULE.findall(case_pill.CASE_PILL_CSS):
        for selector in selectors.split(","):
            rules.append((" ".join(selector.split()), body))
    return rules


def _declared(pattern, selector_test):
    found = []
    for selector, body in _rules():
        if selector_test(selector):
            found.extend(pattern.findall(body))
    return found


def _is_pill(selector, name, night):
    slug = case_pill.case_slug(name)
    return (
        f".case-{slug}" in selector
        and ".case-text" not in selector
        and "case-pills" not in selector
        and (".nightMode" in selector) == night
    )


def _is_tint(selector, name, night):
    slug = case_pill.case_slug(name)
    return (
        f".case-text.case-{slug}" in selector
        and ".case-pill" not in selector.replace(".case-text", "")
        and (".nightMode" in selector) == night
    )


def _strip_tags(text):
    return re.sub(r"<[^>]*>", "", text)


def _show_selector(name):
    return f'.case-pills[data-case*="{name}" i] .case-{case_pill.case_slug(name)}'


@pytest.mark.parametrize("name", CANONICAL)
def test_case_order_and_slugs(name):
    assert name in case_pill.CASE_ORDER
    assert case_pill.case_slug(name) == name.lower()


def test_case_order_is_canonical_and_known_to_case_field():
    assert case_pill.CASE_ORDER == CANONICAL
    assert set(case_pill.CASE_ORDER) <= {name for _, name in CASE_NAMES}


def test_constants():
    assert case_pill.PILL_WRAPPER_CLASS == "case-pills"
    assert case_pill.PROMPT_HINT_ANCHOR == "prompt-hint"


def test_pill_block_is_exactly_the_specified_markup():
    spans = "".join(
        f'<span class="case-pill case-{name.lower()}">{name}</span>'
        for name in CANONICAL
    )
    expected = (
        '{{#Case}}<div class="case-pills" data-case="{{text:Case}}">'
        f"{spans}</div>{{{{/Case}}}}"
    )
    normalised = re.sub(r">\s+<", "><", case_pill.pill_block())
    assert normalised == expected


@pytest.mark.parametrize("name", CANONICAL)
def test_each_case_name_appears_in_exactly_one_span(name):
    block = case_pill.pill_block()
    assert len(re.findall(rf">\s*{name}\s*</span>", block)) == 1


def test_spans_are_in_canonical_order_and_script_free():
    block = case_pill.pill_block()
    assert re.findall(r'class="case-pill case-(\w+)"', block) == [
        name.lower() for name in CANONICAL
    ]
    assert "<script" not in block


def _render(tmp_path, template, fields):
    col = Collection(str(tmp_path / f"pill-{next(_COLLECTION_IDS)}.anki2"))
    try:
        models = col.models
        note_type = models.new("PillTest")
        for field_name in ("Front", "Case"):
            models.add_field(note_type, models.new_field(field_name))
        card_type = models.new_template("Card 1")
        card_type["qfmt"] = template
        card_type["afmt"] = "{{FrontSide}}"
        models.add_template(note_type, card_type)
        models.add(note_type)
        note = col.new_note(models.by_name("PillTest"))
        for key, value in fields.items():
            note[key] = value
        col.add_note(note, col.decks.id("Pill"))
        return note.cards()[0].render_output().question_text
    finally:
        col.close()


def _data_case(rendered):
    match = re.search(r'data-case="([^"]*)"', rendered)
    return match.group(1) if match else None


def test_render_exposes_the_case_text_in_the_attribute(tmp_path):
    out = _render(
        tmp_path,
        "{{Front}}" + case_pill.pill_block(),
        {"Front": "f", "Case": "Accusative, Prepositional"},
    )
    assert 'data-case="Accusative, Prepositional"' in out
    assert out.count("case-pills") == 1
    assert [m for m in re.findall(r"case-pill case-(\w+)", out)] == [
        name.lower() for name in CANONICAL
    ]


def test_render_with_empty_case_has_no_wrapper(tmp_path):
    out = _render(
        tmp_path, "{{Front}}" + case_pill.pill_block(), {"Front": "f", "Case": ""}
    )
    assert "case-pills" not in out
    assert "data-case" not in out


def test_render_strips_html_from_case_and_plain_field_would_not(tmp_path):
    case_html = "<b>Dative</b>"
    good = _render(
        tmp_path,
        "{{Front}}" + case_pill.pill_block(),
        {"Front": "f", "Case": case_html},
    )
    assert _data_case(good) == "Dative"
    assert "<b>" not in good.split('data-case="')[1].split('"')[0]

    naive = case_pill.pill_block().replace("{{text:Case}}", "{{Case}}")
    assert naive != case_pill.pill_block()
    bad = _render(tmp_path, "{{Front}}" + naive, {"Front": "f", "Case": case_html})
    assert _data_case(bad) != "Dative"


ANCHOR_DIV = '<div id="prompt-hint">{{#English}}({{English}}){{/English}}</div>'


@pytest.mark.parametrize(
    "template",
    [
        "{{Front}}\n" + ANCHOR_DIV + "\n<hr>{{Back}}",
        '<div class="a">\n  {{Front}}\n</div>\n'
        '<div class="hint" id="prompt-hint"\n     data-x="1">\n'
        "  {{English}}\n</div>\n<div>tail</div>",
        ANCHOR_DIV,
    ],
)
def test_add_pill_block_inserts_directly_after_the_anchor(template):
    result = case_pill.add_pill_block(template)
    anchor_end = re.search(
        r"<div[^>]*id=\"prompt-hint\".*?</div>", template, re.S
    ).end()
    inserted = "\n" + case_pill.pill_block()
    assert result[anchor_end : anchor_end + len(inserted)] == inserted
    assert result[:anchor_end] == template[:anchor_end]
    assert result[anchor_end + len(inserted) :] == template[anchor_end:]
    assert result.count(case_pill.PILL_WRAPPER_CLASS) == 1


@pytest.mark.parametrize(
    "template",
    [
        "{{Front}}\n" + ANCHOR_DIV,
        "<div>x</div>\n" + ANCHOR_DIV + "\n<div>tail</div>",
    ],
)
def test_add_pill_block_is_idempotent(template):
    once = case_pill.add_pill_block(template)
    assert once != template
    assert case_pill.add_pill_block(once) == once


@pytest.mark.parametrize(
    "template",
    ["{{Front}}", '<div id="other">x</div>', "", '<span id="prompt-hint">x</span>'],
)
def test_add_pill_block_without_anchor_is_a_no_op(template):
    assert case_pill.add_pill_block(template) == template


def test_add_pill_block_custom_anchor():
    template = '<div id="other">x</div>'
    assert case_pill.add_pill_block(template, "other") != template
    assert case_pill.add_pill_block(template, "prompt-hint") == template


def test_css_is_brace_balanced_and_ends_with_a_brace():
    css = case_pill.CASE_PILL_CSS
    assert css.count("{") == css.count("}") > 0
    assert css.rstrip().endswith("}")


def test_wrapper_and_default_hidden_rules():
    rules = dict(_rules())
    assert "text-align: center" in rules[".case-pills"]
    assert "padding-top: .2rem" in rules[".case-pills"]
    assert re.search(r"display\s*:\s*none", rules[".case-pill"])


@pytest.mark.parametrize("name", CANONICAL)
def test_exactly_one_show_rule_per_case(name):
    matching = [body for sel, body in _rules() if sel == _show_selector(name)]
    assert len(matching) == 1
    assert re.search(r"display\s*:\s*inline-block", matching[0])


def test_show_selector_helper_matches_only_the_intended_rule():
    selectors = [sel for sel, _ in _rules() if sel.startswith(".case-pills[")]
    assert sorted(selectors) == sorted(_show_selector(n) for n in CANONICAL)


@pytest.mark.parametrize("name", CANONICAL)
@pytest.mark.parametrize("night", [False, True])
def test_pill_colours_exist_and_are_exact(name, night):
    text_map, bg_map = (DARK_TEXT, DARK_BG) if night else (LIGHT_TEXT, LIGHT_BG)
    texts = _declared(COLOR, lambda s: _is_pill(s, name, night))
    backgrounds = _declared(BACKGROUND, lambda s: _is_pill(s, name, night))
    assert text_map[name] in [t.lower() for t in texts]
    assert bg_map[name] in [b.lower() for b in backgrounds]


@pytest.mark.parametrize("name", CANONICAL)
@pytest.mark.parametrize("night", [False, True])
def test_tint_colours_exist_and_are_exact(name, night):
    text_map = DARK_TEXT if night else LIGHT_TEXT
    texts = _declared(COLOR, lambda s: _is_tint(s, name, night))
    assert text_map[name] in [t.lower() for t in texts]


@pytest.mark.parametrize("name", CANONICAL)
@pytest.mark.parametrize("night", [False, True])
def test_pill_contrast_meets_wcag_aa(name, night):
    text_map, bg_map = (DARK_TEXT, DARK_BG) if night else (LIGHT_TEXT, LIGHT_BG)
    assert contrast(text_map[name], bg_map[name]) >= MIN_CONTRAST


@pytest.mark.parametrize("name", CANONICAL)
@pytest.mark.parametrize("night", [False, True])
def test_tint_contrast_meets_wcag_aa_on_the_page(name, night):
    text_map = DARK_TEXT if night else LIGHT_TEXT
    page = PAGE_DARK if night else PAGE_LIGHT
    assert contrast(text_map[name], page) >= MIN_CONTRAST


def test_contrast_helper_controls():
    assert contrast("#000000", "#ffffff") == pytest.approx(21.0)
    assert contrast("#ffffff", "#ffffff") == pytest.approx(1.0)
    assert contrast("#e65100", PAGE_LIGHT) < MIN_CONTRAST


def test_declared_colours_in_css_all_pass_contrast_in_context():
    for name in CANONICAL:
        for night in (False, True):
            page = PAGE_DARK if night else PAGE_LIGHT
            for text in _declared(COLOR, lambda s: _is_tint(s, name, night)):
                assert contrast(text, page) >= MIN_CONTRAST
            texts = _declared(COLOR, lambda s: _is_pill(s, name, night))
            backgrounds = _declared(BACKGROUND, lambda s: _is_pill(s, name, night))
            for text in texts:
                for background in backgrounds:
                    assert contrast(text, background) >= MIN_CONTRAST


SPAN = '<span class="case-text case-{slug}">{text}</span>'


def _span(slug, text):
    return SPAN.format(slug=slug, text=text)


MAPPING = {
    "in / at (where)": "Prepositional",
    "into (where/what)": "Accusative",
}


@pytest.mark.parametrize(
    ("translation", "mapping", "expected"),
    [
        (
            "in / at (where)<br>into (where/what)",
            MAPPING,
            _span("prepositional", "in / at (where)")
            + "<br>"
            + _span("accusative", "into (where/what)"),
        ),
        (
            "in / at (where)<br/>into (where/what)",
            MAPPING,
            _span("prepositional", "in / at (where)")
            + "<br/>"
            + _span("accusative", "into (where/what)"),
        ),
        (
            "in / at (where)<br />into (where/what)",
            MAPPING,
            _span("prepositional", "in / at (where)")
            + "<br />"
            + _span("accusative", "into (where/what)"),
        ),
        (
            "in / at (where)<br>other",
            MAPPING,
            _span("prepositional", "in / at (where)") + "<br>other",
        ),
        (
            "in / at (where)<br><div>since (when)</div>",
            {"in / at (where)": "Prepositional", "since (when)": "Genitive"},
            _span("prepositional", "in / at (where)")
            + "<br><div>"
            + _span("genitive", "since (when)")
            + "</div>",
        ),
        (
            '<div class="x">from (where)</div><div>to (where)</div>',
            {"from (where)": "Genitive", "to (where)": "Dative"},
            '<div class="x">'
            + _span("genitive", "from (where)")
            + "</div><div>"
            + _span("dative", "to (where)")
            + "</div>",
        ),
        (
            "  padded line  <br>x",
            {"padded line": "Dative"},
            "  " + _span("dative", "padded line") + "  <br>x",
        ),
    ],
)
def test_tint_lines_wraps_matched_lines_only(translation, mapping, expected):
    assert case_pill.tint_lines(translation, mapping) == expected


@pytest.mark.parametrize(
    "translation",
    [
        "in / at (where)<br>into (where/what)",
        "plain text",
        "",
        "<div>a</div><div>b</div>",
    ],
)
def test_tint_lines_empty_mapping_is_identity(translation):
    assert case_pill.tint_lines(translation, {}) == translation


@pytest.mark.parametrize(
    ("translation", "mapping"),
    [
        ("alpha<br>beta", {"gamma": "Genitive"}),
        ("alpha<br>beta", {"alph": "Genitive"}),
        ("alpha<br>beta", {"ALPHA": "Genitive"}),
        ("alpha beta", {"alpha": "Genitive"}),
    ],
)
def test_tint_lines_key_matching_no_line_leaves_text_untouched(translation, mapping):
    assert case_pill.tint_lines(translation, mapping) == translation


def test_tint_lines_matching_key_is_the_positive_control_for_untouched_text():
    translation = "alpha<br>beta"
    assert case_pill.tint_lines(translation, {"alpha": "Genitive"}) != translation
    assert case_pill.tint_lines(translation, {"gamma": "Genitive"}) == translation


@pytest.mark.parametrize("bad", ["Genitiv", "genitive", "Locative", "", "Gen"])
def test_tint_lines_rejects_non_canonical_case(bad):
    with pytest.raises(ValueError, match=r".*"):
        case_pill.tint_lines("alpha", {"alpha": bad})


@pytest.mark.parametrize("good", CANONICAL)
def test_tint_lines_accepts_every_canonical_case(good):
    out = case_pill.tint_lines("alpha", {"alpha": good})
    assert out == _span(good.lower(), "alpha")


@pytest.mark.parametrize(
    ("translation", "mapping"),
    [
        ("in / at (where)<br>into (where/what)", MAPPING),
        ("a<br/>b<br />c", {"a": "Dative", "c": "Genitive"}),
        ("<div>a</div><div>b</div>", {"b": "Instrumental"}),
        ('x<div class="k">y</div>', {"x": "Nominative", "y": "Prepositional"}),
    ],
)
def test_tint_lines_preserves_text_once_tags_are_stripped(translation, mapping):
    out = case_pill.tint_lines(translation, mapping)
    assert out != translation
    assert _strip_tags(out) == _strip_tags(translation)
