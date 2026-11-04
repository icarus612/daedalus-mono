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

# Matches `.qualifier`'s grey, so a hint reads as
# secondary to the word it sits under rather than as part of the answer.
# One rule for every hint id, appended to BOTH families' CSS at the same
# point, so the two trees keep identical base rules.
PROMPT_HINT_CSS = (
    ", ".join(f"#{hint_id}" for hint_id in HINT_IDS) + " {\n"
    "\ttext-align: center;\n"
    "\tfont-size: 1.2rem;\n"
    "\tcolor: #7f7f7f;\n"
    "\tpadding-top: .2rem;\n"
    "}"
)


def _anchor_pattern(anchor_id: str) -> re.Pattern[str]:
    return re.compile(
        rf'(<div[^>]*\bid=["\']{re.escape(anchor_id)}["\'][^>]*>.*?</div>)', re.S
    )


# The pattern demands the closing quote right after the anchor name, so an
# already-inserted `id="russian-distinction"` is never read as `#russian`.
_ANCHORS = {
    anchor: _anchor_pattern(anchor) for anchor in (TRANSLATION_ANCHOR, RUSSIAN_ANCHOR)
}


def hint_div(field_name: str, element_id: str = PROMPT_HINT_ID) -> str:
    """The hint element for `field_name`, empty-safe.

    `{{#Field}}...{{/Field}}` is Anki's own conditional: the parentheses
    exist only when the field does, so an empty field shows nothing
    instead of "()".
    """
    body = f"{{{{#{field_name}}}}}({{{{{field_name}}}}}){{{{/{field_name}}}}}"
    return f'<div id="{element_id}">{body}</div>'


def add_prompt_hint(
    template_html: str,
    field_name: str,
    element_id: str = PROMPT_HINT_ID,
    anchor_id: str = TRANSLATION_ANCHOR,
) -> str:
    """Insert the hint straight after the `#<anchor_id>` div.

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
    if not anchor.search(template_html):
        return template_html
    return anchor.sub(
        lambda m: m.group(1) + "\n" + hint_div(field_name, element_id),
        template_html,
        count=1,
    )
