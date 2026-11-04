"""Compare source-built note values with what a collection stores.

Pure: builds the expected notes from the word list and vocabulary TSVs and
diffs them against notes already read out of a collection. No `anki` import.
"""

import os
from dataclasses import dataclass

from anki_tools import immutable_words_plan as iwp
from anki_tools import mutable_words_plan as mwp

IMMUTABLE_NOTE_TYPE_NAME = "Russian - Immutable Words (Ellis Version)"

TSV_FILES = {
    "Nouns": ("nouns.tsv", mwp.parse_nouns),
    "Verbs": ("verbs.tsv", mwp.parse_verbs),
    "Adjectives": ("adjectives.tsv", mwp.parse_adjectives),
    "Adverbs": ("adverbs.tsv", mwp.parse_adverbs),
    "Pronouns": ("pronouns.tsv", mwp.parse_pronouns),
    "Numerals": ("numerals.tsv", mwp.parse_numerals),
}


@dataclass(frozen=True)
class ExpectedNote:
    guid: str
    note_type: str
    headword: str
    fields: dict[str, str]


@dataclass(frozen=True)
class CollectionNote:
    guid: str
    note_type: str
    fields: dict[str, str]


@dataclass(frozen=True)
class DriftRow:
    guid: str
    note_type: str
    headword: str
    field: str
    collection_value: str
    source_value: str


@dataclass(frozen=True)
class DriftReport:
    drift: list[DriftRow]
    orphans: list[CollectionNote]
    missing: list[ExpectedNote]


def _mutable_headword(row) -> str:
    return getattr(row, "imperfective", None) or row.base_words[0]


def expected_notes(word_list_text: str, source_dir: str) -> list[ExpectedNote]:
    notes = [
        ExpectedNote(
            guid=row.guid,
            note_type=IMMUTABLE_NOTE_TYPE_NAME,
            headword=row.russian,
            fields=dict(zip(iwp.FIELD_NAMES, row.fields())),
        )
        for row in iwp.parse_word_list(word_list_text)
    ]
    for sheet, (file_name, parse) in TSV_FILES.items():
        for row in parse(os.path.join(source_dir, file_name)):
            notes.append(
                ExpectedNote(
                    guid=row.guid,
                    note_type=mwp.NOTE_TYPE_NAMES[sheet],
                    headword=_mutable_headword(row),
                    fields=dict(zip(mwp.FIELD_NAMES[sheet], row.fields())),
                )
            )
    return notes


def managed_note_types() -> frozenset[str]:
    return frozenset({IMMUTABLE_NOTE_TYPE_NAME, *mwp.NOTE_TYPE_NAMES.values()})


def compare(expected: list[ExpectedNote], actual: list[CollectionNote]) -> DriftReport:
    actual_by_guid = {note.guid: note for note in actual}
    expected_guids = {note.guid for note in expected}
    managed = managed_note_types()

    ranked: list[tuple[tuple[str, str, int], DriftRow]] = []
    missing = []
    for note in expected:
        stored = actual_by_guid.get(note.guid)
        if stored is None:
            missing.append(note)
            continue
        for position, (name, source_value) in enumerate(note.fields.items()):
            if name not in stored.fields or stored.fields[name] == source_value:
                continue
            row = DriftRow(
                guid=note.guid,
                note_type=note.note_type,
                headword=note.headword,
                field=name,
                collection_value=stored.fields[name],
                source_value=source_value,
            )
            ranked.append(((note.note_type, note.headword, position), row))

    ranked.sort(key=lambda pair: pair[0])
    orphans = [
        note
        for note in actual
        if note.note_type in managed and note.guid not in expected_guids
    ]
    return DriftReport(
        drift=[row for _, row in ranked], orphans=orphans, missing=missing
    )
