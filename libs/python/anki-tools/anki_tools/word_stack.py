"""Vertical rhythm for the word stack: the headword, its translation, and --
on Verbs -- the counterpart-aspect line beneath them.

The cloned reference note type separates `#front` from `#back` with a 10px
bottom margin. On every card whose word and translation straddle that
boundary -- which is all of them, in both families -- that margin lands
*between* a word and its own gloss, so the pair reads as two blocks rather
than one stack. Zeroing it lets `#russian`/`#translation`'s own padding set
the spacing, evenly, for every line in the stack.

Appended to both families' CSS at the same point, so the two trees keep
identical base rules.

Pure text -- no Anki imports.
"""

WORD_STACK_CSS = (
    "#front {\n"
    "\tmargin-bottom: 0;\n"
    "}\n\n"
    "#russian, #translation {\n"
    "\tpadding: .15rem 0;\n"
    "\tline-height: 1.25;\n"
    "}"
)
