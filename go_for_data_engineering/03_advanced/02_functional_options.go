// Functional options: idiomatic pattern for configurable constructors in Go.
package main

import (
	"fmt"
	"time"
)

type ServerConfig struct {
	addr    string
	timeout time.Duration
	tls     bool
}

type Option func(*ServerConfig)

func WithAddr(a string) Option           { return func(c *ServerConfig) { c.addr = a } }
func WithTimeout(d time.Duration) Option { return func(c *ServerConfig) { c.timeout = d } }
func WithTLS() Option                    { return func(c *ServerConfig) { c.tls = true } }

func NewServer(opts ...Option) *ServerConfig {
	cfg := &ServerConfig{addr: ":8080", timeout: 30 * time.Second}
	for _, opt := range opts {
		opt(cfg)
	}
	return cfg
}

func main() {
	s := NewServer(WithAddr(":9090"), WithTimeout(5*time.Second), WithTLS())
	fmt.Printf("%+v\n", s)
}
