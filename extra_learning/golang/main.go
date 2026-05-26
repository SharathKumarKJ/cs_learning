package main

import (
	"fmt"
	"sync"
	"time"
)

type SafeMap struct {
	mu sync.RWMutex
	m  map[string]int
}

func (sm *SafeMap) Get(k string) int {
	sm.mu.RLock()
	defer sm.mu.Unlock()
	return sm.m[k]
}

func (sm *SafeMap) Set(k string, v int) {
	sm.mu.Lock()
	defer sm.mu.Unlock()
	sm.m[k] = v
}

func main() {
	a := make([]int, 3, 3)
	b := a
	a = append(a, 4)
	fmt.Println(a)
	a[0] = 99
	fmt.Println(b[0])
	fmt.Println(a[0])

	//println("Hello World")
	//
	//var ch chan int
	//var fn func()
	//var err error
	//
	//println(fn)
	//println(ch)
	//println(err)

	type Server struct {
		host    string
		port    int
		debug   bool
		timeout time.Duration
	}

	s := Server{}
	println(s.host, s.port, s.debug, s.timeout)

	//var s []int
	//s = append(s, 1)
	//for i, val := range s {
	//	println(i, val)
	//}

	//var m map[string]int
	//m = make(map[string]int)
	//m["a"] = 1
	//for k, v := range m {
	//	println(k, v)
	//}
}
