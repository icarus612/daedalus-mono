# Build Tools

Common build tools and scripts for the monorepo.

## Python Scripts

The `py-scripts/` directory contains helper scripts for Python packages:

- `py-install`: Creates venv and installs dependencies (Poetry or pip)
- `py-build`: Ensures venv exists and dependencies are up to date
- `py-dev`: Activates venv and runs the appropriate dev command
- `py-lint`: Runs Python linting with ruff

## Usage

These scripts are available in all workspace packages via pnpm/node_modules/.bin after running `pnpm install` at the monorepo root.

In any Python package, you can use:
```json
{
  "scripts": {
    "install": "py-install",
    "build": "py-build",
    "dev": "py-dev",
    "lint": "py-lint"
  },
  "devDependencies": {
    "lib.bash.build-tools": "workspace:*"
  }
}
```