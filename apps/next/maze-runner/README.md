# Maze Runner (Next.js)

A client-side maze builder/solver as a Next.js **Pages Router** app. `pages/index.js` links to `/randomizer` (randomized maze build-and-solve), `/build` (manual builder), and `/info`; the maze data structure and solver live in `components/` (`maze.js`, `node.js`, `runner.js`, plus `header.js`). `pages/api/hello.js` is the untouched create-next-app sample API route.

**Path:** `apps/next/maze-runner`
**Workspace name:** `app.next.maze-runner`

## Stack
Per `package.json`: `next ^12.1.5`, `react ^18.0.0`, `react-dom ^18.0.0`, `sass ^1.32.8` (SCSS modules in `styles/`), `classnames ^2.3.2`.

## Usage
This package is inside the pnpm workspace and runs via root `turbo` (plain Next scripts, no `py-*` wrappers):
- `pnpm install` — dependencies (from the workspace root)
- `pnpm dev` → `next dev` (Next's default port `3000`; this app does not use the Flask apps' port mechanisms)
- `pnpm build` → `next build && next export` (static export into `out/`)
- `pnpm start` → `next start -p $PORT`

## Deploy targets
The directory carries configuration for two different deploy paths:
- **Firebase Hosting** — `firebase.json` serves the static `out/` directory produced by `next export`; `.github/workflows/firebase-hosting-{merge,pull-request}.yml` inside this directory only take effect in the satellite `maze-runner-mono` repo (GitHub only reads workflows from a repo root), not in the monorepo.
- **GCP Cloud Run** — `dockerfile` (node:18-alpine multi-stage, `npm ci`, standalone output, `node server.js` on `PORT` default 8080) plus `cloudbuild.yaml` (service `maze-runner-next`, region `us-central1`) and a `cb.yaml` variant (service `maze-runner-next-js-icarus64`, region `non-regional`). These match the shared [`templates/next-js`](../../../docs/templates/next-js/README.md) deploy template. `next.config.mjs` sets `output: "standalone"` to feed this path, even though the workspace `build` script does a static `next export` instead — two intents coexisting in one package.

## Notes
- A package-local `pnpm-lock.yaml` sits alongside the workspace root lockfile; inside the monorepo, pnpm resolves from the root lockfile, so the local one matters only when the directory is used standalone (e.g. in the satellite repo).
- The `cloudbuild.yaml` docker step points at `apps/next/dockerfile` / build context `apps/next` (one level above this package) — verify those paths before wiring a Cloud Build trigger.
- The original README here was the untouched create-next-app boilerplate; this file supersedes it.
- **Symlink direction exception**: this file is the real source of truth (not a symlink) because `.github/workflows/build-maze-runner.yml` copies this directory verbatim into the external `maze-runner-mono` repo via `cp -R`; a symlinked README would arrive dangling there. The `docs/apps/next/maze-runner/README.md` page is instead the symlink, pointing back at this file. See [../../../docs/known-issues.md#symlink-direction-exception-for-ci-synced-packages](../../../docs/known-issues.md#symlink-direction-exception-for-ci-synced-packages).
