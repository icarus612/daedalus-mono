package err

import "log"

type ErrorHandler[H func()] struct {
	Code        int
	Message     string
	err         error
	handlerFunc H
}

func (eh *ErrorHandler[H]) Check(err error) bool {
	check := err != nil
	if check {
		eh.err = err
	}
	return check
}

func (eh *ErrorHandler[E]) Handle() {
	if eh.err != nil {
		log.Fatal(eh.err)
	}
}

func (eh *ErrorHandler) Chandle(err error) {
	if eh.Check() {
		eh.handlerFunc()
	}
}
