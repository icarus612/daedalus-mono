package err

import (
	"errors"
	"fmt"
	"net"
	"os"
	"testing"
)

// Mock fatal function for testing
var mockFatalCalled bool
var mockFatalError error

func mockFatal(e error) {
	mockFatalCalled = true
	mockFatalError = e
}

// Reset mock state before each test
func resetMock() {
	mockFatalCalled = false
	mockFatalError = nil
}

// Test functions - assuming the original fatal is replaced with mockFatal for testing
var fatal = mockFatal

// Custom error types for testing
type CustomError struct {
	Code    int
	Message string
}

func (ce CustomError) Error() string {
	return fmt.Sprintf("Error %d: %s", ce.Code, ce.Message)
}

type AnotherError struct {
	Reason string
}

func (ae AnotherError) Error() string {
	return fmt.Sprintf("Another error: %s", ae.Reason)
}

func TestHandleFunc(t *testing.T) {
	tests := []struct {
		name        string
		err         error
		expectCall  bool
		expectedErr error
	}{
		{
			name:        "nil error should not call function",
			err:         nil,
			expectCall:  false,
			expectedErr: nil,
		},
		{
			name:        "non-nil error should call function",
			err:         errors.New("test error"),
			expectCall:  true,
			expectedErr: errors.New("test error"),
		},
		{
			name:        "custom error should call function",
			err:         CustomError{Code: 404, Message: "not found"},
			expectCall:  true,
			expectedErr: CustomError{Code: 404, Message: "not found"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var called bool
			var receivedErr error

			HandleFunc(tt.err, func(e error) {
				called = true
				receivedErr = e
			})

			if called != tt.expectCall {
				t.Errorf("Expected function call: %v, got: %v", tt.expectCall, called)
			}

			if tt.expectCall && receivedErr.Error() != tt.expectedErr.Error() {
				t.Errorf("Expected error: %v, got: %v", tt.expectedErr, receivedErr)
			}
		})
	}
}

func TestHandle(t *testing.T) {
	tests := []struct {
		name          string
		err           error
		expectFatal   bool
		expectedError error
	}{
		{
			name:        "nil error should not call fatal",
			err:         nil,
			expectFatal: false,
		},
		{
			name:          "non-nil error should call fatal",
			err:           errors.New("test error"),
			expectFatal:   true,
			expectedError: errors.New("test error"),
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			resetMock()

			Handle(tt.err)

			if mockFatalCalled != tt.expectFatal {
				t.Errorf("Expected fatal called: %v, got: %v", tt.expectFatal, mockFatalCalled)
			}

			if tt.expectFatal && mockFatalError.Error() != tt.expectedError.Error() {
				t.Errorf("Expected fatal error: %v, got: %v", tt.expectedError, mockFatalError)
			}
		})
	}
}

func TestHandleTypeFunc(t *testing.T) {
	tests := []struct {
		name        string
		err         error
		expectCall  bool
		expectedErr error
	}{
		{
			name:       "nil error should not call function",
			err:        nil,
			expectCall: false,
		},
		{
			name:        "matching type should call function",
			err:         &CustomError{Code: 500, Message: "server error"},
			expectCall:  true,
			expectedErr: &CustomError{Code: 500, Message: "server error"},
		},
		{
			name:       "non-matching type should not call function",
			err:        &AnotherError{Reason: "different"},
			expectCall: false,
		},
		{
			name:        "matching PathError should call function",
			err:         &os.PathError{Op: "open", Path: "/test", Err: errors.New("failed")},
			expectCall:  true,
			expectedErr: &os.PathError{Op: "open", Path: "/test", Err: errors.New("failed")},
		},
		{
			name:       "wrong PathError type should not call function",
			err:        &net.OpError{Op: "dial", Net: "tcp", Err: errors.New("refused")},
			expectCall: false,
		},
	}

	t.Run("CustomError type", func(t *testing.T) {
		for _, tt := range tests {
			if tt.name == "matching type should call function" || tt.name == "non-matching type should not call function" || tt.name == "nil error should not call function" {
				t.Run(tt.name, func(t *testing.T) {
					var called bool
					var receivedErr error

					HandleTypeFunc[*CustomError](tt.err, func(e error) {
						called = true
						receivedErr = e
					})

					if called != tt.expectCall {
						t.Errorf("Expected function call: %v, got: %v", tt.expectCall, called)
					}

					if tt.expectCall && receivedErr.Error() != tt.expectedErr.Error() {
						t.Errorf("Expected error: %v, got: %v", tt.expectedErr, receivedErr)
					}
				})
			}
		}
	})

	t.Run("PathError type", func(t *testing.T) {
		for _, tt := range tests {
			if tt.name == "matching PathError should call function" || tt.name == "wrong PathError type should not call function" || tt.name == "nil error should not call function" {
				t.Run(tt.name, func(t *testing.T) {
					var called bool
					var receivedErr error

					HandleTypeFunc[*os.PathError](tt.err, func(e error) {
						called = true
						receivedErr = e
					})

					if called != tt.expectCall {
						t.Errorf("Expected function call: %v, got: %v", tt.expectCall, called)
					}

					if tt.expectCall {
						if pe, ok := receivedErr.(*os.PathError); ok {
							expectedPe := tt.expectedErr.(*os.PathError)
							if pe.Op != expectedPe.Op || pe.Path != expectedPe.Path {
								t.Errorf("Expected PathError: %v, got: %v", expectedPe, pe)
							}
						} else {
							t.Errorf("Expected PathError type, got: %T", receivedErr)
						}
					}
				})
			}
		}
	})
}

func TestHandleType(t *testing.T) {
	tests := []struct {
		name          string
		err           error
		expectFatal   bool
		expectedError error
	}{
		{
			name:        "nil error should not call fatal",
			err:         nil,
			expectFatal: false,
		},
		{
			name:          "matching CustomError should call fatal",
			err:           &CustomError{Code: 404, Message: "not found"},
			expectFatal:   true,
			expectedError: &CustomError{Code: 404, Message: "not found"},
		},
		{
			name:        "non-matching error should not call fatal",
			err:         &AnotherError{Reason: "test"},
			expectFatal: false,
		},
		{
			name:          "matching PathError should call fatal",
			err:           &os.PathError{Op: "read", Path: "/file", Err: errors.New("permission denied")},
			expectFatal:   true,
			expectedError: &os.PathError{Op: "read", Path: "/file", Err: errors.New("permission denied")},
		},
	}

	t.Run("CustomError type", func(t *testing.T) {
		for _, tt := range tests {
			if tt.name != "matching PathError should call fatal" {
				t.Run(tt.name, func(t *testing.T) {
					resetMock()

					HandleType[*CustomError](tt.err)

					if mockFatalCalled != tt.expectFatal {
						t.Errorf("Expected fatal called: %v, got: %v", tt.expectFatal, mockFatalCalled)
					}

					if tt.expectFatal && mockFatalError.Error() != tt.expectedError.Error() {
						t.Errorf("Expected fatal error: %v, got: %v", tt.expectedError, mockFatalError)
					}
				})
			}
		}
	})

	t.Run("PathError type", func(t *testing.T) {
		for _, tt := range tests {
			if tt.name == "matching PathError should call fatal" || tt.name == "nil error should not call fatal" {
				t.Run(tt.name, func(t *testing.T) {
					resetMock()

					HandleType[*os.PathError](tt.err)

					if mockFatalCalled != tt.expectFatal {
						t.Errorf("Expected fatal called: %v, got: %v", tt.expectFatal, mockFatalCalled)
					}

					if tt.expectFatal {
						if pe, ok := mockFatalError.(*os.PathError); ok {
							expectedPe := tt.expectedError.(*os.PathError)
							if pe.Op != expectedPe.Op || pe.Path != expectedPe.Path {
								t.Errorf("Expected PathError: %v, got: %v", expectedPe, pe)
							}
						} else {
							t.Errorf("Expected PathError type, got: %T", mockFatalError)
						}
					}
				})
			}
		}
	})
}

func TestTypedNilErrors(t *testing.T) {
	t.Run("HandleTypeFunc with typed nil", func(t *testing.T) {
		var typedNil *CustomError = nil
		var err error = typedNil

		var called bool
		HandleTypeFunc[*CustomError](err, func(e error) {
			called = true
			if e != nil {
				t.Errorf("Expected nil error, got: %v", e)
			}
		})

		if !called {
			t.Error("Expected function to be called with typed nil")
		}
	})

	t.Run("HandleType with typed nil", func(t *testing.T) {
		resetMock()

		var typedNil *CustomError = nil
		var err error = typedNil

		HandleType[*CustomError](err)

		if !mockFatalCalled {
			t.Error("Expected fatal to be called with typed nil")
		}

		if mockFatalError != nil {
			t.Errorf("Expected nil error in fatal, got: %v", mockFatalError)
		}
	})
}

func TestInterfaceConversion(t *testing.T) {
	t.Run("error interface conversion in HandleTypeFunc", func(t *testing.T) {
		customErr := &CustomError{Code: 500, Message: "server error"}

		HandleTypeFunc[*CustomError](customErr, func(e error) {
			// The error should be convertible back to CustomError
			if ce, ok := e.(*CustomError); ok {
				if ce.Code != 500 || ce.Message != "server error" {
					t.Errorf("Expected CustomError{500, 'server error'}, got: %v", ce)
				}
			} else {
				t.Errorf("Expected CustomError type, got: %T", e)
			}
		})
	})
}

// Benchmark tests
func BenchmarkHandleFunc(b *testing.B) {
	err := errors.New("test error")
	f := func(e error) {}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		HandleFunc(err, f)
	}
}

func BenchmarkHandleTypeFunc(b *testing.B) {
	err := &CustomError{Code: 404, Message: "not found"}
	f := func(e error) {}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		HandleTypeFunc[*CustomError](err, f)
	}
}
