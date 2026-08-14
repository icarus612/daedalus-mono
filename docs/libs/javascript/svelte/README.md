# libs/javascript/svelte

Svelte packages — currently just one, and it's the only modern frontend stack in the repo (Svelte 5 + Vite 5 + Storybook 8, verified from its `package.json`). Like every `libs/javascript/*/*` package it is excluded from the pnpm workspace (the `pnpm-workspace.yaml` globs stop at `libs/*/*`) and must be installed/built manually inside its own directory — see [../../../known-issues.md](../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).

| Package | Docs |
|---|---|
| `resume-builder` | [resume-builder/README.md](resume-builder/README.md) — Svelte component library for a resume/portfolio page; dev via Storybook (`storybook dev -p 6006`), library build via `vite build` |
