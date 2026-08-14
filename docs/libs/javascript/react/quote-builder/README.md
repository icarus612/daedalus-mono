# Quote Builder

React component sources for a project-quote calculator — a multi-step form (`basicNeeds.js`, `frontEndNeeds.js`, `backEndNeeds.js`, `pages.js`, `infoForm.js`) that tallies selected requirements into a price estimate (`priceBox.js`, `scale.js`). It is wired up as a Create React App project (`react-scripts 2.1.1`), but **it is not runnable as-is**: there is no `public/` directory (CRA requires `public/index.html`), no `react-dom` dependency, no `ReactDOM.render` bootstrap anywhere in `src/`, and `src/index.js` imports from `./components/router.js` — a path that doesn't exist (the real file is `src/router.js`). Treat it as a component-source snapshot, not a working app.

**Path:** `libs/javascript/react/quote-builder`
**Workspace name:** `lib.javascript.react.quote-builder`

## Stack
- React `^16.8.6` — old/frozen, not React 18+; **no `react-dom` is declared**, which CRA needs to render anything
- `react-scripts 2.1.1` (Create React App tooling, itself long unmaintained)
- `history ^4.9.0` (client-side routing/navigation)

## Structure / entry points
- `src/index.js` — declared `main`; defines and default-exports the root `QuoteMachine` component (it is *not* a CRA bootstrap — no `ReactDOM.render`), and imports from a nonexistent `./components/router.js` path
- `src/router.js` — routing logic (built on `history`)
- `src/pages.js` — page/step definitions
- `src/basicNeeds.js`, `src/frontEndNeeds.js`, `src/backEndNeeds.js` — quote requirement categories
- `src/priceBox.js`, `src/scale.js` — pricing display/calculation
- `src/infoForm.js`, `src/input.js`, `src/button.js` — form UI components

## Usage
- `npm run dev` / `npm run start` → `react-scripts start`
- `npm run build` → `react-scripts build`
- `npm run test` → `react-scripts test`
- All of these fail as shipped (see the missing `public/` shell, missing `react-dom`, and broken import above). To resurrect it you'd need to add a CRA `public/index.html`, add `react-dom`, add a bootstrap that renders `QuoteMachine`, and fix the `./components/router.js` import to `./router.js`.

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; it must be installed/built manually inside its own directory, and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was the CI-generated directory tree, not package-specific documentation; this page supersedes it.
- React `16.8.6` (the version Hooks first shipped in) + `react-scripts 2.1.1` are both old/frozen; CRA has since been deprecated upstream — treat this as a legacy snapshot, not a template for new work. Even once fixed, `react-scripts 2.x` (webpack 4) fails on modern Node (17+) without `NODE_OPTIONS=--openssl-legacy-provider`.
