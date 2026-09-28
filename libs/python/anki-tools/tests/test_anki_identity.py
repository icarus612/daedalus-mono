"""Equivalence-check tests for anki_tools.anki_identity, authored by the
builder against the pre-move golden fixture (tests/data/immutable_guids.json)
and the live collection's known notetype id -- never against the
implementation directly.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from anki_tools.anki_identity import (
    GUID_ALPHABET,
    base91,
    guid_for_row,
    notetype_id_for_name,
)

_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_GUIDS_FIXTURE = Path(__file__).resolve().parent / "data" / "immutable_guids.json"

NEW_NOTE_TYPE_NAME = "Russian - Immutable Words (Ellis Version)"


def test_guid_for_row_matches_golden_fixture_for_every_row():
    entries = json.loads(_GUIDS_FIXTURE.read_text(encoding="utf-8"))
    assert len(entries) == 207
    for entry in entries:
        assert guid_for_row(entry["russian"], entry["pos"]) == entry["guid"]


def test_notetype_id_for_name_matches_live_collection_value():
    assert notetype_id_for_name(NEW_NOTE_TYPE_NAME) == 3897610691970966744


def _notetype_id_for_name_in_subprocess(name: str, pythonhashseed: str) -> int:
    env = {**os.environ, "PYTHONHASHSEED": pythonhashseed}
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(_PACKAGE_ROOT)!r})\n"
        "from anki_tools.anki_identity import notetype_id_for_name\n"
        f"print(notetype_id_for_name({name!r}))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return int(completed.stdout.strip())


def test_notetype_id_for_name_deterministic_across_fresh_subprocesses():
    first = _notetype_id_for_name_in_subprocess(NEW_NOTE_TYPE_NAME, "0")
    second = _notetype_id_for_name_in_subprocess(NEW_NOTE_TYPE_NAME, "1")
    assert first == second == 3897610691970966744


def test_base91_zero_returns_alphabet_first_char_not_empty():
    result = base91(0)
    assert result == GUID_ALPHABET[0]
    assert result != ""


def _imported_top_level_modules_in_subprocess() -> set[str]:
    code = (
        "import sys\n"
        f"sys.path.insert(0, {str(_PACKAGE_ROOT)!r})\n"
        "before = set(sys.modules)\n"
        "import anki_tools.anki_identity\n"
        "after = set(sys.modules) - before\n"
        "print(','.join(sorted({m.split('.')[0] for m in after})))\n"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        check=True,
    )
    return {m for m in completed.stdout.strip().split(",") if m}


def test_anki_identity_imports_nothing_but_hashlib():
    newly_imported = _imported_top_level_modules_in_subprocess()
    disallowed = newly_imported - {
        "hashlib",
        "_hashlib",
        "_blake2",
        "_sha3",
        "_sha2",
        "anki_tools",
    }
    assert not disallowed, f"unexpected top-level imports: {disallowed}"
