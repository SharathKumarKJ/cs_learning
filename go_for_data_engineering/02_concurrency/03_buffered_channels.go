// Buffered channels decouple sender and receiver up to the buffer size.
package main

import "fmt"

func main() {
	ch := make(chan string, 3)
	ch <- "a"
	ch <- "b"
	ch <- "c"
	// ch <- "d" // would block: buffer is full.
	close(ch)
	for v := range ch {
		fmt.Println(v)
	}
}
