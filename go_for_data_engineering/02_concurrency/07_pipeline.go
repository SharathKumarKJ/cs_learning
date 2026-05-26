// Pipeline pattern: each stage is a goroutine reading from a channel and writing to the next.
// Great for streaming ETL: read -> parse -> transform -> sink.
package main

import "fmt"

func generate(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for _, n := range nums {
			out <- n
		}
	}()
	return out
}

func square(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for v := range in {
			out <- v * v
		}
	}()
	return out
}

func addOne(in <-chan int) <-chan int {
	out := make(chan int)
	go func() {
		defer close(out)
		for v := range in {
			out <- v + 1
		}
	}()
	return out
}

func main() {
	for v := range addOne(square(generate(1, 2, 3, 4, 5))) {
		fmt.Println(v)
	}
}
