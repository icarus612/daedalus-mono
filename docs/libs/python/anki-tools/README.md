# Anki Tools

A grab-bag of small standalone scripts for working with the Anki spaced-repetition app: building decks from delimited text files, inspecting a local Anki collection's deck/options-group structure, and a one-off script for renaming MP3 filenames used in a Japanese-vocabulary deck build. The three scripts are independent entry points, not a cohesive library — `build_deck.py` writes deck files from a dict of cards, `get_deck_info.py` opens a local `collection.anki2` via the `anki` package and groups decks by their options group, and `mp3_filename_update.py` is a hardcoded, machine-specific helper (references `/home/icarus-64/...` paths) tied to a specific vocabulary-deck build.

**Path:** `libs/python/anki-tools`
**Workspace name:** `lib.python.anki-tools`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml` + `poetry.lock`)

## Structure / entry points
- `anki_tools/build_deck.py` — `build_deck()`/`build_decks()`, writes pipe-delimited deck text files from card data; has a CLI (`argparse`) entry point.
- `anki_tools/get_deck_info.py` — reads the local Anki collection (via the `anki` package's `Collection`), lists decks grouped by options group; has a `main()` CLI entry point.
- `anki_tools/mp3_filename_update.py` — one-off script hardcoded to a specific user's Anki media directory and a `created-decks/jlptsensei/...` folder structure; not general-purpose.
- `package.json` exposes these as `bin` entries: `anki-build-deck`, `anki-get-deck-info`, `anki-mp3-filename-update`.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- Run via `pnpm --filter lib.python.anki-tools <script>` or the `bin` commands once installed.

## Notes
- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo — unlike the three-level `neural-networks/*` and `tensorflow/*` packages, which the workspace globs miss; see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- `pyproject.toml` declares no dependencies beyond Python `^3.11`, yet `get_deck_info.py` imports the `anki` package and `mp3_filename_update.py` imports `requests` — those must be installed by hand for the scripts to run.
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- `libs/python/anki-tools/BUILD` is a 0-byte vestigial Bazel file — legacy and unused (see [../../../architecture.md](../../../architecture.md#bazel-legacy-unused)).
