"""The `Case` field: the grammatical case a Russian preposition governs.

Rendered as a compact `(+ gen.)` tag inline beside the Russian word, rather
than only as prose behind the answer side's grey info icon -- for a
preposition the governed case is part of the lemma's identity, so it belongs
where the word is, not one reveal away. The prose stays in `Additional Info`
unchanged; this is an additional, shorter presentation of the same fact.

Derived only for the Prepositions section, whose `Info` column IS the
governed case by construction ("Prepositions never change themselves, though
they dictate the case of the noun that follows them"). Other sections use
that column for unrelated notes, and a case word appearing there does not
mean the row's own word governs it -- `поздравляю`'s "often + с +
instrumental" is governed by `с`, not by `поздравляю`.

Pure text -- no Anki imports.
"""

import re

CASE_FIELD = "Case"
CASE_CLASS = "case"

GOVERNING_SECTION = "Prepositions"

CASE_CSS = (
    ".case {\n"
    "\tfont-size: 0.5em;\n"
    "\tcolor: #7f7f7f;\n"
    "\twhite-space: nowrap;\n"
    "}"
)

CASE_ABBREVIATIONS = (
    ("Nominative", "nom."),
    ("Genitive", "gen."),
    ("Dative", "dat."),
    ("Accusative", "acc."),
    ("Instrumental", "instr."),
    ("Prepositional", "prep."),
)

# A dash clause is editorial commentary, not a second governed case:
# `вопреки`'s "Dative -- one of the few Genitive-looking ones that takes
# Dative" governs the dative ALONE, and reading the whole cell yields a
# wrong "(+ dat./gen.)".
_COMMENTARY = re.compile(r"\s+[—–-]\s+")

# Matched tolerantly (any attribute order, any inner whitespace) because it
# comes from a hand-written template, like `_POS_DIV` in immutable_words_plan.
_RUSSIAN_DIV = re.compile(
    r'([ \t]*)<div[^>]*\bid=["\']russian["\'][^>]*>\s*\{\{Russian\}\}\s*</div>'
)


def case_tag(info: str) -> str:
    """The inline tag for an `Info` cell, e.g. `(+ acc./prep.)`, or `""`.

    Cases appear in the order the cell names them, so a two-case preposition
    reads the way the document writes it (`в / во` -> `(+ acc./prep.)`,
    never the abbreviation table's own order).
    """
    governed = _COMMENTARY.split(info, maxsplit=1)[0]
    found = [
        (match.start(), abbreviation)
        for full, abbreviation in CASE_ABBREVIATIONS
        if (match := re.search(full, governed, re.I))
    ]
    if not found:
        return ""
    return "(+ " + "/".join(abbreviation for _, abbreviation in sorted(found)) + ")"


def case_tag_for_row(pos: str, info: str) -> str:
    """`case_tag(info)` for a governing section's row, `""` for every other."""
    return case_tag(info) if pos == GOVERNING_SECTION else ""


def add_case_tag(template_html: str) -> str:
    """Render `Case` inline after the Russian word, when the note has one.

    Wrapped in `{{#Case}}`/`{{/Case}}` so a row without a case renders
    neither the span nor its leading space. Returns the template unchanged
    when it has no `russian` div (the reverse side's question) or already
    carries the tag. Idempotent.
    """
    if f'class="{CASE_CLASS}"' in template_html:
        return template_html
    return _RUSSIAN_DIV.sub(
        lambda m: (
            f'{m.group(1)}<div id="russian">{{{{Russian}}}}'
            f"{{{{#{CASE_FIELD}}}}}"
            f' <span class="{CASE_CLASS}">{{{{{CASE_FIELD}}}}}</span>'
            f"{{{{/{CASE_FIELD}}}}}</div>"
        ),
        template_html,
    )
