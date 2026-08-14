# CLI Tools

A set of small standalone image/file-conversion CLI scripts: converting Word documents to PDF via `unoconv`, and resizing images (single file, or a whole directory in bulk) via Pillow. Each script is an independent entry point rather than a shared library — there's duplicated resize logic between `mass_re_rez.py` and `re_rez.py`, and `mass_img_resizer.py` imports from `img_resizer.py` for the single-file case. All use the (deprecated, Pillow-version-dependent) `Image.ANTIALIAS` resample constant.

**Path:** `libs/python/cli-tools`
**Workspace name:** `lib.python.cli-tools`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml` + `poetry.lock`)

## Structure / entry points
- `cli_tools/convert_file.py` — `word_to_pdf()`, shells out to `unoconv` to convert a Word doc to PDF; CLI via `sys.argv`.
- `cli_tools/img_resizer.py` — `resize()`, resizes a single image with Pillow and displays/saves the result.
- `cli_tools/mass_img_resizer.py` — `mass_resize()`, loops over a list of `{src, size}` dicts and calls `resize()` from `img_resizer.py` for each.
- `cli_tools/mass_re_rez.py` / `cli_tools/re_rez.py` — near-duplicate directory-wide bulk resize implementations (iterate a directory, resize every `.jpg`/`.png` into an output directory).
- `package.json` exposes `bin` entries: `py-cli-convert-file`, `py-cli-img-resizer`, `py-cli-mass-img-resizer`, `py-cli-mass-re-rez`, `py-cli-re-rez`.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- Run via `pnpm --filter lib.python.cli-tools <script>` or the `bin` commands once installed.

## Notes
- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo — unlike the three-level `neural-networks/*` and `tensorflow/*` packages, which the workspace globs miss; see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- `pyproject.toml` declares no dependencies beyond Python `^3.11`, yet the scripts need Pillow and the external `unoconv` binary; `Image.ANTIALIAS` was removed in Pillow 10, so `mass_re_rez.py`/`re_rez.py` fail on current Pillow.
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- See [static_files/README.md](static_files/README.md) for the sibling `static_files/` asset directory.
