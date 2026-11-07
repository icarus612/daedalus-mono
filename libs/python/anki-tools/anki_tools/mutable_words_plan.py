"""Pure core for the mutable-words deck: Nouns, Verbs, Adjectives, Adverbs.

Turns the four `russian-vocabulary` TSV source sheets into note rows, deck
names, and card templates for `Languages::Russian::4. Mutable Words`. No
Anki imports, no `requests`, no filesystem access beyond the TSV paths
passed in.
"""

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from anki_tools import card_audio, card_dedup, case_pill, distinction, prompt_hint
from anki_tools.anki_identity import guid_for_row, notetype_id_for_name
from anki_tools.audio_naming import (
    audio_field_value,
    build_filename,
    strip_qualifier,
)
from anki_tools.examples_field import EXAMPLES_FIELD

DECK_ROOT = "Languages::Russian::4. Mutable Words"

# The lettered subdecks of this tree, in order. Adverbs is absent on
# purpose: it builds into the Immutable tree below, and leaving a hole here
# would letter the rest a, b, c, e, f.
SUBDECK_LEAVES = {
    "Nouns": "Nouns",
    "Verbs": "Verbs",
    "Adjectives": "Adjectives",
    "Pronouns": "Pronouns",
    "Numerals": "Numerals",
}

# Adverbs do not decline, so they sit under Immutable Words rather than taking
# a letter here. Base and derived stay separate decks: `e. Base Adverbs` holds
# the primitives (тут, вчера), this leaf holds the ones built off an adjective.
SUBDECK_OVERRIDES = {
    "Adverbs": "Languages::Russian::3. Immutable Words::f. Derived Adverbs",
}

VOICE_SLOTS: tuple[str, ...] = ("f1", "m2")

NOTE_TYPE_NAMES = {
    "Nouns": "Russian - Mutable Nouns (Ellis Version)",
    "Verbs": "Russian - Mutable Verbs (Ellis Version)",
    "Adjectives": "Russian - Mutable Adjectives (Ellis Version)",
    "Adverbs": "Russian - Mutable Adverbs (Ellis Version)",
    "Pronouns": "Russian - Mutable Pronouns (Ellis Version)",
    "Numerals": "Russian - Mutable Numerals (Ellis Version)",
}

FIELD_NAMES: dict[str, tuple[str, ...]] = {
    "Nouns": (
        "Russian",
        "Translation",
        "Stress",
        "Gender",
        "Plural",
        "Genitive Sg",
        "Genitive Pl",
        "Animate",
        "Category",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
    ),
    "Verbs": (
        "Imperfective",
        "Perfective",
        "Translation",
        "Stress",
        "Conjugation",
        "я (1sg)",
        "ты (2sg)",
        "они (3pl)",
        "Past (m / f)",
        "Case / Preposition",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio Imperfective",
        "Audio Perfective",
        "Russian Distinction",
        "English Distinction",
        "Case",
    ),
    "Adjectives": (
        "Russian (m)",
        "Translation",
        "Stress",
        "Feminine",
        "Neuter",
        "Plural",
        "Short Form",
        "Comparative",
        "Opposite",
        "Stem Type",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
    ),
    "Adverbs": (
        "Adverb",
        "Translation",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
        "Case",
    ),
    "Pronouns": (
        "Russian",
        "Translation",
        "Stress",
        "Pronoun Type",
        "Gender Forms",
        "Oblique Forms",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
    ),
    "Numerals": (
        "Russian",
        "Translation",
        "Stress",
        "Numeral Type",
        "Case Governed",
        "Gender Forms",
        "Genitive",
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
    ),
}

ROW_SPLITS: dict[str, tuple[tuple[str, str, str], tuple[str, str, str]]] = {
    "направо / справа": (
        ("направо", "to the right", "напра́во"),
        ("справа", "on the right", "спра́ва"),
    ),
    "налево / слева": (
        ("налево", "to the left", "нале́во"),
        ("слева", "on the left", "сле́ва"),
    ),
}

_DECK_HEADER_HTML = '<div id="path"></div>\n<div id="deck">{{Deck}}</div>'

_DECK_HEADER_SCRIPT = """<script>
deck = document.getElementById("deck");
dName = deck.innerText.split("::")
deck.innerHTML = "Russian - " + dName[dName.length-1].split(". ")[1];
document.getElementById("path").innerHTML = dName.join(" > ")
</script>"""

# Verbatim port of the reference note type's own `addTitle` (wraps a
# populated field in `.title`/`.body` divs; no-ops when empty).
_ADD_TITLE_FUNCTION = """function addTitle(id=false, title="") {
	let el = document.getElementById(id);
	if (el.innerText) {
		let t = document.createElement("div");
		t.classList.add("title");
		t.innerHTML = title;

		let b = document.createElement("div");
		b.classList.add("body");
		b.innerHTML = el.innerHTML;

		while(el.firstChild) {
			el.removeChild(el.firstChild);
		}
		el.append(t, b);
	}
}"""


@dataclass(frozen=True)
class NounRow:
    rank: int
    russian: str
    translation: str
    stress: str
    gender: str
    plural: str
    genitive_sg: str
    genitive_pl: str
    animate: str
    category: str
    additional_info: str
    examples: str

    SHEET: ClassVar[str] = "Nouns"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.russian,)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.russian)
        return [
            headword_text(self.russian),
            self.translation,
            self.stress,
            self.gender,
            self.plural,
            self.genitive_sg,
            self.genitive_pl,
            self.animate,
            self.category,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.qualifier_of(self.russian),
            distinction.english_distinction(self.russian),
        ]


@dataclass(frozen=True)
class VerbRow:
    rank: int
    imperfective: str
    perfective: str
    translation: str
    stress: str
    conjugation: str
    ya_1sg: str
    ty_2sg: str
    oni_3pl: str
    past_m_f: str
    case_preposition: str
    additional_info: str
    examples: str
    case: str = ""

    SHEET: ClassVar[str] = "Verbs"

    @property
    def base_words(self) -> tuple[str, ...]:
        """Both aspects, minus any the document marks absent with a dash.

        `стоить` and `ходить` have no perfective at all; the dash records
        that, and a dash is not a word to be voiced, slugged or collided
        against -- the same reason `parse_adverbs` drops a dash-only
        `Adverb`.
        """
        return tuple(
            w for w in (self.imperfective, self.perfective) if w and w.strip() != "—"
        )

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        imperfective_names = audio_names(self.imperfective)
        perfective_names = audio_names(self.perfective)
        return [
            headword_text(self.imperfective),
            headword_text(self.perfective),
            self.translation,
            self.stress,
            self.conjugation,
            self.ya_1sg,
            self.ty_2sg,
            self.oni_3pl,
            self.past_m_f,
            self.case_preposition,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(imperfective_names),
            audio_field_value(perfective_names),
            distinction.qualifier_of(self.imperfective),
            distinction.english_distinction(self.imperfective),
            self.case,
        ]


@dataclass(frozen=True)
class AdjectiveRow:
    rank: int
    russian_m: str
    translation: str
    stress: str
    feminine: str
    neuter: str
    plural: str
    short_form: str
    comparative: str
    opposite: str
    stem_type: str
    additional_info: str
    examples: str

    SHEET: ClassVar[str] = "Adjectives"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.russian_m,)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.russian_m)
        return [
            headword_text(self.russian_m),
            self.translation,
            self.stress,
            self.feminine,
            self.neuter,
            self.plural,
            self.short_form,
            self.comparative,
            self.opposite,
            self.stem_type,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.qualifier_of(self.russian_m),
            distinction.english_distinction(self.russian_m),
        ]


@dataclass(frozen=True)
class AdverbRow:
    rank: int
    adverb: str
    translation: str
    stress: str
    from_adjective: str
    formation: str
    comparative: str
    additional_info: str
    examples: str
    case: str = ""

    SHEET: ClassVar[str] = "Adverbs"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.adverb,)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.adverb)
        return [
            headword_text(self.adverb),
            self.translation,
            self.stress,
            self.from_adjective,
            self.formation,
            self.comparative,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.qualifier_of(self.adverb),
            distinction.english_distinction(self.adverb),
            self.case,
        ]


_CUE_CARRIES_TYPE = frozenset({"ты", "вы"})


def _pronoun_type_shown(russian: str, pronoun_type: str, cue: str) -> str:
    """The Pronoun Type row's value, empty when the English cue already says it.

    An empty field leaves no row on the answer side; the cue stays on the
    English-prompt front untouched. The cue says it when the two are equal, or
    for `ты` and `вы`, whose cue is the type plus the register.
    """
    type_words = card_dedup.content_words(pronoun_type)
    cue_words = card_dedup.content_words(cue)
    if type_words and type_words == cue_words:
        return ""
    if russian in _CUE_CARRIES_TYPE and type_words <= cue_words:
        return ""
    return pronoun_type


@dataclass(frozen=True)
class PronounRow:
    rank: int
    russian: str
    translation: str
    stress: str
    pronoun_type: str
    gender_forms: str
    oblique_forms: str
    additional_info: str
    examples: str

    SHEET: ClassVar[str] = "Pronouns"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.russian,)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.russian)
        cue = distinction.english_distinction(self.russian)
        return [
            headword_text(self.russian),
            self.translation,
            self.stress,
            _pronoun_type_shown(self.russian, self.pronoun_type, cue),
            self.gender_forms,
            self.oblique_forms,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.qualifier_of(self.russian),
            cue,
        ]


@dataclass(frozen=True)
class NumeralRow:
    rank: int
    russian: str
    translation: str
    stress: str
    numeral_type: str
    case_governed: str
    gender_forms: str
    genitive: str
    additional_info: str
    examples: str

    SHEET: ClassVar[str] = "Numerals"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.russian,)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.russian)
        return [
            headword_text(self.russian),
            self.translation,
            self.stress,
            self.numeral_type,
            self.case_governed,
            self.gender_forms,
            self.genitive,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.qualifier_of(self.russian),
            distinction.english_distinction(self.russian),
        ]


def subdeck_name(sheet: str, root: str = DECK_ROOT) -> str:
    """Full deck path for `sheet`, e.g. `{root}::a. Nouns`."""
    if sheet in SUBDECK_OVERRIDES:
        return SUBDECK_OVERRIDES[sheet]
    if sheet not in SUBDECK_LEAVES:
        raise ValueError(f"unknown sheet: {sheet!r}")
    letter = "abcdefghijklmnopqrstuvwxyz"[list(SUBDECK_LEAVES).index(sheet)]
    return f"{root}::{letter}. {SUBDECK_LEAVES[sheet]}"


def all_subdeck_names(root: str = DECK_ROOT) -> list[str]:
    """Every subdeck path the builder writes, in sheet order."""
    return [subdeck_name(sheet, root) for sheet in NOTE_TYPE_NAMES]


def audio_names(base_word: str) -> list[str]:
    """The two predicted media filenames for `base_word`, one per voice slot.

    A word the document marks absent with a dash -- `стоить` and `ходить`
    have no perfective at all -- has no audio to predict. Without this the
    dash slugs to the fallback `word`, and the note ends up pointing at a
    `word_f1.mp3` that nothing will ever generate.
    """
    if not base_word or base_word.strip() == "—":
        return []
    return [build_filename(base_word, slot) for slot in VOICE_SLOTS]


def headword_text(stored: str) -> str:
    """The headword as a note stores it: bare, with the editorial qualifier
    carried by `Russian Distinction` instead of printed twice.

    Deliberately decoupled from `base_words`, which keeps the QUALIFIED text
    because `guid_for_row` hashes it -- stripping it there would re-GUID
    `первый (adjective)` and its four siblings, and the next import would
    insert duplicates instead of updating the user's scheduling.
    """
    return strip_qualifier(stored)


def parse_nouns(tsv_path: str) -> list[NounRow]:
    """Parse `nouns.tsv` into `NounRow`s, in file order."""
    rows: list[NounRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append(
                NounRow(
                    rank=int(row["#"]),
                    russian=row["Russian"],
                    translation=row["English"],
                    stress=row["Stress"],
                    gender=row["Gender"],
                    plural=row["Plural"],
                    genitive_sg=row["Genitive Sg"],
                    genitive_pl=row["Genitive Pl"],
                    animate=row["Animate"],
                    category=row["Category"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                )
            )
    return rows


def parse_verbs(tsv_path: str) -> list[VerbRow]:
    """Parse `verbs.tsv` into `VerbRow`s, in file order."""
    rows: list[VerbRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append(
                VerbRow(
                    rank=int(row["#"]),
                    imperfective=row["Imperfective"],
                    perfective=row["Perfective"],
                    translation=row["English"],
                    stress=row["Stress"],
                    conjugation=row["Conjugation"],
                    ya_1sg=row["я (1sg)"],
                    ty_2sg=row["ты (2sg)"],
                    oni_3pl=row["они (3pl)"],
                    past_m_f=row["Past (m / f)"],
                    case_preposition=row["Case / Preposition"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                    case=row.get("Case", ""),
                )
            )
    return rows


def parse_adjectives(tsv_path: str) -> list[AdjectiveRow]:
    """Parse `adjectives.tsv` into `AdjectiveRow`s, in file order."""
    rows: list[AdjectiveRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append(
                AdjectiveRow(
                    rank=int(row["#"]),
                    russian_m=row["Russian (m)"],
                    translation=row["English"],
                    stress=row["Stress"],
                    feminine=row["Feminine"],
                    neuter=row["Neuter"],
                    plural=row["Plural"],
                    short_form=row["Short Form"],
                    comparative=row["Comparative"],
                    opposite=row["Opposite"],
                    stem_type=row["Stem Type"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                )
            )
    return rows


def parse_adverbs(tsv_path: str) -> list[AdverbRow]:
    """Parse `adverbs.tsv` into `AdverbRow`s: drop placeholder rows, split the
    two slash-joined rows into two each, then renumber `rank` `1..N`.
    """
    parsed: list[AdverbRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            split = ROW_SPLITS.get(row["Adverb"].strip())
            if split is not None:
                for adverb, translation, stress in split:
                    parsed.append(
                        AdverbRow(
                            rank=0,
                            adverb=adverb,
                            translation=translation,
                            stress=stress,
                            from_adjective=row["From Adjective"],
                            formation=row["Formation"],
                            comparative=row["Comparative"],
                            additional_info=row["Additional Info"],
                            examples=row["Examples"],
                            case=row.get("Case", ""),
                        )
                    )
                continue

            signals = {
                "Adverb": row["Adverb"].strip() == "—",
                "Formation": row["Formation"].strip() == "none",
                "English": row["English"].strip() == "",
                "Status": row["Status"].strip() == "",
            }
            if any(signals.values()):
                if not all(signals.values()):
                    disagreeing = [name for name, fired in signals.items() if not fired]
                    raise ValueError(
                        f"adverb row #{row['#']} has disagreeing placeholder "
                        f"signals; did not fire: {disagreeing}"
                    )
                continue

            parsed.append(
                AdverbRow(
                    rank=0,
                    adverb=row["Adverb"],
                    translation=row["English"],
                    stress=row["Stress"],
                    from_adjective=row["From Adjective"],
                    formation=row["Formation"],
                    comparative=row["Comparative"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                    case=row.get("Case", ""),
                )
            )

    return [
        AdverbRow(
            rank=rank,
            adverb=row.adverb,
            translation=row.translation,
            stress=row.stress,
            from_adjective=row.from_adjective,
            formation=row.formation,
            comparative=row.comparative,
            additional_info=row.additional_info,
            examples=row.examples,
            case=row.case,
        )
        for rank, row in enumerate(parsed, start=1)
    ]


def parse_pronouns(tsv_path: str) -> list[PronounRow]:
    """Parse `pronouns.tsv` into `PronounRow`s, in file order."""
    rows: list[PronounRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append(
                PronounRow(
                    rank=int(row["#"]),
                    russian=row["Russian"],
                    translation=row["English"],
                    stress=row["Stress"],
                    pronoun_type=row["Pronoun Type"],
                    gender_forms=row["Gender Forms"],
                    oblique_forms=row["Oblique Forms"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                )
            )
    return rows


def parse_numerals(tsv_path: str) -> list[NumeralRow]:
    """Parse `numerals.tsv` into `NumeralRow`s, in file order."""
    rows: list[NumeralRow] = []
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            rows.append(
                NumeralRow(
                    rank=int(row["#"]),
                    russian=row["Russian"],
                    translation=row["English"],
                    stress=row["Stress"],
                    numeral_type=row["Numeral Type"],
                    case_governed=row["Case Governed"],
                    gender_forms=row["Gender Forms"],
                    genitive=row["Genitive"],
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                )
            )
    return rows


def build_note_type_id(sheet: str) -> int:
    """Deterministic notetype id for `sheet`'s note type name."""
    return notetype_id_for_name(NOTE_TYPE_NAMES[sheet])


def build_template_id(sheet: str, card_index: int) -> int:
    """Deterministic template id for `sheet`'s `card_index`-th card."""
    return notetype_id_for_name(f"{NOTE_TYPE_NAMES[sheet]}\x1ftemplate\x1f{card_index}")


_PRIMARY_FIELD = {
    "Nouns": "Russian",
    "Adjectives": "Russian (m)",
    "Adverbs": "Adverb",
    "Pronouns": "Russian",
    "Numerals": "Russian",
}

_VERB_CARD_CONFIGS: tuple[tuple[str, str, str, str], ...] = (
    (
        "Imperfective",
        "Audio Imperfective",
        "audio-imperfective",
        "__mutableVerbImperfectiveChoice",
    ),
    (
        "Imperfective",
        "Audio Imperfective",
        "audio-imperfective",
        "__mutableVerbImperfectiveChoice",
    ),
    (
        "Perfective",
        "Audio Perfective",
        "audio-perfective",
        "__mutableVerbPerfectiveChoice",
    ),
    (
        "Perfective",
        "Audio Perfective",
        "audio-perfective",
        "__mutableVerbPerfectiveChoice",
    ),
)


# A Verbs card shows one aspect; its partner belongs on the answer side with
# it, with its own recording -- an aspect pair is learnt as a pair.
_ASPECT_COUNTERPART: dict[str, tuple[str, str]] = {
    "Imperfective": ("Perfective", "Audio Perfective"),
    "Perfective": ("Imperfective", "Audio Imperfective"),
}

ASPECT_AUDIO_SLOT_ID = "aspect-audio"
ASPECT_PLAY_FN = "__mutableVerbAspectPlay"


def _slug_for_field_name(field_name: str) -> str:
    """Slug an English field name for use as an HTML id attribute."""
    slug = field_name.lower()
    for char in (" ", "/", "(", ")"):
        slug = slug.replace(char, "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


_DETAIL_ID_OVERRIDES: dict[str, tuple[str, str]] = {
    "Additional Info": ("additional-info", "&#9432;"),
}

_STANDALONE_DETAILS = ("Additional Info", EXAMPLES_FIELD)


def _detail_id_and_title(field_name: str) -> tuple[str, str]:
    """The (element id, title) a detail row uses for `field_name`."""
    if field_name in _DETAIL_ID_OVERRIDES:
        return _DETAIL_ID_OVERRIDES[field_name]
    return _slug_for_field_name(field_name), field_name


def _detail_fields(sheet: str, primary_field: str) -> list[str]:
    """`FIELD_NAMES[sheet]` entries that become detail sections, in field
    order -- everything but the primary word, its translation, Stress (never
    shown on the card), the audio fields, `Rank`, the two distinction cues and
    `Case`, which render elsewhere.
    """
    excluded = {
        "Audio",
        "Audio Imperfective",
        "Audio Perfective",
        "Rank",
        "Stress",
        primary_field,
        "Translation",
        distinction.RUSSIAN_FIELD,
        distinction.ENGLISH_FIELD,
        "Case",
    }
    if sheet == "Verbs":
        excluded |= set(_ASPECT_COUNTERPART)
    return [name for name in FIELD_NAMES[sheet] if name not in excluded]


def _detail_row(field_name: str) -> str:
    """One labelled row, label included inside the field's own conditional so
    an empty field leaves no element behind.
    """
    slug = _slug_for_field_name(field_name)
    return (
        f"{{{{#{field_name}}}}}"
        f'<div id="{slug}">'
        f'<div class="detail-label">{field_name}</div>'
        f'<div class="detail-value">{{{{{field_name}}}}}</div>'
        f"</div>"
        f"{{{{/{field_name}}}}}"
    )


def _detail_block(
    sheet: str,
    primary_field: str,
    extra_titles: Sequence[tuple[str, str]] = (),
) -> tuple[str, str, str]:
    """(details, standalone, script) for `sheet`.

    `details` is the `#details` grid of labelled rows; `standalone` holds the
    `Additional Info` and `Examples` divs, which keep the reference note
    type's `.title`/`.body` treatment via `addTitle` (a verbatim port of the
    reference's own function) and so stay outside the grid. `script` is empty
    when nothing calls `addTitle`.
    """
    fields = _detail_fields(sheet, primary_field)
    rows = [_detail_row(name) for name in fields if name not in _STANDALONE_DETAILS]
    details = _wrap("details", *rows)

    calls = [f'addTitle("{slug}", "{title}");' for slug, title in extra_titles]
    standalone = []
    for field_name in fields:
        if field_name not in _STANDALONE_DETAILS:
            continue
        slug, title = _detail_id_and_title(field_name)
        standalone.append(f'<div id="{slug}">{{{{{field_name}}}}}</div>')
        calls.append(f'addTitle("{slug}", "{title}");')
    script = (
        "\n".join(["<script>", _ADD_TITLE_FUNCTION, *calls, "</script>"])
        if calls
        else ""
    )
    return details, "\n".join(standalone), script


def _all_primary_fields(sheet: str) -> list[str]:
    """Every field name that plays the primary-word role for `sheet`, across
    all of its cards -- one for a single-primary sheet, two (Imperfective,
    Perfective) for Verbs.
    """
    if sheet == "Verbs":
        seen: list[str] = []
        for config in _VERB_CARD_CONFIGS:
            if config[0] not in seen:
                seen.append(config[0])
        return seen
    return [_PRIMARY_FIELD[sheet]]


def _all_detail_slugs() -> list[str]:
    """Every row slug `_detail_block` can emit inside `#details` for any
    sheet/card. Drives `EXTRA_CSS`'s selector list so every row id has a rule
    covering it.
    """
    slugs: list[str] = []
    seen: set[str] = set()
    for sheet in FIELD_NAMES:
        for primary_field in _all_primary_fields(sheet):
            for field_name in _detail_fields(sheet, primary_field):
                if field_name in _STANDALONE_DETAILS:
                    continue
                slug = _slug_for_field_name(field_name)
                if slug not in seen:
                    seen.add(slug)
                    slugs.append(slug)
    return slugs


# Blue/red rather than the intuitive green for perfective: red-green is the
# one pair the common colour-vision deficiencies collapse.
ASPECT_COLOURS = {"imperfective": "#1565c0", "perfective": "#c62828"}

_ASPECT_COLOUR_CSS = "\n\n".join(
    f"#{aspect} .title, #{aspect} .body, .aspect-{aspect} {{\n\tcolor: {colour};\n}}"
    for aspect, colour in ASPECT_COLOURS.items()
)


_ASPECT_LINE_IDS = ", ".join(f"#{aspect}" for aspect in ASPECT_COLOURS)
_ASPECT_WORD_IDS = ", ".join(f"#{aspect}-word" for aspect in ASPECT_COLOURS)
_ASPECT_LINE_TITLES = ", ".join(f"#{aspect} .title" for aspect in ASPECT_COLOURS)
_ASPECT_LINE_BODIES = ", ".join(f"#{aspect} .body" for aspect in ASPECT_COLOURS)

# The counterpart aspect closes the word stack rather than opening the grey
# detail list, so it is centred on the headword and its translation instead
# of inheriting the details' full-width left-aligned row.
_ASPECT_LINE_CSS = (
    f"{_ASPECT_LINE_IDS} {{\n"
    "\tpadding: .15rem 0;\n"
    "\tdisplay: flex;\n"
    "\tflex-wrap: wrap;\n"
    "\tjustify-content: center;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "\twidth: 100%;\n"
    "\ttext-align: center;\n"
    "\tline-height: 1.25;\n"
    "}\n\n"
    f"{_ASPECT_LINE_TITLES} {{\n"
    "\tfont-size: 1.2rem;\n"
    "\tmargin-right: 0;\n"
    "}\n\n"
    f"{_ASPECT_LINE_BODIES} {{\n"
    "\tfont-size: 1.2rem;\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "}\n\n"
    f"#{ASPECT_AUDIO_SLOT_ID} {{\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "}\n\n"
    f"{_ASPECT_WORD_IDS} {{\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "}"
)


def _build_extra_css() -> str:
    """CSS appended to the cloned source note type's CSS (never rewritten in
    place -- see `mutable_words.build_note_types`). Lays the `#details` rows
    out as a centred two-column label/value grid;
    `#audio-imperfective`/`#audio-perfective` close the
    same coverage gap for the Verbs sheet's two audio containers, mirroring
    `#audio`; `.aspect` styles the Verbs reverse fronts' inline aspect
    qualifier.
    """
    slugs = _all_detail_slugs()
    ids = ", ".join(f"#{slug}" for slug in slugs)
    return (
        "#details {\n"
        "\tdisplay: grid;\n"
        "\tgrid-template-columns: max-content max-content;\n"
        "\tcolumn-gap: .6rem;\n"
        "\twidth: max-content;\n"
        "\tmax-width: 100%;\n"
        "\tmargin: 0 auto;\n"
        "}\n\n"
        f"{ids} {{\n"
        "\tdisplay: contents;\n"
        "}\n\n"
        "#details .detail-label, #details .detail-value {\n"
        "\tpadding: 5px 0;\n"
        "\tfont-size: 1.2rem;\n"
        "\tcolor: #656565;\n"
        "\tword-break: break-word;\n"
        "\thyphens: auto;\n"
        "}\n\n"
        "#details .detail-label {\n"
        "\ttext-align: right;\n"
        "}\n\n"
        "#details .detail-value {\n"
        "\ttext-align: left;\n"
        "}\n\n"
        "#audio-imperfective, #audio-perfective {\n"
        "\ttext-align: center;\n"
        "\tpadding-top: .3rem;\n"
        "}\n\n"
        ".aspect {\n"
        "\tfont-size: 0.85em;\n"
        "\tcolor: #656565;\n"
        "\twhite-space: nowrap;\n"
        "}\n\n"
        f"{_ASPECT_LINE_CSS}\n\n"
        f"{_ASPECT_COLOUR_CSS}"
    )


EXTRA_CSS = _build_extra_css()


def _translation_div(sheet: str, primary_field: str) -> str:
    """`{{Translation}}`, with the card's own aspect named after it on Verbs.

    The reverse cards already qualified their prompt this way; the forward
    cards' answer side showed the gloss bare, so nothing on the card said
    which aspect the headword itself was.
    """
    if sheet != "Verbs":
        return '<div id="translation">{{Translation}}</div>'
    aspect = _slug_for_field_name(primary_field)
    counterpart = _ASPECT_COUNTERPART[primary_field][0]
    return (
        '<div id="translation">{{Translation}}'
        f' <span class="aspect aspect-{aspect}">'
        f"({aspect}{{{{^{counterpart}}}}} only{{{{/{counterpart}}}}})</span></div>"
    )


def _add_russian_cue(side_html: str) -> str:
    """The `Russian Distinction` cue under the headword, empty-safe.

    Mirrors `immutable_words.clone_note_type`'s own call. A question that
    shows the gloss rather than the word has no `#russian` div and is
    returned unchanged.
    """
    return prompt_hint.add_prompt_hint(
        side_html,
        distinction.RUSSIAN_FIELD,
        prompt_hint.RUSSIAN_HINT_ID,
        prompt_hint.RUSSIAN_ANCHOR,
    )


def _wrap(element_id: str, *parts: str, attrs: str = "") -> str:
    open_tag = f'<div id="{element_id}"{" " + attrs if attrs else ""}>'
    # Empty parts are dropped rather than emitted as blank lines: a sheet
    # without an aspect row would otherwise differ from a deployed template
    # by whitespace alone, which is noise in any repo-vs-collection diff.
    return "\n".join([open_tag, *(p for p in parts if p), "</div>"])


def build_template(sheet: str, card_index: int) -> tuple[str, str]:
    """The (qfmt, afmt) pair for `sheet`'s `card_index`-th card (0-based).

    Mirrors the reference note type's own structure -- front content in
    `#front`, back content in `#back`, the primary word in `#russian`,
    `{{Translation}}` in `#translation` -- so the CSS cloned from that same
    note type actually applies, instead of the stock `<hr id=answer>` shell
    the templates used to emit.
    """
    if sheet == "Verbs":
        if card_index not in range(4):
            raise ValueError(f"Verbs card_index out of range: {card_index!r}")
        primary_field, audio_field, dom_id, state_key = _VERB_CARD_CONFIGS[card_index]
        audio_side = card_index % 2 == 0
    elif sheet in _PRIMARY_FIELD:
        if card_index not in (0, 1):
            raise ValueError(f"{sheet} card_index out of range: {card_index!r}")
        primary_field = _PRIMARY_FIELD[sheet]
        audio_field, dom_id, state_key = "Audio", "audio", "__mutableAudioChoice"
        audio_side = card_index == 0
    else:
        raise ValueError(f"unknown sheet: {sheet!r}")

    audio_html = card_audio.audio_block(audio_field, dom_id, state_key)
    aspect_div = ""
    extra_titles: list[tuple[str, str]] = []
    if sheet == "Verbs":
        counterpart, counterpart_audio = _ASPECT_COUNTERPART[primary_field]
        aspect_id = _slug_for_field_name(counterpart)
        word_id = f"{aspect_id}-word"
        aspect_div = _wrap(
            aspect_id,
            card_audio.audio_line_block(
                counterpart_audio, ASPECT_AUDIO_SLOT_ID, aspect_id, ASPECT_PLAY_FN
            ),
            _wrap(word_id, f"{{{{{counterpart}}}}}"),
            attrs=(
                f'class="{card_audio.TAPPABLE_CLASS}" onclick="{ASPECT_PLAY_FN}(event)"'
            ),
        )
        aspect_div = f"{{{{#{counterpart}}}}}{aspect_div}{{{{/{counterpart}}}}}"
        extra_titles.append((word_id, counterpart))
    details_html, standalone_html, detail_script = _detail_block(
        sheet, primary_field, extra_titles
    )
    russian_div = f'<div id="russian">{{{{{primary_field}}}}}</div>'
    translation_div = _translation_div(sheet, primary_field)
    has_case = "Case" in FIELD_NAMES[sheet]

    if audio_side:
        front = _wrap("front", _DECK_HEADER_HTML, audio_html, russian_div)
        qfmt = _add_russian_cue(front + _DECK_HEADER_SCRIPT)
        back = _wrap("back", translation_div, aspect_div, details_html, standalone_html)
        back = prompt_hint.add_prompt_hint(back, distinction.ENGLISH_FIELD)
        if has_case:
            back = case_pill.add_pill_block(back)
    else:
        front = _wrap("front", _DECK_HEADER_HTML, translation_div)
        front = prompt_hint.add_prompt_hint(front, distinction.ENGLISH_FIELD)
        if has_case:
            front = case_pill.add_pill_block(front)
        qfmt = front + _DECK_HEADER_SCRIPT
        back = _wrap(
            "back", audio_html, russian_div, aspect_div, details_html, standalone_html
        )
        back = _add_russian_cue(back)

    if sheet == "Verbs":
        qfmt = f"{{{{#{primary_field}}}}}{qfmt}{{{{/{primary_field}}}}}"

    return qfmt, "\n".join(p for p in ("{{FrontSide}}", back, detail_script) if p)
