"""Pure core for the mutable-words deck: Nouns, Verbs, Adjectives, Adverbs.

Turns the four `russian-vocabulary` TSV source sheets into note rows, deck
names, and card templates for `Languages::Russian::4. Mutable Words`. No
Anki imports, no `requests`, no filesystem access beyond the TSV paths
passed in.
"""

import csv
import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar, NamedTuple

from anki_tools import card_audio, case_pill, distinction, prompt_hint
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

PRONOUN_CASES: tuple[str, ...] = (
    "Genitive",
    "Dative",
    "Accusative",
    "Instrumental",
    "Prepositional",
)

PRONOUN_FORM_SLOTS = 11


class PronounSlot(NamedTuple):
    field: str
    case: str
    qualifier: str | None
    role: str | None


PRONOUN_SLOTS: tuple[PronounSlot, ...] = (
    PronounSlot("Nominative f.", "Nominative", "feminine", "f"),
    PronounSlot("Nominative n.", "Nominative", "neutral", "mn"),
    PronounSlot("Nominative pl.", "Nominative", "plural", "pl"),
    PronounSlot("Genitive", "Genitive", None, None),
    PronounSlot("Genitive f.", "Genitive", "feminine", "f"),
    PronounSlot("Genitive pl.", "Genitive", "plural", "pl"),
    PronounSlot("Genitive (н-)", "Genitive", "after a preposition", "after-prep"),
    PronounSlot("Dative", "Dative", None, None),
    PronounSlot("Dative f.", "Dative", "feminine", "f"),
    PronounSlot("Dative pl.", "Dative", "plural", "pl"),
    PronounSlot("Dative (н-)", "Dative", "after a preposition", "after-prep"),
    PronounSlot("Accusative", "Accusative", None, None),
    PronounSlot("Accusative m. living", "Accusative", "masculine, living", "mn"),
    PronounSlot("Accusative n.", "Accusative", "neutral", "mn"),
    PronounSlot("Accusative f.", "Accusative", "feminine", "f"),
    PronounSlot("Accusative pl.", "Accusative", "plural, not living", "pl"),
    PronounSlot("Accusative pl. living", "Accusative", "plural, living", "pl"),
    PronounSlot("Accusative (н-)", "Accusative", "after a preposition", "after-prep"),
    PronounSlot("Instrumental", "Instrumental", None, None),
    PronounSlot("Instrumental f.", "Instrumental", "feminine", "f"),
    PronounSlot("Instrumental pl.", "Instrumental", "plural", "pl"),
    PronounSlot(
        "Instrumental (н-)", "Instrumental", "after a preposition", "after-prep"
    ),
    PronounSlot("Prepositional", "Prepositional", None, None),
    PronounSlot("Prepositional f.", "Prepositional", "feminine", "f"),
    PronounSlot("Prepositional pl.", "Prepositional", "plural", "pl"),
)
PRONOUN_FORM_FIELDS: tuple[str, ...] = tuple(slot.field for slot in PRONOUN_SLOTS)
PRONOUN_NOTE_FORM_FIELDS: tuple[str, ...] = tuple(
    f"Form {k}" for k in range(1, PRONOUN_FORM_SLOTS + 1)
)
PRONOUN_NOTE_AUDIO_FORM_FIELDS: tuple[str, ...] = tuple(
    f"Audio Form {k}" for k in range(1, PRONOUN_FORM_SLOTS + 1)
)
PRONOUN_DERIVED_FIELDS: tuple[str, ...] = (
    "Base Tag",
    "Base Cases",
    *(
        field
        for k in range(1, PRONOUN_FORM_SLOTS + 1)
        for field in (
            f"Form {k}",
            f"Audio Form {k}",
            f"Form {k} Tag",
            f"Form {k} Cases",
        )
    ),
)

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
        "Additional Info",
        "Examples",
        "Rank",
        "Audio",
        "Russian Distinction",
        "English Distinction",
        *PRONOUN_DERIVED_FIELDS,
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


# Pronouns whose cue tells them apart from a look-alike; their Pronoun Type row
# stays off the card so the grammar label is not shown beside the cue.
_TYPE_ROW_HIDDEN = frozenset(
    {"ты", "вы", "твой", "ваш", "кто", "который", "какой", "тот", "себя", "весь"}
)


def _pronoun_type_shown(russian: str, pronoun_type: str, cue: str) -> str:
    """The Pronoun Type row's value, empty for the pronouns that carry a cue."""
    if russian in _TYPE_ROW_HIDDEN:
        return ""
    return pronoun_type


class CaseRow(NamedTuple):
    qualifier: str | None
    role: str | None
    cases: tuple[str, ...]


class PronounForm(NamedTuple):
    text: str
    audio_word: str
    rows: tuple[CaseRow, ...]


_SAMYJ_HOMOGRAPHS = frozenset({"самого", "самой", "самому", "самом"})


def pronoun_audio_word(headword: str, form_text: str) -> str:
    """The audio word for a form: its bare spelling, except the forms of
    `самый` that spell like forms of `сам` and so need their own clips.
    """
    bare = bare_form(form_text)
    if strip_qualifier(headword) == "самый" and bare in _SAMYJ_HOMOGRAPHS:
        return f"{bare}-самый"
    return bare


def render_tag(qualifier: str, role: str) -> str:
    """The inline qualifier tag, e.g. `(feminine)`."""
    return f'<span class="aspect form-{role}">({qualifier})</span>'


_QUALIFIER_ROLES: dict[str, str] = {
    **{
        slot.qualifier: slot.role
        for slot in PRONOUN_SLOTS
        if slot.qualifier and slot.role
    },
    "masculine": "mn",
    "masculine / neutral": "mn",
    "masculine, not living": "mn",
    "without a preposition": "plain-prep",
}


def render_cases(rows: Sequence[CaseRow]) -> str:
    """Plain text: `Dative, Prepositional`, rows joined by `; `, a qualifier
    in brackets after its row's cases. The card script turns it into pills.
    """
    parts = []
    for row in rows:
        if row.qualifier and _QUALIFIER_ROLES.get(row.qualifier) != row.role:
            raise ValueError(f"qualifier {row.qualifier!r} has no role {row.role!r}")
        text = ", ".join(row.cases)
        parts.append(f"{text} ({row.qualifier})" if row.qualifier else text)
    return "; ".join(parts)


def _tag_and_cases(rows: Sequence[CaseRow]) -> tuple[str, str]:
    """(tag HTML, cases text); a lone qualified row hoists its tag out."""
    if len(rows) == 1 and rows[0].qualifier:
        return render_tag(rows[0].qualifier, rows[0].role or ""), render_cases(rows)
    return "", render_cases(rows)


class _Cell(NamedTuple):
    case: str
    text: str
    qualifier: str | None
    role: str | None


def _case_rows(cells: Sequence[_Cell]) -> tuple[CaseRow, ...]:
    """Group `cells` (canonical order) by qualifier, first appearance first."""
    grouped: dict[str | None, tuple[str | None, list[str]]] = {}
    for cell in cells:
        _role, cases = grouped.setdefault(cell.qualifier, (cell.role, []))
        if cell.case not in cases:
            cases.append(cell.case)
    return tuple(
        CaseRow(
            qualifier,
            role,
            tuple(case for case in case_pill.CASE_ORDER if case in cases),
        )
        for qualifier, (role, cases) in grouped.items()
    )


@dataclass(frozen=True)
class PronounRow:
    rank: int
    russian: str
    translation: str
    stress: str
    pronoun_type: str
    additional_info: str
    examples: str
    case_forms: tuple[str, ...] = ("",) * len(PRONOUN_SLOTS)

    SHEET: ClassVar[str] = "Pronouns"

    @property
    def base_words(self) -> tuple[str, ...]:
        return (self.russian,)

    def _cells(self) -> tuple[list[_Cell], list[_Cell]]:
        """(base cells, form cells), each in canonical order."""
        headword = strip_qualifier(self.russian)
        filled = {
            slot.field: text
            for slot, text in zip(PRONOUN_SLOTS, self.case_forms, strict=True)
            if text
        }
        base: list[_Cell] = []
        forms: list[_Cell] = []
        if filled and headword != "себя":
            has_other_nominative = any(
                slot.case == "Nominative" and slot.field in filled
                for slot in PRONOUN_SLOTS
            )
            base.append(
                _Cell(
                    "Nominative",
                    headword,
                    "masculine" if has_other_nominative else None,
                    "mn" if has_other_nominative else None,
                )
            )
        for slot in PRONOUN_SLOTS:
            text = filled.get(slot.field)
            if not text:
                continue
            qualifier, role = slot.qualifier, slot.role
            if slot.field == slot.case:
                if f"{slot.case} (н-)" in filled:
                    qualifier, role = "without a preposition", "plain-prep"
                elif any(
                    other.case == slot.case and other.field in filled
                    for other in PRONOUN_SLOTS
                    if other.field != slot.field
                ):
                    qualifier = (
                        "masculine, not living"
                        if slot.case == "Accusative"
                        else "masculine / neutral"
                    )
                    role = "mn"
            cell = _Cell(slot.case, text, qualifier, role)
            (base if bare_form(text) == headword else forms).append(cell)
        return base, forms

    def base_rows(self) -> tuple[CaseRow, ...]:
        rows = _case_rows(self._cells()[0])
        return tuple(sorted(rows, key=lambda row: row.role == "f"))

    def forms(self) -> tuple[PronounForm, ...]:
        """The distinct non-headword words, at most `PRONOUN_FORM_SLOTS`."""
        groups: dict[str, list[_Cell]] = {}
        for cell in self._cells()[1]:
            groups.setdefault(bare_form(cell.text), []).append(cell)
        if len(groups) > PRONOUN_FORM_SLOTS:
            raise ValueError(
                f"{self.russian!r} has {len(groups)} forms, "
                f"more than {PRONOUN_FORM_SLOTS}"
            )
        return tuple(
            PronounForm(
                cells[0].text,
                pronoun_audio_word(self.russian, cells[0].text),
                _case_rows(cells),
            )
            for cells in groups.values()
        )

    @property
    def audio_words(self) -> tuple[str, ...]:
        words = list(self.base_words)
        for form in self.forms():
            if form.audio_word not in words:
                words.append(form.audio_word)
        return tuple(words)

    @property
    def guid(self) -> str:
        return guid_for_row(self.base_words[0], self.SHEET)

    @property
    def deck(self) -> str:
        return subdeck_name(self.SHEET)

    def fields(self) -> list[str]:
        names = audio_names(self.russian)
        cue = distinction.english_distinction(self.russian)
        base_tag, base_cases = _tag_and_cases(self.base_rows())
        forms = self.forms()
        form_fields: list[str] = []
        for k in range(PRONOUN_FORM_SLOTS):
            if k < len(forms):
                form = forms[k]
                tag, cases = _tag_and_cases(form.rows)
                form_fields += [
                    form.text,
                    audio_field_value(audio_names(form.audio_word)),
                    tag,
                    cases,
                ]
            else:
                form_fields += ["", "", "", ""]
        return [
            headword_text(self.russian),
            self.translation,
            self.stress,
            _pronoun_type_shown(self.russian, self.pronoun_type, cue),
            self.additional_info,
            self.examples,
            str(self.rank),
            audio_field_value(names),
            distinction.russian_distinction(self.russian),
            cue,
            base_tag,
            base_cases,
            *form_fields,
        ]


def bare_form(form: str) -> str:
    """`form` with its stress marks removed."""
    return form.replace("\u0301", "")


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
                    additional_info=row["Additional Info"],
                    examples=row["Examples"],
                    case_forms=tuple(row[field] for field in PRONOUN_FORM_FIELDS),
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


TEMPLATES_PER_SHEET = {"Pronouns": 2 + 2 * PRONOUN_FORM_SLOTS}
PRONOUN_FORM_STATE_KEY = "__mutablePronounFormChoice"
_FORM_LINES_ID = "form-lines"
_CASE_ORDER_JSON = json.dumps(list(case_pill.CASE_ORDER))

_REVEAL_SCRIPT = """(function () {
  var order = @@ORDER@@;
  var own = {};
  document.querySelectorAll(".case-pills .case-row").forEach(function (row) {
    own[row.getAttribute("data-role")] = true;
  });
  var gendered = own.mn || own.f || own.pl;
  var found = [];
  document.querySelectorAll("#form-lines .form-line").forEach(function (line) {
    var src = line.querySelector(".form-src");
    if (!src) return;
    var titles = [];
    var first = order.length;
    src.querySelectorAll(".case-row").forEach(function (row) {
      var role = row.getAttribute("data-role");
      if (gendered && role && !own[role]) return;
      var cases = row.getAttribute("data-cases").split(",");
      first = Math.min(first, order.indexOf(cases[0]));
      var qual = row.getAttribute("data-qual");
      var html = "";
      cases.forEach(function (c) {
        html += '<span class="case-pill case-' + c.toLowerCase() + '">' + c + "</span>";
      });
      if (qual) html += '<span class="aspect form-' + role + '">(' + qual + ")</span>";
      titles.push('<span class="title-row">' + html + "</span>");
    });
    if (!titles.length) return;
    found.push({
      line: line,
      slot: Number(line.id.split("-")[1]),
      first: first,
      title: titles.join(""),
    });
  });
  found.sort(function (a, b) {
    return a.first - b.first || a.slot - b.slot;
  });
  var container = document.getElementById("form-lines");
  found.forEach(function (item) {
    container.appendChild(item.line);
    item.line.hidden = false;
    var word = document.getElementById("form-" + item.slot + "-word");
    addTitle("form-" + item.slot + "-word", item.title);
    var title = word.querySelector(".title");
    if (title) item.line.insertBefore(title, item.line.querySelector(".form-src"));
  });
})();"""

_CASE_ROWS_SCRIPT = """(function () {
  var roles = @@ROLES@@;
  document.querySelectorAll(".case-pills, .form-src").forEach(function (box) {
    if (box.querySelector(".case-row")) return;
    var text = box.textContent.trim();
    if (!text) return;
    var rows = text.split(";");
    var html = "";
    rows.forEach(function (raw) {
      var m = raw.trim().match(/^(.*?)(?:\\s*\\(([^()]*)\\))?$/);
      var cases = m[1].split(",").map(function (c) { return c.trim(); });
      var qual = m[2] || "";
      var role = qual ? roles[qual] || "" : "";
      html += '<div class="case-row" data-cases="' + cases.join(",") +
        '" data-qual="' + qual + '" data-role="' + role + '">';
      cases.forEach(function (c) {
        html += '<span class="case-pill case-' + c.toLowerCase() + '">' + c + "</span>";
      });
      if (qual && rows.length > 1)
        html += '<span class="aspect form-' + role + '">(' + qual + ")</span>";
      html += "</div>";
    });
    box.innerHTML = html;
  });
})();"""


def _case_rows_script() -> str:
    return _CASE_ROWS_SCRIPT.replace("@@ROLES@@", json.dumps(_QUALIFIER_ROLES))


def _reveal_script() -> str:
    reveal = _REVEAL_SCRIPT.replace("@@ORDER@@", _CASE_ORDER_JSON)
    return _case_rows_script() + "\n" + reveal


def _form_line(slot: int) -> str:
    """The hidden counterpart line for slot `slot` (0 is the headword)."""
    if slot == 0:
        word, audio, cases, guard = "Russian", "Audio", "Base Cases", "Base Cases"
    else:
        word = guard = f"Form {slot}"
        audio, cases = f"Audio Form {slot}", f"Form {slot} Cases"
    play_fn = f"__pronounFormPlay_{slot}"
    line_id = f"form-{slot}"
    line = _wrap(
        line_id,
        "\n".join(
            [
                '<div class="form-pair">',
                card_audio.audio_line_block(
                    audio, f"{line_id}-audio", line_id, play_fn
                ),
                _wrap(f"{line_id}-word", f"{{{{{word}}}}}"),
                "</div>",
            ]
        ),
        f'<div class="form-src" hidden>{{{{{cases}}}}}</div>',
        attrs=(
            f'class="form-line {card_audio.TAPPABLE_CLASS}" hidden'
            f' onclick="{play_fn}(event)"'
        ),
    )
    return f"{{{{#{guard}}}}}{line}{{{{/{guard}}}}}"


def _form_lines(slots: Sequence[int]) -> str:
    return _wrap(_FORM_LINES_ID, *(_form_line(slot) for slot in slots))


def _pill_rows_div(cases_field: str) -> str:
    return (
        f'<div class="{case_pill.PILL_WRAPPER_CLASS}">{{{{{cases_field}}}}}</div>'
        f"<script>{_case_rows_script()}</script>"
    )


def _with_hint_and_pills(side_html: str, pills_html: str) -> str:
    side_html = prompt_hint.add_prompt_hint(side_html, distinction.ENGLISH_FIELD)
    return case_pill.insert_after_anchor(side_html, pills_html)


def _pronoun_form_template(slot: int, *, russian_side: bool) -> tuple[str, str]:
    """The (qfmt, afmt) pair for one side of pronoun form slot `slot`."""
    form = f"Form {slot}"
    audio_html = card_audio.audio_block(
        f"Audio {form}", "audio", PRONOUN_FORM_STATE_KEY
    )
    russian_div = f'<div id="russian">{{{{{form}}}}}</div>'
    translation_div = _translation_div("Pronouns", "Russian", f"{{{{{form} Tag}}}}")
    pills_html = _pill_rows_div(f"{form} Cases")
    lines_html = _form_lines(
        [0, *(j for j in range(1, PRONOUN_FORM_SLOTS + 1) if j != slot)]
    )
    info_div = '<div id="additional-info">{{Additional Info}}</div>'
    script = "\n".join(
        [
            "<script>",
            _ADD_TITLE_FUNCTION,
            _reveal_script(),
            'addTitle("additional-info", "&#9432;");',
            "</script>",
        ]
    )

    if russian_side:
        front = _wrap("front", _DECK_HEADER_HTML, audio_html, russian_div)
        qfmt = _add_russian_cue(front + _DECK_HEADER_SCRIPT)
        back = _wrap("back", translation_div, lines_html, info_div)
        back = _with_hint_and_pills(back, pills_html)
    else:
        front = _wrap("front", _DECK_HEADER_HTML, translation_div)
        qfmt = _with_hint_and_pills(front, pills_html) + _DECK_HEADER_SCRIPT
        back = _wrap("back", audio_html, russian_div, lines_html, info_div)
        back = _add_russian_cue(back)
    return f"{{{{#{form}}}}}{qfmt}{{{{/{form}}}}}", "\n".join(
        ["{{FrontSide}}", back, script]
    )


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
        *PRONOUN_FORM_FIELDS,
        *PRONOUN_DERIVED_FIELDS,
    }
    if sheet == "Verbs":
        excluded |= set(_ASPECT_COUNTERPART)
    return [name for name in FIELD_NAMES[sheet] if name not in excluded]


_DETAIL_LABELS = {"Neuter": "Neutral"}


def _detail_row(field_name: str) -> str:
    """One labelled row, label included inside the field's own conditional so
    an empty field leaves no element behind.
    """
    slug = _slug_for_field_name(field_name)
    return (
        f"{{{{#{field_name}}}}}"
        f'<div id="{slug}">'
        f'<div class="detail-label">{_DETAIL_LABELS.get(field_name, field_name)}</div>'
        f'<div class="detail-value">{{{{{field_name}}}}}</div>'
        f"</div>"
        f"{{{{/{field_name}}}}}"
    )


def _detail_block(
    sheet: str,
    primary_field: str,
    extra_titles: Sequence[tuple[str, str]] = (),
    extra_script: str = "",
) -> tuple[str, str, str]:
    """(details, standalone, script) for `sheet`.

    `details` is the `#details` grid of labelled rows; `standalone` holds the
    `Additional Info` and `Examples` divs, which keep the reference note
    type's `.title`/`.body` treatment via `addTitle` (a verbatim port of the
    reference's own function) and so stay outside the grid. `script` is empty
    when nothing calls `addTitle`; `extra_script` runs after the calls.
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
        "\n".join(
            part
            for part in ("<script>", _ADD_TITLE_FUNCTION, *calls, extra_script)
            if part
        )
        + "\n</script>"
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
    "\talign-items: baseline;\n"
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


_FORM_ROLE_COLOURS: dict[str, tuple[str, str]] = {
    "mn": ("#00796b", "#4db6ac"),
    "f": ("#ad1457", "#f48fb1"),
    "pl": ("#6d4c41", "#bcaaa4"),
    "after-prep": ("#605C8B", "#b3aee0"),
    "plain-prep": ("#656565", "#9e9e9e"),
    "fixed": ("#546e7a", "#b0bec5"),
}

_FORM_LINE_SLOTS = range(PRONOUN_FORM_SLOTS + 1)
_FORM_LINE_IDS = ", ".join(f"#form-{j}" for j in _FORM_LINE_SLOTS)
_FORM_AUDIO_IDS = ", ".join(f"#form-{j}-audio" for j in _FORM_LINE_SLOTS)
_FORM_WORD_IDS = ", ".join(f"#form-{j}-word" for j in _FORM_LINE_SLOTS)

PRONOUN_FORM_CSS = (
    ".form-pair {\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "}\n\n"
    "#form-lines {\n"
    "\tdisplay: grid;\n"
    "\tgrid-template-columns: max-content minmax(0, auto);\n"
    "\tcolumn-gap: .8rem;\n"
    "\trow-gap: .5rem;\n"
    "\talign-items: start;\n"
    "\twidth: fit-content;\n"
    "\tmax-width: 100%;\n"
    "\tmargin: 1rem auto 0;\n"
    "\tpadding-top: 1rem;\n"
    "\tborder-top: 1px solid #ccc;\n"
    "}\n\n"
    ".nightMode #form-lines {\n"
    "\tborder-top-color: #555;\n"
    "}\n\n"
    ".case-row {\n"
    "\ttext-align: center;\n"
    "\tpadding: calc(.1rem + 3px) 0;\n"
    "}\n\n"
    ".case-row .case-pill, .title-row .case-pill {\n"
    "\tdisplay: inline-block;\n"
    "}\n\n"
    ".case-row .aspect, .title-row .aspect {\n"
    "\tmargin-left: .3rem;\n"
    "}\n\n"
    ".form-line[hidden], .form-src[hidden], #form-lines .hidden {\n"
    "\tdisplay: none !important;\n"
    "}\n\n"
    f".form-line, {_FORM_LINE_IDS} {{\n"
    "\tdisplay: contents;\n"
    "}\n\n"
    ".form-line .form-pair {\n"
    "\tjustify-self: start;\n"
    "\ttext-align: left;\n"
    "}\n\n"
    ".form-line .title {\n"
    "\tfont-size: 1.2rem;\n"
    "\tmargin-top: .2rem;\n"
    "\tmargin-right: 0;\n"
    "\tmin-width: 0;\n"
    "\tflex: 0 1 auto;\n"
    "\tdisplay: block;\n"
    "\ttext-align: left;\n"
    "\tline-height: 1.6;\n"
    "}\n\n"
    ".form-line .title-row {\n"
    "\tdisplay: block;\n"
    "}\n\n"
    ".form-line .title .case-pill {\n"
    "\tmargin-right: .3rem;\n"
    "}\n\n"
    ".form-line .title .aspect {\n"
    "\twhite-space: normal;\n"
    "\tmargin-left: 0;\n"
    "}\n\n"
    ".form-line .body {\n"
    "\tfont-size: 1.2rem;\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "}\n\n"
    ".form-line > span, .form-line > div:not(.form-src):not(.title),"
    f" {_FORM_AUDIO_IDS}, {_FORM_WORD_IDS} {{\n"
    "\tdisplay: inline-flex;\n"
    "\talign-items: center;\n"
    "\tgap: .4rem;\n"
    "}\n\n"
    + "\n\n".join(
        f".aspect.form-{role} {{\n\tcolor: {day};\n}}"
        for role, (day, _night) in _FORM_ROLE_COLOURS.items()
    )
    + "\n\n"
    + "\n\n".join(
        f".nightMode .aspect.form-{role} {{\n\tcolor: {night};\n}}"
        for role, (_day, night) in _FORM_ROLE_COLOURS.items()
    )
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
        "\tgrid-template-columns: max-content minmax(0, auto);\n"
        "\tcolumn-gap: .6rem;\n"
        "\twidth: fit-content;\n"
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
        f"{_ASPECT_COLOUR_CSS}\n\n"
        f"{PRONOUN_FORM_CSS}"
    )


EXTRA_CSS = _build_extra_css()


def _translation_div(
    sheet: str, primary_field: str, tag_html: str | None = None
) -> str:
    """`{{Translation}}`, with the card's own tag named after it.

    Verbs name the card's aspect, pronouns carry `tag_html`; every other sheet
    shows the gloss bare. The reverse cards already qualified their prompt this
    way; the forward cards' answer side showed the gloss bare, so nothing on the
    card said which aspect the headword itself was.
    """
    if sheet == "Pronouns":
        return f'<div id="translation">{{{{Translation}}}} {tag_html or ""}</div>'
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
        card_count = TEMPLATES_PER_SHEET.get(sheet, 2)
        if card_index not in range(card_count):
            raise ValueError(f"{sheet} card_index out of range: {card_index!r}")
        if sheet == "Pronouns" and card_index >= 2:
            form_index = card_index - 2
            return _pronoun_form_template(
                form_index % PRONOUN_FORM_SLOTS + 1,
                russian_side=form_index < PRONOUN_FORM_SLOTS,
            )
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
    pronoun_pills = ""
    extra_script = ""
    translation_tag = None
    if sheet == "Pronouns":
        aspect_div = _form_lines(range(1, PRONOUN_FORM_SLOTS + 1))
        extra_script = _reveal_script()
        pronoun_pills = (
            f"{{{{#Base Cases}}}}{_pill_rows_div('Base Cases')}{{{{/Base Cases}}}}"
        )
        translation_tag = (
            "{{Base Tag}}{{^Form 1}}"
            '<span class="aspect form-fixed">(never changes)</span>{{/Form 1}}'
        )
    details_html, standalone_html, detail_script = _detail_block(
        sheet, primary_field, extra_titles, extra_script
    )
    russian_div = f'<div id="russian">{{{{{primary_field}}}}}</div>'
    translation_div = _translation_div(sheet, primary_field, translation_tag)
    has_case = "Case" in FIELD_NAMES[sheet]

    if audio_side:
        front = _wrap("front", _DECK_HEADER_HTML, audio_html, russian_div)
        qfmt = _add_russian_cue(front + _DECK_HEADER_SCRIPT)
        back = _wrap("back", translation_div, aspect_div, details_html, standalone_html)
        back = prompt_hint.add_prompt_hint(back, distinction.ENGLISH_FIELD)
        if has_case:
            back = case_pill.add_pill_block(back)
        if pronoun_pills:
            back = case_pill.insert_after_anchor(back, pronoun_pills)
    else:
        front = _wrap("front", _DECK_HEADER_HTML, translation_div)
        front = prompt_hint.add_prompt_hint(front, distinction.ENGLISH_FIELD)
        if has_case:
            front = case_pill.add_pill_block(front)
        if pronoun_pills:
            front = case_pill.insert_after_anchor(front, pronoun_pills)
        qfmt = front + _DECK_HEADER_SCRIPT
        back = _wrap(
            "back", audio_html, russian_div, aspect_div, details_html, standalone_html
        )
        back = _add_russian_cue(back)

    if sheet == "Verbs":
        qfmt = f"{{{{#{primary_field}}}}}{qfmt}{{{{/{primary_field}}}}}"

    return qfmt, "\n".join(p for p in ("{{FrontSide}}", back, detail_script) if p)
