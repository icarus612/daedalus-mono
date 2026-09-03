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

import hashlib
import re
from dataclasses import dataclass

from anki_tools.audio_naming import SLOTS, build_filename

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
#
# `AudioRefs` is the 7th and last field: the same four filenames as `Audio`,
# but as concatenated `[sound:...]` tags. It exists SOLELY so Anki's
# media-usage scan (export bundling, import, Tools -> Check Media) sees those
# filenames as used -- that scan reads note field TEXT DIRECTLY, independent
# of any template, whereas Anki's autoplay is triggered only by
# `[sound:...]` tags present in RENDERED template output. Because of that
# asymmetry, an unrendered field can mark media "used" without ever playing
# it, so `AudioRefs` must NEVER be referenced by any template
# (`{{AudioRefs}}`) -- rendering it would autoplay all four recordings back
# to back, the exact bug the `Audio`/random-JS split (see module docstring)
# was built to avoid. Do not "helpfully" wire it into a template.
FIELD_NAMES = (
    "Russian",
    "Translation",
    "Pronunciation",
    "Part of Speech",
    "Audio",
    "Additional Info",
    "AudioRefs",
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

# Anki's own `anki.utils.base91`/`guid64()` alphabet: `base62` (letters + digits)
# plus these extra printable-ASCII characters (every printable character except
# quotes, backslash, and Anki's own field/record separators). Reproduced here,
# not imported from `anki.utils`, to keep this module's "no Anki imports"
# invariant -- a deterministic GUID should still render in exactly the
# alphabet a genuine Anki-minted GUID would.
_GUID_ALPHABET = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "!#$%&()*+,-./:;<=>?@[]^_`{|}~"
)


def _base91(num: int) -> str:
    """Encode a non-negative int in Anki's own guid64 alphabet.

    Mirrors `anki.utils.base62`/`base91` exactly (same table, same
    algorithm), including its one sharp edge: `num == 0` encodes as the
    empty string in a naive port. Guarded explicitly here (returns the
    alphabet's first character instead) because an empty GUID is a real
    risk this function must not reproduce, however astronomically
    unlikely a zero hash is.
    """
    if num == 0:
        return _GUID_ALPHABET[0]

    base = len(_GUID_ALPHABET)
    digits: list[str] = []
    while num > 0:
        num, remainder = divmod(num, base)
        digits.append(_GUID_ALPHABET[remainder])
    return "".join(reversed(digits))


def guid_for_row(russian: str, pos: str) -> str:
    """Deterministic Anki note GUID for one source row.

    Derived from `russian` + `pos` ONLY -- never from `english`
    (Translation) or anything audio-related, both of which legitimately
    change on a rebuild and must UPDATE the existing note in place, not
    mint a new one. `russian` alone is not enough: "да" is a legitimate
    exact duplicate across Conjunctions and Particles (see `WordRow`'s
    docstring / `ROW_SPLITS`), and the two notes must never collide onto
    the same GUID. `pos` -- the section-heading identity
    ("Prepositions", "Conjunctions", ...), not the full `::`-joined deck
    path from `subdeck_name` -- is what's hashed, so a GUID survives even
    if the user later renumbers the `2.`/`3.`/`4.` deck-root prefix
    (`DECK_ROOT` is user-renumbered territory; see the-ask.md decision 2).

    Uses sha256 over a canonical `pos + "\\x1f" + russian` string (the
    `\\x1f` separator matches `anki.utils.join_fields`'s own convention,
    preventing e.g. `pos="AB", russian="C"` from colliding with
    `pos="A", russian="BC"`), takes the first 8 bytes as a big-endian
    unsigned int, and base91-encodes it -- never Python's built-in
    `hash()`, which is salted per-process specifically to be
    non-reproducible and would silently reintroduce this exact defect.

    Same `(russian, pos)` -> the same 64-bit hash -> the same GUID string,
    every time, on every machine, forever. This is what makes a rebuilt
    `.apkg` re-importable in place instead of duplicating the deck --
    see `immutable_words.py`'s `build_deck_tree`, the only caller.
    """
    canonical = f"{pos}\x1f{russian}".encode()
    digest = hashlib.sha256(canonical).digest()
    num = int.from_bytes(digest[:8], byteorder="big", signed=False)
    return _base91(num)


# Rows that combine two NON-interchangeable words into one source-document
# row split into their own separate cards. Keyed by the exact `.russian`
# text of the raw parsed row. Each entry is a list of (russian, english)
# replacement pairs -- one row in, N rows out, same `pos`.
#
# "словно / будто" -> ONE new row, "словно" alone. "будто" is NOT created
# here: it already exists as its own row, Particles rank 28
# ("| 28 | будто | as if |") -- creating a second "будто" row would be a
# genuine duplicate card, not a legitimate да/да-style repeat. Its nuance
# gloss is applied to that EXISTING row instead, via TRANSLATION_OVERRIDES
# below.
#
# "тоже / также" -> TWO new rows: neither word appears anywhere else in
# the source document (verified against the real 152-row list).
ROW_SPLITS: dict[str, list[tuple[str, str]]] = {
    "словно / будто": [
        ("словно", "as if, like (literary — a poetic simile)"),
    ],
    "тоже / также": [
        (
            "тоже",
            'also, too (same action, different subject — "me too": Я тоже иду)',
        ),
        (
            "также",
            "also, in addition (same subject, an extra thing — "
            "Я также купил хлеб; more formal)",
        ),
    ],
}

# Per-row English overrides, keyed by exact `.russian` text -- applied
# instead of the source document's own gloss. Never edits the source
# document; this is a pure code-side transform.
TRANSLATION_OVERRIDES: dict[str, str] = {
    "-то": (
        "indefinite particle: makes a word specific-but-unknown — "
        'кто-то "someone", что-то "something", где-то "somewhere". '
        "Contrast -нибудь, which is non-specific: "
        'кто-то позвонил "someone called" (a particular person) vs '
        'позови кого-нибудь "call anyone".'
    ),
    "-ка": (
        "softening particle on imperatives: turns an order into a nudge — "
        'скажи-ка "go on, tell me", дай-ка "give it here", '
        'посмотрим-ка "let\'s have a look". Informal, ты-level.'
    ),
    "будто": (
        "as if, as though (often implies doubt — "
        'он будто не знал "as if he didn\'t know", implying he did)'
    ),
}


def _apply_row_transforms(rows: list["WordRow"]) -> list["WordRow"]:
    """Apply `ROW_SPLITS`/`TRANSLATION_OVERRIDES`, then renumber `rank`
    contiguously `1..N` within each `pos`, preserving document order.

    This keeps the existing invariant -- ranks within a section are exactly
    `1..count` with no gaps -- through the split, rather than dropping it.
    """
    expanded: list[WordRow] = []
    for row in rows:
        if row.russian in ROW_SPLITS:
            for split_russian, split_english in ROW_SPLITS[row.russian]:
                expanded.append(
                    WordRow(
                        pos=row.pos,
                        rank=row.rank,
                        russian=split_russian,
                        english=split_english,
                    )
                )
        elif row.russian in TRANSLATION_OVERRIDES:
            expanded.append(
                WordRow(
                    pos=row.pos,
                    rank=row.rank,
                    russian=row.russian,
                    english=TRANSLATION_OVERRIDES[row.russian],
                )
            )
        else:
            expanded.append(row)

    counters: dict[str, int] = {}
    renumbered: list[WordRow] = []
    for row in expanded:
        counters[row.pos] = counters.get(row.pos, 0) + 1
        renumbered.append(
            WordRow(
                pos=row.pos,
                rank=counters[row.pos],
                russian=row.russian,
                english=row.english,
            )
        )
    return renumbered


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

    @property
    def guid(self) -> str:
        """This row's deterministic Anki note GUID -- see `guid_for_row`."""
        return guid_for_row(self.russian, self.pos)

    def fields(self) -> list[str]:
        """The seven field values, in FIELD_NAMES order.

        `Pronunciation` and `Additional Info` are left empty. `Audio` holds the
        four PREDICTED filenames (comma-separated, no spaces), derived from
        `self.russian` via the shared `audio_naming.build_filename` -- the same
        function `elevenlabs_tts.py` uses to name the files it actually writes,
        so the two agree byte-for-byte before any audio file exists. `AudioRefs`
        holds the SAME four filenames, as concatenated `[sound:...]` tags --
        never independently computed -- so the two fields always describe the
        same media (see FIELD_NAMES's comment for why AudioRefs must never be
        rendered by a template).
        """
        audio_names = [build_filename(self.russian, slot) for slot in SLOTS]
        audio_refs = "".join(f"[sound:{name}]" for name in audio_names)
        return [
            self.russian,
            self.english,
            "",
            POS_FIELD_VALUE[self.pos],
            ",".join(audio_names),
            "",
            audio_refs,
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
    rows = _apply_row_transforms(rows)
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
      degrades to doing nothing at all when the list is empty (a defensive
      fallback -- every note this lane creates now ships with `Audio`
      populated, but the script must not assume that), and otherwise picks
      a filename to play via an autoplaying `<audio>` element plus a visible
      replay `<button>`.

    The script defers its actual work one macrotask via `setTimeout(fn, 0)`:
    it runs at parse/DOM-insertion time, before any answer-side `#back`
    element that will ever exist for this render has actually been inserted,
    so a synchronous check could never see it. Once deferred,
    `document.getElementById("back")` reliably discriminates a pure
    question-side render (no `#back` exists yet) from any answer-side render
    (`#back` always exists by then).

    This discrimination matters because `afmt` always re-embeds the
    question side's rendered HTML -- script tag included -- via Anki's own
    `{{FrontSide}}` macro, so a template that places this div on the
    question side re-runs this very script a second time when the answer is
    shown. Without correction that second run would re-roll `Math.random()`
    and autoplay a different file than the one just heard. To prevent that,
    the chosen filename is stashed on `window.__immutableWordsAudioChoice`
    and, on an answer-side render, reused (without autoplaying it again)
    instead of re-rolled -- but ONLY when that stored choice is a member of
    *this* render's own file list. That membership check is the
    anti-staleness guard: without it, a template whose audio div lives only
    on the answer side (never duplicated in from a question side) would
    wrongly reuse a leftover global from a different note reviewed moments
    earlier -- `#back` is present there too, since the div is its
    descendant, even though no genuine question-side pick has happened yet
    for this note. Any render that isn't a genuine same-note duplicate --
    every question-side render, or an answer-side render with no usable
    stored choice -- makes and stores a fresh random pick instead, so a
    later review of the same card also rolls a fresh voice rather than
    repeating one forever.

    The script also renders a `<button>` on every render so the native R-key
    replay isn't simply lost, always wired to whichever `<audio>` element
    this render actually chose or reused.

    Returns the template unchanged when it has no such element - two of the
    four template sides legitimately don't render `{{Audio}}` at all. Idempotent:
    once rewritten, the literal `<div id="audio">{{Audio}}</div>` pattern no
    longer matches, so a second pass is a no-op.
    """
    if not _AUDIO_DIV.search(template_html):
        return template_html

    replacement = """\
<!-- Audio field holds a plain-text, comma/newline-separated list of
     bare media filenames -- it is NOT wrapped in Anki's own sound-tag
     syntax. Anki's backend autoplays every sound-tagged reference in
     a field, in order, before any template JS runs, so three tagged
     recordings would play back to back with no way for JS to
     suppress or reorder that queue. Keeping the field as plain text
     lets the script below pick and play just one.

     The pick must survive unchanged from the question render to the
     answer render of the SAME review: `afmt` always re-embeds the
     question's rendered HTML via `{{FrontSide}}`, which re-runs this
     very script a second time whenever a template places this div on
     the question side -- without this logic that second run would
     call Math.random() again and autoplay a DIFFERENT file than the
     one just heard. The script defers its work with setTimeout(fn, 0)
     because it runs at parse time, before the answer side's own
     `#back` element has actually been inserted into the page --
     checking for it synchronously would never see it. Once deferred,
     document.getElementById("back") reliably tells a pure
     question-side render (no #back anywhere yet) apart from any
     answer-side render (#back always exists by then, whether this
     particular audio div started life on the question side and got
     duplicated in via FrontSide, or lives on the answer side alone).
     window.__immutableWordsAudioChoice carries the chosen filename
     across exactly one such question->answer duplication; every fresh
     render -- every question-side render, or an answer-side render
     whose stored choice doesn't belong to THIS note's own file list
     (a template that only ever shows audio on the answer side, or a
     global left over from a different note reviewed a moment ago) --
     overwrites it with a new random pick, so a later review of the
     same card rolls a fresh voice rather than repeating one forever.
     The script also renders a <button> so the native R-key replay
     isn't simply lost, on both sides, always pointing at whichever
     file this render actually chose or reused. -->
<div id="audio"><span id="audio-data" class="hidden">{{Audio}}</span>
<span id="audio-controls"></span></div>
<script>
(function () {
  var data = document.getElementById("audio-data");
  if (!data) return;
  var text = data.textContent.trim();
  if (!text) return;
  var files = text
    .split(/[,\\n]+/)
    .map(function (f) { return f.trim(); })
    .filter(function (f) { return f.length > 0; });
  if (files.length === 0) return;
  setTimeout(function () {
    var container = document.getElementById("audio");
    if (!container) return;
    var onAnswerSide = !!document.getElementById("back");
    var previous = window.__immutableWordsAudioChoice;
    var reusable = onAnswerSide && !!previous && files.indexOf(previous) !== -1;
    var chosen = reusable
      ? previous
      : files[Math.floor(Math.random() * files.length)];
    window.__immutableWordsAudioChoice = chosen;
    var audio = document.createElement("audio");
    audio.autoplay = !reusable;
    audio.src = chosen;
    var button = document.createElement("button");
    button.textContent = "▶";
    button.addEventListener("click", function () {
      audio.currentTime = 0;
      audio.play();
    });
    container.appendChild(audio);
    container.appendChild(button);
  }, 0);
})();
</script>
"""
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
