// Built-in types and their zero values.
package main

import "fmt"

func main() {
	var (
		i int     // 0
		f float64 // 0.0
		s string  // ""
		b bool    // false
		p *int    // nil
	)
	fmt.Printf("int=%d float=%g string=%q bool=%t ptr=%v\n", i, f, s, b, p)
}
