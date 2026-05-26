// Structs, value vs pointer receivers, constructors.
package main

import "fmt"

type Order struct {
	ID     int
	Amount float64
	Status string
}

// Value receiver: works on a copy.
func (o Order) Summary() string {
	return fmt.Sprintf("order=%d amt=%.2f status=%s", o.ID, o.Amount, o.Status)
}

// Pointer receiver: mutates the original.
func (o *Order) Cancel() {
	o.Status = "CANCELLED"
}

// Constructor convention: NewXxx returning a pointer.
func NewOrder(id int, amt float64) *Order {
	return &Order{ID: id, Amount: amt, Status: "OPEN"}
}

func main() {
	o := NewOrder(1, 250.0)
	fmt.Println(o.Summary())
	o.Cancel()
	fmt.Println(o.Summary())
}
