"""Case pills: the six cases as a row, with the governed ones lit.

The `Case` field holds the governed case names ("Accusative, Prepositional");
the card renders all six pills hidden and CSS shows the ones the field names.
Multi-case words also tint each meaning line in the colour of its case.

Pure text -- no Anki imports.
"""

import re
from collections.abc import Mapping

from anki_tools.case_field import CASE_NAMES

PILL_WRAPPER_CLASS = "case-pills"
PROMPT_HINT_ANCHOR = "prompt-hint"

CASE_ORDER = tuple(full for full, _ in CASE_NAMES)

_CASE_FIELD = "Case"
_TEXT_CLASS = "case-text"

# name -> (light text, light background, dark text, dark background)
_PALETTE = {
    "Nominative": ("#616161", "#eeeeee", "#bdbdbd", "#3a3a3a"),
    "Genitive": ("#c62828", "#fdecea", "#ef9a9a", "#4a2c2c"),
    "Dative": ("#2e7d32", "#e8f5e9", "#a5d6a7", "#2c4030"),
    "Accusative": ("#1565c0", "#e3f2fd", "#90caf9", "#2a3a4d"),
    "Instrumental": ("#c43e00", "#fff3e0", "#ffb74d", "#4d3a1f"),
    "Prepositional": ("#6a1b9a", "#f3e5f5", "#ce93d8", "#40304a"),
}


def case_slug(name: str) -> str:
    """`Genitive` -> `genitive`."""
    return name.lower()


def pill_block() -> str:
    """The template block: six pills in a wrapper rendered only when `Case` is set."""
    pills = "".join(
        f'<span class="case-pill case-{case_slug(name)}">{name}</span>'
        for name in CASE_ORDER
    )
    return (
        f"{{{{#{_CASE_FIELD}}}}}"
        f'<div class="{PILL_WRAPPER_CLASS}" data-case="{{{{text:{_CASE_FIELD}}}}}">'
        f"{pills}</div>"
        f"{{{{/{_CASE_FIELD}}}}}"
    )


def _anchor_pattern(anchor_id: str) -> re.Pattern[str]:
    return re.compile(
        rf'(<div[^>]*\bid=["\']{re.escape(anchor_id)}["\'][^>]*>.*?</div>)', re.S
    )


def add_pill_block(template_html: str, anchor_id: str = PROMPT_HINT_ANCHOR) -> str:
    """Insert the pill block on its own line right after the anchor div.

    Returns the template unchanged when the anchor is absent or the block is
    already present. Idempotent.
    """
    if f'class="{PILL_WRAPPER_CLASS}"' in template_html:
        return template_html
    block = pill_block()
    return _anchor_pattern(anchor_id).sub(
        lambda match: f"{match.group(1)}\n{block}", template_html, count=1
    )


def _css() -> str:
    rules = [
        ".case-pills {\n\ttext-align: center;\n\tpadding-top: .2rem;\n}",
        ".case-pill {\n"
        "\tdisplay: none;\n"
        "\tpadding: .1rem .6rem;\n"
        "\tmargin: 0 .15rem;\n"
        "\tborder-radius: 999px;\n"
        "\tfont-size: .85rem;\n"
        "\tfont-weight: bold;\n"
        "}",
    ]
    for name in CASE_ORDER:
        rules.append(
            f'.case-pills[data-case*="{name}" i] .case-{case_slug(name)} {{\n'
            "\tdisplay: inline-block;\n}"
        )
    for name in CASE_ORDER:
        text, background, _, _ = _PALETTE[name]
        slug = case_slug(name)
        rules.append(
            f".case-pill.case-{slug} {{\n"
            f"\tcolor: {text};\n\tbackground: {background};\n}}"
        )
        rules.append(f".{_TEXT_CLASS}.case-{slug} {{\n\tcolor: {text};\n}}")
    for name in CASE_ORDER:
        _, _, text, background = _PALETTE[name]
        slug = case_slug(name)
        rules.append(
            f".nightMode .case-pill.case-{slug} {{\n"
            f"\tcolor: {text};\n\tbackground: {background};\n}}"
        )
        rules.append(f".nightMode .{_TEXT_CLASS}.case-{slug} {{\n\tcolor: {text};\n}}")
    return "\n\n".join(rules)


CASE_PILL_CSS = _css()

_LINE_SEPARATOR = re.compile(r"(<br\s*/?>|</?div\b[^>]*>)", re.I)


def tint_lines(translation: str, mapping: Mapping[str, str]) -> str:
    """Wrap each translation line named in `mapping` in a span of its case's colour.

    Lines are the text between `<br>` and `<div>` boundaries; only the text is
    wrapped, so removing every tag yields the input's text unchanged.
    """
    for case in mapping.values():
        if case not in CASE_ORDER:
            raise ValueError(f"not a canonical case name: {case!r}")
    if not mapping:
        return translation

    parts = _LINE_SEPARATOR.split(translation)
    for index in range(0, len(parts), 2):
        segment = parts[index]
        case = mapping.get(segment.strip())
        if case is None:
            continue
        text = segment.strip()
        start = segment.index(text)
        parts[index] = (
            f"{segment[:start]}"
            f'<span class="{_TEXT_CLASS} case-{case_slug(case)}">{text}</span>'
            f"{segment[start + len(text) :]}"
        )
    return "".join(parts)
