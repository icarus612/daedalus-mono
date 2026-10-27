"""The grammatical hint shown beside an English prompt on a recall card.

A recall card asks for the Russian word from its English gloss, and 143
English senses in these decks are produced by two or more different Russian
words -- "about" is both `о / об` and `насчёт`, "which" is both `какой` and
`который`. With the gloss alone there is nothing to choose by.

What separates them is already stored, in a real field, already populated:
`Case` on a preposition (Prepositional vs Genitive), `Pronoun Type` on a
pronoun (interrogative vs relative), `Case / Preposition` on a verb. Every
one of those fields rendered only on the ANSWER side, where the choice has
already been made. This module puts it on the question side instead.

Nothing is written into the gloss text. The hint is the field, wrapped by
Anki's own `{{#Field}}` conditional so an empty field renders nothing at
all rather than an empty pair of brackets -- the same "real field, grey, in
parens when non-empty" shape `case_field` uses, rather than a parenthetical
baked into the stored text.

Pure text -- no Anki imports.
"""

import re

PROMPT_HINT_ID = "prompt-hint"

# Matches `.qualifier`'s grey and `#case`'s sizing, so the hint reads as
# secondary to the prompt it sits under rather than as part of the answer.
PROMPT_HINT_CSS = (
    "#prompt-hint {\n"
    "\ttext-align: center;\n"
    "\tfont-size: 1.2rem;\n"
    "\tcolor: #7f7f7f;\n"
    "\tpadding-top: .2rem;\n"
    "}"
)

_TRANSLATION_DIV = re.compile(
    r'(<div[^>]*\bid=["\']translation["\'][^>]*>.*?</div>)', re.S
)


def hint_div(field_name: str) -> str:
    """The hint element for `field_name`, empty-safe.

    `{{#Field}}...{{/Field}}` is Anki's own conditional: the parentheses
    exist only when the field does, so a preposition with no recorded case
    shows nothing instead of "()".
    """
    return (
        f'<div id="{PROMPT_HINT_ID}">'
        f"{{{{#{field_name}}}}}({{{{{field_name}}}}}){{{{/{field_name}}}}}"
        "</div>"
    )


def add_prompt_hint(template_html: str, field_name: str) -> str:
    """Insert the hint straight after the `#translation` div.

    Returns the template unchanged when it shows no translation (a listening
    card's question, or any answer side) or already carries the hint, so
    applying this to every side of every template is safe. Idempotent.
    """
    if f'id="{PROMPT_HINT_ID}"' in template_html:
        return template_html
    if not _TRANSLATION_DIV.search(template_html):
        return template_html
    return _TRANSLATION_DIV.sub(
        lambda m: m.group(1) + "\n" + hint_div(field_name), template_html, count=1
    )
