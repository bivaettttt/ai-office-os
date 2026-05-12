# Legacy Agents

These modules are pre-runtime experiments kept for compatibility with the current
HTTP endpoints in `app.main`.

They are not the Stage 3 agent runtime foundation and should not be extended for
new orchestration work. New agent runtime code should live in a dedicated runtime
layer with explicit capabilities, permissions, and lifecycle boundaries.

Some modules call local model providers or tools. Treat them as legacy adapters
until they are either replaced or wrapped with explicit permissions.
