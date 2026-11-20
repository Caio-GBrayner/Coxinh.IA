# Persistence migration context

## Current MVP decision

The workflow uses LangGraph's in-memory checkpointer and an in-process service. Checkpoints, idempotency records, and per-thread locks exist only for the lifetime of the `InMemoryWorkflow` instance and process. They are suitable for a single-process MVP, tests, and local experimentation, but are not durable storage.

The Impasse interaction has three actions:

- `save` applies supplied ingredients or guidance, increments `state_version`, and leaves the graph interrupted at the Impasse.
- `resume` applies the supplied changes, increments `state_version`, resets only `revision_count`, and continues through Chef and then SubChef.
- `cancel` increments `state_version` and terminates with status `cancelled`.

The caller supplies the same stable `thread_id` and a decision's `expected_state_version` and `idempotency_key`. In-process locks serialize updates for a thread; stale versions are rejected, and repeated keys with the same payload return the original result.

## Limitations accepted for the MVP

- Process or application restart loses graph checkpoints, workflow state, locks, and idempotency records.
- Multiple workers or replicas do not share checkpoints or locks; version checks are not coordinated across processes.
- The in-memory implementation does not provide durable audit history or recovery after a partial external failure.
- The `state_version` and idempotency guarantees apply only to Impasse decisions routed through `InMemoryWorkflow`.

## Work required before production or multi-process deployment

1. Select and configure a durable database and LangGraph checkpointer, such as a PostgreSQL-backed checkpointer.
2. Keep the stable `thread_id` as the checkpoint identity and provide migrations, connection lifecycle management, and operational backup/retention policies.
3. Persist canonical workflow state updates and idempotency records with the checkpoint strategy. Do not rely on process-local locks.
4. Implement atomic compare-and-update for `expected_state_version`: verify the stored version, apply the decision, increment the version, and record its idempotency key in one transaction.
5. Add a unique constraint on the idempotency scope and key. Reusing a key with a different normalized payload must return an explicit error; retrying the same payload must return the original outcome.
6. Define how a database commit and LangGraph checkpoint update stay consistent, including recovery if one succeeds and the other fails.
7. Test restart recovery, concurrent updates from separate processes, stale-version conflicts, idempotent retries after restart, and recovery from interrupted or partially failed graph runs.
8. Add state-schema migrations and preserve `recipe_version`, `revision_count`, `total_attempts`, and `state_version` semantics during upgrades.

The durable implementation must preserve the current interaction contract: saving leaves the graph paused, resuming returns to Chef and SubChef for a fresh review, and cancellation ends the workflow without approving the recipe.
