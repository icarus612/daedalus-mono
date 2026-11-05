"""The free-text case ban: no case name or roundabout case phrase in a note's prose.

Pure text -- no Anki imports.
"""

import re

FREE_TEXT_FIELDS = (
    "Translation",
    "English Distinction",
    "Russian Distinction",
    "Additional Info",
    "Case / Preposition",
)

_CASES = r"(?:nominative|genitive|dative|accusative|instrumental|prepositional)"
_NAMES = rf"\b{_CASES}\b"
_ABBR = r"(?<![\w])(?:nom|gen|dat|acc|instr|inst|prepl|prep)\.(?:\s*(?:sg|pl)\.)?"
_PHRASES = (
    r"\b(?:takes\s+(?:the\s+)?(?:(?:direct|indirect)\s+)?object"
    r"|(?:direct|indirect)\s+object"
    rf"|with\s+the\s+{_CASES}"
    r"|in\s+the\s+\w+\s+case"
    r"|governs?"
    rf"|takes\s+(?:the\s+)?{_CASES})\b"
)

BAN = re.compile("|".join([_NAMES, _ABBR, _PHRASES]), re.I)

_TAGS = re.compile(r"<[^>]*>")


def visible_text(value: str) -> str:
    """`value` with HTML tags removed, so tint markup classes are not prose."""
    return _TAGS.sub("", value)


def ban_hits(value: str) -> list[str]:
    """Every banned fragment in the visible text of `value`."""
    return [match.group(0) for match in BAN.finditer(visible_text(value))]
