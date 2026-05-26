// Circuit breaker: fail fast when a downstream is unhealthy.
// States: closed (normal) -> open (failures > threshold) -> half-open (probe).
package main

import (
	"errors"
	"fmt"
	"sync"
	"time"
)

type state int

const (
	closed state = iota
	open
	halfOpen
)

type Breaker struct {
	mu          sync.Mutex
	state       state
	failures    int
	threshold   int
	openTimeout time.Duration
	openedAt    time.Time
}

func NewBreaker(threshold int, openTimeout time.Duration) *Breaker {
	return &Breaker{threshold: threshold, openTimeout: openTimeout}
}

var ErrOpen = errors.New("circuit open")

func (b *Breaker) Call(fn func() error) error {
	b.mu.Lock()
	if b.state == open {
		if time.Since(b.openedAt) > b.openTimeout {
			b.state = halfOpen
		} else {
			b.mu.Unlock()
			return ErrOpen
		}
	}
	b.mu.Unlock()

	err := fn()

	b.mu.Lock()
	defer b.mu.Unlock()
	if err != nil {
		b.failures++
		if b.failures >= b.threshold {
			b.state = open
			b.openedAt = time.Now()
		}
		return err
	}
	b.failures = 0
	b.state = closed
	return nil
}

func main() {
	b := NewBreaker(3, time.Second)
	for i := 0; i < 5; i++ {
		err := b.Call(func() error { return errors.New("downstream fail") })
		fmt.Println(i, err)
	}
}
