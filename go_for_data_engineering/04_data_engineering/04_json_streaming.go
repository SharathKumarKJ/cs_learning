// Stream-decode a large JSON array without loading it all into memory.
// Pattern for ingesting big JSONL or array files.
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

type Event struct {
	ID     int     `json:"id"`
	Type   string  `json:"type"`
	Amount float64 `json:"amount"`
}

func main() {
	input := `[{"id":1,"type":"click","amount":0},{"id":2,"type":"buy","amount":99.5}]`
	dec := json.NewDecoder(strings.NewReader(input))

	// Consume opening bracket.
	if _, err := dec.Token(); err != nil {
		panic(err)
	}

	for dec.More() {
		var e Event
		if err := dec.Decode(&e); err != nil {
			panic(err)
		}
		fmt.Printf("event: %+v\n", e)
	}
}
