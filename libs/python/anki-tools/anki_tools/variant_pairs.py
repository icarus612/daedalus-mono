"""Variant pairs: two words with one meaning that differ only in register.

One note per pair per part of speech, read from `variant-pairs.tsv`. Three
cards: the default word to English, the variant to English, and English to
both words, each on its own line with its own audio.

Pure: no `anki` imports.
"""

import csv
from dataclasses import dataclass
from pathlib import Path

from anki_tools import card_audio, distinction, immutable_words_plan
from anki_tools.anki_identity import notetype_id_for_name
from anki_tools.audio_naming import audio_field_value, build_filename
from anki_tools.immutable_words_plan import SLOTS

NOTE_TYPE_NAME = "Russian - Variant Pairs (Ellis Version)"
NOTE_TYPE_ID = notetype_id_for_name(NOTE_TYPE_NAME)
TABLE = Path(__file__).parent / "data" / "russian-vocabulary" / "variant-pairs.tsv"
DEFAULT_LABEL = "default"

FIELD_NAMES = (
    "Russian",
    "Variant",
    "Register",
    "Translation",
    "Pronunciation",
    "Part of Speech",
    "Audio",
    "Variant Audio",
    "Additional Info",
    "Examples",
    distinction.RUSSIAN_FIELD,
    distinction.ENGLISH_FIELD,
)

TEMPLATE_NAMES = ("Russian", "Variant", "English")

# The source note's audio files, where they predate this note type and are not
# named after the word they speak.
AUDIO_STEMS = {
    ("Particles", "пусть"): "пусть / пускай",
    ("Conjunctions", "пусть"): "пусть / пускай",
    ("Conjunctions", "чтобы"): "чтобы / чтоб",
}


@dataclass(frozen=True)
class VariantPair:
    deck_leaf: str
    russian: str
    variant: str
    register: str
    translation: str
    additional_info: str
    examples: str
    russian_distinction: str
    english_distinction: str
    guid: str

    @property
    def deck(self) -> str:
        return immutable_words_plan.subdeck_name(self.deck_leaf)

    @property
    def headword(self) -> str:
        return f"{self.russian} / {self.variant}"

    @property
    def part_of_speech(self) -> str:
        return immutable_words_plan.POS_FIELD_VALUE[self.deck_leaf]

    def fields(self) -> list[str]:
        stem = AUDIO_STEMS.get((self.deck_leaf, self.russian), self.russian)
        return [
            self.russian,
            self.variant,
            self.register,
            self.translation,
            "",
            self.part_of_speech,
            audio_field_value(build_filename(stem, slot) for slot in SLOTS),
            audio_field_value(build_filename(self.variant, slot) for slot in SLOTS),
            self.additional_info,
            self.examples,
            self.russian_distinction,
            self.english_distinction,
        ]


def load_pairs(path: Path | str = TABLE) -> list[VariantPair]:
    with open(path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return [
        VariantPair(
            deck_leaf=row["Deck"],
            russian=row["Russian"],
            variant=row["Variant"],
            register=row["Register"],
            translation=row["Translation"],
            additional_info=row["Additional Info"],
            examples=row["Examples"],
            russian_distinction=row["Russian Distinction"],
            english_distinction=row["English Distinction"],
            guid=row["GUID"],
        )
        for row in rows
    ]


_HEADER = """<div id="path"></div>
<div id="deck">{{Deck}}</div>"""

_HEADER_SCRIPT = """<script>
  deck = document.getElementById("deck");
  dName = deck.innerText.split("::")
  deck.innerHTML = "Russian - " + dName[dName.length-1].split(". ")[1];
  document.getElementById("path").innerHTML = dName.join(" > ")
</script>"""


def _hint(dom_id: str, field: str) -> str:
    return (
        f'<span id="{dom_id}">{{{{#{field}}}}}({{{{{field}}}}}){{{{/{field}}}}}</span>'
    )


_ENGLISH_ROW = (
    '<div class="cue-row"><span id="translation">{{Translation}}</span>\n'
    + _hint("prompt-hint", distinction.ENGLISH_FIELD)
    + "</div>"
)

_RUSSIAN_HINT = _hint("russian-distinction", distinction.RUSSIAN_FIELD)

_DETAILS = """<div id="additional-info">{{Additional Info}}</div>
<div id="examples">{{Examples}}</div>
<script>
  function addTitle(id, title) {
    let el = document.getElementById(id);
    if (el && el.innerText) {
      let t = document.createElement("div");
      t.classList.add("title");
      t.innerHTML = title;
      let b = document.createElement("div");
      b.classList.add("body");
      b.innerHTML = el.innerHTML;
      while (el.firstChild) el.removeChild(el.firstChild);
      el.append(t, b);
    }
  }
  addTitle("additional-info", "&#9432;");
  addTitle("examples", "Examples");
</script>"""

_DEFAULT_PLAY = "playPairDefault"
_VARIANT_PLAY = "playPairVariant"


def _pair_line(
    word_field: str, label: str, audio_field: str, slug: str, play_fn: str
) -> str:
    line_id = f"pair-{slug}"
    return (
        f'<div id="{line_id}" class="pair-line {card_audio.TAPPABLE_CLASS}" '
        f'onclick="{play_fn}(event)">'
        f'<span class="pair-word">{{{{{word_field}}}}}</span> '
        f'<span class="pair-label">({label})</span> '
        + card_audio.audio_line_block(audio_field, f"{line_id}-slot", line_id, play_fn)
        + "</div>"
    )


_PAIR_LINES = (
    '<div class="pair-lines">'
    + _pair_line("Russian", DEFAULT_LABEL, "Audio", "default", _DEFAULT_PLAY)
    + _pair_line("Variant", "{{Register}}", "Variant Audio", "variant", _VARIANT_PLAY)
    + "</div>"
)

_AUTOPLAY_DEFAULT = """<script>
setTimeout(function () {
  var player = document.getElementById("pair-default-slot-player");
  if (player) player.play();
}, 50);
</script>"""


def _russian_front(word_field: str, audio_field: str) -> str:
    return (
        '<div id="front">\n'
        + _HEADER
        + "\n"
        + card_audio.audio_block(audio_field, "audio", "__variantPairsAudioChoice")
        + f'<div class="cue-row"><span id="russian">{{{{{word_field}}}}}</span>\n'
        + _RUSSIAN_HINT
        + "</div>\n</div>\n"
        + _HEADER_SCRIPT
    )


def _back(*, autoplay: bool) -> str:
    return (
        "{{FrontSide}}\n\n"
        '<div id="back">\n'
        + ("" if autoplay else _ENGLISH_ROW + "\n")
        + _PAIR_LINES
        + "\n"
        + (_AUTOPLAY_DEFAULT + "\n" if autoplay else "")
        + _DETAILS
        + "\n</div>"
    )


_ENGLISH_FRONT = (
    '<div id="front">\n' + _HEADER + "\n" + _ENGLISH_ROW + "\n</div>\n" + _HEADER_SCRIPT
)

TEMPLATES = {
    "Russian": (_russian_front("Russian", "Audio"), _back(autoplay=False)),
    "Variant": (_russian_front("Variant", "Variant Audio"), _back(autoplay=False)),
    "English": (_ENGLISH_FRONT, _back(autoplay=True)),
}

PAIR_CSS = """.pair-lines {
  margin-top: 1rem;
}

.pair-line {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: .5rem;
  margin: .4rem 0;
}

.pair-label {
  color: grey;
}"""
