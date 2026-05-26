// Builder for complex objects with many optional fields.
// In Go, the functional-options pattern is usually preferred over a Builder struct.
package main

import "fmt"

type Query struct {
	Table   string
	Columns []string
	Where   string
	Limit   int
}

type QueryBuilder struct{ q Query }

func New(table string) *QueryBuilder                       { return &QueryBuilder{q: Query{Table: table}} }
func (b *QueryBuilder) Select(c ...string) *QueryBuilder   { b.q.Columns = c; return b }
func (b *QueryBuilder) WhereClause(w string) *QueryBuilder { b.q.Where = w; return b }
func (b *QueryBuilder) Limit(n int) *QueryBuilder          { b.q.Limit = n; return b }
func (b *QueryBuilder) Build() Query                       { return b.q }

func main() {
	q := New("orders").Select("id", "amount").WhereClause("amount > 100").Limit(10).Build()
	fmt.Printf("%+v\n", q)
}
