# Maze Runner (Python)

A maze generation and solving library plus an interactive CLI solver. `Maze` either wraps an existing text layout or generates a new one; `Runner` builds a graph of the maze's open cells and finds the shortest start-to-end path via breadth-first path propagation; `bin/solver.py` is the interactive front end (build a new maze or upload one from a text file, solve it, and save the original + solved output to a file).

**Path:** `libs/python/maze-runner`
**Workspace name:** `lib.python.maze-runner`

## Stack

- Python `^3.8` via Poetry (`pyproject.toml`, `packages = [{ include = "maze_runner" }]`) — the only Poetry package in `libs/python` that targets `^3.8` rather than `^3.11`.
- No third-party dependencies (standard library only: `random`, `argparse`, `re`).

## Structure / entry points

- `maze_runner/maze.py` — `Maze`: holds a character-grid layout (`wall_char`/`open_char`/`start_char`/`end_char`, defaults `#`, space, `s`, `e`); `build_new(height, width, maze_type)` generates a random maze with start/end placed top-and-bottom (`"h"`), left-and-right (`"v"`), or randomly (`"r"`).
- `maze_runner/node.py` — `Node`: graph node with `children` and a shortest-`path` set.
- `maze_runner/runner.py` — `Runner`: collects open cells as nodes, locates start/end, `make_node_paths()` does the breadth-first search, `build_path()`/`view_completed()` render the solved maze with a path character.
- `bin/solver.py` — interactive CLI (`argparse` flags `-of/--openfile`, `-sf/--savefile`, plus prompts); exposed as the `py-maze-runner` bin entry in `package.json`.
- `examples/m1.txt` … `m5.txt` — sample maze text files (`#` walls, `s` start, `e` end).
- `dist/` — previously built `maze_runner-0.1.0` wheel/sdist artifacts, committed.

## Install / build / run

- In the pnpm workspace: `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`' `py-install`/`py-build`/`py-lint`/`py-dev` wrappers (`pnpm --filter lib.python.maze-runner run build` creates `.venv` and runs `poetry install`).
- Standalone: `python3 -m venv .venv && . .venv/bin/activate && pip install poetry && poetry install`.
- No tests are present.

## Caveats

- `maze_runner/` has no `__init__.py`, even though `pyproject.toml` packages it; `runner.py` uses the relative import `from .node import Node`.
- The stray top-level `__init__.py` next to this README contains `from src import *`, but no `src/` directory exists here — vestigial and broken.
- `bin/solver.py` opens with `from . import Maze, Runner` — a relative import that fails when the file is run directly as a script (`python bin/solver.py`), so the `py-maze-runner` bin entry does not work as-is.
- This directory is copied verbatim (`cp -R`) into the `maze-runner-mono` satellite repo by `.github/workflows/build-maze-runner.yml`, which is why this README is a real file kept in-tree (the monorepo's `docs/libs/python/maze-runner/README.md` is a symlink pointing here, the reverse of the usual docs direction).
