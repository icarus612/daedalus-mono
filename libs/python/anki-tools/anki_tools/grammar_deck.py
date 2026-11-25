#!/usr/bin/env python3
"""Install the Russian grammar-rule deck from `data/russian-grammar/case-endings.tsv`.

Writes straight into the real collection: one note type, one subdeck per source
table, one note per row. Notes are keyed by a deterministic GUID, so a re-run
updates them in place and never touches their scheduling.
"""

import argparse
import csv
import os
import time
from dataclasses import dataclass
from pathlib import Path

from anki.collection import Collection
from anki.errors import AnkiException, DBError
from anki.utils import to_json_bytes

from anki_tools import card_audio, case_pill
from anki_tools.anki_identity import guid_for_row, notetype_id_for_name
from anki_tools.audio_naming import build_filename, get_anki_collection_path

DATA_PATH = Path(__file__).parent / "data" / "russian-grammar" / "case-endings.tsv"
DECK_ROOT = "Languages::Russian::2. Grammar"
OPTIONS_SOURCE_DECK = "Languages::Russian"
NOTE_TYPE_NAME = "Russian - Grammar Rules (Ellis Version)"
NOTE_TYPE_ID = notetype_id_for_name(NOTE_TYPE_NAME)
GUID_NAMESPACE = "Grammar"
FIELD_NAMES = ("Type", "Front", "Target", "Example", "Notes")
MALE_SLOT = "m2"
FEMALE_SLOT = "f1"
TABLE_SUBDECKS = {
    "Singular Noun Endings": "a. Singular Noun Endings",
    "Plural Noun Endings": "b. Plural Noun Endings",
    "Adjective Endings": "c. Adjective Endings",
    "Personal Pronouns": "d. Personal Pronouns",
    "Particles": "e. Particles",
}

_GENDER_COLOURS = {
    "Masculine": ("#00796b", "#4db6ac"),
    "Neuter": ("#00796b", "#4db6ac"),
    "Feminine": ("#ad1457", "#f48fb1"),
    "Plural": ("#6d4c41", "#bcaaa4"),
}
_CASES_JSON = "[" + ",".join(f'"{c}"' for c in case_pill.CASE_ORDER) + "]"
_GENDERS_JSON = "[" + ",".join(f'"{g}"' for g in _GENDER_COLOURS) + "]"
_COLOUR_SCRIPT = """<script>(function () {
  var root = document.querySelector('.g-card');
  if (!root || root.dataset.coloured) return;
  root.dataset.coloured = '1';
  var cases = @@CASES@@, genders = @@GENDERS@@;
  var words = new RegExp('\\\\b(' + cases.concat(genders).join('|') + ')\\\\b', 'g');
  function paint(el, kind) {
    if (!el) return;
    el.innerHTML = el.innerHTML.replace(words, function (w) {
      var slug = w.toLowerCase();
      return cases.indexOf(w) >= 0
        ? '<span class="' + kind + ' case-' + slug + '">' + w + '</span>'
        : '<span class="g-gender g-' + slug + '">' + w + '</span>';
    });
  }
  var front = root.querySelector('.front');
  var asked = cases.filter(function (c) {
    return front && front.textContent.indexOf('→ ' + c) >= 0;
  })[0];
  if (asked) root.classList.add('g-' + asked.toLowerCase());
  paint(front, 'case-pill');
  function plain(t) { return t.replace(/\\u0301/g, ''); }
  function mark(span, keep) {
    var t = span.textContent, j = 0;
    for (var seen = 0; j < t.length && seen < keep; j++) if (t[j] !== '\\u0301') seen++;
    while (j < t.length && t[j] === '\\u0301') j++;
    if (j < t.length) {
      span.innerHTML = t.slice(0, j) + '<b class="g-end">' + t.slice(j) + '</b>';
    }
  }
  root.querySelectorAll('.ex-line').forEach(function (line) {
    var spans = line.querySelectorAll(':scope > span:not(.ex-note)');
    if (spans.length < 3) return;
    var a = plain(spans[0].textContent), b = plain(spans[2].textContent);
    if (b.indexOf('-') > 0) {
      mark(spans[2], b.indexOf('-'));
      return;
    }
    var stem = a.replace(/(ый|ий|ой|[аяоеьй])$/, ''), i = 0;
    while (i < stem.length && i < b.length && a[i] === b[i]) i++;
    mark(spans[0], i);
    mark(spans[2], i);
  });
})();</script>"""
_COLOUR_SCRIPT = _COLOUR_SCRIPT.replace("@@CASES@@", _CASES_JSON)
_COLOUR_SCRIPT = _COLOUR_SCRIPT.replace("@@GENDERS@@", _GENDERS_JSON)

QFMT = (
    '<div class="g-card"><div class="type">{{Type}}</div>\n'
    '<div class="front">{{Front}}</div></div>\n' + _COLOUR_SCRIPT
)
AFMT = (
    '<div class="g-card"><div class="type">{{Type}}</div>\n'
    '<div class="front">{{Front}}</div>\n<hr id=answer>\n'
    '<div class="target">{{Target}}</div>\n'
    '{{#Example}}<div class="example">{{Example}}</div>{{/Example}}\n'
    '{{#Notes}}<div class="notes">{{Notes}}</div>{{/Notes}}</div>\n' + _COLOUR_SCRIPT
)


def _grammar_colour_css() -> str:
    rules = []
    for name, (light, dark) in _GENDER_COLOURS.items():
        rules.append(f".g-{name.lower()} {{ color: {light}; }}")
        rules.append(f".nightMode .g-{name.lower()} {{ color: {dark}; }}")
    for name in case_pill.CASE_ORDER:
        text, _, dark_text, _ = case_pill._PALETTE[name]
        slug = name.lower()
        rules.append(f".g-{slug} .g-end {{ color: {text}; }}")
        rules.append(f".nightMode .g-{slug} .g-end {{ color: {dark_text}; }}")
    return "\n".join(rules) + "\n"


CSS = """.card { font-family: arial; font-size: 22px; text-align: center;
  color: black; background-color: white; }
.type { font-size: 14px; color: #888; }
.front { margin-top: 8px; }
.target { font-size: 34px; font-weight: bold; margin: 12px 0; }
.example { font-size: min(22px, 5vw); color: black; display: grid;
  grid-template-columns: repeat(5, max-content);
  align-items: center; column-gap: 8px; row-gap: 8px;
  width: fit-content; max-width: 100%; margin: 8px auto; }
.notes { font-size: 16px; color: #666; margin-top: 12px; }
.ex-line { display: contents; }
.ex-line > :first-child { grid-column: 1; }
.ex-line > span { justify-self: start; text-align: left; }
.ex-note { grid-column: 5; margin-top: -6px; font-size: 15px; color: #888; }
.nightMode .card, .card.nightMode { color: white; background-color: #2f2f31; }
.nightMode .type, .nightMode .notes { color: #aaa; }
.nightMode .example { color: white; }
.front .case-pill { display: inline-block; font-size: .85em;
  padding: .05em .5em; border-radius: 999px; font-weight: bold; }
.g-gender { font-weight: bold; }
"""
CSS += _grammar_colour_css() + card_audio.AUDIO_BUTTON_CSS
CSS += "\n" + case_pill.CASE_PILL_CSS


@dataclass(frozen=True)
class Example:
    base: str
    form: str
    note: str
    slot: str


def _play(word: str, slot: str) -> str:
    return (
        f'<button class="{card_audio.BUTTON_CLASS} {card_audio.SMALL_BUTTON_CLASS}" '
        'onclick="this.nextElementSibling.play()">&#9654;</button>'
        f'<audio src="{build_filename(word, slot)}" preload="none"></audio>'
    )


def example_line(example: Example) -> str:
    note = f' <span class="ex-note">({example.note})</span>' if example.note else ""
    return (
        '<div class="ex-line">'
        f"{_play(example.base, example.slot)}<span>{example.base}</span>"
        "<span>&rarr;</span>"
        f"{_play(example.form, example.slot)}<span>{example.form}</span>{note}"
        "</div>"
    )


@dataclass(frozen=True)
class GrammarRow:
    table: str
    type: str
    front: str
    target: str
    examples: tuple[Example, Example]
    notes: str

    @property
    def guid(self) -> str:
        return guid_for_row(self.front, GUID_NAMESPACE)

    @property
    def deck(self) -> str:
        return f"{DECK_ROOT}::{TABLE_SUBDECKS[self.table]}"

    def fields(self) -> list[str]:
        example = "".join(example_line(e) for e in self.examples)
        return [self.type, self.front, self.target, example, self.notes]


class SourceError(Exception):
    pass


def parse_rows(path: str | os.PathLike = DATA_PATH) -> list[GrammarRow]:
    """Parse the TSV, rejecting unknown tables, blank targets and duplicate fronts."""
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t", quoting=csv.QUOTE_NONE)
        rows = [
            GrammarRow(
                table=r["Table"],
                type=r["Type"],
                front=r["Front"],
                target=r["Target"],
                examples=(
                    Example(
                        r["Example 1 Base"],
                        r["Example 1 Form"],
                        r["Example 1 Note"],
                        MALE_SLOT,
                    ),
                    Example(
                        r["Example 2 Base"],
                        r["Example 2 Form"],
                        r["Example 2 Note"],
                        FEMALE_SLOT,
                    ),
                ),
                notes=r["Notes"],
            )
            for r in reader
        ]
    seen: set[str] = set()
    for row in rows:
        if row.table not in TABLE_SUBDECKS:
            raise SourceError(f"unknown table {row.table!r} for {row.front!r}")
        if not row.front.strip() or not row.target.strip():
            raise SourceError(f"blank front or target: {row!r}")
        for example in row.examples:
            if not example.base.strip() or not example.form.strip():
                raise SourceError(f"blank example for {row.front!r}")
        if row.front in seen:
            raise SourceError(f"duplicate front: {row.front!r}")
        seen.add(row.front)
    return rows


def ensure_notetype(col: Collection) -> dict:
    """Create the note type under its fixed id, or update its templates in place."""
    existing = col.models.get(NOTE_TYPE_ID)
    if existing is not None:
        existing["tmpls"][0]["qfmt"] = QFMT
        existing["tmpls"][0]["afmt"] = AFMT
        existing["css"] = CSS
        col.models.update_dict(existing)
        return col.models.get(NOTE_TYPE_ID)
    model = col.models.new(NOTE_TYPE_NAME)
    for name in FIELD_NAMES:
        col.models.add_field(model, col.models.new_field(name))
    model["sortf"] = FIELD_NAMES.index("Front")
    template = col.models.new_template("Rule")
    template["qfmt"] = QFMT
    template["afmt"] = AFMT
    col.models.add_template(model, template)
    model["css"] = CSS
    model["id"] = NOTE_TYPE_ID
    model["mod"] = int(time.time())
    model["usn"] = -1
    # add_dict panics on a preset id; this call keeps ours (usn -1 so it syncs).
    col._backend.add_or_update_notetype(
        json=to_json_bytes(model), preserve_usn_and_mtime=True, skip_checks=False
    )
    return col.models.get(NOTE_TYPE_ID)


def ensure_decks(col: Collection) -> dict[str, int]:
    """Create the deck tree, giving new decks the parent Russian deck's options."""
    source = col.decks.by_name(OPTIONS_SOURCE_DECK)
    conf_id = source["conf"] if source is not None else 1
    deck_ids: dict[str, int] = {}
    for name in [DECK_ROOT] + [f"{DECK_ROOT}::{s}" for s in TABLE_SUBDECKS.values()]:
        is_new = col.decks.id_for_name(name) is None
        deck_id = col.decks.id(name, create=True)
        if is_new:
            deck = col.decks.get(deck_id)
            deck["conf"] = conf_id
            col.decks.save(deck)
        deck_ids[name] = deck_id
    return deck_ids


def audio_words(rows: list[GrammarRow]) -> dict[str, set[str]]:
    """Every word each voice must have a recording of, keyed by slot."""
    needed: dict[str, set[str]] = {MALE_SLOT: set(), FEMALE_SLOT: set()}
    for row in rows:
        for example in row.examples:
            needed[example.slot].update((example.base, example.form))
    return needed


@dataclass(frozen=True)
class ApplyResult:
    added: int
    updated: int
    unchanged: int


def apply_rows(col: Collection, rows: list[GrammarRow]) -> ApplyResult:
    """Add missing notes and refresh changed fields; scheduling is never touched."""
    model = ensure_notetype(col)
    deck_ids = ensure_decks(col)
    added = updated = unchanged = 0
    for row in rows:
        note_id = col.db.scalar("select id from notes where guid = ?", row.guid)
        if note_id is None:
            note = col.new_note(model)
            note.guid = row.guid
            for name, value in zip(FIELD_NAMES, row.fields()):
                note[name] = value
            col.add_note(note, deck_ids[row.deck])
            added += 1
            continue
        note = col.get_note(note_id)
        if [note[name] for name in FIELD_NAMES] == row.fields():
            unchanged += 1
            continue
        for name, value in zip(FIELD_NAMES, row.fields()):
            note[name] = value
        col.update_note(note)
        updated += 1
    return ApplyResult(added, updated, unchanged)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-grammar-deck",
        description="Install or refresh the Russian grammar-rule deck.",
    )
    parser.add_argument("--collection", default=None)
    parser.add_argument("--source", default=str(DATA_PATH))
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    rows = parse_rows(args.source)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row.deck] = counts.get(row.deck, 0) + 1
    for deck, n in counts.items():
        print(f"{deck}: {n}")
    if args.dry_run:
        print(f"Dry run: {len(rows)} rows parsed, nothing written.")
        return
    collection_path = args.collection or get_anki_collection_path()
    try:
        col = Collection(collection_path)
    except (DBError, AnkiException) as exc:
        print(f"Could not open the collection (is Anki running?): {exc}")
        raise SystemExit(1)
    try:
        if not args.no_backup:
            backup_dir = os.path.join(os.path.dirname(collection_path), "backups")
            col.create_backup(
                backup_folder=backup_dir, force=True, wait_for_completion=True
            )
        result = apply_rows(col, rows)
        print(
            f"added {result.added}, updated {result.updated}, "
            f"unchanged {result.unchanged}"
        )
    finally:
        col.close()


if __name__ == "__main__":
    main()
