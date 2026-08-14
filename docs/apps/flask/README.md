# apps/flask

Three Flask web apps sharing the same dependency pins (`requirements.txt`: Flask `2.3.3`, Werkzeug `2.3.7`, Jinja2 `3.1.2`) and the same Heroku-style deploy shape (`Procfile` + `runtime.txt`).

| App | Docs |
|---|---|
| maze-runner | [maze-runner/README.md](maze-runner/README.md) |
| pokedex | [pokedex/README.md](pokedex/README.md) |
| weather-fortcast | [weather-fortcast/README.md](weather-fortcast/README.md) |

All three (plus `market-bots`, see [../microservices/market-bots](../microservices/market-bots/README.md)) are affected by the two-port-selection-mechanism inconsistency described in [../../architecture.md](../../architecture.md#known-inconsistency-two-port-selection-mechanisms).
