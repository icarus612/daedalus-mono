# err - Go Error Handling Package

A Go package that simplifies error handling with panic-on-error semantics and type-specific error handling.

## Installation

```bash
go get your-module/err
```

## Quick Start

Transform verbose Go error handling:

```go
// Before
data, err := os.ReadFile("config.txt")
if err != nil {
    log.Panicln(err)
}

val, err := strconv.Atoi("123")
if err != nil {
    log.Fatalln(err)
}
```

Into clean, concise code:

```go
// After
data := err.Check(os.ReadFile("config.txt"))  // panics on error
val := err.Must(strconv.Atoi("123"))          // exits on error
```

## Core Functions

### Basic Error Handling

- **`Check[T](data T, err error) T`** - Returns data if no error, panics otherwise
- **`Must[T](data T, err error) T`** - Returns data if no error, exits program otherwise
- **`Panic(err error)`** - Panics if error is not nil
- **`Fatal(err error)`** - Exits program if error is not nil
- **`Handle(err error, f func(error))`** - Calls function f if error is not nil

### Type-Specific Error Handling

Handle only specific error types:

- **`CheckType[E error, T any](data T, err E) T`** - Like Check, but only for specific error types
- **`MustType[E error, T any](data T, err E) T`** - Like Must, but only for specific error types
- **`PanicType[E error](err error)`** - Panics only if error matches type E
- **`FatalType[E error](err error)`** - Exits only if error matches type E
- **`HandleType[E error](err error, f func(error))`** - Handles only specific error types

## Examples

### Basic Usage

```go
package main

import (
    "os"
    "strconv"
    "your-module/err"
)

func main() {
    // Read file - panic on any error
    data := err.Check(os.ReadFile("config.txt"))
    
    // Parse integer - exit program on any error  
    port := err.Must(strconv.Atoi("8080"))
    
    // Just handle the error if it exists
    err.Fatal(os.Remove("temp.txt"))
}
```

### Type-Specific Error Handling

```go
package main

import (
    "net"
    "os"
    "your-module/err"
)

func main() {
    // Only panic on os.PathError, ignore other errors
    err.PanicType[*os.PathError](someError)
    
    // Only exit on network errors
    err.FatalType[*net.OpError](networkError)
    
    // Handle only specific error types with custom function
    err.HandleType[*os.PathError](someError, func(e error) {
        log.Printf("Path error: %v", e)
    })
}
```

### Using Error Structs

```go
package main

import "your-module/err"

func processFile() {
    e := &err.Error{Message: "Failed to process file"}
    
    // Set error and check if it occurred
    if e.Set(os.ReadFile("missing.txt")) {
        e.Panic() // Will panic with the file error
    }
    
    // Use with type checking
    te := &err.TypeError[*os.PathError]{
        Error: err.Error{Message: "Path operation failed"},
    }
    
    te.Set(somePathError)
    te.Panic() // Only panics if error is *os.PathError
}
```

### Custom Error Handlers

```go
package main

import (
    "fmt"
    "your-module/err"
)

func main() {
    // Create custom handler
    handler := &err.Handler[func(error)]{
        Error: err.Error{Err: someError},
        handle: func(e error) {
            fmt.Printf("Custom handling: %v\n", e)
        },
    }
    
    handler.Handle() // Calls custom handler if error exists
}
```

## Error Struct Fields

### Error
- **`Message string`** - Custom error message
- **`Err error`** - The actual error
- **`ErrInMsg bool`** - Whether to include error in message

### TypeError[E error]
- Embeds `Error`
- **`Type E`** - Stores the specific error type

## When to Use

**Use `Check`** when:
- Errors are truly exceptional
- You want to fail fast
- The error can be recovered with `recover()`

**Use `Must`** when:
- Errors are unrecoverable
- You want the program to exit cleanly
- Initialization code that must succeed

**Use Type-specific functions** when:
- You only care about certain error types
- Different error types need different handling
- You want to ignore expected errors but catch unexpected ones

## Panic vs Fatal

- **Panic** - Can be recovered with `recover()`, prints stack trace
- **Fatal** - Immediately exits program with `os.Exit(1)`, cannot be recovered

## Requirements

- Go 1.18+ (uses generics)

## License

MIT