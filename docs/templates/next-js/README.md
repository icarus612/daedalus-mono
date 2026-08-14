# next-js (deploy template)

Deploy-only scaffolding for shipping a Next.js app to Google Cloud Run — two files, no code, no `package.json` (so it is **not** a pnpm workspace package and has no build/dev scripts):

**Path:** `templates/next-js`

## Contents
- `dockerfile` — multi-stage build on `node:18-alpine`: `npm ci` deps stage, `npm run build` builder stage, then a slim runner that copies `public/`, `.next/standalone`, and `.next/static`, runs as a non-root `nextjs` user, and starts `node server.js` on `PORT` (default `8080`). It relies on Next's standalone output tracing, so the target app must set `output: "standalone"` in its Next config.
- `cloudbuild.yaml` — GCP Cloud Build pipeline: docker build (dockerfile path parameterized via substitutions), push to `gcr.io/$PROJECT_ID/$REPO_NAME:$COMMIT_SHA`, then `gcloud run deploy` to Cloud Run (managed). Substitutions to fill in: `_SERVICE_DIR`, `_DOCKERFILE` (default `dockerfile`), `_SERVICE_NAME` (placeholder — must be replaced), `_REGION` (default `us-central1`).

## Usage
Copy both files into a Next.js app directory, set `output: "standalone"` in `next.config.*`, replace the `_SERVICE_NAME` substitution (and `_SERVICE_DIR`/`_REGION` as needed), and point a Cloud Build trigger at the `cloudbuild.yaml`. `apps/next/maze-runner` carries a near-identical pair of files derived from this template — see [../../apps/next/maze-runner/README.md](../../apps/next/maze-runner/README.md).

## Notes
- The dockerfile installs with `npm ci` from a standalone `package*.json` — it targets a self-contained app repo, not this monorepo's pnpm workspace layout (no `pnpm-lock.yaml`/workspace handling).
- The in-tree `templates/next-js/README.md` was a 0-byte file before this documentation pass.
