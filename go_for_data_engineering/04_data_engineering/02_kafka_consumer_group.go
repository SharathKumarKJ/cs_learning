// Kafka consumer group using segmentio/kafka-go.
// Multiple instances of this process auto-balance partitions within the same GroupID.
package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/segmentio/kafka-go"
)

func main() {
	reader := kafka.NewReader(kafka.ReaderConfig{
		Brokers:        []string{"localhost:9092"},
		GroupID:        "orders-consumer-group",
		Topic:          "orders",
		MinBytes:       1,
		MaxBytes:       10e6,
		CommitInterval: time.Second,      // periodic auto-commit
		StartOffset:    kafka.LastOffset, // start from latest if no committed offset
	})
	defer reader.Close()

	// Graceful shutdown on SIGINT/SIGTERM.
	ctx, cancel := context.WithCancel(context.Background())
	go func() {
		sig := make(chan os.Signal, 1)
		signal.Notify(sig, syscall.SIGINT, syscall.SIGTERM)
		<-sig
		fmt.Println("shutdown signal received")
		cancel()
	}()

	for {
		m, err := reader.FetchMessage(ctx) // FetchMessage + CommitMessages for manual at-least-once
		if err != nil {
			if ctx.Err() != nil {
				fmt.Println("consumer shutting down")
				return
			}
			fmt.Println("fetch error:", err)
			continue
		}
		fmt.Printf("partition=%d offset=%d key=%s value=%s\n", m.Partition, m.Offset, m.Key, m.Value)

		// Process message (idempotent business logic here).

		if err := reader.CommitMessages(ctx, m); err != nil {
			fmt.Println("commit error:", err)
		}
	}
}
