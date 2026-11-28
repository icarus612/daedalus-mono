"""Noun intake: frequency list, skeleton rows, fragment validation and merging."""

import csv
import json
import re
import unicodedata
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

from anki_tools.anki_identity import guid_for_row
from anki_tools.form_fill import (
    Entries,
    OpenRussianIndex,
    cross_check,
    extract_entries,
    generate_value,
    house_stress,
    load_openrussian,
    normalize_lemma,
    openrussian_value,
)
from anki_tools.gloss_separators import normalize_gloss
from anki_tools.mutable_words_plan import NounRow, parse_nouns

DATA_DIR = Path(__file__).parent / "data" / "russian-vocabulary"

NOUN_COLUMNS = (
    "#",
    "Russian",
    "English",
    "Stress",
    "Gender",
    "Plural",
    "Genitive Sg",
    "Genitive Pl",
    "Animate",
    "Category",
    "Additional Info",
    "Examples",
    "Status",
)
FRAGMENT_COLUMNS = NOUN_COLUMNS + ("Degrees", "ipm", "flags")

FLAG_IMMUTABLE_PRESENT = "immutable-present"
FLAG_OTHER_SHEET = "other-sheet-homonym"
FLAG_ADJECTIVAL = "adjectival"
FLAG_PLURAL_ONLY = "plural-only"
FLAG_INDECLINABLE = "indeclinable"
FLAG_NO_WIKT_NOUN = "no-wiktionary-noun"
FLAG_ORDER = (
    FLAG_IMMUTABLE_PRESENT,
    FLAG_OTHER_SHEET,
    FLAG_ADJECTIVAL,
    FLAG_PLURAL_ONLY,
    FLAG_INDECLINABLE,
    FLAG_NO_WIKT_NOUN,
)

OtherHeadwords = dict[str, set[str]]

_ACUTE = "́"
_ADJECTIVAL_ENDINGS = ("ый", "ий", "ой", "ая", "яя", "ое", "ее")
_ADJECTIVAL_PLURAL_ENDINGS = ("ые", "ие")
_MASCULINE_ENDINGS = {
    "ая": ("ый", "ой"),
    "яя": ("ий",),
    "ое": ("ый", "ой"),
    "ее": ("ий",),
    "ые": ("ый", "ий"),
    "ие": ("ый", "ий"),
}
_NOUN_QUALIFIER = " (noun)"
_TOP_COUNT = 2000
_DEGREES = frozenset({"0", "1", "2", "3"})
_CYRILLIC = re.compile("[Ѐ-ӿ]")
_QUALIFIER = re.compile(r"\s*\([^)]*\)\s*$")
_PARENS = re.compile(r"\([^)]*\)")
_TIGHT_SLASH = re.compile(r"\S/|/\S")
_SHEET_FILES = {"adjectives.tsv": "Adjectives", "adverbs.tsv": "Adverbs"}
_OTHER_SHEET_COLUMNS = {
    "Verbs": ("Imperfective", "Perfective"),
    "Adjectives": ("Russian (m)",),
    "Adverbs": ("Adverb",),
    "Pronouns": ("Russian",),
    "Numerals": ("Russian",),
}
_GENDER_TAGS = {"masculine": "m", "feminine": "f", "neuter": "n"}
_OR_GENDERS = {"m": "m", "f": "f", "n": "n", "pl": "pl-only"}
_FORM_FIELDS = ("Plural", "Genitive Sg", "Genitive Pl")
_NO_PLURAL = "—"
_GENDERS = frozenset({"m", "f", "n", "pl-only", "pl", "form"})
_PLURAL_GENDERS = frozenset({"pl-only", "pl"})
_ANIMATES = frozenset({"Yes", "No"})

EXCLUDED_ALREADY_PRESENT = frozenset(
    {
        "кино",
        "кофе",
        "радио",
        "метро",
        "пальто",
        "интервью",
        "кафе",
        "шоссе",
        "такси",
        "бюро",
        "привет",
    }
)


@dataclass(frozen=True)
class FreqRow:
    lemma: str
    ipm: float


@dataclass(frozen=True)
class BuildResult:
    rows: list[dict[str, str]]
    classes: dict[str, list[str]]
    histogram: dict[str, int]
    excluded: list[str]


def load_frequency(path: str | Path) -> list[FreqRow]:
    """Common nouns (PoS exactly `s`) of the RNC list, descending by ipm."""
    rows: list[FreqRow] = []
    with open(path, encoding="utf-8-sig", newline="") as handle:
        for record in csv.DictReader(handle, delimiter="\t"):
            if record["PoS"] != "s":
                continue
            rows.append(FreqRow(record["Lemma"], float(record["Freq(ipm)"])))
    return sorted(rows, key=lambda row: -row.ipm)


def top_nouns(rows: Sequence[FreqRow], count: int) -> list[FreqRow]:
    """The first `count` rows."""
    return list(rows[:count])


def match_key(text: str) -> str:
    """Comparison key: no acute, ё folded to е, no trailing qualifier, lowercase."""
    plain = unicodedata.normalize("NFC", text).replace(_ACUTE, "")
    plain = plain.replace("ё", "е").replace("Ё", "Е")
    return _QUALIFIER.sub("", plain).lower().strip()


def missing(top: Sequence[FreqRow], nouns_rows: Sequence[NounRow]) -> list[FreqRow]:
    """Rows of `top` whose match key matches no existing noun, order preserved."""
    present = {match_key(row.russian) for row in nouns_rows}
    return [row for row in top if match_key(row.lemma) not in present]


def _noun_forms(entries: Entries, key: str) -> list[list] | None:
    noun_entries = [e for e in entries.get(key, []) if e.get("pos") == "noun"]
    if not noun_entries:
        return None
    return [form for entry in noun_entries for form in entry.get("forms", [])]


def _form_tags(forms: Sequence[list]) -> set[str]:
    return {tag for _, tags in forms for tag in tags}


def classify(
    candidate: str,
    other_headwords: OtherHeadwords,
    entries: Entries,
    immutable_words: set[str],
) -> tuple[str, ...]:
    """Flags for a candidate, in FLAG_ORDER.

    immutable-present: match key is in `immutable_words`.
    other-sheet-homonym: match key is in any set of `other_headwords`.
    adjectival: lemma ends ый ий ой ая яя ое ее, or ые/ие and is plural-only,
        or a form is tagged `adjectival`.
    plural-only: a form is tagged `plural-only`, or plural forms but no singular.
    indeclinable: a form is tagged `indeclinable`.
    no-wiktionary-noun: no kaikki entry with pos `noun`.
    """
    key = match_key(candidate)
    forms = _noun_forms(entries, normalize_lemma(candidate))
    tags = _form_tags(forms or [])
    flags = set()
    if key in immutable_words:
        flags.add(FLAG_IMMUTABLE_PRESENT)
    if any(key in headwords for headwords in other_headwords.values()):
        flags.add(FLAG_OTHER_SHEET)
    plural_only = "plural-only" in tags or ("plural" in tags and "singular" not in tags)
    if (
        key.endswith(_ADJECTIVAL_ENDINGS)
        or (plural_only and key.endswith(_ADJECTIVAL_PLURAL_ENDINGS))
        or "adjectival" in tags
    ):
        flags.add(FLAG_ADJECTIVAL)
    if plural_only:
        flags.add(FLAG_PLURAL_ONLY)
    if "indeclinable" in tags:
        flags.add(FLAG_INDECLINABLE)
    if forms is None:
        flags.add(FLAG_NO_WIKT_NOUN)
    return tuple(flag for flag in FLAG_ORDER if flag in flags)


def _or_rows(or_index: OpenRussianIndex, lemma: str) -> list[dict[str, str]]:
    return or_index.get("nouns", {}).get(normalize_lemma(lemma), [])


def _or_column(rows: Sequence[dict[str, str]], column: str) -> str | None:
    for row in rows:
        value = (row.get(column) or "").strip()
        if value:
            return value
    return None


def _kaikki_gender(tags: set[str]) -> str:
    if "plural-only" in tags:
        return "pl-only"
    for tag, gender in _GENDER_TAGS.items():
        if tag in tags:
            return gender
    return ""


def _kaikki_animate(tags: set[str]) -> str:
    if "animate" in tags:
        return "Yes"
    if "inanimate" in tags:
        return "No"
    return ""


def _decide(generated: str | None, other: str | None) -> tuple[str, str]:
    """Value kept and failure reason ('' when the value is kept)."""
    if not generated:
        return "", "missing"
    verdict = cross_check(generated, other)
    if verdict in ("agree", "spelling-only"):
        return generated, ""
    return "", verdict


def skeleton_row(
    candidate: FreqRow, entries: Entries, or_index: OpenRussianIndex
) -> dict[str, str]:
    """Fragment row for a candidate; unverifiable cells stay empty and are flagged."""
    lemma = candidate.lemma
    row = dict.fromkeys(FRAGMENT_COLUMNS, "")
    row.update({"Russian": lemma, "Status": "New", "ipm": f"{candidate.ipm:g}"})
    or_rows = _or_rows(or_index, lemma)
    forms = _noun_forms(entries, normalize_lemma(lemma)) or []
    tags = _form_tags(forms)
    problems: list[str] = []

    accented = _or_column(or_rows, "accented")
    if accented:
        row["Stress"] = house_stress(accented.replace("'", _ACUTE))
    else:
        problems.append("Stress:missing")

    or_gender = _OR_GENDERS.get(_or_column(or_rows, "gender") or "")
    gender = _kaikki_gender(tags) or or_gender or ""
    row["Gender"], reason = _decide(gender, or_gender)
    if reason:
        problems.append(f"Gender:{reason}")

    or_animate = {"1": "Yes", "0": "No"}.get(_or_column(or_rows, "animate") or "")
    animate = _kaikki_animate(tags) or or_animate or ""
    row["Animate"], reason = _decide(animate, or_animate)
    if reason:
        problems.append(f"Animate:{reason}")

    singular_only = "singular-only" in tags or _or_column(or_rows, "sg_only") == "1"
    fields = {"Russian": lemma}
    for field in _FORM_FIELDS:
        if singular_only and field != "Genitive Sg":
            row[field] = _NO_PLURAL
            continue
        generated = generate_value("Nouns", field, fields, entries)
        row[field], reason = _decide(
            generated, _openrussian_form(or_index, field, fields)
        )
        if reason:
            problems.append(f"{field}:{reason}")
    row["flags"] = ";".join(problems)
    return row


def _openrussian_form(
    or_index: OpenRussianIndex, field: str, fields: dict[str, str]
) -> str | None:
    return openrussian_value("Nouns", field, fields, or_index)


def _read_lines(path: str | Path) -> list[list[str]]:
    text = Path(path).read_text(encoding="utf-8")
    return [line.split("\t") for line in text.splitlines() if line.strip()]


def _violations_common(row: dict[str, str]) -> list[str]:
    problems = []
    if row["Status"] != "New":
        problems.append("Status must be New")
    if row["Examples"]:
        problems.append("Examples must be empty")
    english = row["English"]
    if not english.strip():
        problems.append("English is empty")
    else:
        if _CYRILLIC.search(english):
            problems.append("English contains Cyrillic")
        if normalize_gloss(english) != english or "|" in english:
            problems.append("English has a separator other than ' / '")
        if _TIGHT_SLASH.search(_PARENS.sub("", english)):
            problems.append("English has '/' without surrounding spaces")
    return problems


def _noun_vocabulary(data_dir: Path) -> tuple[set[str], set[str], set[str]]:
    rows = _read_lines(data_dir / "nouns.tsv")
    header = rows[0]
    columns = {name: header.index(name) for name in ("Category", "Gender", "Animate")}
    live = {name: {row[index] for row in rows[1:]} for name, index in columns.items()}
    return (
        live["Category"],
        live["Gender"] | _GENDERS,
        live["Animate"] | _ANIMATES,
    )


def validate_fragment(
    path: str | Path, sheet: str, data_dir: str | Path = DATA_DIR
) -> list[str]:
    """Violations of a fragment file against the sheet's rules; empty is clean."""
    if sheet not in ("Nouns", "Adjectives", "Adverbs"):
        raise ValueError(f"unknown sheet: {sheet}")
    data_dir = Path(data_dir)
    lines = _read_lines(path)
    if sheet == "Nouns":
        expected = FRAGMENT_COLUMNS
    else:
        expected = tuple(_read_lines(data_dir / f"{sheet.lower()}.tsv")[0])
    if not lines or tuple(lines[0]) != expected:
        return ["header: does not match the expected columns"]
    categories, genders, animates = (
        _noun_vocabulary(data_dir) if sheet == "Nouns" else (set(), set(), set())
    )
    violations = []
    for number, cells in enumerate(lines[1:], start=1):
        if len(cells) != len(expected):
            violations.append(f"row {number}: expected {len(expected)} cells")
            continue
        row = dict(zip(expected, cells, strict=True))
        problems = _violations_common(row)
        stress = row["Stress"]
        if stress != house_stress(stress):
            problems.append("Stress is not in house format")
        headword = _QUALIFIER.sub("", cells[1])
        if stress.replace(_ACUTE, "") != unicodedata.normalize("NFC", headword):
            problems.append("Stress does not match the headword")
        if sheet == "Nouns":
            problems += _noun_violations(row, categories, genders, animates)
        violations += [f"row {number}: {problem}" for problem in problems]
    return violations


def _noun_violations(
    row: dict[str, str], categories: set[str], genders: set[str], animates: set[str]
) -> list[str]:
    problems = []
    if row["Category"] not in categories:
        problems.append("Category is not an existing category")
    if row["Gender"] not in genders:
        problems.append("Gender is not an existing value")
    if row["Animate"] not in animates:
        problems.append("Animate is not an existing value")
    if row["Degrees"] not in _DEGREES:
        problems.append("Degrees must be 0-3")
    if not row["Plural"]:
        problems.append("Plural is empty")
    if not row["Genitive Sg"] and row["Gender"] not in _PLURAL_GENDERS:
        problems.append("Genitive Sg is empty")
    if not row["Genitive Pl"] and row["Plural"] != _NO_PLURAL:
        problems.append("Genitive Pl is empty")
    for field in ("Genitive Sg", "Genitive Pl"):
        if row[field] == _NO_PLURAL:
            problems.append(f"{field} must be empty, not a dash")
    if row["flags"]:
        problems.append("flags must be empty")
    return problems


def _split_text(path: str | Path) -> tuple[str, list[str]]:
    text = Path(path).read_text(encoding="utf-8")
    return text, text.splitlines()


def _last_rank(rows: Sequence[Sequence[str]]) -> int:
    ranks = [int(row[0]) for row in rows if row[0].isdigit()]
    return max(ranks, default=0)


def merge_rows(tsv_path: str | Path, fragment_paths: Sequence[str | Path]) -> str:
    """New text of an adjectives/adverbs TSV with fragment rows appended."""
    name = Path(tsv_path).name
    sheet = _SHEET_FILES.get(name)
    if sheet is None:
        raise ValueError(f"unknown vocabulary file: {name}")
    text, lines = _split_text(tsv_path)
    header = lines[0].split("\t")
    existing = [line.split("\t") for line in lines[1:] if line.strip()]
    seen = {guid_for_row(row[1], sheet) for row in existing}
    rank = _last_rank(existing)
    appended = []
    for fragment in fragment_paths:
        fragment_lines = _read_lines(fragment)
        if fragment_lines[0] != header:
            raise ValueError(f"{fragment}: header differs from {name}")
        for cells in fragment_lines[1:]:
            guid = guid_for_row(cells[1], sheet)
            if guid in seen:
                raise ValueError(f"duplicate GUID for {cells[1]!r}")
            seen.add(guid)
            rank += 1
            appended.append("\t".join([str(rank), *cells[1:]]))
    if not appended:
        return text
    separator = "" if text.endswith("\n") else "\n"
    return text + separator + "\n".join(appended) + "\n"


def _existing_degrees(paths: Sequence[str | Path]) -> dict[str, tuple[str, str]]:
    degrees: dict[str, tuple[str, str]] = {}
    for path in paths:
        lines = _read_lines(path)
        columns = {name: lines[0].index(name) for name in ("#", "Russian", "Degrees")}
        for cells in lines[1:]:
            degrees[cells[columns["#"]]] = (
                cells[columns["Russian"]],
                cells[columns["Degrees"]],
            )
    return degrees


def merge(
    nouns_path: str | Path,
    batch_paths: Sequence[str | Path],
    existing_degree_paths: Sequence[str | Path],
) -> str:
    """New nouns.tsv text: Degrees column added, new batch rows appended by ipm."""
    text, lines = _split_text(nouns_path)
    header = lines[0]
    existing = [line for line in lines[1:] if line.strip()]
    existing_cells = [line.split("\t") for line in existing]
    degrees = _existing_degrees(existing_degree_paths)
    ranks = {cells[0] for cells in existing_cells}
    unknown = set(degrees) - ranks
    if unknown:
        raise ValueError(f"degrees name unknown ranks: {sorted(unknown)}")
    out = [f"{header}\tDegrees"]
    seen: set[str] = set()
    for line, cells in zip(existing, existing_cells, strict=True):
        russian, value = degrees.get(cells[0], (cells[1], ""))
        if russian != cells[1]:
            raise ValueError(f"rank {cells[0]}: degrees Russian {russian!r} differs")
        if value not in _DEGREES:
            raise ValueError(f"rank {cells[0]}: missing or invalid Degrees")
        seen.add(guid_for_row(cells[1], "Nouns"))
        out.append(f"{line}\t{value}")

    new_rows: list[tuple[float, dict[str, str]]] = []
    batch_russians: set[str] = set()
    for batch in batch_paths:
        lines = _read_lines(batch)
        for cells in lines[1:]:
            row = dict(zip(lines[0], cells, strict=True))
            if row["Russian"] in batch_russians:
                raise ValueError(f"{row['Russian']!r} appears in two batches")
            guid = guid_for_row(row["Russian"], "Nouns")
            if guid in seen:
                raise ValueError(f"duplicate GUID for {row['Russian']!r}")
            seen.add(guid)
            batch_russians.add(row["Russian"])
            new_rows.append((float(row["ipm"]), row))
    rank = _last_rank(existing_cells)
    for _, row in sorted(new_rows, key=lambda item: -item[0]):
        rank += 1
        cells = [str(rank) if col == "#" else row[col] for col in NOUN_COLUMNS]
        out.append("\t".join([*cells, row["Degrees"]]))
    return "\n".join(out) + "\n"


def load_immutable_headwords(path: str | Path) -> set[str]:
    """Match keys of the Russian column of every ranked table row in the list."""
    keys = set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].isdigit() and cells[1]:
            keys.add(match_key(cells[1]))
    return keys


def adjective_lemma(noun: str, adj_lemmas: Collection[str]) -> str | None:
    """Masculine adjective lemma of an adjectival noun, if a known adjective."""
    key = match_key(noun)
    if key.endswith(("ый", "ий", "ой")):
        return noun
    for ending, replacements in _MASCULINE_ENDINGS.items():
        if not key.endswith(ending):
            continue
        stem = noun[: -len(ending)]
        for replacement in replacements:
            if match_key(stem + replacement) in adj_lemmas:
                return stem + replacement
    return None


def _sheet_headwords(data_dir: Path) -> dict[str, set[str]]:
    sheets = {"Nouns": ("Russian",), **_OTHER_SHEET_COLUMNS}
    headwords: dict[str, set[str]] = {}
    for sheet, columns in sheets.items():
        lines = _read_lines(data_dir / f"{sheet.lower()}.tsv")
        indexes = [lines[0].index(column) for column in columns]
        headwords[sheet] = {
            match_key(row[index])
            for row in lines[1:]
            for index in indexes
            if index < len(row) and row[index].strip() not in ("", "—")
        }
    return headwords


def same_spelling_pairs(
    data_dir: str | Path = DATA_DIR, immutable_headwords: Collection[str] = frozenset()
) -> list[tuple[str, tuple[str, ...]]]:
    """Match keys that appear under two or more distinct sheets, sorted by key."""
    sheets: dict[str, set[str]] = {}
    headwords = _sheet_headwords(Path(data_dir))
    headwords["Immutable"] = {match_key(word) for word in immutable_headwords}
    for sheet, keys in headwords.items():
        for key in keys:
            sheets.setdefault(key, set()).add(sheet)
    return [
        (key, tuple(sorted(names)))
        for key, names in sorted(sheets.items())
        if len(names) >= 2
    ]


def _kaikki_noun_words(jsonl_path: str | Path, keys: set[str]) -> dict[str, list[str]]:
    words: dict[str, list[str]] = {}
    with open(jsonl_path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            word = record.get("word", "")
            if record.get("pos") == "noun" and match_key(word) in keys:
                words.setdefault(match_key(word), []).append(word)
    return words


def _real_spelling(
    lemma: str, or_index: OpenRussianIndex, kaikki_words: dict[str, list[str]]
) -> str:
    """Spelling (with ё) under which the sources store the candidate."""
    key = match_key(lemma)
    exact = normalize_lemma(lemma)
    or_nouns = or_index.get("nouns", {})
    if exact in or_nouns:
        return exact
    for stored, rows in or_nouns.items():
        if match_key(stored) == key:
            return (rows[0].get("bare") or stored).strip()
    if any(normalize_lemma(word) == exact for word in kaikki_words.get(key, [])):
        return exact
    kaikki = kaikki_words.get(key, [])
    return kaikki[0] if kaikki else lemma


def build_skeleton(
    freq_path: str | Path,
    nouns_path: str | Path,
    kaikki_jsonl: str | Path,
    openrussian_dir: str | Path,
    immutable_md: str | Path,
    data_dir: str | Path = DATA_DIR,
    excluded: Collection[str] = EXCLUDED_ALREADY_PRESENT,
) -> BuildResult:
    """Skeleton rows for the top 2000 nouns missing from nouns.tsv."""
    candidates = missing(
        top_nouns(load_frequency(freq_path), _TOP_COUNT),
        parse_nouns(str(nouns_path)),
    )
    or_index = load_openrussian(openrussian_dir)
    kaikki_words = _kaikki_noun_words(
        kaikki_jsonl, {match_key(c.lemma) for c in candidates}
    )
    candidates = [
        FreqRow(_real_spelling(c.lemma, or_index, kaikki_words), c.ipm)
        for c in candidates
    ]
    entries = extract_entries(
        kaikki_jsonl, {normalize_lemma(c.lemma) for c in candidates}
    )
    immutable = load_immutable_headwords(immutable_md)
    others = _sheet_headwords(Path(data_dir))
    others.pop("Nouns")
    excluded_keys = {match_key(word) for word in excluded}
    rows: list[dict[str, str]] = []
    classes: dict[str, list[str]] = {flag: [] for flag in FLAG_ORDER}
    histogram = dict.fromkeys(FLAG_ORDER, 0)
    dropped: list[str] = []
    for candidate in candidates:
        flags = classify(candidate.lemma, others, entries, immutable)
        for flag in flags:
            classes[flag].append(candidate.lemma)
        if match_key(candidate.lemma) in excluded_keys:
            dropped.append(candidate.lemma)
            continue
        row = skeleton_row(candidate, entries, or_index)
        row["flags"] = ";".join([*flags, *filter(None, [row["flags"]])])
        if FLAG_IMMUTABLE_PRESENT in flags or FLAG_OTHER_SHEET in flags:
            row["Russian"] += _NOUN_QUALIFIER
        for flag in flags:
            histogram[flag] += 1
        rows.append(row)
    return BuildResult(rows, classes, histogram, dropped)
