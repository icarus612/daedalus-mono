# Digit Recognition (Neural Networks)

Two independent, non-interoperating implementations of an MNIST digit-recognition MLP. `classes/MLP_vanilla.py`'s `Digit_Recognition_MLP` is a from-scratch NumPy implementation (manual forward/backward pass, sigmoid activation, `fetch_openml("mnist_784")` for data) with a `__main__` training/evaluation script. `classes/MLP_tensorflow.py`'s `Digit_Recognition_MLP` is a separate class of the same name built on `tensorflow.keras` (`Sequential`/`Flatten`/`Dense`, `mnist.load_data()`), subclassing `ANN_Shell` from the `abstract-base-classes` package — but its `__init__` references an undefined variable `l` (`load_model(l) if os.path.isfile(l) else self.build()`), which would raise a `NameError` if run; not executed to confirm. Two pre-trained model artifacts (`digit_recognition_model.h5`, `digit_recognition_model.keras`) are committed under `models/`.

**Path:** `libs/python/neural-networks/digit-recognition`
**Workspace name:** `lib.python.neural-networks.digit-recognition`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml`, no `poetry.lock` present) — `pyproject.toml` declares no dependencies beyond the Python version, and `requirements.txt` is empty, despite the code importing `numpy`, `scikit-learn`, and `tensorflow`.

## Structure / entry points
- `classes/MLP_vanilla.py` — pure-NumPy `Digit_Recognition_MLP` with `forward`/`backward`/`train`/`predict`, plus a `__main__` block that fetches MNIST, trains, and prints test accuracy.
- `classes/MLP_tensorflow.py` — Keras-based `Digit_Recognition_MLP(ANN_Shell)`; `build()`, `train()`, and a `__main__` block calling `.train()` then `.save()` (no `save()` method is defined on the class, so this would also fail if run).
- `models/digit_recognition_model.h5`, `models/digit_recognition_model.keras` — committed pre-trained model weights.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- No `bin` entries; run scripts directly, e.g. `python classes/MLP_vanilla.py`.

## Notes
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Excluded from the pnpm/turbo workspace — see [../../../../known-issues.md](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- See [../abstract-base-classes/README.md](../abstract-base-classes/README.md) for the `ANN_Shell` base class `MLP_tensorflow.py` subclasses (import path mismatch noted there).
