"""Tests for Packet W1-P6 — `open-ai-gym` dedupe + identity + import fixes.

Per the contract, `libs/python/neural-networks/open-ai-gym/` is the sole
surviving copy of this library (D2): the duplicate under
`libs/python/tensorflow/open-ai-gym/` — which carried an unresolvable
`{path = "../abstract-base-classes"}` dependency — must be deleted entirely.

Within the surviving copy, the stray 0-byte `__init__.py` at the hyphenated
directory root must be deleted (it is not the real package init), while the
real package init `open_ai_gym/__init__.py` (snake_case, inside the actual
package directory) must remain untouched.

Finally, `open_ai_gym/classes/lunar_lander_v2.py` must no longer contain the
old Python-2-style implicit same-directory sibling import
`from env_builder import EnvBuilder` (it is replaced with the absolute form
`from open_ai_gym.classes.env_builder import EnvBuilder`).

These are structural/text-content checks only — no `tensorflow`/`gymnasium`
import or runtime verification here; that is deferred to the e2e tail per
the contract.
"""

import pathlib


def _find_repo_root(start: pathlib.Path) -> pathlib.Path:
    """Walk upward from `start` until a `.git` directory is found."""
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root (.git) above {start}")


REPO_ROOT = _find_repo_root(pathlib.Path(__file__).resolve())

TENSORFLOW_DUPLICATE = REPO_ROOT / "libs" / "python" / "tensorflow" / "open-ai-gym"

SURVIVOR_ROOT = REPO_ROOT / "libs" / "python" / "neural-networks" / "open-ai-gym"
STRAY_ROOT_INIT = SURVIVOR_ROOT / "__init__.py"
REAL_PACKAGE_INIT = SURVIVOR_ROOT / "open_ai_gym" / "__init__.py"
LUNAR_LANDER_V2 = SURVIVOR_ROOT / "open_ai_gym" / "classes" / "lunar_lander_v2.py"

OLD_BROKEN_IMPORT = "from env_builder import EnvBuilder"


def test_tensorflow_duplicate_does_not_exist():
    """The duplicate `libs/python/tensorflow/open-ai-gym/` must be deleted (D2)."""
    assert not TENSORFLOW_DUPLICATE.exists()


def test_stray_hyphenated_root_init_does_not_exist():
    """The stray 0-byte `__init__.py` at the hyphenated root must be deleted."""
    assert not STRAY_ROOT_INIT.exists()


def test_real_package_init_exists():
    """The real package init `open_ai_gym/__init__.py` must remain, untouched."""
    assert REAL_PACKAGE_INIT.is_file()


def test_lunar_lander_v2_has_no_old_broken_import_line():
    """`lunar_lander_v2.py` must contain no line matching the old implicit import."""
    source = LUNAR_LANDER_V2.read_text()
    lines = source.splitlines()
    matching_lines = [line for line in lines if OLD_BROKEN_IMPORT in line]
    assert matching_lines == [], (
        f"Found old broken implicit import in {LUNAR_LANDER_V2}: {matching_lines}"
    )
