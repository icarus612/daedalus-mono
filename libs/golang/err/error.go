package err

type Error struct {
	Code    int
	Message string
	err     error
}

func (e *Error) Panic()               { Panic(e.err) }
func (e *Error) Fatal()               { Fatal(e.err) }
func (e *Error) Handle(f func(error)) { Handle(e.err, f) }
func (e *Error) Check(data any)       { Check(data, e.err) }
func (e *Error) Must(data any)        { Must(data, e.err) }
