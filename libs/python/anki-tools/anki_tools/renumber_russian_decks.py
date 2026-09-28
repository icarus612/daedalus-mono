#!/usr/bin/env python3
"""Renumber three sibling Russian decks to free up the '3.' slot.

Mutates the real Anki collection. A backup is taken before applying, and
`--revert` applies the inverse renaming to undo a previous run.
"""

import argparse
import os

from anki.collection import Collection
from anki.errors import AnkiException, DBError

from anki_tools.audio_naming import get_anki_collection_path
from anki_tools.immutable_words import assert_unmodified

DECK_PREFIX = "Languages::Russian::"

RENAMES = (
    ("3. Sentences (lingo llama)", "4. Sentences (lingo llama)"),
    ("4. 100 Words & Phrases", "5. 100 Words & Phrases"),
    ("5. Master Russian 300+", "6. Master Russian 300+"),
)


def full_deck_name(short_name: str) -> str:
    return DECK_PREFIX + short_name


def build_plan(revert: bool) -> tuple[tuple[str, str], ...]:
    """Return the ordered rename pairs, as full deck names."""
    plan = []
    for old, new in reversed(RENAMES):
        if revert:
            old, new = new, old
        plan.append((full_deck_name(old), full_deck_name(new)))
    return tuple(plan)


class PrecheckError(Exception):
    pass


def precheck(col, plan: tuple[tuple[str, str], ...]) -> None:
    for old, new in plan:
        if col.decks.id_for_name(old) is None:
            raise PrecheckError(f"deck not found: {old!r}")
        if col.decks.id_for_name(new) is not None:
            raise PrecheckError(f"deck already exists: {new!r}")


def snapshot_russian_subtree(col) -> dict[int, tuple[str, int]]:
    snapshot = {}
    for entry in col.decks.all_names_and_ids():
        if not entry.name.startswith("Languages::Russian"):
            continue
        card_count = len(col.decks.cids(entry.id, children=False))
        snapshot[entry.id] = (entry.name, card_count)
    return snapshot


def apply_plan(col, plan: tuple[tuple[str, str], ...]) -> list[tuple[str, str]]:
    applied = []
    for old, new in plan:
        deck_id = col.decks.id_for_name(old)
        col.decks.rename(deck_id, new)
        applied.append((old, new))
    return applied


def _expected_after_name(name: str, plan: tuple[tuple[str, str], ...]) -> str:
    for old, new in plan:
        if name == old or name.startswith(old + "::"):
            return name.replace(old, new, 1)
    return name


def verify_renumber(
    before: dict, after: dict, plan: tuple[tuple[str, str], ...]
) -> None:
    changed_ids = set(before) ^ set(after)
    if changed_ids:
        raise AssertionError(f"deck set changed: deck id {changed_ids.pop()}")
    for deck_id, (before_name, before_count) in before.items():
        after_name, after_count = after[deck_id]
        if before_count != after_count:
            raise AssertionError(f"card count changed for deck id {deck_id}")
        expected_name = _expected_after_name(before_name, plan)
        if after_name != expected_name:
            raise AssertionError(
                f"deck id {deck_id} name mismatch: "
                f"expected {expected_name!r}, got {after_name!r}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="anki-renumber-russian-decks",
        description=(
            "Renumber the Languages::Russian sibling decks to free up the '3.' slot."
        ),
    )
    parser.add_argument(
        "--collection",
        dest="collection",
        type=str,
        default=None,
        help="Override the auto-detected collection path.",
    )
    parser.add_argument(
        "--backup-dir",
        dest="backup_dir",
        type=str,
        default=None,
        help="Directory to store the backup in. Default: <collection dir>/backups.",
    )
    parser.add_argument(
        "--no-backup",
        dest="no_backup",
        action="store_true",
        default=False,
        help="Skip taking a backup before applying.",
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Plan and print the result, but write nothing.",
    )
    parser.add_argument(
        "--yes",
        "-y",
        dest="yes",
        action="store_true",
        default=False,
        help="Skip the interactive confirmation prompt.",
    )
    parser.add_argument(
        "--revert",
        dest="revert",
        action="store_true",
        default=False,
        help="Apply the inverse renaming (undo a previous run).",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    plan = build_plan(args.revert)

    collection_path = args.collection or get_anki_collection_path()
    mtime_before = os.path.getmtime(collection_path)

    try:
        col = Collection(collection_path)
    except DBError as exc:
        print(f"Could not open the collection: {exc}")
        print("Make sure Anki is not running when you execute this script.")
        raise SystemExit(1)
    except AnkiException as exc:
        print(f"Anki reported an error opening the collection: {exc}")
        raise SystemExit(1)

    try:
        try:
            precheck(col, plan)
        except PrecheckError as exc:
            print(str(exc))
            raise SystemExit(1)

        if not args.no_backup:
            backup_dir = args.backup_dir or os.path.join(
                os.path.dirname(collection_path), "backups"
            )
            os.makedirs(backup_dir, exist_ok=True)
            created = col.create_backup(
                backup_folder=backup_dir, force=True, wait_for_completion=True
            )
            if not created:
                print("Backup skipped: collection unchanged since last backup.")

        for old, new in plan:
            print(f"{old} -> {new}")

        if args.dry_run:
            assert_unmodified(collection_path, mtime_before)
            print("Dry run: nothing written.")
            raise SystemExit(0)

        if not args.yes:
            answer = input("Apply these changes? [y/N] ")
            if answer.strip().lower() != "y":
                print("Aborted: nothing written.")
                raise SystemExit(1)

        before = snapshot_russian_subtree(col)
        apply_plan(col, plan)
        after = snapshot_russian_subtree(col)
        verify_renumber(before, after, plan)
        print(f"Renamed {len(plan)} deck(s).")
        raise SystemExit(0)
    finally:
        col.close()


if __name__ == "__main__":
    main()
