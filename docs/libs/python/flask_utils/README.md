# flask_utils

A tiny shared helper module used by the Flask apps: `port_finder.py` provides `find_available_port(start_port=3000, end_port=3100)`, which honors a `PORT` environment variable if set and available, then falls back to scanning the given port range (via a raw `socket.bind` probe in `is_port_available()`) for a free port, raising `RuntimeError` if none is found in range. `__init__.py` is empty — it exists only to make the directory importable as a package.

**Path:** `libs/python/flask_utils`

## Stack
- Plain Python, no `pyproject.toml`, no `package.json`, no dependency manifest at all — this is not a Poetry or pnpm-managed package. It's a bare importable Python package consumed via a filesystem path hack rather than the workspace graph.

## Structure / entry points
- `__init__.py` — empty, marks the directory as a package.
- `port_finder.py` — `find_available_port()`, `is_port_available()`.

## Usage
- Not installed or built through any workspace tooling. Consumers (`apps/flask/maze-runner/main.py`, `apps/flask/pokedex/main.py`, `apps/flask/weather-fortcast/main.py`) do:
  ```python
  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../libs/python"))
  from flask_utils.port_finder import find_available_port
  ```
  This is a raw relative-path `sys.path` insertion, invisible to pnpm/turbo's dependency graph — see [../../../architecture.md](../../../architecture.md#dependency-graph).

## Notes
- No source `README.md` existed for this package before this documentation pass; the in-tree `libs/python/flask_utils/README.md` is a symlink to this page.
- There is a near-identical hyphenated duplicate at `libs/python/flask-utils/port_finder.py` (same file content, no `__init__.py`, no `package.json`) which is not importable as a Python module and appears dead/orphaned — covered in [../README.md](../README.md#flask_utils-vs-flask-utils-duplicate-one-dead), not documented separately here per that page's note.
- See also [../../../known-issues.md](../../../known-issues.md#flask-utils-vs-flask_utils-duplication) for the fuller writeup of this duplication.
