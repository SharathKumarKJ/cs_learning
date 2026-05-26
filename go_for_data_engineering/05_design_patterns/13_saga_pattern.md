# Saga Pattern (Distributed Transactions)

## Problem
A business transaction spans multiple services (place order → reserve inventory → charge card → schedule shipment). No single DB transaction can cover them; failures partway through must not leave the system inconsistent.

## Solution
Break the transaction into a sequence of **local transactions**, each emitting an event that triggers the next step. If any step fails, run **compensating transactions** in reverse to undo prior steps.

## Two flavors
- **Choreography**: each service listens to events and decides what to do. Decentralized, no orchestrator, but harder to reason about as the graph grows.
- **Orchestration**: a central saga orchestrator (state machine) calls services in order, handling compensations. Easier to observe and test; introduces a single coordinator.

## Example (orchestration, Go pseudocode)
```go
type Saga struct{ steps []Step }
type Step struct {
    Action       func(ctx context.Context) error
    Compensation func(ctx context.Context) error
}

func (s *Saga) Execute(ctx context.Context) error {
    completed := 0
    for i, step := range s.steps {
        if err := step.Action(ctx); err != nil {
            for j := i - 1; j >= 0; j-- {
                _ = s.steps[j].Compensation(ctx)
            }
            return fmt.Errorf("step %d failed: %w", i, err)
        }
        completed++
    }
    return nil
}
```

## Considerations
- All steps and compensations must be **idempotent** (retries are inevitable).
- Persist saga state durably (DB or workflow engine like Temporal, Cadence, AWS Step Functions).
- Watch for **semantic locks** (e.g. "reserved" status) so concurrent sagas don't conflict.
- Eventual consistency — clients see intermediate states briefly.
