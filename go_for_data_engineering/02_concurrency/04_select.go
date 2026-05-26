// select picks the first ready channel operation — the core of multiplexing.
package main

import (
	"fmt"
	"time"
)

func main() {
	a := make(chan string)
	b := make(chan string)
	go func() { time.Sleep(100 * time.Millisecond); a <- "from a" }()
	go func() { time.Sleep(50 * time.Millisecond); b <- "from b" }()

	for i := 0; i < 2; i++ {
		select {
		case v := <-a:
			fmt.Println(v)
		case v := <-b:
			fmt.Println(v)
		case <-time.After(500 * time.Millisecond):
			fmt.Println("timeout")
		}
	}
}
