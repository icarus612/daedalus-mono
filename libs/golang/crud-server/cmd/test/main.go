package main

import basic "github.com/icarus612/crudServer-lib-GO/basic"

func main() {

	b := basic.NewBasicCRUD()
	b.Serve()
}
