"""The `Examples` field shared by the Immutable and Mutable Russian note types.

Standalone Russian usage examples live here, not in `Translation` or inline in
`Additional Info`. Rendered through the same `addTitle` detail block as
`Additional Info`, and nothing at all when empty. Pure text -- no Anki imports.
"""

import re

EXAMPLES_FIELD = "Examples"
EXAMPLES_ID = "examples"

EXAMPLES_CSS = (
    "#examples {\n"
    "\tpadding: 5px 0;\n"
    "\tdisplay: inline-flex;\n"
    "\ttext-align: left;\n"
    "\twidth: 100%;\n"
    "\tword-break: break-word;\n"
    "\thyphens: auto;\n"
    "\talign-items: start;\n"
    "}\n\n"
    "#examples .title {\n"
    "\tfont-size: 1.2rem;\n"
    "\tdisplay: inline-flex;\n"
    "\tcolor: #656565;\n"
    "}\n\n"
    "#examples .body {\n"
    "\tfont-size: 1.2rem;\n"
    "\tcolor: #656565;\n"
    "\tpadding-top: 2px;\n"
    "}"
)

_INFO_DIV = re.compile(
    r'^([ \t]*)<div id="additional-info">\{\{Additional Info\}\}</div>[ \t]*$', re.M
)
_INFO_TITLE_CALL = re.compile(
    r'^([ \t]*)addTitle\("additional-info", "&#9432;"\);[ \t]*$', re.M
)


def add_examples_block(template_html: str) -> str:
    """Add the `Examples` div and its `addTitle` call after `Additional Info`'s.

    Returns the template unchanged when it lacks either the `additional-info`
    div or its `addTitle` call (the sides that never render it), or already
    carries an `examples` div. Idempotent.
    """
    if f'id="{EXAMPLES_ID}"' in template_html:
        return template_html
    if not (_INFO_DIV.search(template_html) and _INFO_TITLE_CALL.search(template_html)):
        return template_html
    with_div = _INFO_DIV.sub(
        lambda m: (
            f'{m.group(0)}\n{m.group(1)}<div id="{EXAMPLES_ID}">'
            f"{{{{{EXAMPLES_FIELD}}}}}</div>"
        ),
        template_html,
    )
    return _INFO_TITLE_CALL.sub(
        lambda m: (
            f'{m.group(0)}\n{m.group(1)}addTitle("{EXAMPLES_ID}", "{EXAMPLES_FIELD}");'
        ),
        with_div,
    )
