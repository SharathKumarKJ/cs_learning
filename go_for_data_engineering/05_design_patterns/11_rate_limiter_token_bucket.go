// Token-bucket rate limiter — allow N ops/sec with bursts up to capacity.
package main

import (
	"fmt"
	"sync"
	"time"
)

type Limiter struct {
	mu         sync.Mutex
	tokens     float64
	capacity   float64
	ratePerSec float64
	last       time.Time
}

func NewLimiter(ratePerSec, capacity float64) *Limiter {
	return &Limiter{tokens: capacity, capacity: capacity, ratePerSec: ratePerSec, last: time.Now()}
}

func (l *Limiter) Allow() bool {
	l.mu.Lock()
	defer l.mu.Unlock()
	now := time.Now()
	elapsed := now.Sub(l.last).Seconds()
	l.tokens = min(l.capacity, l.tokens+elapsed*l.ratePerSec)
	l.last = now
	if l.tokens >= 1 {
		l.tokens--
		return true
	}
	return false
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

func main() {
	l := NewLimiter(2, 5) // 2/sec, burst 5
	for i := 0; i < 8; i++ {
		fmt.Println(i, l.Allow())
		time.Sleep(100 * time.Millisecond)
	}
}
