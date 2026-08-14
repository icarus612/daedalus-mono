"""Contract tests for W1-P12 (web-crawlers package skeleton) and W1-P13
(web-crawlers real defects: F821 x4, E999 x1, shadowing renames x2).

Written from the contract text alone (`.artifacts/contracts/l2.md`, packets
W1-P12 and W1-P13) — never from the implementation.
"""

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest


def _find_repo_root(start: Path) -> Path:
    """Walk upward from `start` until a `.git` entry is found."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"could not locate repo root (.git) starting from {start}")


REPO_ROOT = _find_repo_root(Path(__file__).parent)
PKG_ROOT = REPO_ROOT / "libs" / "python" / "web-crawlers"
WC = PKG_ROOT / "web_crawlers"


# ---------------------------------------------------------------------------
# W1-P12 — package skeleton: missing __init__.py in 22 directories
# ---------------------------------------------------------------------------

# Reproduced verbatim from the contract's "Missing `__init__.py` (22
# directories)" list (packet W1-P12).
MISSING_INIT_DIRS = [
    "web_crawlers/",
    "web_crawlers/anki_scrapers/",
    "web_crawlers/anki_scrapers/bash/",
    "web_crawlers/anki_scrapers/c_cpp/",
    "web_crawlers/anki_scrapers/data_flair/",
    "web_crawlers/anki_scrapers/golang/",
    "web_crawlers/anki_scrapers/japanese/archived/",
    "web_crawlers/anki_scrapers/japanese/helpers/",
    "web_crawlers/anki_scrapers/javascript/",
    "web_crawlers/anki_scrapers/machine_learning/",
    "web_crawlers/anki_scrapers/multi_language/",
    "web_crawlers/anki_scrapers/python/",
    "web_crawlers/anki_scrapers/russian/",
    "web_crawlers/anki_scrapers/sql/",
    "web_crawlers/anki_scrapers/ss64_bash/",
    "web_crawlers/anki_scrapers/text_to_speech/",
    "web_crawlers/anki_scrapers/text_to_speech/audio_files/",
    "web_crawlers/anki_scrapers/tutorialspoint/",
    "web_crawlers/anki_scrapers/vim/",
    "web_crawlers/anki_scrapers/w3Schools/",
    "web_crawlers/site_scrapers/",
    "web_crawlers/util_scrapers/",
]


def test_missing_init_dirs_list_has_22_entries():
    assert len(MISSING_INIT_DIRS) == 22


@pytest.mark.parametrize("rel_dir", MISSING_INIT_DIRS)
def test_init_py_present_in_directory(rel_dir):
    init_path = PKG_ROOT / rel_dir / "__init__.py"
    assert init_path.is_file(), f"expected {init_path} to exist"


@pytest.mark.parametrize("rel_dir", MISSING_INIT_DIRS)
def test_init_py_is_empty(rel_dir):
    """Contract's test oracle: each added __init__.py is empty (0 bytes or a
    single trailing newline)."""
    init_path = PKG_ROOT / rel_dir / "__init__.py"
    content = init_path.read_bytes()
    assert content in (
        b"",
        b"\n",
        b"\r\n",
    ), f"expected {init_path} to be empty, got {content!r}"


def test_japanese_and_utils_init_not_overwritten():
    """The contract says japanese/ and utils/ already have __init__.py and
    should be skipped, not overwritten — they must still exist."""
    for rel_dir in (
        "web_crawlers/anki_scrapers/japanese/",
        "web_crawlers/anki_scrapers/utils/",
    ):
        init_path = PKG_ROOT / rel_dir / "__init__.py"
        assert init_path.is_file(), f"expected {init_path} to exist"


# ---------------------------------------------------------------------------
# W1-P13 — real defects
# ---------------------------------------------------------------------------

STEAM_PY = WC / "site_scrapers" / "steam.py"
COMMON_WORDS_2000 = WC / "anki_scrapers" / "japanese" / "common_words_2000.py"
GET_MASTERRUSSIAN_1000 = WC / "anki_scrapers" / "russian" / "get_masterrussian_1000.py"
ADVANCED_TTS = WC / "anki_scrapers" / "text_to_speech" / "advanced_google_TTS.py"
BASIC_TTS = WC / "anki_scrapers" / "text_to_speech" / "basic_google_TTS.py"

PYTHON_DIR = WC / "anki_scrapers" / "python"
SYS_MODULE_SCRAPER = PYTHON_DIR / "sys_module_scraper.py"
MATPLOTLIB_API_SCRAPER = PYTHON_DIR / "matplotlib_api_scraper.py"
OLD_SYS_PY = PYTHON_DIR / "sys.py"
OLD_MATPLOTLIB_PY = PYTHON_DIR / "matplotlib.py"


# --- steam.py: E999 (TabError from mixed tabs/spaces + truncated ternary) ---


def test_steam_py_parses_with_ast():
    source = STEAM_PY.read_text()
    # Must not raise SyntaxError (or its TabError subclass).
    ast.parse(source)


def test_steam_py_tokenizes_without_tab_error():
    source_bytes = STEAM_PY.read_bytes()
    try:
        tokens = list(tokenize.tokenize(io.BytesIO(source_bytes).readline))
    except (TabError, IndentationError, tokenize.TokenizeError) as exc:
        pytest.fail(f"tokenizing {STEAM_PY} raised {exc!r}")
    assert tokens  # sanity: tokenization actually produced tokens


# --- common_words_2000.py: F821 (`idx` undefined) ---


def test_common_words_2000_has_no_idx_reference():
    source = COMMON_WORDS_2000.read_text()
    assert "idx" not in source, (
        "common_words_2000.py should no longer reference the undefined "
        "name 'idx' anywhere"
    )


def test_common_words_2000_calls_build_cards_with_literal_2000():
    source = COMMON_WORDS_2000.read_text()
    tree = ast.parse(source)

    module_level_calls = [
        node.value
        for node in tree.body
        if isinstance(node, ast.Expr)
        and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Name)
        and node.value.func.id == "build_cards"
    ]
    assert module_level_calls, (
        "expected a module-level call to build_cards() in common_words_2000.py"
    )

    call = module_level_calls[0]
    assert call.args, "build_cards() call must have a positional argument"
    first_arg = call.args[0]
    assert isinstance(first_arg, ast.Constant) and first_arg.value == "2000", (
        "build_cards()'s first positional argument must be the literal string "
        "'2000', regardless of source quote style"
    )


# --- get_masterrussian_1000.py: F821 (`r` undefined, dead `return r`) ---


def test_get_masterrussian_1000_has_no_bare_return_r_line():
    source = GET_MASTERRUSSIAN_1000.read_text()
    lines = [line.strip() for line in source.splitlines()]
    assert "return r" not in lines, (
        "get_masterrussian_1000.py should no longer contain the dead "
        "'return r' line referencing the undefined name 'r'"
    )


def test_get_masterrussian_1000_parses_with_ast():
    source = GET_MASTERRUSSIAN_1000.read_text()
    ast.parse(source)


# --- advanced_google_TTS.py / basic_google_TTS.py: F821 + AttributeError ---


def _assert_tts_file_fixed(path: Path):
    source = path.read_text()

    assert "args.file_name" not in source, (
        f"{path} should no longer reference the nonexistent 'args.file_name' attribute"
    )

    # No undefined bare `word` / `file` reference passed directly into
    # build_and_save(...) *call sites* (the pre-fix bug) — the fixed code
    # passes `card[0]` / `card[1]` instead. Only inspect call sites, not the
    # `def build_and_save(word, ...)` signature itself (which legitimately
    # names its first parameter `word` and is untouched by this fix).
    call_sites = [
        line
        for line in source.splitlines()
        if "build_and_save(" in line and not line.strip().startswith("def ")
    ]
    assert call_sites, f"expected to find build_and_save(...) call sites in {path}"
    for line in call_sites:
        assert re.search(r"build_and_save\(\s*word\b", line) is None, (
            f"{path} still passes a bare, undefined 'word' into a "
            f"build_and_save(...) call: {line!r}"
        )
        assert re.search(r"build_and_save\(\s*file\b", line) is None, (
            f"{path} still passes a bare, undefined 'file' into a "
            f"build_and_save(...) call: {line!r}"
        )

    assert "card[0]" in source, (
        f"{path} should use card[0] in build_and_save(...) calls"
    )
    assert "card[1]" in source, f"{path} should use card[1] for the file_name kwarg"

    ast.parse(source)


def test_advanced_google_tts_fixed():
    _assert_tts_file_fixed(ADVANCED_TTS)


def test_basic_google_tts_fixed():
    _assert_tts_file_fixed(BASIC_TTS)


def test_advanced_and_basic_tts_remain_identical():
    """Contract: keep the two files exact duplicates after the fix too."""
    assert ADVANCED_TTS.read_text() == BASIC_TTS.read_text()


# --- shadowing renames (C13) ---


def test_sys_module_scraper_renamed():
    assert SYS_MODULE_SCRAPER.is_file(), (
        "expected anki_scrapers/python/sys.py to be renamed to sys_module_scraper.py"
    )
    assert not OLD_SYS_PY.exists(), (
        "anki_scrapers/python/sys.py should no longer exist after the rename"
    )


def test_matplotlib_api_scraper_renamed():
    assert MATPLOTLIB_API_SCRAPER.is_file(), (
        "expected anki_scrapers/python/matplotlib.py to be renamed to "
        "matplotlib_api_scraper.py"
    )
    assert not OLD_MATPLOTLIB_PY.exists(), (
        "anki_scrapers/python/matplotlib.py should no longer exist after the rename"
    )
