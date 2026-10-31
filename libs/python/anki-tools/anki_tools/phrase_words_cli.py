#!/usr/bin/env python3
"""Audit every word in the Russian phrase deck against the taught decks.

Reports, per bucket, every distinct word token across all phrase-deck
entries -- single-word entries and multi-word phrases alike -- with the
taught word it resolved to and the phrase it came from. Nothing is written:
the collection is opened, read, and closed.

Three resolution modes, narrowing in that order:

* default -- stored surface forms, then lemma rewriting.
* `--no-lemma` -- stored surface forms only.
* `--headwords-only --no-lemma` -- headwords only, which is what an earlier
  pass measured and what reproduces its counts.

See `anki_tools.phrase_words` for the resolution rules.
"""

import argparse
import sys

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools import phrase_words as pw
from anki_tools.audio_naming import get_anki_collection_path

SECTION_ORDER = (
    pw.MISSING,
    pw.ALL_NEW,
    pw.PART_NEW,
    pw.SUSPENDED,
    pw.NO_CARDS,
    pw.STUDIED,
)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="anki-phrase-words",
        description=(
            "List every word in the Russian phrase deck, grouped by whether "
            "the taught decks cover it and what state its cards are in. "
            "Read-only."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection_path",
        default=None,
        help="Path to collection.anki2. Defaults to the usual profile path.",
    )
    parser.add_argument(
        "--note-type",
        dest="note_type",
        default=pw.PHRASE_NOTE_TYPE,
        help="Note type holding the phrases. Default: the phrase deck's own.",
    )
    parser.add_argument(
        "--no-lemma",
        action="store_true",
        help="Resolve only against forms the taught notes spell out.",
    )
    parser.add_argument(
        "--headwords-only",
        action="store_true",
        help="Build the taught index from headwords alone, ignoring the "
        "inflection fields.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
        help="Output format. Default: text.",
    )
    return parser


def read_note_types(col):
    """`(id, name, field_names)` per note type in the collection."""
    types = []
    for entry in col.models.all_names_and_ids():
        model = col.models.get(entry.id)
        types.append((entry.id, entry.name, [f["name"] for f in model["flds"]]))
    return types


def read_notes(col, note_type_id):
    return col.db.all("select id, flds from notes where mid = ?", note_type_id)


def read_card_rows(col):
    rows = {}
    for note_id, card_type, queue in col.db.all("select nid, type, queue from cards"):
        rows.setdefault(note_id, []).append((card_type, queue))
    return rows


def _taught_word(note_id, field_names, fields, headwords_only):
    if not headwords_only:
        return pw.taught_word(note_id, field_names, fields)
    kept = [
        (name, value)
        for name, value in zip(field_names, fields)
        if name in pw.HEADWORD_FIELDS
    ]
    return pw.taught_word(
        note_id, [name for name, _ in kept], [value for _, value in kept]
    )


def collect(col, note_type, headwords_only):
    """`(phrases, index, card_rows, counts)` read out of the collection.

    Raises `LookupError` when no note type matches `note_type`.
    """
    wanted = note_type.strip()
    phrase_type = None
    taught_types = []
    for note_type_id, name, field_names in read_note_types(col):
        if name.strip() == wanted:
            phrase_type = (note_type_id, field_names)
        elif pw.is_taught_note_type(name):
            taught_types.append((note_type_id, field_names))
    if phrase_type is None:
        raise LookupError(wanted)

    phrase_type_id, phrase_fields = phrase_type
    russian = phrase_fields.index("Russian")
    phrases = [row[1].split("\x1f")[russian] for row in read_notes(col, phrase_type_id)]

    words = []
    for note_type_id, field_names in taught_types:
        for note_id, flds in read_notes(col, note_type_id):
            word = _taught_word(
                note_id, field_names, flds.split("\x1f"), headwords_only
            )
            if word is not None:
                words.append(word)

    counts = {
        "phrases": len(phrases),
        "taught_notes": len(words),
        "taught_types": len(taught_types),
    }
    return phrases, pw.build_index(words), read_card_rows(col), counts


def describe_mode(no_lemma, headwords_only):
    source = "headwords only" if headwords_only else "headwords + inflections"
    return f"{source}, {'no lemmatization' if no_lemma else 'lemma-aware'}"


def render_text(records, header):
    grouped = pw.group_by_state(records)
    lines = list(header)
    lines.append("")
    lines.append(f"{len(records)} distinct word token(s)")
    lines.append("")
    for state in pw.STATES:
        lines.append(f"  {state:10} {len(grouped[state])}")
    for state in SECTION_ORDER:
        bucket = grouped[state]
        if not bucket:
            continue
        lines.append("")
        lines.append(f"== {state} ({len(bucket)}) ==")
        for record in bucket:
            lines.append(f"  {_text_word(record)}")
    return "\n".join(lines)


def _text_word(record):
    sources = " | ".join(record.phrases)
    if record.headword is None:
        return f"{record.token:22} < {sources}"
    origin = f"({record.via}: {record.matched})"
    return f"{record.token:22} = {record.headword:26} {origin:34} < {sources}"


def render_markdown(records, header):
    grouped = pw.group_by_state(records)
    lines = ["# Russian phrase deck -- every word", ""]
    lines.extend(f"- {line}" for line in header)
    lines.append(f"- {len(records)} distinct word token(s)")
    lines.append("")
    lines.append("| bucket | words |")
    lines.append("|---|---|")
    for state in pw.STATES:
        lines.append(f"| {state} | {len(grouped[state])} |")
    for state in SECTION_ORDER:
        bucket = grouped[state]
        if not bucket:
            continue
        lines.extend(["", f"## {state} ({len(bucket)})", ""])
        lines.append("| word | taught as | matched | from |")
        lines.append("|---|---|---|---|")
        for record in bucket:
            headword = record.headword or "--"
            matched = f"{record.via}: {record.matched}" if record.via else "--"
            sources = " / ".join(record.phrases)
            lines.append(f"| `{record.token}` | {headword} | {matched} | {sources} |")
    return "\n".join(lines)


def main(argv=None):
    args = build_parser().parse_args(argv)
    path = args.collection_path or get_anki_collection_path()

    try:
        col = Collection(path)
    except (DBError, AnkiException) as error:
        print(f"could not open {path}: {error}", file=sys.stderr)
        return 2
    try:
        phrases, index, card_rows, counts = collect(
            col, args.note_type, args.headwords_only
        )
    except LookupError as error:
        print(f"no note type named {error.args[0]!r}", file=sys.stderr)
        return 1
    finally:
        col.close()

    records = pw.audit(phrases, index, card_rows, use_lemma=not args.no_lemma)
    header = [
        f"collection: {path}",
        f"note type: {args.note_type.strip()} ({counts['phrases']} note(s))",
        f"taught index: {len(index)} form(s) from {counts['taught_notes']} "
        f"note(s) across {counts['taught_types']} note type(s)",
        f"resolution: {describe_mode(args.no_lemma, args.headwords_only)}",
    ]
    render = render_markdown if args.format == "markdown" else render_text
    print(render(records, header))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
