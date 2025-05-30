package err

type ErrorHandler[H func(error)] struct {
	Error
	handlerFunc H
}

func (eh *ErrorHandler[H]) Handle() {
	Handle(eh.Err, eh.handlerFunc)
}
