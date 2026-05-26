// Pointers, copying, and when to use value vs pointer.
package main

import "fmt"

type Counter struct{ n int }

func (c Counter) IncValue()    { c.n++ } // mutates a COPY, no effect outside.
func (c *Counter) IncPointer() { c.n++ } // mutates the original.

func main() {
	c := Counter{}
	c.IncValue()
	c.IncPointer()
	c.IncPointer()
	fmt.Println("final:", c.n) // 2, not 3
}
