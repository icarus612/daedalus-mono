"""Structural (text-based) tests for the F821 fix in classes/MLP_tensorflow.py.

Contract (packet W1-P8, `libs/python/neural-networks/digit-recognition`):
the file's `__init__` previously referenced an undefined bare name `l` twice:

    self.model = load_model(l) if os.path.isfile(l) else self.build()

The fix replaces both occurrences of the bare `l` with `self.model_location`
(a property exposed by the `ANN_Shell` base class):

    def __init__(self):
        self.model = (
            load_model(self.model_location)
            if os.path.isfile(self.model_location)
            else self.build()
        )

These tests perform a pure text/substring check on the file's source only —
no import of tensorflow or the module itself is required, and no other part
of the file is inspected.
"""

from pathlib import Path

import pytest

SOURCE_PATH = Path(__file__).resolve().parent.parent / "classes" / "MLP_tensorflow.py"


@pytest.fixture(scope="module")
def source_text():
    assert SOURCE_PATH.is_file(), f"expected source file at {SOURCE_PATH}"
    return SOURCE_PATH.read_text()


def test_buggy_load_model_call_is_gone(source_text):
    """The prior-buggy `load_model(l)` call site must no longer appear."""
    assert "load_model(l)" not in source_text


def test_buggy_isfile_call_is_gone(source_text):
    """The prior-buggy `isfile(l)` call site must no longer appear."""
    assert "isfile(l)" not in source_text


def test_model_location_replacement_present(source_text):
    """`self.model_location` must appear at least twice: once for each of
    the two positions the old bare `l` occupied (the `load_model(...)` call
    and the `os.path.isfile(...)` call)."""
    assert source_text.count("self.model_location") >= 2
