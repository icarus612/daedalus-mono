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


def sanitize_word_slug(word: str) -> str:
    """Turn a Russian word/phrase into a filesystem-safe, readable slug.

    No hash suffix, by design (the user asked for `[word]_[slot].mp3`, not
    an opaque hash) -- but that is safe ONLY because it has been VERIFIED
    collision-free across the real 152-row source word list, including the
    genuinely awkward rows ("в / во", "ни... ни...", "-то", "несмотря на то,
    что", ...): see `test_slug_collision_free_across_real_source_word_list`.
    The one repeated slug that DOES occur ("да", appearing twice with
    identical text under two different parts of speech) is a legitimate
    duplicate -- same word, same audio, correctly sharing one file -- not a
    collision between two different words.

    If a future word list ever produces a genuine collision (two DIFFERENT
    strings sanitizing to the same slug), that must be reported and
    resolved explicitly, never silently patched by re-adding a hash here.
    """
    normalized = unicodedata.normalize("NFC", word.strip())
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
    """
    return SPOKEN_TEXT_OVERRIDES.get(source_text, source_text)


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
