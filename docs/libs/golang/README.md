# libs/golang

Independent Go modules, each with its own `go.mod` and its own Go version (no repo-wide `go.work`). All are recognized by the pnpm/turbo workspace (`package.json` wrappers shell out to `go build/test/vet/fmt`). Each module's own module path is `github.com/dae-go/<name>` — rewritten there by the `sync-go-packages.yml` CI workflow, which mirrors each of these directories into a standalone repo under the `dae-go` GitHub org; see [../../architecture.md](../../architecture.md#cicd-this-repo-is-a-source-of-truth-that-fans-out).

| Package | Go version | Docs |
|---|---|---|
| `complex-dsa` | 1.24.2 | [complex-dsa/README.md](complex-dsa/README.md) |
| `crud-server` | 1.21 | [crud-server/README.md](crud-server/README.md) |
| `err` | 1.24.2 | [err/README.md](err/README.md) |
| `maze-runner` | 1.21 | [maze-runner/README.md](maze-runner/README.md) |
| `process-monitor` | 1.24.2 | [process-monitor/README.md](process-monitor/README.md) |
| `pythonify` | 1.22 | [pythonify/README.md](pythonify/README.md) |
| `auth-go` | — | *(empty placeholder — no files)* |

Convention: `cmd/`, `internal/`, `pkg/` layout, concrete types (no `interface{}`), no `time.Sleep`, table-driven `_test.go` files alongside source in `pkg/`. See [../../conventions.md](../../conventions.md#go).
