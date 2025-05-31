package err

import (
	"errors"
	"fmt"
	"testing"
)

// A note on testing Fatal and Must functions:
// (Courtesy of your AI Overlords)
// These functions call log.Fatalln which exits the program, making them
// difficult to test in unit tests. In production code, you might want to:
// 1. Use dependency injection to make the logger configurable
// 2. Use these functions only in main() or initialization code
// 3. Use Panic/Check variants in testable code

// Custom error types for testing
type CustomError struct {
	msg string
}

func (e CustomError) Error() string {
	return e.msg
}

type AnotherError struct {
	code int
}

func (e AnotherError) Error() string {
	return fmt.Sprintf("error code: %d", e.code)
}

// Test basic Handle function
func TestHandle(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		called := false
		Handle(nil, func(error) {
			called = true
		})
		if called {
			t.Error("handler should not be called for nil error")
		}
	})

	t.Run("with non-nil error", func(t *testing.T) {
		called := false
		err := errors.New("test error")
		Handle(err, func(e error) {
			called = true
			if e != err {
				t.Errorf("expected error %v, got %v", err, e)
			}
		})
		if !called {
			t.Error("handler should be called for non-nil error")
		}
	})
}

// Test Panic function
func TestPanic(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for nil error")
			}
		}()
		Panic(nil)
	})

	t.Run("with non-nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		Panic(errors.New("test error"))
	})
}

// Test Check function
func TestCheck(t *testing.T) {
	t.Run("with nil error", func(t *testing.T) {
		result := Check("test data", nil)
		if result != "test data" {
			t.Errorf("expected 'test data', got %v", result)
		}
	})

	t.Run("with non-nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		Check("test data", errors.New("test error"))
	})

	t.Run("with different types", func(t *testing.T) {
		// Test with int
		intResult := Check(42, nil)
		if intResult != 42 {
			t.Errorf("expected 42, got %v", intResult)
		}

		// Test with struct
		type TestStruct struct {
			Value string
		}
		structResult := Check(TestStruct{Value: "test"}, nil)
		if structResult.Value != "test" {
			t.Errorf("expected 'test', got %v", structResult.Value)
		}
	})
}

// Test HandleType function
func TestHandleType(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		called := false
		err := CustomError{msg: "custom error"}
		HandleType[CustomError](err, func(e error) {
			called = true
			if _, ok := e.(CustomError); !ok {
				t.Error("expected CustomError type")
			}
		})
		if !called {
			t.Error("handler should be called for matching error type")
		}
	})

	t.Run("with non-matching error type", func(t *testing.T) {
		called := false
		err := errors.New("standard error")
		HandleType[CustomError](err, func(e error) {
			called = true
		})
		if called {
			t.Error("handler should not be called for non-matching error type")
		}
	})

	t.Run("with nil error", func(t *testing.T) {
		called := false
		HandleType[CustomError](nil, func(e error) {
			called = true
		})
		if called {
			t.Error("handler should not be called for nil error")
		}
	})
}

// Test PanicType function
func TestPanicType(t *testing.T) {
	t.Run("with matching error type", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for matching error type")
			}
		}()
		PanicType[CustomError](CustomError{msg: "custom error"})
	})

	t.Run("with non-matching error type", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for non-matching error type")
			}
		}()
		PanicType[CustomError](errors.New("standard error"))
	})

	t.Run("with nil error", func(t *testing.T) {
		defer func() {
			if r := recover(); r != nil {
				t.Error("should not panic for nil error")
			}
		}()
		PanicType[CustomError](nil)
	})
}

// Test FatalType function (similar to PanicType but uses Fatal)
func TestFatalType(t *testing.T) {
	// Note: We can't easily test FatalType because it calls log.Fatalln
	// which exits the program
	t.Skip("FatalType calls log.Fatalln which exits the program")
}

// Test CheckType function
func TestCheckType(t *testing.T) {
	t.Run("with zero-valued error", func(t *testing.T) {
		// Note: var err CustomError creates a zero-valued struct, not nil
		// This will still trigger the handler because it's not nil
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for zero-valued error")
			}
		}()
		var err CustomError
		CheckType("test data", err)
	})

	t.Run("with non-zero error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic for non-nil error")
			}
		}()
		err := CustomError{msg: "custom error"}
		CheckType("test data", err)
	})
}

// Test MustType function (similar to CheckType but uses Fatal)
func TestMustType(t *testing.T) {
	// Note: We can't easily test MustType because it calls log.Fatalln
	// which exits the program. In a real application, you might want to
	// use dependency injection to make this testable.
	t.Skip("MustType calls log.Fatalln which exits the program")
}

// Test practical usage patterns
func TestPracticalUsage(t *testing.T) {
	// Test with functions that return (T, error)
	t.Run("Check with function returning data and error", func(t *testing.T) {
		getValue := func() (string, error) {
			return "success", nil
		}
		result := Check(getValue())
		if result != "success" {
			t.Errorf("expected 'success', got %v", result)
		}
	})

	t.Run("Check with function returning error", func(t *testing.T) {
		defer func() {
			if r := recover(); r == nil {
				t.Error("should panic when function returns error")
			}
		}()
		getValue := func() (string, error) {
			return "", errors.New("failed")
		}
		Check(getValue())
	})

	// Test error type checking in realistic scenarios
	t.Run("HandleType with wrapped errors", func(t *testing.T) {
		// This demonstrates that HandleType only handles exact type matches
		customErr := CustomError{msg: "custom"}
		wrappedErr := fmt.Errorf("wrapped: %w", customErr)

		called := false
		HandleType[CustomError](wrappedErr, func(e error) {
			called = true
		})
		if called {
			t.Error("HandleType should not handle wrapped errors")
		}
	})
}

// Test error type checking with interface types
func TestErrorTypeWithInterfaces(t *testing.T) {
	t.Run("multiple error types", func(t *testing.T) {
		customErr := CustomError{msg: "custom"}
		anotherErr := AnotherError{code: 404}

		// Test HandleType with CustomError
		customCalled := false
		HandleType[CustomError](customErr, func(e error) {
			customCalled = true
		})
		if !customCalled {
			t.Error("HandleType should handle CustomError")
		}

		// Test HandleType with AnotherError
		anotherCalled := false
		HandleType[AnotherError](anotherErr, func(e error) {
			anotherCalled = true
		})
		if !anotherCalled {
			t.Error("HandleType should handle AnotherError")
		}

		// Test HandleType with wrong type
		wrongCalled := false
		HandleType[CustomError](anotherErr, func(e error) {
			wrongCalled = true
		})
		if wrongCalled {
			t.Error("HandleType should not handle wrong error type")
		}
	})
}

// Benchmark tests
func BenchmarkHandle(b *testing.B) {
	err := errors.New("test error")
	for i := 0; i < b.N; i++ {
		Handle(err, func(e error) {})
	}
}

func BenchmarkHandleNil(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Handle(nil, func(e error) {})
	}
}

func BenchmarkCheck(b *testing.B) {
	for i := 0; i < b.N; i++ {
		_ = Check("data", nil)
	}
}

func BenchmarkHandleType(b *testing.B) {
	err := CustomError{msg: "test"}
	for i := 0; i < b.N; i++ {
		HandleType[CustomError](err, func(e error) {})
	}
}

// Example tests
func ExampleHandle() {
	err := errors.New("something went wrong")
	Handle(err, func(e error) {
		fmt.Println("Error handled:", e)
	})
	// Output: Error handled: something went wrong
}

func ExampleCheck() {
	// This example shows how Check returns data when there's no error
	data := Check("success", nil)
	fmt.Println(data)
	// Output: success
}

func ExampleHandleType() {
	// This example shows type-specific error handling
	err := CustomError{msg: "custom problem"}
	HandleType[CustomError](err, func(e error) {
		fmt.Println("Custom error:", e)
	})
	// Output: Custom error: custom problem
}
