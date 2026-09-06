# Compatibility entry point

The canonical operating contract is [AGENTS.md](AGENTS.md). Read and follow it.
The full pre-migration contract is preserved in
[the retired original](docs/archive/agent-runtime/CLAUDE.pre-codex.md).

Codex owns this workspace. A Claude session must not launch queues, regear, or process
landings concurrently with the registered Codex owner. See
[operations and rollback](docs/CODEX_OPERATIONS.md).
