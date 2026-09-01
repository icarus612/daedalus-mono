"""Make `anki_tools` importable under a bare/ambient `pytest`, uninstalled.

The project's own runner (`uv run --group dev pytest`, what `pnpm test` /
`py-test` invoke) always resolves `anki_tools` correctly -- `uv` builds and
installs this package into its managed venv first. But at least one Stop
hook (`workflow-diff-check.sh`) invokes the ambient `pytest` found via
`command -v pytest` (typically a pyenv shim with no project venv active),
and does so from the WORKTREE ROOT, several directories above this package.
Without help, that pytest fails collection on every test here with
`ModuleNotFoundError: No module named 'anki_tools'` -- reproduced identically
on the pre-existing `tests/test_due_plan.py`, so this is not specific to any
one test file.

Deliberately a `conftest.py`, not `[tool.pytest.ini_options] pythonpath` in
`pyproject.toml`: pytest discovers a `conftest.py` by walking UP from each
collected test file's own directory, regardless of where pytest was invoked
from or what `rootdir` it settles on. An ini option, by contrast, is only
read from whichever config file pytest decides governs the run, which is
resolved relative to `rootdir`/invocation directory -- when the hook invokes
pytest from the worktree root (above this package), pytest may pick a
different (or no) ini file and silently never see this package's
`pythonpath` setting at all. Living at the PACKAGE root (this directory,
one level above `tests/`) is what makes this file discovered no matter
which directory pytest was launched from.
"""

import os
import sys

_PACKAGE_ROOT = os.path.dirname(os.path.abspath(__file__))
if _PACKAGE_ROOT not in sys.path:
    sys.path.insert(0, _PACKAGE_ROOT)
