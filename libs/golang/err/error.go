package err

type Error struct {
	// Code    int
	Message string
	Err     error
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

func (e *Error) PanicType(err error)                 { PanicType[E](e.Err) }
func (e *Error) FatalType(err error)                 { FatalType[E](e.Err) }
func (e *Error) HandleType(f func(error), err error) { HandleType[E](e.Err, f) }
func (e *Error) CheckType(data any)                  { Check(data, e.Err) }
func (e *Error) MustType(data any)                   { Must(data, e.Err) }
