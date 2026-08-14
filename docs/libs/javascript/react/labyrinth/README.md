# Labyrinth

A Next.js application using the Pages Router, with `pages/`, `components/`, `sections/`, `modules/`, and per-scope Sass modules under `styles/` (`styles/pages`, `styles/components`, `styles/sections`). Uses `animejs` for animation and `classnames` for conditional class composition.

**Path:** `libs/javascript/react/labyrinth`
**Workspace name:** `lib.javascript.react.labyrinth`

## Stack
- Next.js `^12.1.5` (Pages Router)
- React `^18.0.2`, React DOM `^18.0.0`
- `animejs ^3.2.1`, `classnames ^2.3.2`, `sass ^1.32.8`

## Structure / entry points
- `pages/index.js`, `pages/_app.js`, `pages/boilerplate-page.js`, `pages/api/` — Next.js Pages Router routes and custom App
- `components/`, `sections/`, `modules/` — UI building blocks
- `styles/` (`styles/pages`, `styles/components`, `styles/sections`) — Sass modules scoped per page/component/section
- `public/`, `public/images/` — static assets

## Usage
- `npm run dev` → `next dev`
- `npm run build` → `next build`
- `npm run start` → `next start -p $PORT`

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; run `pnpm install` inside this directory before `pnpm dev`/`pnpm build`, and note that any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was generic personal-profile boilerplate, not package-specific documentation; this page supersedes it.
- Next.js `12` and React `18` are both several major versions behind current; treat this as a legacy app rather than a template for new work.
