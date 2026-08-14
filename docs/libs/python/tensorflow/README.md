# libs/python/tensorflow

A single-package category: [`open-ai-gym`](open-ai-gym/README.md), a Gymnasium + TensorFlow/Keras reinforcement-learning experiment that is a byte-for-byte duplicate of `libs/python/neural-networks/open-ai-gym` (differing only in its exact `3.11` Python pin, a committed `poetry.lock`, and a path dependency on `../abstract-base-classes` that does not exist under this directory).

Like the `neural-networks/*` packages, it sits three levels deep and is therefore **excluded from the pnpm workspace** (the workspace globs only reach `libs/*/*`) — root `pnpm install`/`turbo` silently skip it, so it must be set up manually. See [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
