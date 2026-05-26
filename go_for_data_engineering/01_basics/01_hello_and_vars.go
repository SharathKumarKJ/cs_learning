// Hello world + variable declarations.
// Run: go run 01_hello_and_vars.go
package main

import "fmt"

func main() {
	// Short declaration (inside funcs only).
	name := "Asha"
	// Typed declaration.
	var age int = 30
	// Multiple values.
	x, y := 10, 20
	// Constant.
	const pi = 3.14159

	fmt.Println("hello,", name, "age", age, "sum", x+y, "pi", pi)
}
