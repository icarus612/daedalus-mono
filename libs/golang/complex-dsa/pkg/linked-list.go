package complex_dsa

import "github.com/dae-go/complex-dsa/pkg/nodes"

type LinkedList struct {
	Head *nodes.SNode
	Tail *nodes.SNode
}

type FullLinkedList struct {
	LinkedList
}
