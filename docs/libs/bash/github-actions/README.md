# github-actions

Helper scripts invoked by (or written for) the repo's GitHub Actions workflows — see [../../../architecture.md](../../../architecture.md#cicd-this-repo-is-a-source-of-truth-that-fans-out). The in-tree `README.md` was empty (0 bytes); this page documents the scripts actually present.

**Path:** `libs/bash/github-actions`
**Workspace name:** `lib.bash.github-actions`

## Scripts

### `create-mono-file-tree.sh` (bin: `create-mono-file-tree`)

Recursively walks a directory tree and prints an HTML `<pre>`-style tree in which every directory containing a `README.md`/`README.txt`/`README` becomes an `<a href="/<relative-path>">` link. Takes an optional base-directory argument (defaults to `$PWD`).

Used by two workflows:
- `.github/workflows/update-readme.yml` — regenerates this repo's root `README.md` project-structure section (which is why the root README must never be hand-edited).
- `.github/workflows/build-maze-runner.yml` — regenerates the README of the external `maze-runner-mono` repo after syncing content into it.

### `build-maze-runner.sh` (bin: `build-maze-runner`)

Clones `icarus612/maze-runner-mono`, copies the maze-runner implementations (Flask and Next apps; Python, Node, React, Solid libs) into it, and commits/pushes.

**Not currently runnable or referenced**: the file contains literal GitHub Actions template syntax (`${{ secrets.PAT }}`) that bash cannot expand, and `build-maze-runner.yml` does not call it — the workflow inlines its own (slightly different) copy steps instead. Treat this script as a superseded draft of that workflow.

## Package scripts

`package.json` scripts are all no-op echoes (`build`, `dev`, `lint`); the value of this package is the two bins above plus their use from CI.
