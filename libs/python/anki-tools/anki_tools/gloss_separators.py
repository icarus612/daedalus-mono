"""Normalize the separators between English glosses to a single ` / `.

The English gloss fields (`English` in the source tables, `Translation` on the
note types) accumulated three separators for the same job -- `;`, `,` and `/`.
This module collapses the first two onto the third.

Only TOP-LEVEL punctuation separates glosses. A `;` or `,` inside parentheses
(`you (singular, informal)`), inside double quotes (`"once, twice..."`), or
inside an HTML tag is grammar rather than a separator and is left alone. HTML
tags and entities pass through opaquely, so the `<br>` that puts each
prepositional case on its own line survives. Pure text -- no Anki imports.
"""

import re

GLOSS_SEPARATOR = " / "

_OPAQUE = re.compile(r"<[^>]*>|&[a-zA-Z#0-9]+;")
_SEPARATORS = ";,"
_OPEN_QUOTES = '"“'
_CLOSE_QUOTES = '"”'


def normalize_gloss(text: str) -> str:
    """Replace every top-level `;` or `,` in `text` with ` / `.

    Existing `/` is never reformatted: `(what/where)` stays tight and an
    already-separated `in / at` is left as it is. Idempotent.
    """
    out: list[str] = []
    index = 0
    depth = 0
    quoted = False
    while index < len(text):
        opaque = _OPAQUE.match(text, index)
        if opaque:
            out.append(opaque.group(0))
            index = opaque.end()
            continue
        char = text[index]
        if quoted and char in _CLOSE_QUOTES:
            quoted = False
        elif not quoted and char in _OPEN_QUOTES:
            quoted = True
        elif not quoted and char == "(":
            depth += 1
        elif not quoted and char == ")":
            depth = max(0, depth - 1)
        elif not quoted and depth == 0 and char in _SEPARATORS:
            while out and out[-1].endswith(" "):
                out[-1] = out[-1][:-1]
                if not out[-1]:
                    out.pop()
            out.append(GLOSS_SEPARATOR)
            index += 1
            while index < len(text) and text[index] in " \t ":
                index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out).strip()
