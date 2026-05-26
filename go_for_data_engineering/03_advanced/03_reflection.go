// Reflection: runtime type inspection (use sparingly — slow and bypasses static safety).
package main

import (
	"fmt"
	"reflect"
)

type User struct {
	ID   int    `json:"id" db:"user_id"`
	Name string `json:"name" db:"name"`
}

func PrintTags(v any) {
	t := reflect.TypeOf(v)
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		fmt.Printf("%s: json=%q db=%q\n", f.Name, f.Tag.Get("json"), f.Tag.Get("db"))
	}
}

func main() {
	PrintTags(User{})
}
