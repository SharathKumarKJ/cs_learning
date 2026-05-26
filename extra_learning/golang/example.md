# Go Concurrency Examples

## 1. Limit API Requests (Don't Hammer Server)

```go
package main

import (
	"fmt"
	"io"
	"net/http"
	"sync"
	"time"
)

func main() {
	sem := make(chan struct{}, 5)  // Max 5 concurrent requests
	var wg sync.WaitGroup

	urls := []string{
		"https://api.example.com/data1",
		"https://api.example.com/data2",
		"https://api.example.com/data3",
		// ... 100 more URLs
	}

	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			
			sem <- struct{}{}        // Acquire slot
			defer func() { <-sem }() // Release slot
			
			fmt.Printf("Fetching: %s\n", u)
			resp, err := http.Get(u)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			defer resp.Body.Close()
			
			body, _ := io.ReadAll(resp.Body)
			fmt.Printf("Got %d bytes from %s\n", len(body), u)
		}(url)
	}

	wg.Wait()
	fmt.Println("All requests completed")
}
```

**Why:** If you spawn 100 goroutines making API calls simultaneously, the server might:
- Rate-limit you (429 Too Many Requests)
- Block your IP
- Crash under load

**With semaphore:** Only 5 requests run at a time, preventing server overload.

---

## 2. Control Database Connections

```go
package main

import (
	"database/sql"
	"fmt"
	"sync"
	"time"
)

type DBPool struct {
	sem chan struct{}
	db  *sql.DB
}

func NewDBPool(maxConnections int, db *sql.DB) *DBPool {
	return &DBPool{
		sem: make(chan struct{}, maxConnections),
		db:  db,
	}
}

func (p *DBPool) Query(query string, args ...interface{}) (*sql.Rows, error) {
	p.sem <- struct{}{}        // Acquire connection slot
	defer func() { <-p.sem }() // Release slot

	fmt.Printf("Executing query: %s\n", query)
	return p.db.Query(query, args...)
}

func main() {
	// Simulate database
	// db, _ := sql.Open("postgres", "...")
	
	pool := NewDBPool(3, nil)  // Max 3 concurrent queries
	var wg sync.WaitGroup

	for i := 1; i <= 10; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			
			query := fmt.Sprintf("SELECT * FROM users WHERE id = %d", id)
			fmt.Printf("Worker %d: requesting query\n", id)
			
			// This will block if 3 queries already running
			_, err := pool.Query(query)
			if err != nil {
				fmt.Printf("Error: %v\n", err)
				return
			}
			
			fmt.Printf("Worker %d: query completed\n", id)
			time.Sleep(500 * time.Millisecond)
		}(i)
	}

	wg.Wait()
	fmt.Println("All queries completed")
}
```

**Why:** Databases have limited connections. If 100 goroutines try to connect simultaneously:
- Connection pool exhausts
- Queries timeout
- Database crashes

**With semaphore:** Only 3 queries run at a time, respecting connection limits.

---

## 3. Rate Limiting

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

type RateLimiter struct {
	sem   chan struct{}
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
		return true  // Token available
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
```

**Output:**
```
[15:04:05] Request 1: ALLOWED
[15:04:05] Request 2: ALLOWED
[15:04:05] Request 3: ALLOWED
[15:04:05] Request 4: ALLOWED
[15:04:05] Request 5: ALLOWED
[15:04:05] Request 6: REJECTED (rate limit)
[15:04:05] Request 7: REJECTED (rate limit)
[15:04:06] Request 8: ALLOWED  (new second, tokens refilled)
[15:04:06] Request 9: ALLOWED
```

**Why:** Prevent abuse by limiting requests per time period:
- API quotas (100 requests/minute)
- User actions (1 login attempt/second)
- Resource consumption (prevent DOS)

---

## Summary Table

| Use Case | Semaphore Size | Purpose |
|----------|---|---|
| API Requests | Fixed (5-10) | Prevent server overload |
| DB Connections | Pool size (10-50) | Respect connection limits |
| Rate Limiting | Rate × interval | Control requests/time |
