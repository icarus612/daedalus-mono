"""Structure tests for the abstract-base-classes restructure (contract packet W1-P7).

Covers, per the contract's current-structure -> target-structure table and the
`pyproject.toml`/`mlp.py`/`mlp_vanilla.py` specifications:

- the old `src/` directory is gone
- `abstract_base_classes/ann_shell.py` exists at the package ROOT (not under
  `shells/`, per the contract's explicit note about consumer import expectations)
- `abstract_base_classes/shells/mlp.py` parses without a SyntaxError (the E999
  regression test — the file used to be missing a colon and have no body at all)
- if the package happens to be importable already, `MLP_Shell` from
  `abstract_base_classes.shells.mlp` subclasses
  `abstract_base_classes.ann_shell.ANN_Shell`

This test writes nothing and does not read the implementation; it asserts only
what the contract specifies.
"""

import ast
import importlib
import pathlib

import pytest


def _find_repo_root(start: pathlib.Path) -> pathlib.Path:
    """Walk upward from `start` until a `.git` directory/file is found."""
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"could not locate repo root (.git) starting from {start}")


REPO_ROOT = _find_repo_root(pathlib.Path(__file__).parent)
PACKAGE_DIR = (
    REPO_ROOT / "libs" / "python" / "neural-networks" / "abstract-base-classes"
)


def test_old_src_directory_does_not_exist():
    """The pre-restructure `src/` directory must be gone entirely."""
    assert not (PACKAGE_DIR / "src").exists()


def test_ann_shell_moved_to_package_root():
    """`ann_shell.py` must live at the package root, not under `shells/`.

    Per the contract: all three consumers (digit-recognition's
    `MLP_tensorflow.py`, both open-ai-gym copies' `env_builder.py`) import
    `from abstract_base_classes.ann_shell import ANN_Shell` — a top-level
    module, not `abstract_base_classes.shells.ann_shell`.
    """
    ann_shell_path = PACKAGE_DIR / "abstract_base_classes" / "ann_shell.py"
    assert ann_shell_path.is_file()

    # And it must NOT also exist under shells/ instead.
    misplaced = PACKAGE_DIR / "abstract_base_classes" / "shells" / "ann_shell.py"
    assert not misplaced.exists()


def test_mlp_shell_parses_without_syntax_error():
    """E999 regression test: `shells/mlp.py` used to be missing a colon and had
    no body at all. `ast.parse` must now succeed."""
    mlp_path = PACKAGE_DIR / "abstract_base_classes" / "shells" / "mlp.py"
    assert mlp_path.is_file()

    source = mlp_path.read_text()
    try:
        ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"shells/mlp.py failed to parse (E999 regression): {exc}")


def test_mlp_shell_subclasses_ann_shell_when_importable():
    """If the package is importable (uv workspace wiring happens in a later
    wave, so this may not yet be the case), `MLP_Shell` in
    `abstract_base_classes.shells.mlp` must subclass
    `abstract_base_classes.ann_shell.ANN_Shell`.
    """
    pytest.importorskip("abstract_base_classes")

    try:
        ann_shell_module = importlib.import_module("abstract_base_classes.ann_shell")
        mlp_module = importlib.import_module("abstract_base_classes.shells.mlp")
    except ImportError as exc:
        pytest.skip(f"abstract_base_classes not fully importable yet: {exc}")

    ANN_Shell = ann_shell_module.ANN_Shell
    MLP_Shell = mlp_module.MLP_Shell

    assert issubclass(MLP_Shell, ANN_Shell)
