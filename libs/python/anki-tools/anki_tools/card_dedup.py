"""Duplicate-information check for one rendered card side.

Every piece of information appears once per side. A side's rendered HTML is
split into labelled segments and three rules run over them:

- equal: two segments are equal after normalization.
- contained: every content word of a cue or info segment appears in one other
  single segment, or (cues only) in the union of the side's other segments.
- case-name: a case name appears more than once across the pills and the text.

The helper carries no exemptions of its own; callers pass an `Exemptions`.
Pure text -- no Anki imports.
"""

import re
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser

CASE_NAMES = (
    "Nominative",
    "Genitive",
    "Dative",
    "Accusative",
    "Instrumental",
    "Prepositional",
)

HEADWORD = "headword"
SENSE = "sense"
PAREN = "paren"
GLOSS_ALL = "gloss-all"
CUE = "cue"
INFO = "info"
DETAIL = "detail"
PILL = "pill"
EXAMPLES = "examples"
LABEL = "label"
OTHER = "other"

RULE_EQUAL = "equal"
RULE_CONTAINED = "contained"
RULE_UNION = "union"
RULE_CASE = "case-name"

_CUE_IDS = ("prompt-hint", "russian-distinction")
_HEADWORD_IDS = ("russian", "perfective-word", "imperfective-word")
_IGNORED_IDS = ("path", "deck")
_IGNORED_TAGS = ("script", "style", "audio", "button", "template")
_VOID_TAGS = ("br", "hr", "img", "input", "meta", "link", "wbr")
_BREAK_TAGS = ("br", "div", "p", "li", "tr", "hr")
_PAREN_TEXT = re.compile(r"\(([^()]*)\)")
_WORD = re.compile(r"[^\W\d_]+(?:['-][^\W\d_]+)*")
_COMBINING = dict.fromkeys(range(0x0300, 0x0370))


@dataclass(frozen=True)
class Segment:
    kind: str
    text: str
    label: str = ""
    derived: bool = False

    @property
    def norm(self) -> str:
        return normalize(self.text)


@dataclass(frozen=True)
class Exemptions:
    """Every way a caller relaxes the rules. Empty means strict."""

    ignored_labels: frozenset[str] = frozenset()
    equal_skip_kinds: frozenset[str] = frozenset()
    equal_skip_labels: frozenset[str] = frozenset()
    equal_skip_kind_pairs: frozenset[tuple[str, str]] = frozenset()
    stopwords: frozenset[str] = frozenset()
    case_words_allowed: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Violation:
    rule: str
    texts: tuple[str, ...]

    def __str__(self) -> str:
        return f"{self.rule}: " + " | ".join(self.texts)


def normalize(text: str) -> str:
    """Lowercase, drop stress marks, fold ё to е, keep only letters and digits."""
    folded = unicodedata.normalize("NFD", text).translate(_COMBINING)
    folded = unicodedata.normalize("NFC", folded).lower().replace("ё", "е")
    return " ".join(re.findall(r"[^\W_]+", folded))


def content_words(text: str, stopwords: frozenset[str] = frozenset()) -> set[str]:
    return {
        word
        for word in normalize(text).split()
        if word not in stopwords and not word.isdigit()
    }


class _Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, str, bool]] = []
        self.pieces: list[tuple[str, str]] = []
        self.segments: list[Segment] = []
        self.label = ""
        self.pill_cases: list[str] = []

    def _kind(self) -> str:
        return self.stack[-1][1] if self.stack else OTHER

    def _ignored(self) -> bool:
        return any(ignored for _, _, ignored in self.stack)

    def _flush(self) -> None:
        merged: list[tuple[str, str]] = []
        for kind, text in self.pieces:
            if merged and merged[-1][0] == kind:
                merged[-1] = (kind, merged[-1][1] + text)
            else:
                merged.append((kind, text))
        self.pieces = []
        for kind, text in merged:
            text = " ".join(text.split())
            if text:
                self._emit(kind, text)

    def _emit(self, kind: str, text: str) -> None:
        if kind == LABEL:
            self.label = text
            return
        if kind == CUE:
            wrapped = text.startswith("(") and text.endswith(")")
            self.segments.append(Segment(CUE, text[1:-1] if wrapped else text))
        elif kind == SENSE:
            self._emit_gloss_line(text)
        elif kind == DETAIL:
            self.segments.append(Segment(DETAIL, text, label=self.label))
        else:
            self.segments.append(Segment(kind, text))

    def _emit_gloss_line(self, text: str) -> None:
        self.segments.append(Segment(GLOSS_ALL, text, derived=True))
        for match in _PAREN_TEXT.finditer(text):
            self.segments.append(Segment(PAREN, match.group(1)))
        bare = _PAREN_TEXT.sub(" ", text)
        for sense in bare.split(" / "):
            sense = " ".join(sense.split())
            if sense:
                self.segments.append(Segment(SENSE, sense))

    def _classify(self, tag: str, attrs: dict[str, str]) -> tuple[str, bool]:
        element_id = attrs.get("id", "")
        classes = attrs.get("class", "").split()
        if tag in _IGNORED_TAGS or "hidden" in classes or element_id in _IGNORED_IDS:
            return OTHER, True
        if "case-pills" in classes:
            return PILL, True
        if element_id == "translation":
            return SENSE, False
        if element_id in _CUE_IDS:
            return CUE, False
        if element_id in _HEADWORD_IDS:
            return HEADWORD, False
        if element_id == "additional-info":
            return INFO, False
        if element_id == "examples":
            return EXAMPLES, False
        if "detail-label" in classes or "aspect" in classes:
            return LABEL, False
        if "detail-value" in classes:
            return DETAIL, False
        return self._kind(), False

    def handle_starttag(self, tag: str, attrs_list: list) -> None:
        attrs = {name: value or "" for name, value in attrs_list}
        if tag in _BREAK_TAGS:
            self._flush()
        if tag in _VOID_TAGS:
            return
        kind, ignored = self._classify(tag, attrs)
        if kind == PILL and not self._ignored():
            for name in attrs.get("data-case", "").split(","):
                name = name.strip()
                if name:
                    self.segments.append(Segment(PILL, name))
        self.stack.append((tag, kind, ignored))

    def handle_startendtag(self, tag: str, attrs_list: list) -> None:
        if tag in _BREAK_TAGS:
            self._flush()

    def handle_endtag(self, tag: str) -> None:
        if tag in _BREAK_TAGS:
            self._flush()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if not self._ignored():
            self.pieces.append((self._kind(), data))

    def handle_comment(self, data: str) -> None:
        return


def segments(side_html: str) -> list[Segment]:
    collector = _Collector()
    collector.feed(side_html)
    collector.close()
    collector._flush()
    return collector.segments


def _case_count(text: str, name: str) -> int:
    return len(re.findall(rf"(?<![^\W\d_]){name}(?![^\W\d_])", text, re.I))


def _equal_violations(found: list[Segment], exempt: Exemptions) -> list[Violation]:
    seen: dict[str, Segment] = {}
    out: list[Violation] = []
    for segment in found:
        if segment.derived or segment.kind in exempt.equal_skip_kinds:
            continue
        if segment.kind == DETAIL and segment.label in exempt.equal_skip_labels:
            continue
        norm = segment.norm
        if not norm:
            continue
        first = seen.get(norm)
        if first is None:
            seen[norm] = segment
        elif (first.kind, segment.kind) not in exempt.equal_skip_kind_pairs:
            out.append(Violation(RULE_EQUAL, (first.text, segment.text)))
    return out


def _contained_violations(found: list[Segment], exempt: Exemptions) -> list[Violation]:
    out: list[Violation] = []
    for index, subject in enumerate(found):
        if subject.kind not in (CUE, INFO):
            continue
        words = content_words(subject.text, exempt.stopwords)
        if not words:
            continue
        others = [
            other
            for other_index, other in enumerate(found)
            if other_index != index and other.kind != EXAMPLES
        ]
        for other in others:
            if words <= content_words(other.text, exempt.stopwords):
                out.append(Violation(RULE_CONTAINED, (subject.text, other.text)))
                break
        else:
            if subject.kind == CUE:
                union: set[str] = set()
                for other in others:
                    if other.derived:
                        continue
                    union |= content_words(other.text, exempt.stopwords)
                if words <= union:
                    out.append(Violation(RULE_UNION, (subject.text,)))
    return out


def _case_violations(found: list[Segment], exempt: Exemptions) -> list[Violation]:
    out: list[Violation] = []
    for name in CASE_NAMES:
        if name.lower() in exempt.case_words_allowed:
            continue
        hits = [
            segment.text
            for segment in found
            if not segment.derived and segment.kind not in (HEADWORD, EXAMPLES)
            for _ in range(_case_count(segment.text, name))
        ]
        if len(hits) > 1:
            out.append(Violation(RULE_CASE, (name, *hits)))
    return out


def violations(side_html: str, exempt: Exemptions = Exemptions()) -> list[Violation]:
    """Every rule broken by one rendered side, in rule order."""
    found = [
        segment
        for segment in segments(side_html)
        if not (segment.kind == DETAIL and segment.label in exempt.ignored_labels)
    ]
    return (
        _equal_violations(found, exempt)
        + _contained_violations(found, exempt)
        + _case_violations(found, exempt)
    )
