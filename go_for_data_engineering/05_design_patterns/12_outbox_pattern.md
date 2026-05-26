# Transactional Outbox Pattern

## Problem
Publishing an event to Kafka and writing to your database in one logical action — without two-phase commit. Naive code that writes the row then publishes can leave them inconsistent if the publish fails after the commit (or vice versa).

## Solution
1. In the same DB transaction that writes the business row, also insert a row into an `outbox` table containing the event payload.
2. A separate **outbox relay** worker polls (or tails CDC of) the outbox table and publishes pending rows to Kafka, marking them sent.
3. Consumers receive **at-least-once** delivery (must be idempotent) but no more lost or duplicated writes vs the DB state.

## Sketch (Go pseudocode)
```go
tx, _ := db.BeginTx(ctx, nil)
_, err := tx.Exec("INSERT INTO orders ...")
_, err = tx.Exec("INSERT INTO outbox(topic, payload) VALUES($1, $2)", "orders", payload)
err = tx.Commit()

// Separate worker:
for {
    rows := db.Query("SELECT id, topic, payload FROM outbox WHERE sent_at IS NULL LIMIT 100 FOR UPDATE SKIP LOCKED")
    for r := range rows {
        kafka.Publish(r.topic, r.payload)
        db.Exec("UPDATE outbox SET sent_at = now() WHERE id = $1", r.id)
    }
}
```

## When to use
Any time you need consistency between a DB write and an event publish — order placed, user registered, payment captured, etc. Standard pattern in event-driven microservices.

## Variants
- **CDC-based**: Debezium tails Postgres WAL → Kafka directly (no polling), the most scalable.
- **Inbox pattern** on the consumer side: dedupe by event ID stored in DB.
