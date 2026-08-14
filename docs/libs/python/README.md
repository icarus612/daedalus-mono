# libs/python

| Package | Docs | In pnpm/turbo workspace? |
|---|---|---|
| `anki-tools` | [anki-tools/README.md](anki-tools/README.md) | yes |
| `cli-tools` | [cli-tools/README.md](cli-tools/README.md) | yes |
| `maze-runner` | [maze-runner/README.md](maze-runner/README.md) | yes |
| `pyto-widgets` | [pyto-widgets/README.md](pyto-widgets/README.md) | yes |
| `web-crawlers` | [web-crawlers/README.md](web-crawlers/README.md) | yes |
| `flask_utils` | [flask_utils/README.md](flask_utils/README.md) | no `package.json` — plain import target, see below |
| `neural-networks/` | [neural-networks/README.md](neural-networks/README.md) | **no** (4 packages) |
| `tensorflow/open-ai-gym` | [tensorflow/open-ai-gym/README.md](tensorflow/open-ai-gym/README.md) | **no** |
| `pytorch/` | *(empty placeholder — no files, see [known-issues](../../known-issues.md#libspythonpytorch-is-empty))* | n/a |

The Poetry-based libs (`anki-tools`, `cli-tools`, `maze-runner`, `web-crawlers`, `pyto-widgets`) target Python `^3.11`, except `maze-runner` which targets `^3.8`. All five are recognized by the pnpm workspace and use `libs/bash/build-tools`'s `py-*` wrappers — see [../../architecture.md](../../architecture.md#the-cross-language-wrapper-pattern).

## `flask_utils` vs `flask-utils` (duplicate, one dead)

`libs/python/flask_utils/` (underscore) has an `__init__.py` and is what `apps/flask/*/main.py` actually imports via a raw `sys.path` hack (not a workspace dependency). `libs/python/flask-utils/` (hyphen) contains an identical copy of `port_finder.py` but no `__init__.py` and no `package.json` — it cannot be imported as a Python module and appears to be dead/orphaned. Documented here only; no `docs/libs/python/flask-utils` page was created since there's nothing distinct to say about it beyond "duplicate, unused" (see [../../known-issues.md](../../known-issues.md#flask-utils-vs-flask_utils-duplication)).
