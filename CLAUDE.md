# Repo instructions

- **Work lands by merging the feature branch into `main` locally, then pushing `main` — do not open
  pull requests.** This is how work has landed here; an earlier automated run opened a PR (#23) by
  following a generic default instead of this repo's actual practice.
- **`main` is the base branch**, matching `CLAUDE_BASE_BRANCH` in `.claude/settings.json` and
  `.agents/settings.json`.
- **This file is the authority on that point, not git history.** History mixes both patterns — several
  recent commits are squash-merged PRs (`#16`, `#18`-`#22`), while the two most recent
  `feat(anki-tools)` commits went straight to `main` — so history alone does not settle it.
