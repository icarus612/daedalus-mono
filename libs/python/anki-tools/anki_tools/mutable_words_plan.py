"""Pure core for the mutable-words deck: Nouns, Verbs, Adjectives, Adverbs.

Turns the four `russian-vocabulary` TSV source sheets into note rows, deck
names, and card templates for `Languages::Russian::3. Mutable Words`. No
Anki imports, no `requests`, no filesystem access beyond the TSV paths
passed in.
"""

import csv
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from anki_tools import card_audio
from anki_tools.anki_identity import guid_for_row, notetype_id_for_name
from anki_tools.audio_naming import audio_field_value, build_filename
from anki_tools.examples_field import EXAMPLES_FIELD

DECK_ROOT = "Languages::Russian::3. Mutable Words"

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
    "Adverbs": "Languages::Russian::2. Immutable Words::f. Derived Adverbs",
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
            self.russian,
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
            self.imperfective,
            self.perfective,
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
            self.russian_m,
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
            self.adverb,
            self.translation,
            self.stress,
            self.from_adjective,
            self.formation,
            self.comparative,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
        ]


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
        return [
            self.russian,
            self.translation,
            self.stress,
            self.pronoun_type,
            self.gender_forms,
            self.oblique_forms,
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
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
            self.russian,
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


def _detail_fields(sheet: str, primary_field: str) -> list[str]:
    """`FIELD_NAMES[sheet]` entries that become titled detail sections, in
    field order -- everything but the primary word, its translation, Stress
    (never shown on the card), the audio fields, and `Rank`.
    """
    excluded = {
        "Audio",
        "Audio Imperfective",
        "Audio Perfective",
        "Rank",
        "Stress",
        primary_field,
        "Translation",
    }
    if sheet == "Verbs":
        excluded |= set(_ASPECT_COUNTERPART)
    return [name for name in FIELD_NAMES[sheet] if name not in excluded]


def _detail_block(
    sheet: str,
    primary_field: str,
    extra_titles: Sequence[tuple[str, str]] = (),
) -> tuple[str, str]:
    """(divs, script) for `sheet`'s detail sections.

    Mirrors how the reference note type treats its own single "Additional
    Info" field: each populated field becomes a `.title`/`.body` pair via
    `addTitle`, itself a verbatim port of the reference's own function.
    "Additional Info" keeps the reference's own id and icon, reusing the
    shared CSS's `#additional-info` rule unchanged; every other field gets
    its own id, grouped into `EXTRA_CSS`'s selector list under the same
    layout rule, since the reference note type has no field of its own to
    model them on.
    """
    divs = []
    calls = [f'addTitle("{slug}", "{title}");' for slug, title in extra_titles]
    for field_name in _detail_fields(sheet, primary_field):
        if field_name == "Additional Info":
            slug, title = "additional-info", "&#9432;"
        else:
            slug, title = _slug_for_field_name(field_name), field_name
        divs.append(f'<div id="{slug}">{{{{{field_name}}}}}</div>')
        calls.append(f'addTitle("{slug}", "{title}");')
    script = "\n".join(["<script>", _ADD_TITLE_FUNCTION, *calls, "</script>"])
    return "\n".join(divs), script


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
    """Every slug `_detail_block` can emit for any sheet/card, excluding
    "Additional Info" (styled via the reference's own `#additional-info`
    rule) and "Examples" (styled by `examples_field.EXAMPLES_CSS`), neither
    of which this rule covers. Drives `EXTRA_CSS`'s selector lists so every id
    `_detail_block` emits has a rule covering it.
    """
    slugs: list[str] = []
    seen: set[str] = set()
    for sheet in FIELD_NAMES:
        for primary_field in _all_primary_fields(sheet):
            for field_name in _detail_fields(sheet, primary_field):
                if field_name in ("Additional Info", EXAMPLES_FIELD):
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
    place -- see `mutable_words.build_note_types`). Generalizes the
    reference's own `#additional-info` layout to every other detail-section
    id `_detail_block` can emit, since the reference note type has no field
    to model them on; `#audio-imperfective`/`#audio-perfective` close the
    same coverage gap for the Verbs sheet's two audio containers, mirroring
    `#audio`; `.aspect` styles the Verbs reverse fronts' inline aspect
    qualifier.
    """
    slugs = _all_detail_slugs()
    ids = ", ".join(f"#{slug}" for slug in slugs)
    titles = ", ".join(f"#{slug} .title" for slug in slugs)
    bodies = ", ".join(f"#{slug} .body" for slug in slugs)
    return (
        f"{ids} {{\n"
        "\tpadding: 5px 0;\n"
        "\tdisplay: inline-flex;\n"
        "\ttext-align: left;\n"
        "\twidth: 100%;\n"
        "\tword-break: break-word;\n"
        "\thyphens: auto;\n"
        "\talign-items: start;\n"
        "}\n\n"
        f"{titles} {{\n"
        "\tfont-size: 1.2rem;\n"
        "\tdisplay: inline-flex;\n"
        "\tcolor: #656565;\n"
        "}\n\n"
        f"{bodies} {{\n"
        "\tfont-size: 1.2rem;\n"
        "\tcolor: #656565;\n"
        "\tpadding-top: 2px;\n"
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
    return (
        '<div id="translation">{{Translation}}'
        f' <span class="aspect aspect-{aspect}">({aspect})</span></div>'
    )


def _wrap(element_id: str, *parts: str, attrs: str = "") -> str:
    open_tag = f'<div id="{element_id}"{" " + attrs if attrs else ""}>'
    return "\n".join([open_tag, *parts, "</div>"])


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
        extra_titles.append((word_id, counterpart))
    detail_divs, detail_script = _detail_block(sheet, primary_field, extra_titles)
    russian_div = f'<div id="russian">{{{{{primary_field}}}}}</div>'
    translation_div = _translation_div(sheet, primary_field)

    if audio_side:
        front = _wrap("front", _DECK_HEADER_HTML, audio_html, russian_div)
        qfmt = front + _DECK_HEADER_SCRIPT
        back = _wrap("back", translation_div, aspect_div, detail_divs)
        afmt = "\n".join(["{{FrontSide}}", back, detail_script])
    else:
        front = _wrap("front", _DECK_HEADER_HTML, translation_div)
        qfmt = front + _DECK_HEADER_SCRIPT
        back = _wrap("back", audio_html, russian_div, aspect_div, detail_divs)
        afmt = "\n".join(["{{FrontSide}}", back, detail_script])

    return qfmt, afmt
