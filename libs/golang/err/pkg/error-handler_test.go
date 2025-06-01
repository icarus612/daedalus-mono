package err

import (
	"errors"
	"fmt"
	"sync"
	"testing"
)

// Test Handler struct
func TestHandler_Handle(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		called := false
		h := &Handler[func(error)]{
			Error: Error{Message: "test handler"},
			handle: func(err error) {
				called = true
			},
		}
		h.Handle()
		if called {
			t.Error("handler should not be called for nil error")
		}
	})

	t.Run("with non-nil error", func(t *testing.T) {
		called := false
		testErr := errors.New("test error")
		h := &Handler[func(error)]{
			Error: Error{
				Message: "test handler",
				Err:     testErr,
			},
			handle: func(err error) {
				called = true
				if err != testErr {
					t.Errorf("expected error %v, got %v", testErr, err)
				}
			},
		}
		h.Handle()
		if !called {
			t.Error("handler should be called for non-nil error")
		}
	})

	t.Run("with nil handler function", func(t *testing.T) {
		// This should panic when trying to call nil function
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic when handler is nil")
			}
		}()
		h := &Handler[func(error)]{
			Error: Error{
				Message: "test handler",
				Err:     errors.New("test error"),
			},
			handle: nil,
		}
		h.Handle()
	})
}

// Test Handler with different function signatures
func TestHandlerWithDifferentSignatures(t *testing.T) {
	t.Run("handler with capture", func(t *testing.T) {
		var capturedError error
		h := &Handler[func(error)]{
			Error: Error{
				Message: "capture test",
				Err:     errors.New("capture me"),
			},
			handle: func(err error) {
				capturedError = err
			},
		}
		h.Handle()
		if capturedError == nil || capturedError.Error() != "capture me" {
			t.Error("error should be captured")
		}
	})

	t.Run("handler with side effects", func(t *testing.T) {
		counter := 0
		h := &Handler[func(error)]{
			Error: Error{
				Message: "side effect test",
				Err:     errors.New("test"),
			},
			handle: func(err error) {
				counter++
			},
		}
		h.Handle()
		if counter != 1 {
			t.Errorf("expected counter to be 1, got %d", counter)
		}
	})
}

// Test TypeHandler struct
func TestTypeHandler_Handle(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		called := false
		customErr := CustomError{msg: "custom error"}
		th := &TypeHandler[func(error), CustomError]{
			Handler: Handler[func(error)]{
				Error: Error{
					Message: "type handler",
					Err:     customErr,
				},
				handle: func(err error) {
					called = true
					if _, ok := err.(CustomError); !ok {
						t.Error("expected CustomError type")
					}
				},
			},
			Type: customErr,
		}
		th.Handle()
		if !called {
			t.Error("handler should be called for matching error")
		}
	})

	t.Run("with non-matching error type", func(t *testing.T) {
		// Note: TypeHandler.Handle() doesn't use HandleType,
		// so it will still call the handler even for non-matching types
		called := false
		th := &TypeHandler[func(error), CustomError]{
			Handler: Handler[func(error)]{
				Error: Error{
					Message: "type handler",
					Err:     errors.New("standard error"),
				},
				handle: func(err error) {
					called = true
				},
			},
		}
		th.Handle()
		if !called {
			t.Error("handler should be called (TypeHandler.Handle uses Handle, not HandleType)")
		}
	})

	t.Run("with nil error", func(t *testing.T) {
		called := false
		th := &TypeHandler[func(error), CustomError]{
			Handler: Handler[func(error)]{
				Error: Error{Message: "type handler"},
				handle: func(err error) {
					called = true
				},
			},
		}
		th.Handle()
		if called {
			t.Error("handler should not be called for nil error")
		}
	})
}

// Test practical usage patterns
func TestHandlerPracticalUsage(t *testing.T) {
	t.Run("reusable error handler", func(t *testing.T) {
		loggedErrors := []string{}
		logger := func(err error) {
			loggedErrors = append(loggedErrors, err.Error())
		}

		// Create reusable handler
		h1 := &Handler[func(error)]{
			Error: Error{
				Message: "operation 1",
				Err:     errors.New("error 1"),
			},
			handle: logger,
		}
		h1.Handle()

		h2 := &Handler[func(error)]{
			Error: Error{
				Message: "operation 2",
				Err:     errors.New("error 2"),
			},
			handle: logger,
		}
		h2.Handle()

		if len(loggedErrors) != 2 {
			t.Errorf("expected 2 logged errors, got %d", len(loggedErrors))
		}
		if loggedErrors[0] != "error 1" || loggedErrors[1] != "error 2" {
			t.Error("errors not logged correctly")
		}
	})

	t.Run("handler with closure", func(t *testing.T) {
		prefix := "ERROR: "
		h := &Handler[func(error)]{
			Error: Error{
				Message: "closure test",
				Err:     errors.New("test error"),
			},
			handle: func(err error) {
				formatted := prefix + err.Error()
				if formatted != "ERROR: test error" {
					t.Errorf("unexpected formatted error: %s", formatted)
				}
			},
		}
		h.Handle()
	})

	t.Run("concurrent handler usage", func(t *testing.T) {
		var mu sync.Mutex
		errors := []string{}

		handler := func(err error) {
			mu.Lock()
			errors = append(errors, err.Error())
			mu.Unlock()
		}

		var wg sync.WaitGroup
		for i := 0; i < 5; i++ {
			wg.Add(1)
			go func(id int) {
				defer wg.Done()
				h := &Handler[func(error)]{
					Error: Error{
						Message: fmt.Sprintf("concurrent %d", id),
						Err:     fmt.Errorf("error %d", id),
					},
					handle: handler,
				}
				h.Handle()
			}(i)
		}
		wg.Wait()

		if len(errors) != 5 {
			t.Errorf("expected 5 errors, got %d", len(errors))
		}
	})
}

// Test TypeHandler with different error types
func TestTypeHandlerWithMultipleTypes(t *testing.T) {
	t.Run("TypeHandler with AnotherError", func(t *testing.T) {
		handled := false
		anotherErr := AnotherError{code: 404}
		th := &TypeHandler[func(error), AnotherError]{
			Handler: Handler[func(error)]{
				Error: Error{
					Message: "not found",
					Err:     anotherErr,
				},
				handle: func(err error) {
					handled = true
					if ae, ok := err.(AnotherError); ok {
						if ae.code != 404 {
							t.Errorf("expected code 404, got %d", ae.code)
						}
					} else {
						t.Error("expected AnotherError type")
					}
				},
			},
			Type: anotherErr,
		}
		th.Handle()
		if !handled {
			t.Error("error should be handled")
		}
	})
}

// Test edge cases
func TestHandlerEdgeCases(t *testing.T) {
	t.Run("handler modification after creation", func(t *testing.T) {
		callCount := 0
		h := &Handler[func(error)]{
			Error: Error{
				Message: "mutable",
				Err:     errors.New("test"),
			},
			handle: func(err error) {
				callCount++
			},
		}

		h.Handle()
		if callCount != 1 {
			t.Errorf("expected call count 1, got %d", callCount)
		}

		// Change handler function
		h.handle = func(err error) {
			callCount += 2
		}
		h.Handle()
		if callCount != 3 {
			t.Errorf("expected call count 3, got %d", callCount)
		}
	})

	t.Run("error modification between calls", func(t *testing.T) {
		var lastError error
		h := &Handler[func(error)]{
			Error: Error{
				Message: "changing errors",
			},
			handle: func(err error) {
				lastError = err
			},
		}

		// First call with nil error
		h.Handle()
		if lastError != nil {
			t.Error("expected nil error")
		}

		// Set error and call again
		h.Err = errors.New("new error")
		h.Handle()
		if lastError == nil || lastError.Error() != "new error" {
			t.Error("expected 'new error'")
		}
	})
}

// Benchmark tests
func BenchmarkHandler_Handle(b *testing.B) {
	h := &Handler[func(error)]{
		Error: Error{
			Message: "benchmark",
			Err:     errors.New("test error"),
		},
		handle: func(err error) {},
	}
	for i := 0; i < b.N; i++ {
		h.Handle()
	}
}

func BenchmarkTypeHandler_Handle(b *testing.B) {
	th := &TypeHandler[func(error), CustomError]{
		Handler: Handler[func(error)]{
			Error: Error{
				Message: "benchmark",
				Err:     CustomError{msg: "test"},
			},
			handle: func(err error) {},
		},
	}
	for i := 0; i < b.N; i++ {
		th.Handle()
	}
}

// Example tests
func ExampleHandler() {
	// Create a handler with a logging function
	h := &Handler[func(error)]{
		Error: Error{
			Message: "database operation failed",
			Err:     errors.New("connection timeout"),
		},
		handle: func(err error) {
			fmt.Printf("Error occurred: %v\n", err)
		},
	}

	h.Handle()
	// Output: Error occurred: connection timeout
}

func ExampleTypeHandler() {
	// Create a type-specific handler
	customErr := CustomError{msg: "validation failed"}
	th := &TypeHandler[func(error), CustomError]{
		Handler: Handler[func(error)]{
			Error: Error{
				Message: "input validation",
				Err:     customErr,
			},
			handle: func(err error) {
				if ce, ok := err.(CustomError); ok {
					fmt.Printf("Custom error: %s\n", ce.msg)
				}
			},
		},
		Type: customErr,
	}

	th.Handle()
	// Output: Custom error: validation failed
}

func ExampleHandler_reusable() {
	// Example showing reusable error handling logic
	notifier := func(err error) {
		fmt.Printf("Notifying admin about: %v\n", err)
	}

	// Multiple operations using the same handler
	operation1 := &Handler[func(error)]{
		Error:  Error{Err: errors.New("disk full")},
		handle: notifier,
	}

	operation2 := &Handler[func(error)]{
		Error:  Error{Err: errors.New("memory exhausted")},
		handle: notifier,
	}

	operation1.Handle()
	operation2.Handle()
	// Output:
	// Notifying admin about: disk full
	// Notifying admin about: memory exhausted
}
