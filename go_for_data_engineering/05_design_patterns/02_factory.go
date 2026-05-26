// Factory: return an interface based on type parameter.
package main

import "fmt"

type Notifier interface {
	Send(msg string) error
}

type emailN struct{}

func (emailN) Send(msg string) error { fmt.Println("email:", msg); return nil }

type smsN struct{}

func (smsN) Send(msg string) error { fmt.Println("sms:", msg); return nil }

func NewNotifier(kind string) (Notifier, error) {
	switch kind {
	case "email":
		return emailN{}, nil
	case "sms":
		return smsN{}, nil
	default:
		return nil, fmt.Errorf("unknown notifier %q", kind)
	}
}

func main() {
	n, _ := NewNotifier("email")
	_ = n.Send("hello")
}
