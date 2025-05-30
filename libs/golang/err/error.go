package err

type Error struct {
	Code    int
	Message string
	err     error
}

func (e *Error) Check(err error) bool {
	check := err != nil
	if check {
		e.err = err
	}
	return check
}

func (e *Error) Handle(f func(error)) { Handle(e.err, f) }

func (e *ErrorHandler[E]) Chandle(err error) {
	if e.Check(e.err) {
		e.handlerFunc(e.err)
	}
}
