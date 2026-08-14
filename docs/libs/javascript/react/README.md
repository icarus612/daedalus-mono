# libs/javascript/react

A mix of frameworks despite the shared directory name — verified per-package from each `package.json`:

| Package | Actual stack | Docs |
|---|---|---|
| `e-card` | static HTML/CSS/images, **no React dependency at all** — `build`/`lint` scripts are no-op echoes | [e-card/README.md](e-card/README.md) |
| `labyrinth` | Next.js `^12.1.5`, React `^18.0.2` (Pages Router) | [labyrinth/README.md](labyrinth/README.md) |
| `markdown-builder` | create-react-app (`react-scripts 2.1.1`), React `^16.6.1` — old/frozen | [markdown-builder/README.md](markdown-builder/README.md) |
| `maze-runner` | plain JS source files (`src/index.js`, `src/randomizer.js`, `src/build.js`), **no React dependency declared**, no real build config | [maze-runner/README.md](maze-runner/README.md) |
| `quest` | Next.js `^12.1.5`, React `^18.0.0` (Pages Router) | [quest/README.md](quest/README.md) |
| `quote-builder` | create-react-app (`react-scripts 2.1.1`), React `^16.8.6` — old/frozen | [quote-builder/README.md](quote-builder/README.md) |

All six are excluded from the pnpm workspace ([../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo)).
