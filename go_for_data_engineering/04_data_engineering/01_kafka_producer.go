// Kafka producer using segmentio/kafka-go (pure Go, no librdkafka dependency).
// go get github.com/segmentio/kafka-go
// Run a local Kafka broker first.
package main

import (
	"context"
	"fmt"
	"time"

	"github.com/segmentio/kafka-go"
)

func main() {
	writer := &kafka.Writer{
		Addr:         kafka.TCP("localhost:9092"),
		Topic:        "orders",
		Balancer:     &kafka.Hash{}, // partition by key
		RequiredAcks: kafka.RequireAll,
		Async:        false,
		BatchSize:    100,
		BatchTimeout: 10 * time.Millisecond,
	}
	defer writer.Close()

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	for i := 1; i <= 5; i++ {
		err := writer.WriteMessages(ctx, kafka.Message{
			Key:   []byte(fmt.Sprintf("customer-%d", i%2)),
			Value: []byte(fmt.Sprintf(`{"order_id":%d,"amount":%d}`, i, i*100)),
			Headers: []kafka.Header{
				{Key: "source", Value: []byte("go-service")},
			},
		})
		if err != nil {
			fmt.Println("write error:", err)
			return
		}
		fmt.Println("sent order", i)
	}
}
