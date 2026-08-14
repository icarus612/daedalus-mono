# Pyto Widgets

Verified empty stub: this package has a `pyproject.toml` (with `package-mode = false`, meaning Poetry treats it as a non-distributable/non-packaged project) and an empty `requirements.txt`, but no Python source files or package directory exist anywhere under `libs/python/pyto-widgets/` — no `pyto_widgets/` module, no loose `.py` files. It's presumably reserved for a "Pyto" (iOS Python IDE) widgets integration that was never implemented, but that's unverified.

**Path:** `libs/python/pyto-widgets`
**Workspace name:** `lib.python.pyto-widgets`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml` + `poetry.lock`), `package-mode = false`

## Structure / entry points
- No source files present — `pyproject.toml`, `requirements.txt` (empty), `package.json` only.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`. There is nothing for `py-lint`/`py-build` to actually act on beyond the empty config.

## Notes
- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo — unlike the three-level `neural-networks/*` and `tensorflow/*` packages, which the workspace globs miss; see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Whether this package is reserved for future work or leftover cruft was not verified — flagged here rather than asserted.
