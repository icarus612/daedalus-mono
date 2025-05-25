package pkg

type CRUD interface {
	Serve()
	GetItem()
	GetItems()
	CreateItem()
	UpdateItem()
	DeleteItem()
	HandleItem()
}
