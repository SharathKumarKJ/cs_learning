// Decorator: wrap a function/struct to add behavior (logging, caching, metrics, retry).
package main

import (
	"fmt"
	"time"
)

type Handler func(req string) string

func WithLogging(next Handler) Handler {
	return func(req string) string {
		start := time.Now()
		resp := next(req)
		fmt.Printf("req=%s elapsed=%s\n", req, time.Since(start))
		return resp
	}
}

func WithCache(next Handler) Handler {
	cache := map[string]string{}
	return func(req string) string {
		if v, ok := cache[req]; ok {
			return v + " (cached)"
		}
		v := next(req)
		cache[req] = v
		return v
	}
}

func main() {
	base := Handler(func(req string) string { return "hello " + req })
	wrapped := WithLogging(WithCache(base))
	fmt.Println(wrapped("asha"))
	fmt.Println(wrapped("asha"))
}
