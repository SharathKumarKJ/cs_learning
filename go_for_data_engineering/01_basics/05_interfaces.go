// Interfaces: implicit satisfaction, polymorphism, the empty interface.
package main

import "fmt"

type Notifier interface {
	Notify(msg string) error
}

type EmailNotifier struct{ Addr string }

func (e EmailNotifier) Notify(msg string) error {
	fmt.Printf("email to %s: %s\n", e.Addr, msg)
	return nil
}

type SlackNotifier struct{ Channel string }

func (s SlackNotifier) Notify(msg string) error {
	fmt.Printf("slack #%s: %s\n", s.Channel, msg)
	return nil
}

func broadcast(notifiers []Notifier, msg string) {
	for _, n := range notifiers {
		_ = n.Notify(msg)
	}
}

func main() {
	notifiers := []Notifier{
		EmailNotifier{Addr: "asha@example.com"},
		SlackNotifier{Channel: "alerts"},
	}
	broadcast(notifiers, "pipeline failed")
}
