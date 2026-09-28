"""Pure core for the mutable-words deck: Nouns, Verbs, Adjectives, Adverbs.

Turns the four `russian-vocabulary` TSV source sheets into note rows, deck
names, and card templates for `Languages::Russian::3. Mutable Words`. No
Anki imports, no `requests`, no filesystem access beyond the TSV paths
passed in.
"""

import csv
from dataclasses import dataclass
from typing import ClassVar

from anki_tools import card_audio
from anki_tools.anki_identity import guid_for_row, notetype_id_for_name
from anki_tools.audio_naming import build_filename

DECK_ROOT = "Languages::Russian::3. Mutable Words"

SUBDECK_LEAVES = {
    "Nouns": "Nouns",
    "Verbs": "Verbs",
    "Adjectives": "Adjectives",
    "Adverbs": "Adverbs",
}

VOICE_SLOTS: tuple[str, ...] = ("f1", "m2")

NOTE_TYPE_NAMES = {
    "Nouns": "Russian - Mutable Nouns (Ellis Version)",
    "Verbs": "Russian - Mutable Verbs (Ellis Version)",
    "Adjectives": "Russian - Mutable Adjectives (Ellis Version)",
    "Adverbs": "Russian - Mutable Adverbs (Ellis Version)",
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
        "Rank",
        "Audio",
        "AudioRefs",
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
        "Rank",
        "Audio Imperfective",
        "Audio Perfective",
        "AudioRefs",
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
        "Rank",
        "Audio",
        "AudioRefs",
    ),
    "Adverbs": (
        "Adverb",
        "Translation",
        "Stress",
        "From Adjective",
        "Formation",
        "Comparative",
        "Additional Info",
        "Rank",
        "Audio",
        "AudioRefs",
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

_ADD_TITLE_SCRIPT = """<script>
function addTitle(fieldId, icon) {
  var el = document.getElementById(fieldId);
  if (!el || !el.textContent.trim()) return;
  el.insertAdjacentHTML("beforebegin", '<div class="detail-title">' + icon + '</div>');
}
</script>"""


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
        audio_refs = "".join(f"[sound:{name}]" for name in names)
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
            str(self.rank),
            ",".join(names),
            audio_refs,
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

    SHEET: ClassVar[str] = "Verbs"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.imperfective, self.perfective)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        imperfective_names = audio_names(self.imperfective)
        perfective_names = audio_names(self.perfective)
        audio_refs = "".join(
            f"[sound:{name}]" for name in (*imperfective_names, *perfective_names)
        )
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
            str(self.rank),
            ",".join(imperfective_names),
            ",".join(perfective_names),
            audio_refs,
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
        audio_refs = "".join(f"[sound:{name}]" for name in names)
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
            str(self.rank),
            ",".join(names),
            audio_refs,
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
        audio_refs = "".join(f"[sound:{name}]" for name in names)
        return [
            self.adverb,
            self.translation,
            self.stress,
            self.from_adjective,
            self.formation,
            self.comparative,
            self.additional_info,
            str(self.rank),
            ",".join(names),
            audio_refs,
        ]


def subdeck_name(sheet: str, root: str = DECK_ROOT) -> str:
    """Full deck path for `sheet`, e.g. `{root}::a. Nouns`."""
    if sheet not in SUBDECK_LEAVES:
        raise ValueError(f"unknown sheet: {sheet!r}")
    letter = "abcdefghijklmnopqrstuvwxyz"[list(SUBDECK_LEAVES).index(sheet)]
    return f"{root}::{letter}. {SUBDECK_LEAVES[sheet]}"


def all_subdeck_names(root: str = DECK_ROOT) -> list[str]:
    """Every subdeck path, in `SUBDECK_LEAVES` order."""
    return [subdeck_name(sheet, root) for sheet in SUBDECK_LEAVES]


def audio_names(base_word: str) -> list[str]:
    """The two predicted media filenames for `base_word`, one per voice slot."""
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
        )
        for rank, row in enumerate(parsed, start=1)
    ]


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


def _slug_for_field_name(field_name: str) -> str:
    """Slug an English field name for use as an HTML id attribute."""
    slug = field_name.lower()
    for char in (" ", "/", "(", ")"):
        slug = slug.replace(char, "-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")


def _details_block(sheet: str, primary_field: str) -> str:
    excluded = {
        "Audio",
        "Audio Imperfective",
        "Audio Perfective",
        "AudioRefs",
        "Rank",
        primary_field,
        "Translation",
    }
    lines = [_ADD_TITLE_SCRIPT]
    for field_name in FIELD_NAMES[sheet]:
        if field_name in excluded:
            continue
        slug = _slug_for_field_name(field_name)
        lines.append(f'<div id="{slug}">{{{{{field_name}}}}}</div>')
        lines.append(f'<script>addTitle("{slug}", "&#9432;");</script>')
    return "\n".join(lines)


def build_template(sheet: str, card_index: int) -> tuple[str, str]:
    """The (qfmt, afmt) pair for `sheet`'s `card_index`-th card (0-based)."""
    header = _DECK_HEADER_HTML + _DECK_HEADER_SCRIPT

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
    details_block = _details_block(sheet, primary_field)

    if audio_side:
        qfmt = "\n".join([header, audio_html, f"{{{{{primary_field}}}}}"])
        afmt = "\n".join(
            ["{{FrontSide}}", "<hr id=answer>", "{{Translation}}", details_block]
        )
    else:
        if sheet == "Verbs":
            qfmt = "\n".join(
                [
                    header,
                    "{{Translation}}",
                    f'<div class="detail-title">{primary_field}</div>',
                ]
            )
        else:
            qfmt = "\n".join([header, "{{Translation}}"])
        afmt = "\n".join(
            [
                "{{FrontSide}}",
                "<hr id=answer>",
                audio_html,
                f"{{{{{primary_field}}}}}",
                details_block,
            ]
        )

    return qfmt, afmt
