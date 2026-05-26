// Fan-out: multiple workers consume from one input channel.
// Fan-in:  merge multiple output channels into one.
package main

import (
	"fmt"
	"sync"
)

func producer(out chan<- int) {
	for i := 1; i <= 10; i++ {
		out <- i
	}
	close(out)
}

func square(in <-chan int, out chan<- int) {
	for v := range in {
		out <- v * v
	}
	close(out)
}

func merge(channels ...<-chan int) <-chan int {
	var wg sync.WaitGroup
	out := make(chan int)
	for _, c := range channels {
		wg.Add(1)
		go func(ch <-chan int) {
			defer wg.Done()
			for v := range ch {
				out <- v
			}
		}(c)
	}
	go func() { wg.Wait(); close(out) }()
	return out
}

func main() {
	in := make(chan int)
	go producer(in)

	// Fan-out: 3 squarers reading the same channel.
	c1 := make(chan int)
	c2 := make(chan int)
	c3 := make(chan int)
	go square(in, c1)
	go square(in, c2)
	go square(in, c3)

	// Fan-in: merge results.
	for v := range merge(c1, c2, c3) {
		fmt.Println(v)
	}
}
