// sync.Mutex / RWMutex / Once / WaitGroup — the toolbox for shared state.
package main

import (
	"fmt"
	"sync"
)

type SafeCounter struct {
	mu sync.RWMutex
	n  int
}

func (c *SafeCounter) Inc() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.n++
}

func (c *SafeCounter) Get() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.n
}

var (
	once   sync.Once
	config map[string]string
)

func loadConfig() {
	once.Do(func() {
		fmt.Println("loading config (runs exactly once)")
		config = map[string]string{"env": "prod"}
	})
}

func main() {
	c := &SafeCounter{}
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() { defer wg.Done(); c.Inc() }()
	}
	wg.Wait()
	fmt.Println("final count:", c.Get())

	// Once: idempotent initialization across goroutines.
	for i := 0; i < 3; i++ {
		go loadConfig()
	}
	loadConfig()
}
