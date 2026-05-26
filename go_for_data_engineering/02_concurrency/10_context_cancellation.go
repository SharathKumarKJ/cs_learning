// context.Context: the standard way to carry deadlines, cancellation, and request-scoped values.
// Always pass ctx as the first argument; never store it in a struct.
package main

import (
	"context"
	"fmt"
	"time"
)

func slowOp(ctx context.Context, id int) error {
	select {
	case <-time.After(300 * time.Millisecond):
		fmt.Printf("op %d completed\n", id)
		return nil
	case <-ctx.Done():
		return ctx.Err() // context.Canceled or context.DeadlineExceeded
	}
}

func main() {
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	if err := slowOp(ctx, 1); err != nil {
		fmt.Println("op 1 error:", err)
	}

	ctx2, cancel2 := context.WithCancel(context.Background())
	go func() {
		time.Sleep(100 * time.Millisecond)
		cancel2()
	}()
	if err := slowOp(ctx2, 2); err != nil {
		fmt.Println("op 2 error:", err)
	}
}
