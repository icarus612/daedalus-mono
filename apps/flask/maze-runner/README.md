# Maze Runner (Flask)

A Flask web app that builds and solves mazes. Users can either upload a text-based maze file (`/upload_maze`) or generate one from a width/height/type form (`/make_maze`); either way the app runs it through the local `modules.maze.Maze` / `modules.runner.Runner` classes, prints whether the maze is solvable, and (if so) computes and renders the solution path back into `templates/index.html`, using signed cookies to pass the maze layout and solved path across the redirect.

**Path:** `apps/flask/maze-runner`
**Workspace name:** `app.flask.maze-runner`

## Stack
- Python, Flask `2.3.3` (per `requirements.txt`, shared across all `apps/flask/*` apps), pinned alongside `gunicorn==20.1.0`, `Jinja2==3.1.2`, `Werkzeug==2.3.7`, `itsdangerous==2.1.2`, `flask-bootstrap4==4.0.2`, `flask_sslify==0.1.5`, `flask-fontawesome==0.1.5`, `MarkupSafe==2.1.3`, `requests==2.28.0`
- `runtime.txt` pins `python-3.8.0` for the Heroku-style deploy
- A `pyproject.toml`/`poetry.lock`/`setup.py` also exist in this directory declaring a near-empty Poetry package (`maze-runner`, no dependencies listed) — this predates or duplicates the `requirements.txt` approach; since `libs/bash/build-tools`'s `py-install`/`py-build` scripts check for `pyproject.toml` *before* `requirements.txt`, running `pnpm install`/`pnpm build` here would install via Poetry (effectively installing nothing) rather than `pip install -r requirements.txt`. Not reconciled during this pass — flag before relying on `pnpm install` to actually provision Flask.

## Structure / entry points
- `main.py` — Flask app and routes (`/`, `/upload_maze`, `/make_maze`)
- `modules/maze.py`, `modules/node.py`, `modules/runner.py` — maze data structure and solver
- `templates/index.html`, `static/` — view and static assets
- `Procfile` — `web: gunicorn main:app -b "0.0.0.0:$PORT" -w 3`
- `requirements.txt`, `runtime.txt` — pip/Heroku-style dependency and runtime pins
- `pyproject.toml`, `poetry.lock`, `setup.py` — parallel/legacy Poetry packaging (see Stack note above)

## Usage
- `pnpm install` (→ `py-install`), `pnpm build` (→ `py-build`), `pnpm dev` (→ `py-dev`), `pnpm lint` (→ `py-lint`) — thin wrappers from `libs/bash/build-tools`
- Production: `gunicorn main:app -b "0.0.0.0:$PORT" -w 3` per `Procfile`
- Direct: `python main.py`, which self-selects a free port in `3000`–`3100` via `find_available_port` — see Notes below

## Notes
- `main.py` does `sys.path.insert(0, "../../../libs/python")` and then imports `flask_utils.port_finder.find_available_port` and a local `modules.maze` — a filesystem-based cross-package dependency that is invisible to the pnpm/turbo workspace graph. See [../../../docs/architecture.md#dependency-graph](../../../docs/architecture.md#dependency-graph).
- There are two conflicting port-selection mechanisms in play for this app: `py-dev` (in `libs/bash/build-tools`) hardcodes port `5001` for this directory and launches via `flask run --port=5001`, while `main.py` itself, when run directly (`python main.py`), self-selects a free port in `3000`–`3100` via `find_available_port`. Since `pnpm dev` invokes `py-dev`, the `find_available_port` code path only actually runs when `main.py` is executed directly rather than via the workspace `dev` script. See [../../../docs/architecture.md#known-inconsistency-two-port-selection-mechanisms](../../../docs/architecture.md#known-inconsistency-two-port-selection-mechanisms).
- The original in-repo README was the CI-generated directory tree combined with generic profile boilerplate, not package-specific documentation; this page supersedes it.
- **Symlink direction exception**: this file is the real source of truth (not a symlink) because `.github/workflows/build-maze-runner.yml` copies this directory verbatim into the external `maze-runner-mono` repo via `cp -R`; a symlinked README would arrive dangling there. The `docs/apps/flask/maze-runner/README.md` page is instead the symlink, pointing back at this file. See [../../../docs/known-issues.md#symlink-direction-exception-for-ci-synced-packages](../../../docs/known-issues.md#symlink-direction-exception-for-ci-synced-packages).
