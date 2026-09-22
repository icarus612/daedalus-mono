"""Shared audio-naming convention for the Russian immutable-words lane.

Pure module -- `os`, `re`, `unicodedata` only. No Anki imports, no
`requests`. Both `anki_tools/immutable_words_plan.py` (the deck-building
side, itself Anki-free) and `anki_tools/elevenlabs_tts.py` (the
Anki-agnostic TTS side) import from here, so the filename a note *predicts*
and the filename the TTS side actually *writes* are computed by the exact
same code path and can never drift apart.

Two separate, deliberately un-mergeable concerns live here:

- `build_filename` (and `sanitize_word_slug`, which it's built on) always
  derives from the RAW SOURCE text of a row/word -- e.g. `"в / во"` yields
  the slug `"в-во"`. This is the filename identity; it never changes based
  on what gets spoken.
- `spoken_text_for` is a separate, later transform applied only when
  building the text actually sent to a TTS API -- never when building a
  filename. Collapsing these two into one value is the single easiest
  mistake to make in this lane; keep them apart.
"""

import os
import re
import unicodedata

# The four default roster slots -- see `elevenlabs_tts.Voice.slot` for the
# full voice roster this pairs with. Kept here, not there, because
# `immutable_words_plan.py` needs the slot list to predict Audio-field
# filenames without importing anything ElevenLabs- or Anki-related.
SLOTS: tuple[str, ...] = ("f1", "f2", "m1", "m2")

# Cyrillic letters, digits, and underscore all count as "word" characters
# under Python's unicode-aware \w, so the source text survives intact; every
# run of anything else (spaces, "/", ",", ".", quotes, ...) collapses to a
# single hyphen. This alone makes "/" -- which cannot appear in a filename
# at all -- disappear along with every other filesystem-hostile character.
_UNSAFE_RUN = re.compile(r"[^\w\-]+", re.UNICODE)
_MULTI_HYPHEN = re.compile(r"-{2,}")

# A trailing "(...)" qualifier on a source row's Russian text, e.g.
# "как (conjunction)". See `strip_qualifier`.
_TRAILING_QUALIFIER = re.compile(r"\s*\([^()]*\)\s*$")


def strip_qualifier(word: str) -> str:
    """Drop a trailing parenthetical qualifier from a Russian source string.

    Three words in the source document -- `как`, `когда`, `пока` -- are
    genuinely two parts of speech at once, so each appears twice: once under
    Conjunctions and once under Base Adverbs. Their `Russian` text carries a
    qualifier ("как (conjunction)" / "как (adverb)") purely so the two cards
    can be told apart at a glance while reviewing.

    That qualifier is EDITORIAL, not part of the word. It must never reach:

    - a filename, or the two senses would want `как-conjunction_f1.mp3` and
      `как-adverb_f1.mp3` -- two copies of one identical recording, and
      neither matching the `как_f1.mp3` that already exists in the media
      folder with review history behind it; or
    - the text sent to a TTS API, which would dutifully read the English
      word "conjunction" out loud in the middle of a Russian recording.

    Stripping it in both places means both senses share the one recording of
    the one word, which is exactly right -- `sanitize_word_slug`'s docstring
    already names two identical Russian strings under different parts of
    speech as a legitimate shared file rather than a collision. This is the
    same situation, reached by a different route.

    Only a trailing parenthetical is stripped, and only a non-nested one.
    Parentheses elsewhere in a row's text are left alone.
    """
    return _TRAILING_QUALIFIER.sub("", word.strip())


def sanitize_word_slug(word: str) -> str:
    """Turn a Russian word/phrase into a filesystem-safe, readable slug.

    No hash suffix, by design (the user asked for `[word]_[slot].mp3`, not
    an opaque hash) -- but that is safe ONLY because it has been VERIFIED
    collision-free across the real 151-row source word list, including the
    genuinely awkward rows ("в / во", "ни... ни...", "-то", "несмотря на то,
    что", ...): see `test_slug_collision_free_across_real_source_word_list`.
    Every slug in the current list is distinct -- but the sanitizer must
    still treat two IDENTICAL Russian strings appearing under different
    parts of speech as a legitimate shared file, not a collision, should
    such a case ever recur (it has before, and does not today only because
    a duplicate note was removed from the source document).

    If a future word list ever produces a genuine collision (two DIFFERENT
    strings sanitizing to the same slug), that must be reported and
    resolved explicitly, never silently patched by re-adding a hash here.
    """
    normalized = unicodedata.normalize("NFC", strip_qualifier(word))
    slug = _UNSAFE_RUN.sub("-", normalized)
    slug = _MULTI_HYPHEN.sub("-", slug).strip("-")
    if not slug:
        slug = "word"
    return slug


def build_filename(word: str, slot: str, dir_name: str | None = None) -> str:
    """The filename for one (word, slot) pair: `<word-slug>_<slot>.mp3`.

    When `dir_name` is `None`, returns the bare filename (no path join) --
    this is what the deck builder needs for the `Audio` field, which must
    hold bare filenames, never paths. When `dir_name` is given, joins as
    `os.path.join(dir_name, name)`.
    """
    word_slug = sanitize_word_slug(word)
    name = f"{word_slug}_{slot}.mp3"
    if dir_name is None:
        return name
    return os.path.join(dir_name, name)


# Keyed by the EXACT source-row text, table-driven, no branching logic
# elsewhere. `словно / будто` and `тоже / также` never reach `spoken_text_for`
# as combined strings any more -- they are split into standalone single-word
# rows upstream, in `immutable_words_plan.py`'s `ROW_SPLITS` -- so they need
# no override here; each split word speaks itself.
SPOKEN_TEXT_OVERRIDES: dict[str, str] = {
    "в / во": "во",
    "с / со": "со",
    "к / ко": "ко",
    "о / об": "об",
    "-то": "то",
    "-ка": "ка",
    "чтобы / чтоб": "чтобы",
    "пусть / пускай": "пусть",
    "ни... ни...": "ни, ни",
    "то... то...": "то, то",
}


def spoken_text_for(source_text: str) -> str:
    """The text to actually send to a TTS API for `source_text`.

    A separate, later transform from filename-building: this is applied
    only at the point of building the API payload, never at the point of
    building a filename. `build_filename` always uses the raw source text.

    The one thing the two DO share is `strip_qualifier`: an editorial
    "(conjunction)"/"(adverb)" suffix is not part of the word, so it is
    absent from the filename and absent from what gets spoken. The override
    table is keyed on the stripped text, so "как (conjunction)" and plain
    "как" resolve through the same entry rather than needing one each.
    """
    stripped = strip_qualifier(source_text)
    return SPOKEN_TEXT_OVERRIDES.get(stripped, stripped)


def parse_audio_filenames(value: str) -> list[str]:
    """Split an `Audio`-field value into its bare filenames.

    Mirrors the card template's own JS split (`/[,\\n]+/` in
    `rewrite_audio_playback`) byte-for-byte, so the Python side that later
    looks these files up on disk agrees exactly with what the browser will
    try to play. Entries are stripped; empty/whitespace-only entries
    (including from an empty or whitespace-only `value`) are dropped, so an
    empty `Audio` field yields `[]`, never `[""]`.
    """
    return [name.strip() for name in re.split(r"[,\n]+", value) if name.strip()]


def get_anki_collection_path() -> str:
    if os.name == "nt":  # Windows
        return os.path.expanduser(
            "~\\AppData\\Roaming\\Anki2\\User 1\\collection.anki2"
        )
    elif os.name == "posix":  # macOS/Linux
        return os.path.expanduser("~/.local/share/Anki2/User 1/collection.anki2")
    else:
        raise OSError("Unsupported operating system")


def get_anki_media_dir(collection_path: str | None = None) -> str:
    """The Anki media directory sibling to the collection file.

    Derives from `collection_path` if given, else from
    `get_anki_collection_path()`.
    """
    return os.path.join(
        os.path.dirname(collection_path or get_anki_collection_path()),
        "collection.media",
    )
