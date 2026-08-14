# Markdown Builder

A Create React App project (`react-scripts 2.1.1`) that renders and edits markdown, using `marked` to parse markdown to HTML and `react-bootstrap` for UI components. Entry point is the standard CRA `src/index.js` → `src/App.js`.

**Path:** `libs/javascript/react/markdown-builder`
**Workspace name:** `lib.javascript.react.markdown-builder`

## Stack
- React `^16.6.1`, React DOM `^16.6.1` — old/frozen, not React 18+
- `react-scripts 2.1.1` (Create React App tooling, itself long unmaintained)
- `marked ^0.5.1` (markdown parsing), `react-bootstrap ^0.32.4`

## Structure / entry points
- `src/index.js` — CRA entry point
- `src/App.js` / `src/App.css` — root component
- `src/App.test.js` — CRA default test
- `src/serviceWorker.js` — CRA default service worker registration
- `public/` — CRA static assets/HTML shell

## Usage
- `npm run dev` / `npm run start` → `react-scripts start`
- `npm run build` → `react-scripts build`
- `npm run test` → `react-scripts test`
- `npm run eject` → `react-scripts eject`

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; run `pnpm install` inside this directory before any of the scripts above, and note that any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was generic personal-profile boilerplate, not package-specific documentation; this page supersedes it.
- React `16` + `react-scripts 2.1.1` are both old/frozen; this predates React Hooks-era conventions and CRA has since been deprecated upstream in favor of frameworks like Next.js/Vite — treat this as a legacy app, not a template for new work. `react-scripts 2.x` (webpack 4) also fails to start/build on modern Node (17+) without `NODE_OPTIONS=--openssl-legacy-provider` or an old Node (≤16).
