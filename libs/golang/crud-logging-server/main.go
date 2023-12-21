package main

import (
	"server/crud"
)

func main() {

	b := crud.NewBasicCRUD()
	b.Serve()
}
