# Web Crawlers

A large collection of independent scraping scripts, grouped into three areas: `site_scrapers/` (scrapers for specific sites — Steam, Medium, Newegg, a "words to own words" site, CubeTutor), `util_scrapers/` (generic helpers — grabbing audio/images from a URL, extracting inline JS), and `anki_scrapers/` (by far the largest — dozens of per-topic scripts, organized by subject: JavaScript, Go, Python, SQL, C/C++, bash, vim, Russian, and especially Japanese-language vocabulary, that scrape reference sites and format the results for building Anki decks, including a `japanese/archived/` subfolder of superseded scripts and audio-generation helpers via Google TTS/`ttsmp3`). No `requirements.txt` content is declared (`requirements.txt` is empty) and `pyproject.toml` declares no dependencies beyond the Python version, so the actual third-party packages each script needs (e.g. `requests`, `selenium`, `beautifulsoup4`, `gTTS`) are not tracked at the package level.

**Path:** `libs/python/web-crawlers`
**Workspace name:** `lib.python.web-crawlers`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml` + `poetry.lock`) — no `[tool.poetry.dependencies]` beyond the Python version pin, and `requirements.txt` is empty; per-script third-party imports are not declared anywhere.

## Structure / entry points
- `web_crawlers/site_scrapers/` — per-site scrapers (`steam.py`, `medium.py`, `new_egg.py`, `wtow_site.py`, `cube_tutor.py`).
- `web_crawlers/util_scrapers/` — generic helpers: `audio_from_url.py`, `image_from_url.py`, `js_grabber.py`.
- `web_crawlers/anki_scrapers/` — the bulk of the package: language/topic-specific scrapers (`javascript/`, `golang/`, `python/`, `sql/`, `bash/`, `c_cpp/`, `vim/`, `russian/`, `japanese/` and its `helpers/`/`archived/` subfolders, `text_to_speech/` audio generation, `machine_learning/`, `multi_language/`, `tutorialspoint/`, `data_flair/`, `ss64_bash/`, `w3Schools/`) — these feed Anki deck content, tying this package conceptually to `anki-tools`.
- No package-level `__init__.py`/single entry point — scripts are run individually.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- No `bin` entries are declared; scripts are invoked directly (e.g. `python -m web_crawlers.anki_scrapers.japanese.smart_audio_jlpt_nrkt`).

## Notes
- **In the pnpm workspace** (matched by the `libs/*/*` glob) and driven by root turbo — unlike the three-level `neural-networks/*` and `tensorflow/*` packages, which the workspace globs miss; see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Dependency declarations are effectively absent (empty `requirements.txt`, dependency-free `pyproject.toml`) despite scripts clearly needing third-party packages (scraping/HTTP/Selenium/TTS libraries) — flagged here as unverified rather than asserted broken, since it wasn't tested whether `py-install` actually succeeds.
