# Weather Fortcast (Flask)

A Flask web app that shows current weather for a city via the OpenWeatherMap API. `/` renders a search form (`templates/weather.html`); `/get_weather` (POST) redirects to `/weather`, which queries `api.openweathermap.org/data/2.5/weather` with city / optional state / country / unit and renders the conditions and temperature. Any lookup failure re-renders the form with an error message. (The "fortcast" spelling is the package's actual name — directory, workspace name, and `bin` entry all use it.)

**Path:** `apps/flask/weather-fortcast`
**Workspace name:** `app.flask.weather-fortcast`

## Stack
- Python, Flask `2.3.3` (per `requirements.txt`, the same pin set shared by all `apps/flask/*` apps): `gunicorn==20.1.0`, `Jinja2==3.1.2`, `Werkzeug==2.3.7`, `itsdangerous==2.1.2`, `flask-bootstrap4==4.0.2`, `flask_sslify==0.1.5`, `flask-fontawesome==0.1.5`, `MarkupSafe==2.1.3`, `requests==2.28.0`
- `runtime.txt` pins `python-3.8.0` for the Heroku-style deploy; `flask_sslify` is only activated when a `DYNO` env var is present (i.e. on Heroku)

## Structure / entry points
- `main.py` — the entire app: Flask setup and routes (`/`, `/weather`, `/get_weather`)
- `templates/weather.html`, `static/` — view and assets
- `Procfile` — `web: gunicorn main:app -b "0.0.0.0:$PORT" -w 3`
- `requirements.txt`, `runtime.txt` — pip/Heroku-style dependency and runtime pins

## Usage
This package is inside the pnpm workspace; its `package.json` scripts are thin wrappers over `libs/bash/build-tools` (`lib.bash.build-tools`), driven by root `turbo`:
- `pnpm install` → `py-install` (creates `.venv`, `pip install -r requirements.txt`)
- `pnpm build` → `py-build`
- `pnpm dev` → `py-dev` (runs `flask run` on the fixed port **5003**)
- `pnpm lint` → `py-lint`
- Production: `gunicorn main:app -b "0.0.0.0:$PORT" -w 3` per `Procfile`
- Direct: `python main.py` self-selects a free port in `3000`–`3100` via `find_available_port`

## Notes
- **Hard-coded API key**: the OpenWeatherMap `appid` is embedded directly in the request URLs in `main.py` rather than read from an env var — it is committed to the repo.
- **Two port mechanisms**: `py-dev` hardcodes port `5003` for this directory, while `main.py` run directly self-selects `3000`–`3100` via `flask_utils.port_finder.find_available_port`. See [../../../known-issues.md#two-flask-dev-port-mechanisms](../../../known-issues.md#two-flask-dev-port-mechanisms).
- `main.py` does `sys.path.insert(0, ../../../libs/python)` to import `flask_utils` — a filesystem cross-package dependency invisible to the pnpm/turbo graph.
- The previous in-repo README was generic personal-profile boilerplate (identical across several packages), not documentation of this app; this page supersedes it.
