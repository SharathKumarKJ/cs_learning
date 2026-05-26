// Observer: publish/subscribe using channels — Go-idiomatic.
package main

import (
	"fmt"
	"sync"
)

type Event struct{ Topic, Body string }

type Bus struct {
	mu   sync.RWMutex
	subs map[string][]chan Event
}

func NewBus() *Bus { return &Bus{subs: map[string][]chan Event{}} }

func (b *Bus) Subscribe(topic string) <-chan Event {
	ch := make(chan Event, 16)
	b.mu.Lock()
	b.subs[topic] = append(b.subs[topic], ch)
	b.mu.Unlock()
	return ch
}

func (b *Bus) Publish(e Event) {
	b.mu.RLock()
	defer b.mu.RUnlock()
	for _, ch := range b.subs[e.Topic] {
		select {
		case ch <- e:
		default: /* drop on slow consumer */
		}
	}
}

func main() {
	bus := NewBus()
	ch := bus.Subscribe("orders")
	go func() {
		for ev := range ch {
			fmt.Println("got:", ev)
		}
	}()
	bus.Publish(Event{Topic: "orders", Body: "order-1"})
	bus.Publish(Event{Topic: "orders", Body: "order-2"})
}
