# Web Crawlers

A collection of three standalone, unconnected scraper scripts, each targeting a different site: `cubeTutor-site/spider.js` (a raw `fetch()` POST replaying a captured CubeTutor form request, logging the JSON response), `freeCodeCamp-site/spider.js` (fetches `freecodecamp.org/news/` with `request` and parses it with `cheerio`), and `medium-site/spider.js` (same `request`+`cheerio` pattern against `medium.com/topic/members`). There is no shared entry point, index, or CLI tying them together — each is a script meant to be run individually with `node`.

**Path:** `libs/javascript/node/web-crawlers`
**Workspace name:** `lib.javascript.node.web-crawlers`

## Stack
- Node.js, CommonJS (`require`)
- `cheerio ^1.0.0-rc.3` (HTML parsing)
- `request ^2.88.0` (HTTP client — long deprecated/unmaintained on npm)

## Structure / entry points
- `cubeTutor-site/spider.js` — one-shot `fetch()` script replaying a captured form POST
- `freeCodeCamp-site/spider.js` — `request` + `cheerio` scraper for freeCodeCamp's news page
- `medium-site/spider.js` — `request` + `cheerio` scraper for Medium's members/topics page
- `package.json`'s `main` field points at `index.js`, which does not exist anywhere in this package

## Usage
- No `dev`/`start` script is defined; scripts are run directly, e.g. `node freeCodeCamp-site/spider.js`
- `npm run build` / `npm run lint` → no-op echo placeholders
- `npm run test` → placeholder that exits with an error (no tests configured)

## Notes
- **Not a pnpm workspace member** — every `libs/javascript/*/*` package sits one level too deep for the `libs/*/*` globs in `pnpm-workspace.yaml`, so root `pnpm install` and `turbo` silently skip it; install its dependencies manually inside this directory (`pnpm install` here) before running the spiders, and note that any `workspace:*` dependencies these excluded packages declare cannot resolve. See [known-issues](../../../../known-issues.md#workspace-glob-excludes-a-third-of-the-repo).
- The original in-repo README was the CI-generated directory tree, not package-specific documentation; this page supersedes it.
- The `request` package has been deprecated by its maintainers since 2020; any future work on this package should consider replacing it (e.g. with `fetch`, as `cubeTutor-site/spider.js` already does).
- `package.json`'s `main: "index.js"` does not resolve to a real file — there is no root-level `index.js` in this package.
