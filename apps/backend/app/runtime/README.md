# Legacy Runtime

This folder contains an old project runner used by the existing `/runtime`
endpoints. It can install dependencies and start local frontend processes.

Do not use this as the foundation for Stage 3 agent runtime. A new runtime layer
should define explicit capabilities, execution permissions, process lifecycle,
and logging before invoking external commands.
