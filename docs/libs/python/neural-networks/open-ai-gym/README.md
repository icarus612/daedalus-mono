# Open AI Gym (Neural Networks)

A reinforcement-learning experiment on top of Gymnasium (the maintained fork of OpenAI Gym) and TensorFlow/Keras. `EnvBuilder` (`classes/env_builder.py`) wraps a Gymnasium environment, subclassing `ANN_Shell` from `abstract-base-classes`, and provides environment reset/render/step-loop helpers (`load_env`, `attempt`). `LunarLanderV2` (`classes/lunar_lander_v2.py`) subclasses `EnvBuilder` for the `LunarLander-v2` environment specifically, building a small Dense Q-network (`build_model`) and tracking Q-learning hyperparameters (`alpha`, `gamma`, `epsilon`). `lunar_lander_v2.py` imports `EnvBuilder` via a bare `from env_builder import EnvBuilder` rather than a relative package import.

**Path:** `libs/python/neural-networks/open-ai-gym`
**Workspace name:** `lib.python.neural-networks.open-ai-gym`

## Stack
- Python `^3.11` via Poetry (`pyproject.toml`, no `poetry.lock` present). Declares real dependencies directly in `pyproject.toml`: `tensorflow ^2.6.0`, `numpy ^1.26.3`, `gymnasium ^0.29.1` (with `box2d`, `atari`, `mujoco` extras), plus a path dependency on the sibling package: `abstract_base_classes = {path = "../abstract-base-classes"}`.

## Structure / entry points
- `open_ai_gym/classes/env_builder.py` — `EnvBuilder(ANN_Shell)`.
- `open_ai_gym/classes/lunar_lander_v2.py` — `LunarLanderV2(EnvBuilder)`, a small Dense Q-network for the LunarLander-v2 Gymnasium environment.
- `open_ai_gym/models/lunar_lander_v2.keras`, `open_ai_gym/models/env_builder.keras` — committed model artifacts.
- Top-level `__init__.py` is empty.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- No `bin` entries; run scripts directly.

## Notes
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Excluded from the pnpm/turbo workspace — see [../../../../known-issues.md](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- This package's source code (`open_ai_gym/classes/env_builder.py`, `lunar_lander_v2.py`, and both `.keras` model files) is byte-for-byte identical to [../../tensorflow/open-ai-gym/README.md](../../tensorflow/open-ai-gym/README.md) — the two directories appear to be duplicates of the same package, differing only in exact vs. caret Python version pin and the presence of a committed `poetry.lock` in the `tensorflow/` copy.
- Path-depends on [../abstract-base-classes/README.md](../abstract-base-classes/README.md), whose actual module layout doesn't match the `abstract_base_classes.ann_shell` import path used here — unverified whether this import resolves at runtime.
