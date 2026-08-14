# Maze Runner (Node)

A small dependency-free maze-generation and -solving library. `src/index.js` exports four factory functions — `Maze`, `Runner`, `Node`, and `QuickSolver` — where `Maze` builds or parses a grid maze (wall/start/end/open characters), `Node` models a graph node with a visited-path set, and `Runner` walks a `Maze`'s open cells to find a solution path.

**Path:** `libs/javascript/node/maze-runner`
**Package name:** `lib.javascript.node.maze-runner`

## Stack
- Plain Node.js (no framework); `package.json` declares no dependencies
- Mixed module syntax: `src/index.js`, `src/maze.js`, and `src/node.js` use ESM `export`, while `src/runner.js` opens with CommonJS `require("./node")` yet ends with `export default Runner`, and `src/quick-solver.js` mixes `require` and `import` in the same file — and `package.json` has no `"type": "module"`, so Node rejects the ESM syntax under its default CJS resolution

## Structure / entry points
- `src/index.js` — entry point (`export { Maze, Runner, Node, QuickSolver }`), though `package.json`'s `main` field points at the nonexistent `src/lib/index.js` (there is no `src/lib` directory; the real files live directly under `src/`)
- `src/maze.js` — `Maze` factory: builds/parses a maze layout from a wall/start/end/open character grid
- `src/runner.js` — `Runner` factory: finds open nodes and paths through a `Maze`
- `src/node.js` — `Node` factory: graph node with children and a visited-path set
- `src/quick-solver.js` — `QuickSolver`: a CLI-style helper intended to build/solve a maze from `process.argv`, but broken (see Notes)
- `examples/` — sample maze text files (`m1.txt`–`m5.txt`; `#` walls, `s` start, `e` end)

## Usage
- `npm run dev` → `node src/index.js` (fails as shipped — see the module-syntax note above)
- `npm run build` / `npm run lint` → no-op echo placeholders
- `npm run test` → placeholder that exits with an error (no tests configured)

## Notes
- Not a pnpm workspace member — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; it must be installed/built manually inside its own directory, and any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../docs/known-issues.md#workspace-glob-excludes-a-third-of-the-repo) (link resolves in the daedalus-mono source repo).
- `src/quick-solver.js` is broken as written: it mixes `require("fs")` with `import` statements in the same file, declares a local `const QuickSolver` while also importing `QuickSolver` from `.` (duplicate identifier), and imports from `../lib/maze` / `../lib/runner` — paths that don't exist (the real files are `./maze.js` / `./runner.js`).
- This README is deliberately a real file, not a symlink into `/docs`: `.github/workflows/build-maze-runner.yml` copies this directory verbatim (`cp -R`) into the `maze-runner-mono` satellite repo, where a symlink would arrive dangling. The `/docs` counterpart (`docs/libs/javascript/node/maze-runner/README.md`) is a symlink back to this file.
