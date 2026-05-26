// Chain of responsibility: middleware pattern, common in HTTP servers.
package main

import (
	"fmt"
)

type Middleware func(next func(string)) func(string)

func chain(mws ...Middleware) Middleware {
	return func(final func(string)) func(string) {
		for i := len(mws) - 1; i >= 0; i-- {
			final = mws[i](final)
		}
		return final
	}
}

func auth(next func(string)) func(string) {
	return func(s string) { fmt.Println("auth ok"); next(s) }
}
func log_(next func(string)) func(string) {
	return func(s string) { fmt.Println("log:", s); next(s) }
}

func main() {
	handler := chain(log_, auth)(func(s string) { fmt.Println("handler:", s) })
	handler("hello")
}
