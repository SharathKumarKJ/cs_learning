// Retry with exponential backoff + jitter, context-aware.
package main

import (
	"context"
	"errors"
	"fmt"
	"math/rand"
	"time"
)

func Retry(ctx context.Context, attempts int, baseDelay time.Duration, fn func() error) error {
	var err error
	for i := 0; i < attempts; i++ {
		err = fn()
		if err == nil {
			return nil
		}
		if ctx.Err() != nil {
			return ctx.Err()
		}
		// Exponential backoff with jitter.
		delay := baseDelay * (1 << i)
		jitter := time.Duration(rand.Int63n(int64(delay / 4)))
		select {
		case <-time.After(delay + jitter):
		case <-ctx.Done():
			return ctx.Err()
		}
	}
	return fmt.Errorf("after %d attempts: %w", attempts, err)
}

func main() {
	ctx := context.Background()
	count := 0
	err := Retry(ctx, 4, 100*time.Millisecond, func() error {
		count++
		if count < 3 {
			return errors.New("transient")
		}
		return nil
	})
	fmt.Println("done after", count, "err:", err)
}
