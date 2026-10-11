"""Display styling for a headword's editorial qualifier.

Three words in the Immutable document (`как`, `когда`, `пока`) and the two
`правда` senses carry a trailing parenthetical in their `Russian` text --
"когда (conjunction)" -- so the cards for one spelling are told apart on
sight. That qualifier is EDITORIAL: `audio_naming.strip_qualifier` keeps it
out of filenames and TTS text, and it must read as secondary on the card too.

It cannot be styled by CSS alone. The qualifier is part of the field's TEXT,
not an element, and the field text is load-bearing -- `guid_for_row` hashes
it and `build_filename` derives the media name from it -- so wrapping it in
markup at build time is not an option. This script does the wrapping in the
rendered DOM instead, touching nothing that is stored.

Pure text -- no Anki imports.
"""

import re

QUALIFIER_CLASS = "qualifier"

# 0.5em against `#russian`'s own 2.2rem lands near `#part-of-speech`'s
# 1.2rem -- clearly secondary to the headword rather than competing with it.
QUALIFIER_CSS = (
    ".qualifier {\n"
    "\tfont-size: 20px;\n"
    "\tcolor: #7f7f7f;\n"
    "\twhite-space: nowrap;\n"
    "}"
)

# Anchored to the end, so a `#russian` that already ends in the `Case`
# span's own element is left alone rather than double-wrapped.
QUALIFIER_SCRIPT = """<script>
(function () {
\tvar el = document.getElementById("russian");
\tif (!el || el.querySelector(".qualifier")) return;
\tvar m = el.innerHTML.match(/^([\\s\\S]*\\S)(\\s*\\([^()]*\\))\\s*$/);
\tif (m) {
\t\tel.innerHTML = m[1] + ' <span class="qualifier">' + m[2].trim() + "</span>";
\t}
})();
</script>"""

_RUSSIAN_DIV = re.compile(r'<div[^>]*\bid=["\']russian["\']')


def add_qualifier_script(template_html: str) -> str:
    """Append the qualifier-wrapping script to a side that shows the word.

    Returns the template unchanged when it has no `russian` div (the reverse
    side's question) or already carries the script. Idempotent.
    """
    if QUALIFIER_SCRIPT in template_html:
        return template_html
    if not _RUSSIAN_DIV.search(template_html):
        return template_html
    return template_html + "\n" + QUALIFIER_SCRIPT
