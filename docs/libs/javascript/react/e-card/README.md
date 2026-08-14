# e-Card

A single static HTML page (`index.html`) implementing a click-to-flip greeting card: a `.card` div toggles an `open` class on click via a few lines of vanilla JS, with the flip/reveal effect done entirely in CSS (no animation library is actually loaded, despite the page's own copy describing it as "a fun little card with a jQuery animation"). The front face reveals a message and links out to `github.com/icarus612`. Images (`front.jpg`, `middle.jpg`, `middle2.png`, `logo.jpg`, `sig.png`, `noSig.png`, `github.png`) are the card's artwork, referenced directly by the HTML/CSS.

**Path:** `libs/javascript/react/e-card`
**Workspace name:** `lib.javascript.react.e-card`

## Stack
- Static HTML/CSS/vanilla JS only — **no React, and no dependencies of any kind** (`package.json` has no `dependencies` section at all)
- Despite living under `libs/javascript/react/`, this is not a React project

## Structure / entry points
- `index.html` — the entire application: markup, inline `<style>`, and inline `<script>`
- `front.jpg`, `middle.jpg`, `middle2.png`, `logo.jpg`, `sig.png`, `noSig.png`, `github.png` — static image assets used by the card

## Usage
- `npm run build` / `npm run lint` → no-op echo placeholders; there is no `dev`, `start`, or `test` script
- In practice: open `index.html` directly in a browser, or serve the directory with any static file server

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it (harmless here: there is nothing to install or build), and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was the CI-generated directory tree, not package-specific documentation; this page supersedes it.
- Filed under `libs/javascript/react/` but contains no React (or any framework) code — it's a plain static HTML page misfiled by category.
