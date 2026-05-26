// Error wrapping (Go 1.13+): preserve cause chain, inspect with errors.Is / errors.As.
package main

import (
	"errors"
	"fmt"
	"os"
)

func readConfig() error {
	_, err := os.Open("/nonexistent/config.yaml")
	if err != nil {
		return fmt.Errorf("read config: %w", err)
	}
	return nil
}

func main() {
	err := readConfig()
	if err != nil {
		fmt.Println("got:", err)
		if errors.Is(err, os.ErrNotExist) {
			fmt.Println("-> file does not exist (matched via errors.Is on wrapped err)")
		}
		var pathErr *os.PathError
		if errors.As(err, &pathErr) {
			fmt.Println("-> path was:", pathErr.Path)
		}
	}
}
