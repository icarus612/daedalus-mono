# Maze Runner (React)

React/JSX page sources for a maze builder/solver UI — `src/index.js` (a landing page linking to a "Randomized" quick-builder and a "Build Your Own" custom builder), `src/randomizer.js` (renders and solves a randomly generated maze with scale controls), and `src/build.js` (a click-to-paint grid editor for placing wall/start/end tiles, then solving). All three use React hooks and JSX and import from `components/`, `styles/*.module.scss`, and `next/link` — i.e. they were written against a Next.js app shell (they mirror `apps/next/maze-runner/pages/` in the daedalus-mono repo) — but **no such shell, no React, and no build tooling exists in this package**: `package.json` declares no `dependencies` at all, and `build`/`lint` are no-op echo placeholders.

**Path:** `libs/javascript/react/maze-runner`
**Package name:** `lib.javascript.react.maze-runner`

## Stack
- React function components with hooks, JSX, `next/link`, and Sass CSS modules **as source syntax only** — none of `react`, `next`, `classnames`, or `sass` is declared in `package.json`, and there is no bundler/build configuration in the package
- Despite the "plain `.js`" file extensions, these files are JSX and cannot run under Node or a browser as-is; they are source-only

## Structure / entry points
- `src/index.js` — landing page with links to `/randomizer` and `/build` (uses `next/link`, implying an unincluded Next.js host app)
- `src/randomizer.js` — random maze generation + solve UI, using `Maze`/`Runner`/`Header` components imported from an unincluded `components/` module path
- `src/build.js` — manual maze grid editor + solve UI, same unincluded `components/` dependency

## Usage
- `npm run build` / `npm run lint` → no-op echo placeholders; there is no `dev`, `start`, or `test` script
- These files are not runnable in isolation — there's no bundler, no `react`/`next` dependency, and the `components/`, `styles/*.module.scss` import paths they rely on aren't present in this package. The working, runnable version of this UI is `apps/next/maze-runner` in the daedalus-mono repo.

## Notes
- Not a pnpm workspace member — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it, and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../docs/known-issues.md#workspace-glob-excludes-a-third-of-the-repo) (link resolves in the daedalus-mono source repo).
- Likely extracted/leftover page source from the Next.js app (compare the sibling `quest`/`labyrinth` packages, which have real Next.js scaffolding) rather than a working standalone package.
- This README is deliberately a real file, not a symlink into `/docs`: `.github/workflows/build-maze-runner.yml` copies this directory verbatim (`cp -R`) into the `maze-runner-mono` satellite repo, where a symlink would arrive dangling. The `/docs` counterpart (`docs/libs/javascript/react/maze-runner/README.md`) is a symlink back to this file.
