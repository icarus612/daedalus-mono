# Resume Builder

A Svelte component library for building a personal resume/portfolio page: `src/index.js` re-exports `Hero`, `Navbar`, `Skills`, `Services`, `Resume`, `Portfolio`, and `Contact` components from `src/components/`. Each component has a matching Storybook `.stories.js` file for isolated development and review.

**Path:** `libs/javascript/svelte/resume-builder`
**Workspace name:** `lib.javascript.svelte.resume-builder`

## Stack
- Svelte `^5.0.0` (runes-capable) — the only modern frontend stack in this repo
- Vite `^5.4.0` (library build via `@sveltejs/vite-plugin-svelte ^4.0.0`)
- Storybook `^8.6.14` (`@storybook/svelte-vite`, `@storybook/addon-essentials`, `@storybook/addon-docs`)
- TypeScript `^5.0.0` (devDependency; note `svelte ^5.0.0` is redundantly listed in both `dependencies` and `devDependencies`)

## Structure / entry points
- `src/index.js` — package entry, re-exporting each component
- `src/components/*.svelte` — `Hero`, `Navbar`, `Skills`, `Services`, `Resume`, `Portfolio`, `Contact`
- `src/components/*.stories.js` — one Storybook story file per component
- `.storybook/main.js`, `.storybook/preview.js` — Storybook configuration
- `vite.config.js` — Vite library-mode build: entry `src/index.js`, global name `ResumeBuilder`, `svelte` externalized; output file names follow `index.${format}.js`

## Usage (standalone, inside this directory)
- Install: `pnpm install` (the package has its own `pnpm-lock.yaml` and `node_modules`, independent of the root workspace)
- `pnpm dev` / `pnpm storybook` → `storybook dev -p 6006` (the primary dev entry)
- `pnpm build` → `vite build` (library build to `dist/`)
- `pnpm preview` → `vite preview`
- `pnpm build-storybook` → `storybook build`
- `prepublishOnly` runs `build` automatically before publish

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; it must be installed/built manually inside its own directory (hence its own `pnpm-lock.yaml`), and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- **Publish-field mismatch:** `package.json` declares `main: dist/index.js`, `module: dist/index.esm.js`, and `types: dist/index.d.ts`, but the Vite config emits `index.<format>.js` (e.g. `index.es.js`, `index.umd.js` — Vite has no `esm` format name and never emits a bare `index.js`), and nothing in the build generates `.d.ts` declarations (no dts plugin is configured). As published-package metadata, all three fields point at files the build does not produce.
- The original in-repo README existed but was empty (0 bytes) — there was no boilerplate or prior content to preserve or supersede.
