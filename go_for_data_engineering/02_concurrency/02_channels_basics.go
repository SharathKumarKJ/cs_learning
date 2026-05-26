// Channels are the primary way goroutines communicate.
// Unbuffered: send blocks until a receiver is ready.
package main

import "fmt"

func produce(ch chan<- int) {
	for i := 1; i <= 5; i++ {
		ch <- i
	}
	close(ch) // always close from the sender side.
}

func main() {
	ch := make(chan int)
	go produce(ch)
	for v := range ch { // range stops automatically when channel is closed.
		fmt.Println("got:", v)
	}
}
