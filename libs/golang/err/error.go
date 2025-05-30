package err

type Error struct {
	// Code    int
	Message  string
	Err      error
	ErrInMsg bool
}

type TypeError[E error] struct {
	Error
	Type E
}

func (e *Error) Set(err error) bool {
	isErr := err != nil
	if isErr {
		e.Err = err
	}
	return isErr
}

func (e *Error) Panic()               { Panic(e.Err) }
func (e *Error) Fatal()               { Fatal(e.Err) }
func (e *Error) Handle(f func(error)) { Handle(e.Err, f) }
func (e *Error) Check(data any)       { Check(data, e.Err) }
func (e *Error) Must(data any)        { Must(data, e.Err) }

func (te *TypeError[E]) Panic()               { PanicType[E](te.Err) }
func (te *TypeError[E]) Fatal()               { FatalType[E](te.Err) }
func (te *TypeError[E]) Handle(f func(error)) { HandleType[E](te.Err, f) }
func (te *TypeError[E]) Check(data any)       { CheckType[E](data, te.Err.(E)) }
func (te *TypeError[E]) Must(data any)        { MustType[E](data, te.Err.(E)) }
