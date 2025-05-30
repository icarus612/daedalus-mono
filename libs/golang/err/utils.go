package err

import (
	"fmt"
	"log"
	"os"
)

func logF(e error) { log.Fatalln(e) }
func printF(e error) {
	fmt.Println(e)
	os.Exit(1)
}

func Handle(err error, f func(error)) {
	if err != nil {
		f(err)
	}
}

func Print(err error) { Handle(err, printF) }
func Log(err error)   { Handle(err, logF) }

func HandleType[T error](err error, f func(error)) {
	if typedErr, ok := err.(T); ok {
		Handle(typedErr, f)
	}
}

func PrintType[T error](err error) { HandleType[T](err, printF) }
func LogType[T error](err error)   { HandleType[T](err, logF) }
