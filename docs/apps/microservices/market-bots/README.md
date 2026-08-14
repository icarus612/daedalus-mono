# Market Bots (Python microservice)

A headless Python service (no web server) that wires up stock-market API clients. On start, `main.py` loads a local `.env` (via `python-dotenv`), initializes an `Alphavantage` controller with `ALPHAVANTAGE_API` and a `Robinhood` controller with `RH_UNAME`/`RH_PASSWORD` (the Robinhood constructor logs in immediately), then — unless the Alpha Vantage key is the literal string `demo` — fetches a daily time series and renders it as a matplotlib closing-price chart (`plt.show()`, so it expects a display). Each step prints a status line and failures are caught and printed rather than fatal.

**Path:** `apps/microservices/market-bots`
**Workspace name:** `app.microservices.market-bots`

## Stack
- Python; `requirements.txt` lists **unpinned** dependencies: `python-dotenv`, `requests`, `pandas`, `numpy`, `alpha-vantage`, `matplotlib`, `robin-stocks`, `pyotp`

## Structure / entry points
- `main.py` — service entry point (see above)
- `controllers/alphavantage.py` — `Alphavantage`: Alpha Vantage REST wrapper (ticker data, `TimeSeries` via the `alpha_vantage` package, daily-series plot)
- `controllers/robinhood.py` — `Robinhood`: logs into the Robinhood OAuth endpoint with username/password and exposes account/portfolio helpers (`requests` + `robin_stocks`)
- `controllers/base_trade_bot_RH.py` — `TradeBot` buy/sell/hold scaffolding on `robin_stocks` with optional `pyotp` MFA; **not imported by `main.py`** and it imports `from src.utilities import RobinhoodCredentials`, a module that does not exist anywhere in this package, so it cannot currently be imported as-is
- `bots/bot.py` — standalone example trading-loop script with placeholder credentials (`YOUR_USERNAME`); also not imported by `main.py`

## Configuration
Requires a `.env` file in the package directory providing at least:
- `ALPHAVANTAGE_API` — Alpha Vantage API key (`demo` skips the data fetch)
- `RH_UNAME`, `RH_PASSWORD` — Robinhood credentials

A `.env` already exists in the working tree and is **not** gitignored — see [../../../known-issues.md#env-present-in-appsmicroservicesmarket-bots-not-gitignored](../../../known-issues.md#env-present-in-appsmicroservicesmarket-bots-not-gitignored). Verified further during this pass: `git ls-files apps/microservices/market-bots/.env` shows the file is already **tracked and committed** (not merely un-ignored) — its contents were not opened here (secrets-shaped file), but any credentials in it should be treated as already exposed in git history and rotated.

## Usage
This package is inside the pnpm workspace; its `package.json` scripts are thin wrappers over `libs/bash/build-tools` (`lib.bash.build-tools`), driven by root `turbo`:
- `pnpm install` → `py-install` (creates `.venv`, `pip install -r requirements.txt`)
- `pnpm build` → `py-build`
- `pnpm dev` → `py-dev`; since `main.py` contains no Flask import, `py-dev` simply runs `python main.py` (the `market-bots → 5004` port mapping inside `py-dev` exists but never triggers for this non-Flask app; see [../../../known-issues.md#two-flask-dev-port-mechanisms](../../../known-issues.md#two-flask-dev-port-mechanisms))
- `pnpm lint` → `py-lint`
- Direct: `python main.py`

## Notes
- This is a run-once script rather than a long-lived daemon: after the optional plot it prints "running..." and exits; there is no scheduler or event loop in `main.py`.
- The previous in-repo README was generic personal-profile boilerplate (identical across several packages), not documentation of this service; this page supersedes it.
