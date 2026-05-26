// sync/atomic for lock-free counters; sync.Pool for object reuse to reduce GC pressure.
package main

import (
	"fmt"
	"sync"
	"sync/atomic"
)

func main() {
	var hits int64
	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			atomic.AddInt64(&hits, 1)
		}()
	}
	wg.Wait()
	fmt.Println("atomic hits:", atomic.LoadInt64(&hits))

	pool := sync.Pool{
		New: func() any { return make([]byte, 0, 4096) },
	}
	buf := pool.Get().([]byte)
	buf = append(buf, "hello"...)
	fmt.Println("buf:", string(buf))
	buf = buf[:0] // reset
	pool.Put(buf) // return to pool
}
