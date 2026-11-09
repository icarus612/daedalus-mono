"""Collision analysis and qualifier classification for the Russian decks.

Two English senses that two notes share, and what separates the notes, is
`find_collisions`. Deciding what each qualifier (a Translation parenthetical,
the English Distinction cue, Additional Info) should become is `classify`.
Pure text -- no Anki imports; files are read only by `load_notes` and the CLI.
"""

import argparse
import html
import re
from collections.abc import Collection, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass, field, fields
from itertools import combinations
from pathlib import Path

from anki_tools import case_field, distinction, immutable_words_plan, mutable_words_plan
from anki_tools.audio_naming import strip_qualifier
from anki_tools.gloss_separators import normalize_gloss

IMMUTABLE_NOTE_TYPE = "Russian - Immutable Words (Ellis Version)"
PACKAGE_ROOT = Path(__file__).parent.parent
DEFAULT_SOURCE = PACKAGE_ROOT / "tests" / "data" / "source-word-list.md"
DEFAULT_VOCAB_DIR = Path(__file__).parent / "data" / "russian-vocabulary"

_MUTABLE_PARSERS = (
    ("nouns", mutable_words_plan.parse_nouns),
    ("verbs", mutable_words_plan.parse_verbs),
    ("adjectives", mutable_words_plan.parse_adjectives),
    ("adverbs", mutable_words_plan.parse_adverbs),
    ("pronouns", mutable_words_plan.parse_pronouns),
    ("numerals", mutable_words_plan.parse_numerals),
)

_TAG = re.compile(r"<[^>]*>")
_BOUNDARY = re.compile(r"<\s*(?:br\s*/?|/?\s*div[^>]*)>", re.I)
_SPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class Note:
    family: str
    note_type: str
    section: str
    deck: str
    headword: str
    guid: str
    translation: str
    russian_distinction: str
    english_distinction: str
    additional_info: str
    cases: frozenset[str]


_CASE_ABBREVIATIONS = {
    "acc": "Accusative",
    "gen": "Genitive",
    "dat": "Dative",
    "instr": "Instrumental",
    "prep": "Prepositional",
}
_CASE_PATTERN = re.compile(
    r"\b(?:(?P<full>"
    + "|".join(full for full, _ in case_field.CASE_NAMES)
    + r")\b|(?P<abbr>"
    + "|".join(_CASE_ABBREVIATIONS)
    + r")\.)",
    re.I,
)
_CASE_WORD = re.compile(r"(?<!\bin that )\bcase\b|\bgovern", re.I)


def cases_in(text: str) -> frozenset[str]:
    """Canonical case names in `text`: full names and `acc.`-style abbreviations."""
    found: set[str] = set()
    for match in _CASE_PATTERN.finditer(text):
        if match["full"]:
            found.add(match["full"].capitalize())
        else:
            found.add(_CASE_ABBREVIATIONS[match["abbr"].lower()])
    return frozenset(found)


def has_case_text(text: str) -> bool:
    """True when `text` names a case or talks about case or government."""
    return bool(cases_in(text)) or bool(_CASE_WORD.search(text))


def load_notes(
    source_md: Path | str,
    vocabulary_dir: Path | str,
    government: Mapping[str, case_field.CaseGovernment] | None = None,
) -> list[Note]:
    """Every immutable then mutable note, with provisional or governed `cases`."""
    notes: list[Note] = []
    text = Path(source_md).read_text(encoding="utf-8")
    for row in immutable_words_plan.parse_word_list(text):
        provisional = (
            cases_in(case_field.case_name(row.info))
            if row.pos == case_field.GOVERNING_SECTION
            else frozenset()
        )
        notes.append(
            _note(
                "immutable",
                IMMUTABLE_NOTE_TYPE,
                row.pos,
                row.deck,
                row.russian,
                row.guid,
                row.english,
                row.info,
                provisional,
            )
        )
    for stem, parse in _MUTABLE_PARSERS:
        for mutable in parse(str(Path(vocabulary_dir) / f"{stem}.tsv")):
            provisional = (
                cases_in(mutable.case_preposition)
                if mutable.SHEET == "Verbs"
                else frozenset()
            )
            notes.append(
                _note(
                    "mutable",
                    mutable_words_plan.NOTE_TYPE_NAMES[mutable.SHEET],
                    mutable.SHEET,
                    mutable.deck,
                    mutable.base_words[0],
                    mutable.guid,
                    mutable.translation,
                    mutable.additional_info,
                    provisional,
                )
            )
    if government is None:
        return notes
    return [
        _with_cases(note, frozenset(government[note.guid].cases))
        if note.guid in government
        else note
        for note in notes
    ]


def _note(
    family: str,
    note_type: str,
    section: str,
    deck: str,
    headword: str,
    guid: str,
    translation: str,
    additional_info: str,
    cases: frozenset[str],
) -> Note:
    return Note(
        family=family,
        note_type=note_type,
        section=section,
        deck=deck,
        headword=headword,
        guid=guid,
        translation=translation,
        russian_distinction=distinction.qualifier_of(headword),
        english_distinction=distinction.ENGLISH_DISTINCTIONS.get(headword, ""),
        additional_info=additional_info,
        cases=cases,
    )


def _with_cases(note: Note, cases: frozenset[str]) -> Note:
    values = {f.name: getattr(note, f.name) for f in fields(note)}
    values["cases"] = cases
    return Note(**values)


def _clean(text: str) -> str:
    return _SPACE.sub(" ", html.unescape(_TAG.sub("", text))).strip()


def _split_top(text: str, separator: str = " / ") -> list[str]:
    parts: list[str] = []
    depth = 0
    start = 0
    index = 0
    while index < len(text):
        char = text[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)
        elif depth == 0 and text.startswith(separator, index):
            parts.append(text[start:index])
            index += len(separator)
            start = index
            continue
        index += 1
    parts.append(text[start:])
    return parts


def _top_level_parens(text: str) -> list[tuple[int, int]]:
    """Spans of the outermost balanced parentheticals, tags skipped."""
    spans: list[tuple[int, int]] = []
    depth = 0
    start = 0
    index = 0
    while index < len(text):
        tag = _TAG.match(text, index)
        if tag:
            index = tag.end()
            continue
        char = text[index]
        if char == "(":
            if depth == 0:
                start = index
            depth += 1
        elif char == ")" and depth > 0:
            depth -= 1
            if depth == 0:
                spans.append((start, index + 1))
        index += 1
    return spans


def _pieces(translation: str) -> list[tuple[str, str]]:
    """(raw piece, cleaned segment) for every non-empty gloss segment."""
    pieces: list[tuple[str, str]] = []
    for chunk in _BOUNDARY.split(normalize_gloss(translation)):
        for part in _split_top(chunk):
            cleaned = _clean(part)
            if cleaned:
                pieces.append((part, cleaned))
    return pieces


def gloss_segments(translation: str) -> tuple[str, ...]:
    """The separate English glosses of a Translation, parentheticals kept."""
    return tuple(cleaned for _, cleaned in _pieces(translation))


def sense_key(segment: str) -> str:
    """A segment reduced to the words that identify its sense."""
    previous = None
    while previous != segment:
        previous = segment
        segment = re.sub(r"\([^()]*\)", "", segment)
    return _SPACE.sub(" ", segment.casefold()).strip(".,;: ").strip()


def senses(translation: str) -> tuple[str, ...]:
    """Distinct non-empty `sense_key`s of a Translation, in order."""
    keys: dict[str, None] = {}
    for segment in gloss_segments(translation):
        key = sense_key(segment)
        if key:
            keys[key] = None
    return tuple(keys)


_POS_ALLOWED = {
    "Adjectives": {"adj", "adjective"},
    "Base Adverbs": {"adv", "adverb"},
    "Derived Adverbs": {"adv", "adverb"},
    "Nouns": {"noun"},
    "Indeclinable Nouns": {"noun"},
    "Verbs": {"verb"},
    "Numerals": {"numeral"},
    "Pronouns": {"pronoun"},
    "Prepositions": {"prep", "preposition"},
    "Conjunctions": {"conj", "conjunction"},
    "Particles": {"particle"},
}
_LABELS = sorted(
    {label for labels in _POS_ALLOWED.values() for label in labels},
    key=len,
    reverse=True,
)
_ABBREVIATED_LABELS = {"adj", "adv", "noun", "verb"}
_LABEL_ALTERNATION = "|".join(_LABELS)
_LEADING_LABEL = re.compile(
    rf"^(?P<label>{_LABEL_ALTERNATION})(?:\.(?=$|[\s:;,(])|(?=$|[\s:;,(]))", re.I
)
_TRAILING_LABEL = re.compile(rf"\(\s*(?P<label>{_LABEL_ALTERNATION})\.?\s*\)\s*$", re.I)
_DECK_PREFIX = re.compile(r"^[A-Za-z]\.\s+")


def deck_label(deck: str) -> str:
    """The deck's own name: last `::` component without its letter prefix."""
    return _DECK_PREFIX.sub("", deck.rsplit("::", 1)[-1])


def _allowed_labels(deck: str) -> set[str]:
    return _POS_ALLOWED.get(deck_label(deck), set())


def _bare_label(cue: str) -> str:
    return cue.strip().casefold().rstrip(".")


def is_bare_pos_cue(cue: str, deck: str) -> bool:
    """The whole cue is just a part-of-speech label the deck header already shows."""
    return _bare_label(cue) in _allowed_labels(deck)


@dataclass(frozen=True)
class PosCueCounts:
    leading: int
    bare: int
    bare_abbreviated: int
    qualified: int
    trailing: int


def pos_cue_counts(notes: Sequence[Note]) -> PosCueCounts:
    """How English cues relate to part-of-speech labels."""
    leading = bare = bare_abbreviated = qualified = trailing = 0
    for note in notes:
        cue = note.english_distinction.strip()
        if not cue:
            continue
        match = _LEADING_LABEL.match(cue)
        if match:
            leading += 1
            label = match["label"].casefold()
            if is_bare_pos_cue(cue, note.deck):
                bare += 1
                bare_abbreviated += label in _ABBREVIATED_LABELS
            elif label in _allowed_labels(note.deck) and _label_residual(cue, match):
                qualified += 1
        if _TRAILING_LABEL.search(cue):
            trailing += 1
    return PosCueCounts(leading, bare, bare_abbreviated, qualified, trailing)


def _label_residual(cue: str, match: re.Match[str]) -> str:
    rest = cue[match.end() :].strip(" \t:;,")
    if rest.startswith("(") and rest.endswith(")"):
        rest = rest[1:-1].strip()
    return rest


def leading_pos_residual(cue: str, deck: str) -> str | None:
    """The cue minus a part-of-speech label the deck header already states."""
    cue = cue.strip()
    allowed = _allowed_labels(deck)
    match = _LEADING_LABEL.match(cue)
    if match and match["label"].casefold() in allowed:
        return _label_residual(cue, match)
    trailing = _TRAILING_LABEL.search(cue)
    if trailing and trailing["label"].casefold() in allowed:
        return cue[: trailing.start()].strip()
    return None


def strip_case_part(cue: str) -> str:
    """The non-case remainder of a cue: case pieces keep only their parenthetical."""
    if not has_case_text(cue):
        return cue
    kept: list[str] = []
    for piece in re.split(r"[;:]", cue):
        if not has_case_text(piece):
            if piece.strip():
                kept.append(piece.strip())
            continue
        for start, end in _top_level_parens(piece):
            inner = piece[start + 1 : end - 1].strip()
            if inner:
                kept.append(inner)
    return "; ".join(kept)


def cue_residual(cue: str, deck: str) -> str:
    """What a cue still says once case text and a header-repeating label are gone."""
    residual = strip_case_part(cue)
    leading = leading_pos_residual(residual, deck)
    return residual if leading is None else leading


def pair_separator(a: Note, b: Note) -> str:
    """What tells two notes apart on the card: `header`, `pill` or `none`."""
    if deck_label(a.deck) != deck_label(b.deck):
        return "header"
    if a.cases and b.cases and a.cases != b.cases:
        return "pill"
    return "none"


@dataclass(frozen=True)
class CollisionGroup:
    sense: str
    members: tuple[Note, ...]
    mechanism: str
    unseparated: tuple[tuple[str, str], ...]


def find_collisions(notes: Sequence[Note]) -> list[CollisionGroup]:
    """Every English sense held by two or more notes, with what separates them."""
    holders: dict[str, list[int]] = {}
    for index, note in enumerate(notes):
        for sense in senses(note.translation):
            holders.setdefault(sense, []).append(index)
    groups: list[CollisionGroup] = []
    for sense in sorted(holders):
        if len(holders[sense]) < 2:
            continue
        members = tuple(notes[index] for index in holders[sense])
        separators = {
            (a.guid, b.guid): pair_separator(a, b) for a, b in combinations(members, 2)
        }
        kinds = set(separators.values())
        if "none" in kinds:
            mechanism = "cue"
        elif kinds == {"header"}:
            mechanism = "header"
        elif kinds == {"pill"}:
            mechanism = "pill"
        else:
            mechanism = "header+pill"
        unseparated = tuple(pair for pair, kind in separators.items() if kind == "none")
        groups.append(CollisionGroup(sense, members, mechanism, unseparated))
    return groups


def format_groups_table(groups: Sequence[CollisionGroup]) -> str:
    """Tab-separated `sense  mechanism  members` table, one line per group."""
    lines = ["sense\tmechanism\tmembers"]
    for group in groups:
        members = " | ".join(
            f"{note.headword} [{deck_label(note.deck)}; "
            f"{','.join(sorted(note.cases)) or '-'}]"
            for note in group.members
        )
        lines.append(f"{group.sense}\t{group.mechanism}\t{members}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class CueUse:
    headword: str
    guid: str
    cue: str
    groups: tuple[str, ...]
    role: str
    separates: bool


def map_cues(notes: Sequence[Note], groups: Sequence[CollisionGroup]) -> list[CueUse]:
    """How each English cue serves the collision groups its note belongs to."""
    by_guid = {note.guid: note for note in notes}
    note_groups: dict[str, list[str]] = {}
    partners: dict[str, list[str]] = {}
    for group in groups:
        for member in group.members:
            note_groups.setdefault(member.guid, []).append(group.sense)
        for first, second in group.unseparated:
            partners.setdefault(first, []).append(second)
            partners.setdefault(second, []).append(first)
    uses: list[CueUse] = []
    for note in notes:
        cue = note.english_distinction
        if not cue:
            continue
        if note.guid in partners:
            role = "needed"
            mine = cue_residual(cue, note.deck)
            separates = all(
                _separates(mine, by_guid[other]) for other in partners[note.guid]
            )
        else:
            role = "covered" if note.guid in note_groups else "none"
            separates = False
        uses.append(
            CueUse(
                note.headword,
                note.guid,
                cue,
                tuple(note_groups.get(note.guid, ())),
                role,
                separates,
            )
        )
    return uses


def _separates(mine: str, other: Note) -> bool:
    theirs = cue_residual(other.english_distinction, other.deck)
    return bool(mine or theirs) and mine != theirs


_STOP_WORDS = frozenset(
    "a an the of to or and in on at for by with as is it be from into not also".split()
)


def stems(text: str) -> frozenset[str]:
    """Truncated content-word stems of `text`."""
    result: set[str] = set()
    for token in re.findall(r"[^\W_]+", _TAG.sub(" ", text).lower()):
        if len(token) < 2 or token in _STOP_WORDS:
            continue
        if len(token) > 3:
            for suffix in ("ing", "ed", "es", "s"):
                if token.endswith(suffix):
                    token = token[: -len(suffix)]
                    break
        result.add(token[:5])
    return frozenset(result)


def restates(small: str, big: str) -> bool:
    """`small` adds no content word that `big` lacks."""
    small_stems = stems(small)
    return bool(small_stems) and small_stems <= stems(big)


@dataclass(frozen=True)
class TranslationQualifier:
    text: str
    segment: int
    segments: int
    attached: bool = field(default=False, compare=False)


def translation_qualifiers(translation: str) -> list[TranslationQualifier]:
    """Top-level parentheticals of a raw gloss, in order, with their segment."""
    pieces = _pieces(translation)
    result: list[TranslationQualifier] = []
    for number, (part, _) in enumerate(pieces, 1):
        for start, end in _top_level_parens(part):
            result.append(
                TranslationQualifier(
                    text=_clean(part[start + 1 : end - 1]),
                    segment=number,
                    segments=len(pieces),
                    attached=start > 0 and not part[start - 1].isspace(),
                )
            )
    return result


def remove_parentheticals(translation: str, indexes: Collection[int]) -> str:
    """The raw gloss without the parentheticals at `indexes`, tags left intact."""
    spans = _top_level_parens(translation)
    for index in sorted(indexes, reverse=True):
        start, end = spans[index]
        before = translation[:start].rstrip()
        if not before or before.endswith(">"):
            end = len(translation) - len(translation[end:].lstrip())
        else:
            start = len(before)
        translation = translation[:start] + translation[end:]
    return translation


def outside_parentheses(text: str) -> str:
    """Text with parentheticals and tags removed and whitespace collapsed."""
    for start, end in reversed(_top_level_parens(text)):
        text = text[:start] + text[end:]
    return _SPACE.sub(" ", _TAG.sub("", text)).strip()


ACTIONS = (
    "move-to-distinction",
    "keep-inline",
    "drop-duplicate",
    "drop-header-duplicate",
    "drop-case",
    "rewrite-cue-non-case",
    "keep",
)

COLUMNS = (
    "family",
    "note type",
    "headword (keyed)",
    "guid",
    "source field",
    "qualifier text",
    "applies to",
    "action",
    "resulting Translation",
    "resulting English Distinction",
    "resulting Additional Info",
    "reason",
    "decision",
)


@dataclass(frozen=True)
class ClassificationRow:
    family: str
    note_type: str
    headword: str
    guid: str
    source_field: str
    qualifier_text: str
    applies_to: str
    action: str
    resulting_translation: str
    resulting_english_distinction: str
    resulting_additional_info: str
    reason: str
    decision: str


@dataclass(frozen=True)
class _Finding:
    source_field: str
    qualifier_text: str
    applies_to: str
    action: str
    reason: str


_GRAMMAR_MARKERS = frozenset("s es to is are one ones".split())
_PROMPT_WORDS = frozenset(
    "whom what where when how whose who something someone somebody".split()
)
_REMOVED_FROM_TRANSLATION = (
    "move-to-distinction",
    "drop-case",
    "drop-header-duplicate",
)
_WHOLE = "whole word"


def _classify_qualifier(
    qualifier: TranslationQualifier, note: Note, single_line_tail: bool
) -> tuple[str, str, str]:
    """(action, applies to, reason) for one Translation parenthetical."""
    text = qualifier.text
    sense = f"sense {qualifier.segment} of {qualifier.segments}"
    if has_case_text(text):
        return "drop-case", _WHOLE, "the Case pill already states the case"
    if _bare_label(text) in _allowed_labels(note.deck):
        return "drop-header-duplicate", _WHOLE, "repeats the deck header"
    if text.casefold() in _GRAMMAR_MARKERS or qualifier.attached:
        return "keep", _WHOLE, "grammar marker"
    words = re.findall(r"[^\W\d_]+", text.casefold())
    if words and all(word in _PROMPT_WORDS for word in words):
        return "keep-inline", sense, "prompt word for one sense"
    if qualifier.segments == 1:
        return "move-to-distinction", _WHOLE, "single sense; qualifies the whole word"
    if single_line_tail:
        return (
            "keep-inline",
            sense,
            "attaches by position to the last synonym; may cover all senses",
        )
    return "keep-inline", sense, "qualifies one sense of several"


def _is_single_line_tail(
    qualifier: TranslationQualifier,
    qualifiers: Sequence[TranslationQualifier],
    translation: str,
) -> bool:
    return (
        qualifier.segments > 1
        and qualifier.segment == qualifier.segments
        and not _BOUNDARY.search(translation)
        and all(other.segment == qualifier.segment for other in qualifiers)
    )


def _dedupe(texts: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for text in texts:
        if text and text.casefold() not in seen:
            seen.add(text.casefold())
            result.append(text)
    return result


def _classify_cue(note: Note, translation_all: str, role: str) -> tuple[str, str, str]:
    """(action, resulting cue, reason) for a note's English Distinction."""
    cue = note.english_distinction
    if has_case_text(cue):
        residual = strip_case_part(cue)
        if role == "needed" and not residual:
            return (
                "rewrite-cue-non-case",
                "",
                "needs editorial cue: the case text was the only separator",
            )
        if not residual:
            return "drop-case", "", "cue is only case text"
        if restates(residual, translation_all):
            return "drop-case", "", "non-case remainder restates the Translation"
        if role != "needed":
            return "drop-case", "", f"cue serves no unseparated pair ({role})"
        return "rewrite-cue-non-case", residual, "keeps the non-case remainder"
    leading = leading_pos_residual(cue, note.deck)
    if leading is not None:
        if not leading or restates(leading, translation_all):
            return "drop-header-duplicate", "", "repeats the deck header"
        return "drop-header-duplicate", leading, "header label removed; remainder kept"
    if restates(cue, translation_all):
        return "drop-duplicate", "", "restates the Translation"
    reason = "separates a collision" if role == "needed" else f"serves no pair ({role})"
    return "keep", cue, reason


def classify(
    notes: Sequence[Note], groups: Sequence[CollisionGroup] | None = None
) -> list[ClassificationRow]:
    """One row per qualifier of every note, with the resulting field values."""
    if groups is None:
        groups = find_collisions(notes)
    roles = {use.guid: use.role for use in map_cues(notes, groups)}
    rows: list[ClassificationRow] = []
    for note in notes:
        findings, translation, cue_result, info = _classify_note(
            note, notes, roles.get(note.guid, "none")
        )
        rows.extend(
            ClassificationRow(
                note.family,
                note.note_type,
                note.headword,
                note.guid,
                finding.source_field,
                finding.qualifier_text,
                finding.applies_to,
                finding.action,
                translation,
                cue_result,
                info,
                finding.reason,
                "",
            )
            for finding in findings
        )
    return rows


def _classify_note(
    note: Note, notes: Sequence[Note], role: str
) -> tuple[list[_Finding], str, str, str]:
    findings: list[_Finding] = []
    if note.russian_distinction:
        bare = strip_qualifier(note.headword)
        sharing = [
            other.headword
            for other in notes
            if other.guid != note.guid and strip_qualifier(other.headword) == bare
        ]
        reason = (
            "shares the bare headword with " + ", ".join(sharing)
            if sharing
            else "no other note shares the bare headword"
        )
        findings.append(
            _Finding(
                "Russian Distinction", note.russian_distinction, _WHOLE, "keep", reason
            )
        )

    qualifiers = translation_qualifiers(note.translation)
    removed: list[int] = []
    moved: list[str] = []
    for position, qualifier in enumerate(qualifiers):
        action, applies_to, reason = _classify_qualifier(
            qualifier,
            note,
            _is_single_line_tail(qualifier, qualifiers, note.translation),
        )
        findings.append(
            _Finding("Translation", qualifier.text, applies_to, action, reason)
        )
        if action in _REMOVED_FROM_TRANSLATION:
            removed.append(position)
        if action == "move-to-distinction":
            moved.append(qualifier.text)

    translation_all = _clean(_TAG.sub(" ", note.translation))
    cue_result = ""
    cue = note.english_distinction
    if cue:
        action, cue_result, reason = _classify_cue(note, translation_all, role)
        findings.append(_Finding("English Distinction", cue, _WHOLE, action, reason))

    info = note.additional_info
    resulting_info = info
    if info:
        info_stems = stems(info)
        known = set().union(
            *(stems(q.text) for q in qualifiers),
            stems(cue),
            stems(note.russian_distinction),
        )
        shared = info_stems & known
        if len(info_stems) >= 2 and len(shared) / len(info_stems) >= 0.6:
            leftover = ", ".join(sorted(info_stems - known)) or "none"
            findings.append(
                _Finding(
                    "Additional Info",
                    info,
                    _WHOLE,
                    "drop-duplicate",
                    f"{len(shared)}/{len(info_stems)} stems restate qualifiers; "
                    f"leftover: {leftover}",
                )
            )
            resulting_info = ""

    translation = remove_parentheticals(note.translation, removed)
    distinction_text = "; ".join(_dedupe([*moved, cue_result]))
    return findings, translation, distinction_text, resulting_info


def _cell(value: str) -> str:
    return re.sub(r"[\t\r\n]+", " ", value)


def format_classification_tsv(rows: Sequence[ClassificationRow]) -> str:
    """The classification as a tab-separated review sheet."""
    lines = ["\t".join(COLUMNS)]
    for row in rows:
        lines.append("\t".join(_cell(getattr(row, f.name)) for f in fields(row)))
    return "\n".join(lines) + "\n"


def parse_classification_tsv(text: str) -> list[ClassificationRow]:
    """Inverse of `format_classification_tsv`."""
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or tuple(lines[0].split("\t")) != COLUMNS:
        raise ValueError("classification TSV header does not match COLUMNS")
    rows: list[ClassificationRow] = []
    for number, line in enumerate(lines[1:], 2):
        cells = line.split("\t")
        if len(cells) != len(COLUMNS):
            raise ValueError(f"line {number}: expected {len(COLUMNS)} columns")
        rows.append(ClassificationRow(*cells))
    return rows


def check_rows(rows: Sequence[ClassificationRow], notes: Sequence[Note]) -> list[str]:
    """Violation messages for a classification; an empty list means clean."""
    by_guid = {note.guid: note for note in notes}
    problems: list[str] = []
    translation_texts: dict[str, list[str]] = {}
    cue_guids: set[str] = set()
    for row in rows:
        label = f"{row.headword} ({row.source_field})"
        note = by_guid.get(row.guid)
        if note is None:
            problems.append(f"{label}: unknown guid {row.guid}")
        elif outside_parentheses(row.resulting_translation) != outside_parentheses(
            note.translation
        ):
            problems.append(
                f"{label}: resulting Translation changes words outside brackets"
            )
        if row.action not in ACTIONS:
            problems.append(f"{label}: unknown action {row.action!r}")
        if any(
            has_case_text(q.text)
            for q in translation_qualifiers(row.resulting_translation)
        ):
            problems.append(f"{label}: resulting Translation contains case text")
        if has_case_text(row.resulting_english_distinction):
            problems.append(
                f"{label}: resulting English Distinction contains case text"
            )
        if row.source_field == "English Distinction":
            cue_guids.add(row.guid)
        elif row.source_field == "Translation":
            translation_texts.setdefault(row.guid, []).append(row.qualifier_text)
    for note in notes:
        if note.english_distinction and note.guid not in cue_guids:
            problems.append(
                f"{note.headword}: English cue has no English Distinction row"
            )
        expected = sorted(
            _cell(q.text) for q in translation_qualifiers(note.translation)
        )
        if expected != sorted(translation_texts.get(note.guid, [])):
            problems.append(
                f"{note.headword}: Translation parentheticals lack matching rows"
            )
    return problems


def _iter_pos_counts(counts: PosCueCounts) -> Iterator[str]:
    for name, value in asdict(counts).items():
        yield f"{name}: {value}"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--vocab-dir", type=Path, default=DEFAULT_VOCAB_DIR)
    parser.add_argument("--government", type=Path)
    parser.add_argument("--groups", action="store_true")
    parser.add_argument("--pos-counts", action="store_true")
    parser.add_argument("--write-classification", type=Path)
    parser.add_argument("--check-classification", type=Path)
    args = parser.parse_args(argv)

    government = (
        case_field.load_case_government(args.government) if args.government else None
    )
    notes = load_notes(args.source, args.vocab_dir, government)
    if args.groups:
        print(format_groups_table(find_collisions(notes)), end="")
    if args.pos_counts:
        print("\n".join(_iter_pos_counts(pos_cue_counts(notes))))
    fresh = format_classification_tsv(classify(notes))
    if args.write_classification:
        args.write_classification.write_text(fresh, encoding="utf-8")
    if args.check_classification:
        text = args.check_classification.read_text(encoding="utf-8")
        problems = check_rows(parse_classification_tsv(text), notes)
        if text != fresh:
            problems.append("classification differs from a fresh regeneration")
        print("\n".join(problems))
        return 1 if problems else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
