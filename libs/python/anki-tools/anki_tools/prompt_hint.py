"""The grammatical hint shown beside a word on a card.

A recall card asks for the Russian word from its English gloss, and 143
English senses in these decks are produced by two or more different Russian
words -- "about" is both `о / об` and `насчёт`, "which" is both `какой` and
`который`. With the gloss alone there is nothing to choose by. The mirror
problem sits on the other side: one spelling, two parts of speech -- `как`
is both a conjunction and an adverb -- so the headword alone does not say
which card is being asked for either.

What separates them is already stored, in real fields, already populated:
`English Distinction` and `Russian Distinction` on both note-type families.
Every one of those fields rendered only where the choice had already been
made. This module puts each one beside the word it disambiguates.

Nothing is written into the gloss text. The hint is the field, wrapped by
Anki's own `{{#Field}}` conditional so an empty field renders nothing at
all rather than an empty pair of brackets.

Pure text -- no Anki imports.
"""

import re

PROMPT_HINT_ID = "prompt-hint"
RUSSIAN_HINT_ID = "russian-distinction"

TRANSLATION_ANCHOR = "translation"
RUSSIAN_ANCHOR = "russian"

HINT_IDS = (PROMPT_HINT_ID, RUSSIAN_HINT_ID)

CUE_ROW_CLASS = "cue-row"
CUE_ROW_OPEN = f'<div class="{CUE_ROW_CLASS}">'

# One div per line: the word (with any aspect span inside it) and its hint are
# sibling spans. The line spans the screen less 9px each side, whatever the
# card's own padding. The hint takes its own line only when the word field
# itself is multi-line; otherwise it wraps as one unit, never mid-phrase.
PROMPT_HINT_CSS = (
    f".{CUE_ROW_CLASS} {{\n"
    "\ttext-align: center;\n"
    "\tbox-sizing: border-box;\n"
    "\twidth: calc(100vw - 18px);\n"
    "\tmargin-left: calc(50% - 50vw + 9px);\n"
    "}\n\n" + ", ".join(f"#{hint_id}" for hint_id in HINT_IDS) + " {\n"
    "\tdisplay: inline-block;\n"
    "\tvertical-align: middle;\n"
    "\tfont-size: 1.2rem;\n"
    "\tcolor: #7f7f7f;\n"
    "}\n\n" + ", ".join(f"#{hint_id}:empty" for hint_id in HINT_IDS) + " {\n"
    "\tdisplay: none;\n"
    "}\n\n"
    + ", ".join(
        f"#{anchor}:has({tag}) ~ #{hint_id}:not(:empty)"
        for anchor, hint_id in (
            (TRANSLATION_ANCHOR, PROMPT_HINT_ID),
            (RUSSIAN_ANCHOR, RUSSIAN_HINT_ID),
        )
        for tag in ("br", "div")
    )
    + " {\n"
    "\tdisplay: block;\n"
    "}"
)


def _anchor_pattern(anchor_id: str) -> re.Pattern[str]:
    return re.compile(
        rf'(<(div|span)[^>]*\bid=["\']{re.escape(anchor_id)}["\'][^>]*>.*?</\2>)', re.S
    )


# The pattern demands the closing quote right after the anchor name, so an
# already-inserted `id="russian-distinction"` is never read as `#russian`.
_ANCHORS = {
    anchor: _anchor_pattern(anchor) for anchor in (TRANSLATION_ANCHOR, RUSSIAN_ANCHOR)
}


def _as_span(element_html: str) -> str:
    if not element_html.startswith("<div"):
        return element_html
    return "<span" + element_html[len("<div") : -len("</div>")] + "</span>"


def hint_div(field_name: str, element_id: str = PROMPT_HINT_ID) -> str:
    """The hint element for `field_name`, empty-safe.

    `{{#Field}}...{{/Field}}` is Anki's own conditional: the parentheses
    exist only when the field does, so an empty field shows nothing
    instead of "()".
    """
    body = f"{{{{#{field_name}}}}}({{{{{field_name}}}}}){{{{/{field_name}}}}}"
    return f'<span id="{element_id}">{body}</span>'


def add_prompt_hint(
    template_html: str,
    field_name: str,
    element_id: str = PROMPT_HINT_ID,
    anchor_id: str = TRANSLATION_ANCHOR,
) -> str:
    """Insert the hint straight after the `#<anchor_id>` div, both wrapped in one
    `.cue-row` so the hint sits beside the word.

    Returns the template unchanged when that div is absent -- a listening
    card's question shows no translation, a recall card's question shows no
    headword -- or when `element_id` is already present, so applying this to
    every side of every template is safe. Idempotent.

    Two calls sharing one anchor stack in reverse call order: each lands
    immediately after the anchor and pushes the earlier one down.
    """
    if f'id="{element_id}"' in template_html:
        return template_html
    anchor = _ANCHORS.get(anchor_id) or _anchor_pattern(anchor_id)
    match = anchor.search(template_html)
    if match is None:
        return template_html
    start, end = match.span(1)
    hint = hint_div(field_name, element_id)
    if template_html[:start].endswith(CUE_ROW_OPEN):
        return template_html[:end] + "\n" + hint + template_html[end:]
    return (
        template_html[:start]
        + CUE_ROW_OPEN
        + _as_span(match.group(1))
        + "\n"
        + hint
        + "</div>"
        + template_html[end:]
    )
