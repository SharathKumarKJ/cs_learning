// Postgres example using database/sql + lib/pq driver.
// go get github.com/lib/pq
package main

import (
	"context"
	"database/sql"
	"fmt"
	"log"
	"time"

	_ "github.com/lib/pq"
)

type Order struct {
	ID       int
	Customer string
	Amount   float64
}

func main() {
	db, err := sql.Open("postgres", "postgres://user:pass@localhost:5432/app?sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	db.SetConnMaxIdleTime(5 * time.Minute)

	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	rows, err := db.QueryContext(ctx, `SELECT id, customer, amount FROM orders WHERE amount > $1 LIMIT 10`, 100.0)
	if err != nil {
		log.Fatal(err)
	}
	defer rows.Close()

	for rows.Next() {
		var o Order
		if err := rows.Scan(&o.ID, &o.Customer, &o.Amount); err != nil {
			log.Fatal(err)
		}
		fmt.Printf("%+v\n", o)
	}
	if err := rows.Err(); err != nil {
		log.Fatal(err)
	}
}
