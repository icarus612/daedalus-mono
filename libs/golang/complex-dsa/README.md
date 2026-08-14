# complex-dsa

An early-stage Go library of composite data-structure building blocks. It currently defines linked-list and node types only — there are no methods, algorithms, binaries, or tests yet.

## What's here

```
pkg/
├── linked-list.go   # LinkedList / FullLinkedList structs (package complex_dsa)
└── nodes/
    ├── snode.go     # SNode: singly linked node
    └── dnode.go     # DNode: doubly linked node
```

- `LinkedList` — holds `Head` and `Tail` pointers to `nodes.SNode`.
- `FullLinkedList` — embeds `LinkedList` (no additional fields yet).
- `nodes.SNode` — `Value any`, `Child *SNode`.
- `nodes.DNode` — `Value any`, `Child *DNode`, `Parent *DNode`.

Node values are typed `any`; no constructors or traversal/insert/remove operations are implemented.

## Installation

```bash
go get github.com/dae-go/complex-dsa
```

Requires Go 1.24.2 (per `go.mod`). No external dependencies.

## Usage

```go
import (
    dsa "github.com/dae-go/complex-dsa/pkg"
    "github.com/dae-go/complex-dsa/pkg/nodes"
)

list := dsa.LinkedList{
    Head: &nodes.SNode{Value: 1},
}
```

Build and test:

```bash
go build ./...
go test ./...   # no test files yet
go vet ./... && go fmt ./...
```

## Development

This library is automatically synced from the monorepo. Please make changes in `libs/golang/complex-dsa` of the [main repository](https://github.com/icarus612/daedalus-mono).
