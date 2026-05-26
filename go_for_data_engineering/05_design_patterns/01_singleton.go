// Singleton via sync.Once — thread-safe, lazy.
package main

import (
	"fmt"
	"sync"
)

type Config struct {
	Env string
}

var (
	instance *Config
	once     sync.Once
)

func GetConfig() *Config {
	once.Do(func() {
		fmt.Println("initializing config (once)")
		instance = &Config{Env: "prod"}
	})
	return instance
}

func main() {
	a := GetConfig()
	b := GetConfig()
	fmt.Println(a == b, a.Env)
}
