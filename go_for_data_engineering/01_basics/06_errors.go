// Idiomatic Go error handling: sentinel errors, wrapped errors, custom errors.
package main

import (
	"errors"
	"fmt"
)

// Sentinel error: compare with errors.Is.
var ErrNotFound = errors.New("not found")

// Custom error type: carry context.
type ValidationError struct {
	Field   string
	Message string
}

func (v *ValidationError) Error() string {
	return fmt.Sprintf("validation failed on %s: %s", v.Field, v.Message)
}

func lookup(id int) (string, error) {
	if id <= 0 {
		return "", &ValidationError{Field: "id", Message: "must be positive"}
	}
	if id == 42 {
		return "Asha", nil
	}
	// Wrap to preserve cause chain.
	return "", fmt.Errorf("lookup id=%d: %w", id, ErrNotFound)
}

func main() {
	for _, id := range []int{0, 7, 42} {
		name, err := lookup(id)
		switch {
		case err == nil:
			fmt.Println("found:", name)
		case errors.Is(err, ErrNotFound):
			fmt.Println("missing:", err)
		default:
			var ve *ValidationError
			if errors.As(err, &ve) {
				fmt.Println("bad input on field:", ve.Field)
			} else {
				fmt.Println("error:", err)
			}
		}
	}
}
