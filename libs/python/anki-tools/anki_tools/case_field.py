"""The `Case` field: the grammatical case a Russian preposition governs.

Rendered as its own labelled row on the answer side, through the same
`addTitle` block every other grammar fact uses -- `Case / Preposition` on
Verbs, `Case Governed` on Numerals, `Gender` and `Plural` on Nouns. The field
holds the case NAME alone; the template decides how it is presented.

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
CASE_ID = "case"

GOVERNING_SECTION = "Prepositions"

# The same row layout the Mutable note types give every grammar field via
# `mutable_words_plan.EXTRA_CSS`, so a `Case` row on a preposition reads
# identically to `Case / Preposition` on a verb. The Immutable note type is
# cloned from a source that has no field of its own to model this on.
CASE_CSS = (
    "#case {\n"
    "\tpadding: 5px 0;\n"
    "\tdisplay: inline-flex;\n"
    "\ttext-align: left;\n"
    "\twidth: 100%;\n"
    "\tword-break: break-word;\n"
    "\thyphens: auto;\n"
    "\talign-items: start;\n"
    "}\n\n"
    "#case .title {\n"
    "\tfont-size: 1.2rem;\n"
    "\tdisplay: inline-flex;\n"
    "\tcolor: #656565;\n"
    "}\n\n"
    "#case .body {\n"
    "\tfont-size: 1.2rem;\n"
    "\tcolor: #656565;\n"
    "\tpadding-top: 2px;\n"
    "}"
)


# Spelled out, never abbreviated: "prep." is reference-book shorthand that
# also looks like "preposition" -- the one thing it does not mean.
CASE_NAMES = (
    ("Nominative", "Nominative"),
    ("Genitive", "Genitive"),
    ("Dative", "Dative"),
    ("Accusative", "Accusative"),
    ("Instrumental", "Instrumental"),
    ("Prepositional", "Prepositional"),
)

# A dash clause is editorial commentary, not a second governed case:
# `вопреки`'s "Dative -- one of the few Genitive-looking ones that takes
# Dative" governs the dative ALONE, and reading the whole cell yields a
# wrong "Dative or Genitive".
_COMMENTARY = re.compile(r"\s+[—–-]\s+")

_INFO_DIV = re.compile(
    r'^([ \t]*)<div id="additional-info">\{\{Additional Info\}\}</div>[ \t]*$', re.M
)
_INFO_TITLE_CALL = re.compile(
    r'^([ \t]*)addTitle\("additional-info", "&#9432;"\);[ \t]*$', re.M
)


def case_name(info: str) -> str:
    """The governed case named by an `Info` cell, e.g. `Accusative or Prepositional`.

    Cases appear in the order the cell names them, so a two-case preposition
    reads the way the document writes it (`в / во` -> `Accusative or
    Prepositional`, never the table's own order).
    """
    governed = _COMMENTARY.split(info, maxsplit=1)[0]
    found = [
        (match.start(), name)
        for full, name in CASE_NAMES
        if (match := re.search(full, governed, re.I))
    ]
    if not found:
        return ""
    return " or ".join(name for _, name in sorted(found))


def case_name_for_row(pos: str, info: str) -> str:
    """`case_name(info)` for a governing section's row, `""` for every other."""
    return case_name(info) if pos == GOVERNING_SECTION else ""


# Everything the `Case` field already carries. What survives its removal is
# the only part `Additional Info` still has to say.
_CASE_WORDS = re.compile("|".join(full for full, _ in CASE_NAMES), re.I)
_ONLY_FILLER = re.compile(
    r"^[\s;,/()&.–—-]*(?:and|or)?[\s;,/()&.–—-]*$", re.I
)


def residual_info(info: str) -> str:
    """What `Additional Info` should still say once `Case` renders the case.

    A cell that names the case and NOTHING else is wholly redundant with the
    `Case` row -- "Prepositional" under `о / об` states the same fact twice --
    so it reduces to "". A cell that also says WHEN each case applies
    ("Accusative for motion in; Prepositional for location") keeps its
    wording, because the field can only list the cases, never choose between
    them. Dash commentary is always kept.
    """
    parts = _COMMENTARY.split(info, maxsplit=1)
    head = parts[0]
    tail = parts[1] if len(parts) > 1 else ""
    kept = "" if _ONLY_FILLER.match(_CASE_WORDS.sub("", head)) else head.strip()
    return "; ".join(p for p in (kept, tail.strip()) if p)


def residual_info_for_row(pos: str, info: str) -> str:
    """`residual_info` for a governing section's row, `info` for every other."""
    return residual_info(info) if pos == GOVERNING_SECTION else info


def add_case_row(template_html: str) -> str:
    """Add the `Case` div and its `addTitle` call above `Additional Info`'s.

    Grammar rows come before the `&#9432;` detail block and `Examples`, which
    is the order Verbs and Numerals already render theirs in. Returns the
    template unchanged when it lacks either the `additional-info` div or its
    `addTitle` call (the sides that never render it), or already carries a
    `case` div. Idempotent.
    """
    if f'id="{CASE_ID}"' in template_html:
        return template_html
    if not (_INFO_DIV.search(template_html) and _INFO_TITLE_CALL.search(template_html)):
        return template_html
    with_div = _INFO_DIV.sub(
        lambda m: (
            f'{m.group(1)}<div id="{CASE_ID}">{{{{{CASE_FIELD}}}}}</div>\n'
            f"{m.group(0)}"
        ),
        template_html,
    )
    return _INFO_TITLE_CALL.sub(
        lambda m: (
            f'{m.group(1)}addTitle("{CASE_ID}", "{CASE_FIELD}");\n{m.group(0)}'
        ),
        with_div,
    )
