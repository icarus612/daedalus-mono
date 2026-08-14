# build-tools

Bash wrapper scripts that let pnpm/Turborepo drive Python packages uniformly. This package is the linchpin of the repo's cross-language wrapper pattern — see [../../../architecture.md](../../../architecture.md#the-cross-language-wrapper-pattern).

**Path:** `libs/bash/build-tools`
**Workspace name:** `lib.bash.build-tools`

## The bin scripts

`package.json` exposes four scripts from `py-scripts/` as `bin` entries, so any workspace package that depends on this one gets them on its `node_modules/.bin` PATH:

| Bin | Behavior (verified from `py-scripts/`) |
|---|---|
| `py-install` | Creates `.venv`; if `pyproject.toml` exists installs Poetry into the venv and runs `poetry install`, else `pip install -r requirements.txt`; errors if neither file exists |
| `py-build` | Same as `py-install` but creates `.venv` only if missing (idempotent re-install/update) |
| `py-dev` | Activates `.venv`; if `main.py` imports Flask, runs `flask run` with a fixed per-directory port (`maze-runner`→5001, `pokedex`→5002, `weather-fortcast`→5003, `market-bots`→5004, else 5000); otherwise runs `python main.py`; for libraries (no `main.py`) exits 0 |
| `py-lint` | Activates `.venv` (creating it if missing), `pip install -q ruff`, then `ruff check .` |

All scripts run in the *consumer package's* working directory and use `python3 -m venv`.

## How Python packages consume it

Every Python app/lib declares this package as a workspace dependency and points its own scripts at the bins:

```json
{
  "scripts": {
    "install": "py-install",
    "build": "py-build",
    "dev": "py-dev",
    "lint": "py-lint"
  },
  "devDependencies": {
    "lib.bash.build-tools": "workspace:*"
  }
}
```

(Example verified from `libs/python/anki-tools/package.json`; the same shape appears across `libs/python/*` and the Flask apps.)

## Own scripts

- `build` — `chmod +x py-scripts/*`. Because `turbo.json`'s `build` task declares `dependsOn: ["^build"]`, this runs before any consumer's build, guaranteeing the bins are executable.
- `dev` / `lint` — no-op echoes.

## Notes

- No shell version is pinned; scripts use `#!/bin/bash` with `set -e`.
- `libs/bash/cli-tools` carries older copies of `py-install`/`py-build`/`py-dev` under `src/py-scripts/` and `bin/`; the copies here in `build-tools` are the ones wired into the workspace.
