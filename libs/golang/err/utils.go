package err

import (
	"log"
)

// Helper functions with type conversions (any... to error)
func logP(e error) { log.Panicln(e) }
func logF(e error) { log.Fatalln(e) }

// Basic functions

func Handle(err error, f func(error)) {
	if err != nil {
		f(err)
	}
}

func Panic(err error) { Handle(err, logP) }
func Fatal(err error) { Handle(err, logF) }

func Check[T any](data T, err error) T {
	Handle(err, logP)
	return data
}

func Must[T any](data T, err error) T {
	Handle(err, logF)
	return data
}

// With error type checking

func HandleType[E error](err error, f func(error)) {
	if typedErr, ok := err.(E); ok {
		Handle(typedErr, f)
	}
}

func PanicType[E error](err error) { HandleType[E](err, logP) }
func LogType[E error](err error)   { HandleType[E](err, logF) }

func CheckType[T any, E error](data T, err E) T {
	HandleType[E](err, logP)
	return data
}

func MustType[T any, E error](data T, err error) T {
	HandleType[E](err, logF)
	return data
}
