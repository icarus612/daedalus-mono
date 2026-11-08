"""Contract tests for the grammatical hint under an English prompt."""

import inspect

import pytest

from anki_tools import distinction, prompt_hint
from anki_tools.mutable_words_plan import FIELD_NAMES, build_template

FIELD = distinction.ENGLISH_FIELD
TRANSLATION_DIV = '<div id="translation">{{Translation}}</div>'
PROMPT_SIDE = f'<div id="front">\n{TRANSLATION_DIV}\n</div>'


def test_hint_is_wrapped_in_ankis_own_empty_field_conditional():
    out = prompt_hint.hint_div(FIELD)
    assert f"{{{{#{FIELD}}}}}" in out
    assert f"{{{{{FIELD}}}}}" in out
    assert f"{{{{/{FIELD}}}}}" in out
    assert f"({{{{{FIELD}}}}})" in out


def test_hint_goes_straight_after_the_translation():
    out = prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD)
    assert TRANSLATION_DIV + "\n" + prompt_hint.hint_div(FIELD) in out


@pytest.mark.parametrize(
    "html",
    [
        '<div id="front">\n<div id="russian">{{Russian}}</div>\n</div>',
        '<div id="back">\n<div id="audio"></div>\n</div>',
        "{{FrontSide}}",
        "",
    ],
)
def test_a_side_that_shows_no_translation_is_left_alone(html):
    assert prompt_hint.add_prompt_hint(html, FIELD) == html


def test_is_idempotent():
    once = prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD)
    assert prompt_hint.add_prompt_hint(once, FIELD) == once


def test_css_styles_every_element_the_hint_emits():
    for hint_id in prompt_hint.HINT_IDS:
        assert f"#{hint_id}" in prompt_hint.PROMPT_HINT_CSS
    assert prompt_hint.PROMPT_HINT_CSS.rstrip().endswith("}")


RUSSIAN_DIV = '<div id="russian">{{Russian}}</div>'


def test_element_id_names_the_div_the_hint_emits():
    out = prompt_hint.hint_div(distinction.RUSSIAN_FIELD, prompt_hint.RUSSIAN_HINT_ID)
    assert out.startswith(f'<div id="{prompt_hint.RUSSIAN_HINT_ID}">')


def test_hint_goes_straight_after_the_headword_on_the_russian_anchor():
    out = prompt_hint.add_prompt_hint(
        RUSSIAN_DIV,
        distinction.RUSSIAN_FIELD,
        prompt_hint.RUSSIAN_HINT_ID,
        prompt_hint.RUSSIAN_ANCHOR,
    )
    assert out == (
        prompt_hint.CUE_ROW_OPEN
        + RUSSIAN_DIV
        + "\n"
        + prompt_hint.hint_div(distinction.RUSSIAN_FIELD, prompt_hint.RUSSIAN_HINT_ID)
        + "</div>"
        + prompt_hint.FIT_HINT_SCRIPT
    )


def test_word_and_hint_share_one_centred_row():
    out = prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD)
    assert (
        prompt_hint.CUE_ROW_OPEN
        + TRANSLATION_DIV
        + "\n"
        + prompt_hint.hint_div(FIELD)
        + "</div>"
    ) in out
    css = prompt_hint.PROMPT_HINT_CSS
    assert ".cue-row {" in css
    for rule in ("display: flex", "justify-content: center", "align-items: center"):
        assert rule in css
    assert "\twidth:" not in css


def test_an_inserted_russian_hint_is_never_its_own_anchor():
    once = prompt_hint.add_prompt_hint(
        RUSSIAN_DIV,
        distinction.RUSSIAN_FIELD,
        prompt_hint.RUSSIAN_HINT_ID,
        prompt_hint.RUSSIAN_ANCHOR,
    )
    bare = prompt_hint.hint_div(distinction.RUSSIAN_FIELD, prompt_hint.RUSSIAN_HINT_ID)
    assert (
        prompt_hint.add_prompt_hint(
            bare,
            distinction.RUSSIAN_FIELD,
            "second-hint",
            prompt_hint.RUSSIAN_ANCHOR,
        )
        == bare
    )
    assert once.count(f'id="{prompt_hint.RUSSIAN_HINT_ID}"') == 1


def test_two_hints_on_one_anchor_stack_in_reverse_call_order():
    out = prompt_hint.add_prompt_hint(PROMPT_SIDE, "Other", "second-hint")
    out = prompt_hint.add_prompt_hint(out, FIELD)
    assert (
        TRANSLATION_DIV
        + "\n"
        + prompt_hint.hint_div(FIELD)
        + "\n"
        + prompt_hint.hint_div("Other", "second-hint")
    ) in out


def test_the_case_hint_is_gone_from_the_public_surface():
    assert prompt_hint.HINT_IDS == (
        prompt_hint.PROMPT_HINT_ID,
        prompt_hint.RUSSIAN_HINT_ID,
    )
    assert not hasattr(prompt_hint, "PROMPT_CASE_ID")
    assert "prompt-case" not in prompt_hint.PROMPT_HINT_CSS
    assert "prompt-case" not in prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD)


@pytest.mark.parametrize(
    "func,expected",
    [
        (
            prompt_hint.hint_div,
            [("field_name", inspect.Parameter.empty), ("element_id", "prompt-hint")],
        ),
        (
            prompt_hint.add_prompt_hint,
            [
                ("template_html", inspect.Parameter.empty),
                ("field_name", inspect.Parameter.empty),
                ("element_id", "prompt-hint"),
                ("anchor_id", prompt_hint.TRANSLATION_ANCHOR),
            ],
        ),
    ],
)
def test_signatures_are_pinned(func, expected):
    params = inspect.signature(func).parameters
    assert [(n, p.default) for n, p in params.items()] == expected


def test_constants_are_kept():
    assert prompt_hint.PROMPT_HINT_ID == "prompt-hint"
    assert prompt_hint.RUSSIAN_HINT_ID
    assert prompt_hint.TRANSLATION_ANCHOR == "translation"
    assert prompt_hint.RUSSIAN_ANCHOR == "russian"


@pytest.mark.parametrize(
    "call",
    [
        lambda: prompt_hint.hint_div(FIELD, unless_field="X"),
        lambda: prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD, unless_field="X"),
    ],
)
def test_the_removed_unless_field_parameter_is_rejected(call):
    with pytest.raises(TypeError):
        call()


def test_the_current_call_shape_is_accepted():
    assert prompt_hint.hint_div(FIELD)
    assert prompt_hint.add_prompt_hint(PROMPT_SIDE, FIELD)


def _card_indices(sheet):
    return range(4) if sheet == "Verbs" else range(2)


@pytest.mark.parametrize(
    "sheet,card_index",
    [(sheet, i) for sheet in FIELD_NAMES for i in _card_indices(sheet)],
)
def test_the_hint_rides_the_prompt_and_never_an_answer(sheet, card_index):
    qfmt, afmt = build_template(sheet, card_index)
    marker = f'id="{prompt_hint.PROMPT_HINT_ID}"'
    english_prompt = 'id="translation"' in qfmt
    assert (marker in qfmt) == english_prompt
    assert afmt.count(marker) == (0 if english_prompt else 1)


@pytest.mark.parametrize("sheet", list(FIELD_NAMES))
def test_every_sheet_has_a_recall_card_carrying_the_hint(sheet):
    carried = [
        i
        for i in _card_indices(sheet)
        if f'id="{prompt_hint.PROMPT_HINT_ID}"' in build_template(sheet, i)[0]
    ]
    assert carried
    assert FIELD in FIELD_NAMES[sheet]
