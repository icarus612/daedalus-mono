# Build Scripts

A small internal Node.js utility for generating a Svelte component barrel file. `src/index.js` runs `generateComponentIndex()`, which scans a `src/lib/components` directory for `.svelte` files and writes an `index.js` with a named `export { default as ComponentName } from './ComponentName.svelte'` line for each one (PascalCasing the file name). It has no dependencies, no build step, and no dev server — it's a one-shot codegen script.

**Path:** `libs/javascript/node/build-scripts`
**Workspace name:** `lib.javascript.node.build-scripts`

## Stack
- Node.js (ESM `import`/`export` syntax, no `"type"` field in `package.json`)
- No runtime or dev dependencies declared

## Structure / entry points
- `src/index.js` — entry point; imports and immediately invokes `generate-component-index.js`.
- `src/generate-component-index.js` — the only script actually wired up; generates the Svelte component barrel file described above.
- `src/generate-image-src.js` — dead code: byte-for-byte identical to `generate-component-index.js` (same function body, same `componentsDir`/`.svelte` scan) despite its "image src" name. Not imported anywhere.
- `src/generate-build-index.js` — dead code: not imported anywhere, and would throw at runtime — it references a `componentsDir` variable that is never defined in that file.

## Usage
- `pnpm dev` → runs `echo 'No dev command for library'` (no-op placeholder; there is no `build`, `lint`, or `test` script defined in `package.json`).
- In practice this script is meant to be run directly, e.g. `node src/index.js` from a project that has a `src/lib/components` directory of `.svelte` files.

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; it must be installed/built manually inside its own directory, and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was the CI-generated directory tree, not package-specific documentation; this page supersedes it.
- Two of the three scripts in `src/` (`generate-image-src.js`, `generate-build-index.js`) are unused/dead code and the latter contains a reference-error bug; only `generate-component-index.js` is actually exercised by `src/index.js`.
