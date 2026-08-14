# Maze Runner (Go)

A Go library and pair of CLI tools that generate random multi-level (3D) ASCII mazes and solve them with a breadth-first search, printing both the raw maze and the solved path.

## What's here

```
.
├── cmd/
│   ├── cli-solver/     # Interactive solver: prompts for size, maze type, and path character
│   └── quick-solver/   # Flag-driven solver: -length, -width, -height, -mazeType, -pathChar
├── pkg/
│   ├── maze.go         # Maze type, NewMaze, random layout generation (BuildNew)
│   ├── runner.go       # Runner type, NewRunner: BFS over the layout, shortest-path tracking
│   ├── node.go         # Node / RunnerNode
│   ├── path.go         # Point ([3]int) and Path (map[Point]bool)
│   └── utils.go        # Floor / Layout types, Traverse, Print, DeepCopy
└── bin/                # Prebuilt binaries (cli-solver, quick-solver)
```

## How it works

- `NewMaze([3]int{length, width, height}, buildType)` allocates a `Layout` (slice of floors, each a 2D grid of `Node`s) and randomly fills it with walls (`#`), open spaces (` `), floor/stair cells (`f`) linking levels, a start (`s`), and an end (`e`).
- `NewRunner(maze, pathChar)` finds the endpoints, walks the maze breadth-first (`MakeNodePaths`), records the shortest path found, and writes the path character into a deep copy of the layout (`BuildPath`).
- `Runner.Completed` reports whether the end was reached; `ViewCompleted()` prints the solved maze, `ViewCompletedPath()` prints the path coordinates.

## Usage

### Interactive CLI

```bash
go run ./cmd/cli-solver
# Prompts: L x W x H size (defaults 40 x 20 x 3), maze type, path character (default x)
```

### Flag-driven CLI

```bash
go run ./cmd/quick-solver -length 20 -width 20 -height 3 -pathChar x
```

Flags (with defaults): `-length 20`, `-width 20`, `-height 3`, `-mazeType r`, `-pathChar x`.

### As a library

```go
import mr "github.com/dae-go/maze-runner/pkg"

m := mr.NewMaze([3]int{40, 20, 3}, 'r')
r := mr.NewRunner(m, 'x')

m.ViewLayout()
if r.Completed {
    r.ViewCompleted()
}
```

## Installation

```bash
go get github.com/dae-go/maze-runner
```

Requires Go 1.21 (per `go.mod`). No external dependencies.

## Build & test

```bash
go build -o bin/cli-solver ./cmd/cli-solver
go build -o bin/quick-solver ./cmd/quick-solver
go test ./...   # no test files yet
```

## Development

This library is automatically synced from the monorepo. Please make changes in `libs/golang/maze-runner` of the [main repository](https://github.com/icarus612/daedalus-mono). Sibling implementations of the same idea exist there in Python, JavaScript, and as Flask/Next.js apps.
