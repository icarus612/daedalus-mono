package err

type Handler[H func(error)] struct {
	Error
	handle H
}

type TypeHandler[H func(error), E error] struct {
	Handler[H]
	Type E
}

func (h *Handler[H]) Handle() {
	Handle(h.Err, h.handle)
}

func (th *TypeHandler[H, E]) Handle() {
	Handle(th.Err, th.handle)
}
