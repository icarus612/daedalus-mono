"""Contract tests for the four `anki_tools` CLI entry points, written from
the packet contract text alone. The implementation modules are never read
by this file's author.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE_ROOT = Path(__file__).resolve().parents[1]

ENTRY_POINTS = [
    ("anki-vocabulary-source", "vocabulary_source"),
    ("anki-mutable-words", "mutable_words"),
    ("anki-mutable-words-audio", "mutable_words_audio"),
    ("anki-renumber-russian-decks", "renumber_russian_decks"),
]


@pytest.mark.parametrize("bin_name,module_name", ENTRY_POINTS)
def test_help_is_side_effect_free(bin_name, module_name, tmp_path):
    fake_home = tmp_path / "home"
    fake_home.mkdir()

    env = os.environ.copy()
    env["HOME"] = str(fake_home)
    env["http_proxy"] = "http://127.0.0.1:1"
    env["https_proxy"] = "http://127.0.0.1:1"

    result = subprocess.run(
        [sys.executable, "-m", f"anki_tools.{module_name}", "--help"],
        cwd=PACKAGE_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip().startswith("usage:")
    assert result.stderr == ""
    assert not (fake_home / ".local").exists()


@pytest.mark.parametrize("bin_name,module_name", ENTRY_POINTS)
def test_module_is_shebanged_and_executable(bin_name, module_name):
    module_path = PACKAGE_ROOT / "anki_tools" / f"{module_name}.py"

    with open(module_path, encoding="utf-8") as f:
        first_line = f.readline().strip()

    assert first_line == "#!/usr/bin/env python3"
    assert os.access(module_path, os.X_OK)
