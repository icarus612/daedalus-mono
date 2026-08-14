# libs/bash

Pure CLI shims, installed as `bin` entries in `package.json` (no formal shell version pin). All three are recognized by the pnpm workspace.

| Package | Docs | Role |
|---|---|---|
| `build-tools` | [build-tools/README.md](build-tools/README.md) | `py-install`/`py-build`/`py-dev`/`py-lint` wrapper scripts consumed by every Python app/lib — see [../../architecture.md](../../architecture.md#the-cross-language-wrapper-pattern) |
| `cli-tools` | [cli-tools/README.md](cli-tools/README.md) | general CLI helper scripts |
| `github-actions` | [github-actions/README.md](github-actions/README.md) | scripts invoked by `.github/workflows/*` (e.g. `create-mono-file-tree.sh`), see [../../architecture.md](../../architecture.md#cicd-this-repo-is-a-source-of-truth-that-fans-out) |
