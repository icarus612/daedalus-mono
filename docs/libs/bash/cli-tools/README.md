# cli-tools

Personal shell-environment toolkit ("Daedalus"): a collection of bash functions and aliases plus an installer that wires them into the user's shell. Unlike `build-tools`, nothing here is consumed by other workspace packages — it is installed onto the developer's machine.

**Path:** `libs/bash/cli-tools`
**Workspace name:** `lib.bash.cli-tools`

## Installation

`install.sh` (exposed as the `system-install` script and the `cli-tools-install` bin):

1. Copies every `*.sh` under `src/` (recursively, including `src/git-commands/`) to `~/.daedalus/bash/`.
2. Generates `~/.daedalus/bash/workbench.sh` that sources all of them.
3. Appends `source ~/.daedalus/bash/workbench.sh` to the first of `.bashrc`, `.bash_profile`, `.zshrc`, `.zprofile` found.
4. Prints the installed function and alias names.

Linux/Unix only; re-running replaces any existing `~/.daedalus` install.

```bash
pnpm --filter lib.bash.cli-tools run system-install   # or ./install.sh
```

## What gets installed (from `src/`)

- `base.sh` — `lcount` (count directory entries), `bfor` (run a command for each item of a list/dir/file)
- `python.sh` — `penv` (create + activate a venv, optional `-r requirements.txt` install)
- `alias.sh` — `prun` (`poetry run python`), `pclean` (rebuild Poetry env), `gsup`, `gsadd`
- `dae.sh` — `dae` (run a script from `~/.daedalus/python/`)
- `git-commands/gclone.sh` — `gclone` (clone `git@github.com:icarus612/<repo>` and init submodules)
- `git-commands/gup.sh` — `gup` (add/commit/push helper with branch, message, remote-init, and submodule options)
- `git-commands/loops.sh` — `gsf` (`git submodule foreach`), `gsfor` (run a command in every nested git repo)
- `git-commands/submodule-helpers.sh` — `gsinit`, `gsclone`, `gspull`, plus a duplicate `gclone` definition

## Notes / caveats (verified from source)

- `gclone` is defined in both `gclone.sh` and `submodule-helpers.sh`; whichever is sourced last wins.
- `dae.sh` has a `#!/usr/bin/python3` shebang on a file containing a bash function, and its `if $USER == "root"` test is not valid bash — the `dae` helper is broken as written.
- `src/py-scripts/` (`py-build`, `py-dev`, `py-install`) and `bin/` (`py-build`, `py-install`) duplicate older versions of the [build-tools](../build-tools/README.md) scripts; they are not exposed as bins here and `install.sh` ignores them (it only copies `*.sh` files).
- `package.json` has no `build`/`test` scripts, only `system-install` and a no-op `lint`.
