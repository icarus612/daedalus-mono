# Abstract Base Classes (Neural Networks)

A small, incomplete scaffold of shared base classes intended to be reused by the other `neural-networks` packages: `ANN_Shell` (a base class with model-name/path helpers derived from `sys.argv`, plus a `model` loaded via a `load_model()` method) and `MLP_Shell` (subclasses `ANN_Shell`, adds unimplemented `forward`/`backward`/`train`/layer-creation stubs — all bodies are `pass`). A separate `nodes/basic.py` defines a `Basic` class whose `__init__` is defined without a `self` parameter, which would raise a `TypeError` if instantiated as a normal instance method — this was not executed to confirm, but is visibly a bug on read.

**Path:** `libs/python/neural-networks/abstract-base-classes`
**Workspace name:** `lib.python.neural-networks.abstract-base-classes`

## Stack
- Python `<4.0` via Poetry (`pyproject.toml` + `poetry.lock`) — no lower bound on the Python version, unlike every other Poetry package in this repo which pins a floor (`^3.11` or `^3.8`).

## Structure / entry points
- `src/shells/ANN.py` — `ANN_Shell`, `get_name()`, `get_path()`.
- `src/shells/MLP.py` — `MLP_Shell(ANN_Shell)`, imports `from ANN import ANN_Shell` (a bare top-level import rather than a relative/package import; there's no `__init__.py` in `src/shells/`, so this depends on `ANN.py`'s directory being on `sys.path` directly).
- `src/shells/MLP_vanilla.py` — a second, more fleshed-out `MLP_Shell(ANN_Shell)` with stub `forward`/`backward`/`train`/layer-creation methods (all `pass`); same bare-import pattern as `MLP.py`.
- `src/nodes/basic.py` — `Basic` class; `__init__` has no `self` parameter (looks like a bug).
- `pyproject.toml` declares `packages = [{ include = "src" }]`.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- Consumed by `open-ai-gym` (both the `neural-networks/open-ai-gym` and `tensorflow/open-ai-gym` copies) via a `pyproject.toml` path dependency (`abstract_base_classes = {path = "../abstract-base-classes"}`), though the code those packages actually import (`from abstract_base_classes.ann_shell import ANN_Shell`, see `digit-recognition/classes/MLP_tensorflow.py`) doesn't match this package's real module path (`src/shells/ANN.py`, no `ann_shell.py` module) — unverified whether this import actually resolves.

## Notes
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Excluded from the pnpm/turbo workspace — see [../../../../known-issues.md](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
