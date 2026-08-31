"""Pure core for `anki-immutable-words`.

Turns the Russian invariable-words source document into the note rows and deck
names that make up `Languages::Russian::2. Immutable Words`, and derives the new
note type's templates from an existing one. Everything here is plain text and
data manipulation - no Anki imports, no collection access, no filesystem access.
`anki_tools/immutable_words.py` is the only caller and owns all Anki plumbing.

The run this serves is create-only: nothing here matches against, moves, or
otherwise reads existing notes. Each source row becomes exactly one new note.

Also covers the audio-playback rewrite: Anki's backend autoplays every
`[sound:...]` tag found in a field, all of them, in document order, before any
template JavaScript runs - so a field holding three `[sound:...]` tags plays
all three back to back and template JS cannot suppress or reorder that queue.
To get "one of three recordings, chosen at random, per render" the `Audio`
field instead holds a plain-text, comma/newline-separated list of bare media
filenames (never `[sound:...]` tags), and `rewrite_audio_playback` rewrites the
template side that renders that field so its own JavaScript does the picking
and playing.
"""

import re
from dataclasses import dataclass

# Deck the four part-of-speech subdecks hang off. The `2. ` prefix is the user's
# choice; they renumber the sibling Russian decks themselves.
DECK_ROOT = "Languages::Russian::2. Immutable Words"

# Source-document section heading (the English part, before the Russian gloss)
# -> the subdeck leaf name. Order here is the document's order and fixes the
# `a.`/`b.`/`c.`/`d.` prefixes below. Names are plural by explicit instruction.
SUBDECK_LEAVES = {
    "Prepositions": "Prepositions",
    "Conjunctions": "Conjunctions",
    "Particles": "Particles",
    "Indeclinable Nouns": "Indeclinable Nouns",
}

# Field order of the note type, cloned from the source note type. `Part of
# Speech` is still populated (it is useful in the browser's search) but is no
# longer rendered on either side of the card - the deck name carries it instead.
FIELD_NAMES = (
    "Russian",
    "Translation",
    "Pronunciation",
    "Part of Speech",
    "Audio",
    "Additional Info",
)

# The singular part-of-speech value written into the `Part of Speech` field,
# keyed by the same section heading as SUBDECK_LEAVES.
POS_FIELD_VALUE = {
    "Prepositions": "preposition",
    "Conjunctions": "conjunction",
    "Particles": "particle",
    "Indeclinable Nouns": "indeclinable noun",
}

# A markdown table row: | rank | russian | english |
_TABLE_ROW = re.compile(r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", re.M)

# A `### Heading` section break in the source document.
_SECTION = re.compile(r"^###\s+(.+?)\s*$", re.M)

# The one element both templates use to show the part of speech. Matched
# tolerantly (any attribute order, any inner whitespace) because it is being
# removed from a hand-written template, not from generated markup.
_POS_DIV = re.compile(
    r"^[ \t]*<div[^>]*\bid=[\"']part-of-speech[\"'][^>]*>.*?</div>[ \t]*\r?\n?",
    re.M | re.S,
)

# The element both audio-rendering template sides use. Matched with the same
# tolerance as _POS_DIV: any attribute order, any inner whitespace, since it
# too comes from hand-written markup.
_AUDIO_DIV = re.compile(
    r"^[ \t]*<div[^>]*\bid=[\"']audio[\"'][^>]*>\s*\{\{Audio\}\}\s*</div>[ \t]*\r?\n?",
    re.M | re.S,
)


class SourceDocumentError(Exception):
    """The source document did not contain the expected four word-list sections."""


@dataclass(frozen=True)
class WordRow:
    pos: str  # section heading, e.g. "Prepositions" - a SUBDECK_LEAVES key
    rank: int  # the source table's rank column, kept for stable ordering
    russian: str  # the Russian text, verbatim from the document
    english: str  # the English gloss, verbatim from the document

    @property
    def deck(self) -> str:
        """Full `::` deck path this row's note belongs in."""
        return subdeck_name(self.pos)

    def fields(self) -> list[str]:
        """The six field values, in FIELD_NAMES order.

        `Pronunciation`, `Audio` and `Additional Info` are left empty; audio is
        a separate, later step.
        """
        return [
            self.russian,
            self.english,
            "",
            POS_FIELD_VALUE[self.pos],
            "",
            "",
        ]


def subdeck_name(pos: str, root: str = DECK_ROOT) -> str:
    """Full deck path for a part of speech, e.g. `...::a. Prepositions`.

    The `<letter>. ` prefix is load-bearing, not decorative: both card templates
    build their header with `deckName.split(". ")[1]`, so a leaf without a
    `". "` in it renders as `Russian - undefined`.
    """
    if pos not in SUBDECK_LEAVES:
        raise SourceDocumentError(f"unknown part of speech: {pos!r}")
    letter = "abcdefghijklmnopqrstuvwxyz"[list(SUBDECK_LEAVES).index(pos)]
    return f"{root}::{letter}. {SUBDECK_LEAVES[pos]}"


def all_subdeck_names(root: str = DECK_ROOT) -> list[str]:
    """Every subdeck path, in document order."""
    return [subdeck_name(pos, root) for pos in SUBDECK_LEAVES]


def parse_word_list(text: str) -> list[WordRow]:
    """Parse Part 1 of the source document into rows, in document order.

    Only the four sections named in SUBDECK_LEAVES are read; Part 2 of the
    document (the text-to-speech add-on guide) has no tables and is ignored.
    """
    sections = list(_SECTION.finditer(text))
    if not sections:
        raise SourceDocumentError("no '### ' sections found in the source document")

    rows: list[WordRow] = []
    seen: set[str] = set()
    for i, match in enumerate(sections):
        # The English part of e.g. "Prepositions (Предлоги)".
        heading = match.group(1).split(" (")[0].strip()
        if heading not in SUBDECK_LEAVES:
            continue
        end = sections[i + 1].start() if i + 1 < len(sections) else len(text)
        body = text[match.end() : end]
        seen.add(heading)
        for rank, russian, english in _TABLE_ROW.findall(body):
            rows.append(
                WordRow(
                    pos=heading,
                    rank=int(rank),
                    russian=russian.strip(),
                    english=english.strip(),
                )
            )

    missing = set(SUBDECK_LEAVES) - seen
    if missing:
        raise SourceDocumentError(
            f"source document is missing section(s): {sorted(missing)}"
        )
    if not rows:
        raise SourceDocumentError("source document sections contained no table rows")
    return rows


def strip_part_of_speech(template_html: str) -> str:
    """Remove the part-of-speech element from one side of a card template.

    Returns the template unchanged when it has no such element - Card 1's answer
    side and Card 2's question side legitimately don't. Idempotent: once removed,
    the pattern no longer matches, so a second pass is a no-op.
    """
    return _POS_DIV.sub("", template_html)


def rewrite_audio_playback(template_html: str) -> str:
    """Rewrite the `{{Audio}}`-rendering element into a JS-driven random player.

    Anki autoplays every `[sound:...]` tag in a field, in order, before any
    template JavaScript runs, so the `Audio` field can never hold `[sound:...]`
    tags if only one of several recordings should play. Instead the field holds
    a plain-text, comma/newline-separated list of bare media filenames, and this
    rewrite replaces the literal `<div id="audio">{{Audio}}</div>` block with:

    - the same `{{Audio}}` field reference, still present (so Anki still fills
      it in), but now wrapped in an element carrying the note type's own
      existing `.hidden` class (`display: none !important`) so it is never
      shown as raw text; and
    - a `<script>` block that reads that hidden text, splits it into filenames,
      degrades to doing nothing at all when the list is empty (every note this
      lane creates ships with an empty `Audio` field), and otherwise picks one
      filename at random and plays it via an autoplaying `<audio>` element plus
      a visible replay `<button>`.

    Returns the template unchanged when it has no such element - two of the
    four template sides legitimately don't render `{{Audio}}` at all. Idempotent:
    once rewritten, the literal `<div id="audio">{{Audio}}</div>` pattern no
    longer matches, so a second pass is a no-op.
    """
    if not _AUDIO_DIV.search(template_html):
        return template_html

    replacement = (
        "<!-- Audio field holds a plain-text, comma/newline-separated list of\n"
        "     bare media filenames -- it is NOT wrapped in Anki's own sound-tag\n"
        "     syntax. Anki's backend autoplays every sound-tagged reference in\n"
        "     a field, in order, before any template JS runs, so three tagged\n"
        "     recordings would play back to back with no way for JS to\n"
        "     suppress or reorder that queue. Keeping the field as plain text\n"
        "     lets the script below pick and play just one. The script also\n"
        "     renders a <button> so the native R-key replay isn't simply\n"
        "     lost. -->\n"
        '<div id="audio"><span id="audio-data" class="hidden">{{Audio}}</span>'
        '<span id="audio-controls"></span></div>\n'
        "<script>\n"
        "(function () {\n"
        '  var data = document.getElementById("audio-data");\n'
        "  if (!data) return;\n"
        "  var text = data.textContent.trim();\n"
        "  if (!text) return;\n"
        "  var files = text\n"
        "    .split(/[,\\n]+/)\n"
        "    .map(function (f) { return f.trim(); })\n"
        "    .filter(function (f) { return f.length > 0; });\n"
        "  if (files.length === 0) return;\n"
        "  var chosen = files[Math.floor(Math.random() * files.length)];\n"
        '  var container = document.getElementById("audio");\n'
        '  var audio = document.createElement("audio");\n'
        "  audio.autoplay = true;\n"
        "  audio.src = chosen;\n"
        '  var button = document.createElement("button");\n'
        '  button.textContent = "\\u25b6";\n'
        '  button.addEventListener("click", function () {\n'
        "    audio.currentTime = 0;\n"
        "    audio.play();\n"
        "  });\n"
        "  container.appendChild(audio);\n"
        "  container.appendChild(button);\n"
        "})();\n"
        "</script>\n"
    )
    # A plain string replacement (not a lambda) would have re.sub interpret the
    # JS source's own backslash escapes (\n, ▶, ...) as regex template
    # backreferences, so pass it through a callable instead.
    return _AUDIO_DIV.sub(lambda _match: replacement, template_html)


def counts_by_deck(rows: list[WordRow]) -> dict[str, int]:
    """Note count per deck path, in document order. Cards are twice this."""
    counts: dict[str, int] = {name: 0 for name in all_subdeck_names()}
    for row in rows:
        counts[row.deck] += 1
    return counts
