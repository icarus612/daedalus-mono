# Open AI Gym (TensorFlow variant)

A byte-for-byte duplicate of [../../neural-networks/open-ai-gym/README.md](../../neural-networks/open-ai-gym/README.md) — verified identical `open_ai_gym/classes/env_builder.py` and `open_ai_gym/classes/lunar_lander_v2.py` (`diff` shows no output), and identical model artifacts. `EnvBuilder` wraps a Gymnasium environment (subclassing `ANN_Shell` from `abstract-base-classes`), and `LunarLanderV2` subclasses it with a small Dense Q-network for the `LunarLander-v2` environment.

**Path:** `libs/python/tensorflow/open-ai-gym`
**Workspace name:** `lib.python.tensorflow.open-ai-gym`

## Stack
- Python `3.11` (exact pin, not `^3.11`) via Poetry (`pyproject.toml` + a committed `poetry.lock` — unlike the `neural-networks/open-ai-gym` copy, which has no lock file). Same dependencies otherwise: `tensorflow ^2.6.0`, `numpy ^1.26.3`, `gymnasium ^0.29.1` (`box2d`/`atari`/`mujoco` extras), and a path dependency `abstract_base_classes = {path = "../abstract-base-classes"}` — note this path resolves to `libs/python/tensorflow/abstract-base-classes`, which does not exist; the only `abstract-base-classes` package in the repo lives under `libs/python/neural-networks/`. Unverified whether `poetry install` actually succeeds here.

## Structure / entry points
- `open_ai_gym/classes/env_builder.py` — `EnvBuilder(ANN_Shell)` (identical to the neural-networks copy).
- `open_ai_gym/classes/lunar_lander_v2.py` — `LunarLanderV2(EnvBuilder)` (identical to the neural-networks copy).
- `open_ai_gym/models/lunar_lander_v2.keras`, `open_ai_gym/models/env_builder.keras` — committed model artifacts.

## Usage
- `package.json` scripts (`install`, `build`, `lint`, `dev`) shell out to `libs/bash/build-tools`'s `py-install`/`py-build`/`py-lint`/`py-dev` wrappers, declared via a `workspace:*` devDependency on `lib.bash.build-tools`.
- No `bin` entries; run scripts directly.

## Notes
- The original in-repo README was generic profile boilerplate (a "dev.icarus" personal-portfolio blurb with a GitHub project directory tree), not package-specific documentation; this page supersedes it.
- Excluded from the pnpm/turbo workspace — see [../../../../known-issues.md](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- What distinguishes this directory from `libs/python/neural-networks/open-ai-gym` is minimal and arguably nothing intentional: an exact vs. caret Python pin, and a committed lock file vs. none. This looks like an accidental duplicate rather than a deliberate TensorFlow-specific variant — flagged for whoever owns cleanup, not asserted as settled.
