package err

import (
	"errors"
	"fmt"
	"testing"
)

// Test Error struct and its methods
func TestError_Set(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		e := &Error{Message: "test message"}
		result := e.Set(nil)
		if result {
			t.Error("Set should return false for nil error")
		}
		if e.Err != nil {
			t.Error("Err field should remain nil")
		}
	})

	t.Run("with non-nil error", func(t *testing.T) {
		e := &Error{Message: "test message"}
		testErr := errors.New("test error")
		result := e.Set(testErr)
		if !result {
			t.Error("Set should return true for non-nil error")
		}
		if e.Err != testErr {
			t.Errorf("expected Err to be %v, got %v", testErr, e.Err)
		}
	})

	t.Run("overwriting existing error", func(t *testing.T) {
		e := &Error{
			Message: "test message",
			Err:     errors.New("old error"),
		}
		newErr := errors.New("new error")
		result := e.Set(newErr)
		if !result {
			t.Error("Set should return true for non-nil error")
		}
		if e.Err != newErr {
			t.Errorf("expected Err to be %v, got %v", newErr, e.Err)
		}
	})
}

func TestError_Panic(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for nil error")
			}
		}()
		e := &Error{Message: "test"}
		e.Panic()
	})

	t.Run("with non-nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		e := &Error{
			Message: "test",
			Err:     errors.New("test error"),
		}
		e.Panic()
	})
}

func TestError_Fatal(t *testing.T) {
	// Note: We can't test Fatal because it calls log.Fatalln
	t.Skip("Fatal calls log.Fatalln which exits the program")
}

func TestError_Handle(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		called := false
		e := &Error{Message: "test"}
		e.Handle(func(error) {
			called = true
		})
		if called {
			t.Error("handler should not be called for nil error")
		}
	})

	t.Run("with non-nil error", func(t *testing.T) {
		called := false
		testErr := errors.New("test error")
		e := &Error{
			Message: "test",
			Err:     testErr,
		}
		e.Handle(func(err error) {
			called = true
			if err != testErr {
				t.Errorf("expected error %v, got %v", testErr, err)
			}
		})
		if !called {
			t.Error("handler should be called for non-nil error")
		}
	})
}

func TestError_Check(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		e := &Error{Message: "test"}
		// Should not panic
		e.Check("test data")
	})

	t.Run("with non-nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		e := &Error{
			Message: "test",
			Err:     errors.New("test error"),
		}
		e.Check("test data")
	})
}

func TestError_Must(t *testing.T) {
	// Note: We can't test Must because it calls log.Fatalln
	t.Skip("Must calls log.Fatalln which exits the program")
}

// Test TypeError struct and its methods
func TestTypeError_Panic(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for matching error type")
			}
		}()
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     CustomError{msg: "custom error"},
			},
		}
		te.Panic()
	})

	t.Run("with non-matching error type", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for non-matching error type")
			}
		}()
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     errors.New("standard error"),
			},
		}
		te.Panic()
	})

	t.Run("with nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for nil error")
			}
		}()
		te := &TypeError[CustomError]{
			Error: Error{Message: "test"},
		}
		te.Panic()
	})
}

func TestTypeError_Fatal(t *testing.T) {
	// Note: We can't test Fatal because it calls log.Fatalln
	t.Skip("Fatal calls log.Fatalln which exits the program")
}

func TestTypeError_Handle(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		called := false
		customErr := CustomError{msg: "custom error"}
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     customErr,
			},
		}
		te.Handle(func(err error) {
			called = true
			if _, ok := err.(CustomError); !ok {
				t.Error("expected CustomError type")
			}
		})
		if !called {
			t.Error("handler should be called for matching error type")
		}
	})

	t.Run("with non-matching error type", func(t *testing.T) {
		called := false
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     errors.New("standard error"),
			},
		}
		te.Handle(func(err error) {
			called = true
		})
		if called {
			t.Error("handler should not be called for non-matching error type")
		}
	})
}

func TestTypeError_Check(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     CustomError{msg: "custom error"},
			},
		}
		te.Check("test data")
	})

	t.Run("with non-matching error type - panic on type assertion", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic on type assertion failure")
			}
		}()
		// This will panic due to failed type assertion te.Err.(E)
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "test",
				Err:     errors.New("standard error"),
			},
		}
		te.Check("test data")
	})

	t.Run("with nil error - panic on type assertion", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic on nil type assertion")
			}
		}()
		// This will panic due to type assertion on nil
		te := &TypeError[CustomError]{
			Error: Error{Message: "test"},
		}
		te.Check("test data")
	})
}

func TestTypeError_Must(t *testing.T) {
	// Note: We can't test Must because it calls log.Fatalln
	t.Skip("Must calls log.Fatalln which exits the program")
}

// Test TypeError with different error types
func TestTypeErrorWithDifferentTypes(t *testing.T) {
	t.Run("TypeError with AnotherError type", func(t *testing.T) {
		anotherErr := AnotherError{code: 500}
		te := &TypeError[AnotherError]{
			Error: Error{
				Message: "server error",
				Err:     anotherErr,
			},
			Type: anotherErr,
		}

		called := false
		te.Handle(func(err error) {
			called = true
			if ae, ok := err.(AnotherError); !ok || ae.code != 500 {
				t.Error("expected AnotherError with code 500")
			}
		})
		if !called {
			t.Error("handler should be called")
		}
	})
}

// Test practical usage patterns
func TestErrorPracticalUsage(t *testing.T) {
	t.Run("error chain with Set and Handle", func(t *testing.T) {
		e := &Error{Message: "operation failed"}

		// Simulate an operation that might fail
		err := simulateOperation(false)
		if e.Set(err) {
			handled := false
			e.Handle(func(err error) {
				handled = true
			})
			if !handled {
				t.Error("error should have been handled")
			}
		}
	})

	t.Run("conditional error handling", func(t *testing.T) {
		e := &Error{Message: "conditional operation"}

		// Only set error if operation fails
		if err := simulateOperation(true); e.Set(err) {
			t.Error("should not have error for successful operation")
		}

		// Error remains unset, so Panic should not panic
		e.Panic()
	})

	t.Run("TypeError for API error handling", func(t *testing.T) {
		// Simulate handling specific error types from an API
		apiErr := CustomError{msg: "API rate limit exceeded"}
		te := &TypeError[CustomError]{
			Error: Error{
				Message: "API call failed",
				Err:     apiErr,
			},
		}

		// Only handle specific error type
		handled := false
		te.Handle(func(err error) {
			if ce, ok := err.(CustomError); ok && ce.msg == "API rate limit exceeded" {
				handled = true
			}
		})
		if !handled {
			t.Error("should handle API rate limit error")
		}
	})
}

// Helper function for testing
func simulateOperation(success bool) error {
	if success {
		return nil
	}
	return errors.New("operation failed")
}

// Benchmark tests
func BenchmarkError_Set(b *testing.B) {
	e := &Error{Message: "benchmark"}
	err := errors.New("test error")
	for i := 0; i < b.N; i++ {
		e.Set(err)
	}
}

func BenchmarkError_Handle(b *testing.B) {
	e := &Error{
		Message: "benchmark",
		Err:     errors.New("test error"),
	}
	for i := 0; i < b.N; i++ {
		e.Handle(func(error) {})
	}
}

func BenchmarkTypeError_Handle(b *testing.B) {
	te := &TypeError[CustomError]{
		Error: Error{
			Message: "benchmark",
			Err:     CustomError{msg: "test"},
		},
	}
	for i := 0; i < b.N; i++ {
		te.Handle(func(error) {})
	}
}

// Example tests
func ExampleError_Set() {
	e := &Error{Message: "database operation"}

	// Simulate a database operation
	err := errors.New("connection timeout")
	if e.Set(err) {
		fmt.Println("Error occurred:", e.Message)
	}
	// Output: Error occurred: database operation
}

func ExampleError_Handle() {
	e := &Error{
		Message: "file operation",
		Err:     errors.New("file not found"),
	}

	e.Handle(func(err error) {
		fmt.Printf("Handling error: %v\n", err)
	})
	// Output: Handling error: file not found
}

func ExampleTypeError_Handle() {
	// Create a TypeError for handling specific error types
	te := &TypeError[CustomError]{
		Error: Error{
			Message: "validation",
			Err:     CustomError{msg: "invalid input"},
		},
	}

	te.Handle(func(err error) {
		if ce, ok := err.(CustomError); ok {
			fmt.Printf("Custom error handled: %v\n", ce.msg)
		}
	})
	// Output: Custom error handled: invalid input
}
