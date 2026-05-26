package main

import (
	"fmt"
	"sync"
	"time"
)

type RateLimiter struct {
	sem    chan struct{}
	ticker *time.Ticker
}

// NewRateLimiter creates a limiter allowing `rate` requests per `interval`
func NewRateLimiter(rate int, interval time.Duration) *RateLimiter {
	rl := &RateLimiter{
		sem:    make(chan struct{}, rate),
		ticker: time.NewTicker(interval),
	}

	// Refill tokens periodically
	go func() {
		for range rl.ticker.C {
			// Try to refill all slots
			for i := 0; i < rate; i++ {
				select {
				case rl.sem <- struct{}{}:
				default:
					// Slot already full
				}
			}
		}
	}()

	return rl
}

func (rl *RateLimiter) Allow() bool {
	select {
	case <-rl.sem:
		return true // Token available
	default:
		return false // No tokens available
	}
}

func main() {
	// Allow 5 requests per second
	limiter := NewRateLimiter(5, 1*time.Second)
	var wg sync.WaitGroup

	for i := 1; i <= 20; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()

			if limiter.Allow() {
				fmt.Printf("[%s] Request %d: ALLOWED\n", time.Now().Format("15:04:05"), id)
			} else {
				fmt.Printf("[%s] Request %d: REJECTED (rate limit)\n", time.Now().Format("15:04:05"), id)
			}
		}(i)
	}

	wg.Wait()
}
