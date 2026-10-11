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
    "\tfont-size: 20px;\n"
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

# The English side, matched the same way. `{{Translation}}` sits on its own
# indented lines in the hand-written template, so `\s*` has to span newlines.
_TRANSLATION_DIV = re.compile(
    r'([ \t]*)<div[^>]*\bid=["\']translation["\'][^>]*>\s*'
    r'\{\{Translation\}\}\s*</div>'
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


# Everything the `Case` tag already carries. What survives its removal is the
# only part `Additional Info` still has to say.
_CASE_WORDS = re.compile("|".join(full for full, _ in CASE_ABBREVIATIONS), re.I)
_ONLY_FILLER = re.compile(
    r"^[\s;,/()&.\u2013\u2014-]*(?:and|or)?[\s;,/()&.\u2013\u2014-]*$", re.I
)


def residual_info(info: str) -> str:
    """What `Additional Info` should still say once `Case` renders the case.

    A cell that names the case and NOTHING else is wholly redundant with the
    inline tag -- "Prepositional" under `о / об (+ prep.)` states the same
    fact twice -- so it reduces to "". A cell that also says WHEN each case
    applies ("Accusative for motion in; Prepositional for location") keeps
    its wording, because the tag can only list the cases, never choose
    between them. Dash commentary is always kept.
    """
    parts = _COMMENTARY.split(info, maxsplit=1)
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    kept = "" if _ONLY_FILLER.match(_CASE_WORDS.sub("", head)) else head.strip()
    return "; ".join(p for p in (kept, tail.strip()) if p)


def residual_info_for_row(pos: str, info: str) -> str:
    """`residual_info` for a governing section's row, `info` for every other."""
    return residual_info(info) if pos == GOVERNING_SECTION else info


def add_case_tag(template_html: str) -> str:
    """Render `Case` inline beside the ENGLISH, on every side that shows it.

    The case rides with the English and never with the Russian. On the
    English-prompt side that is the only thing that makes the prompt
    answerable: `about` alone cannot distinguish `о / об` from `насчёт`,
    nor `before` `до` from `перед`, but `about (+ prep.)` and
    `about (+ gen.)` each name exactly one preposition. Beside the Russian
    it would be pure restatement -- the word is already shown, and on the
    Russian-prompt side the case is something to recall, not be handed.

    Wrapped in `{{#Case}}`/`{{/Case}}` so a row without a case renders
    neither the span nor its leading space. Returns the template unchanged
    when it shows no translation, or already carries the tag. Idempotent.
    """
    if f'class="{CASE_CLASS}"' in template_html:
        return template_html
    return _TRANSLATION_DIV.sub(
        lambda m: (
            f'{m.group(1)}<div id="translation">{{{{Translation}}}}'
            f"{{{{#{CASE_FIELD}}}}}"
            f' <span class="{CASE_CLASS}">{{{{{CASE_FIELD}}}}}</span>'
            f"{{{{/{CASE_FIELD}}}}}</div>"
        ),
        template_html,
    )
