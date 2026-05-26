// A struct that owns a channel — encapsulates a concurrent component.
// Pattern used widely for background workers, event buses, queues.
package main

import (
	"fmt"
	"sync"
	"time"
)

type EventBus struct {
	events chan string
	wg     sync.WaitGroup
	quit   chan struct{}
}

func NewEventBus() *EventBus {
	bus := &EventBus{
		events: make(chan string, 100),
		quit:   make(chan struct{}),
	}
	bus.wg.Add(1)
	go bus.loop()
	return bus
}

func (b *EventBus) loop() {
	defer b.wg.Done()
	for {
		select {
		case ev := <-b.events:
			fmt.Println("handled event:", ev)
		case <-b.quit:
			fmt.Println("bus shutting down")
			return
		}
	}
}

func (b *EventBus) Publish(ev string) { b.events <- ev }

func (b *EventBus) Stop() {
	close(b.quit)
	b.wg.Wait()
}

func main() {
	bus := NewEventBus()
	for i := 0; i < 5; i++ {
		bus.Publish(fmt.Sprintf("event-%d", i))
	}
	time.Sleep(50 * time.Millisecond)
	bus.Stop()
}
