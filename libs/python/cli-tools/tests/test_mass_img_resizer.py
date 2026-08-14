"""Tests for the implicit-import fix in `cli_tools/mass_img_resizer.py`.

Per the contract (Packet W1-P9), the old bare/implicit import
`from img_resizer import resize` must be replaced with the absolute import
`from cli_tools.img_resizer import resize` (not a relative `from .img_resizer
import resize`), so the module works both as an installed package import and
as a standalone script invocation (the `package.json` `bin` entry
`"py-cli-mass-img-resizer": "cli_tools/mass_img_resizer.py"`).
"""

import pathlib

import pytest

SOURCE_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "cli_tools" / "mass_img_resizer.py"
)


def _read_source() -> str:
    return SOURCE_PATH.read_text()


def test_old_broken_bare_import_is_gone():
    """The old broken bare import must not appear anywhere in the source."""
    source = _read_source()
    assert "from img_resizer import resize" not in source


def test_fixed_absolute_import_is_present():
    """The fixed absolute import must be present, per the contract's specified fix."""
    source = _read_source()
    assert "from cli_tools.img_resizer import resize" in source


def test_mass_resize_importable_without_import_error():
    """If `cli_tools` is importable, `mass_resize` must import cleanly.

    Guarded because `uv` isn't wired into this worktree yet, so `cli_tools`
    may not be on the import path / installed.
    """
    pytest.importorskip("cli_tools")
    try:
        from cli_tools.mass_img_resizer import mass_resize  # noqa: F401
    except ImportError as exc:
        pytest.fail(f"importing mass_resize raised ImportError: {exc}")
