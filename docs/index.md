# geno-msg

Inter-agent messaging for the geno ecosystem. Send messages between coding agent sessions using file-based storage, CLI, MCP tools, or automatic hooks.

## Three layers, one storage

All three interfaces read and write the same JSON files at `~/.geno/messages/`. Pick whichever fits your workflow -- or use all of them.

- **CLI** -- for humans and scripts: `geno-msg send`, `geno-msg inbox`
- **MCP** -- for agents: `send_message`, `read_messages`, `list_sessions` as native tools
- **Hook** -- automatic inbox check at the start of each turn

## Navigation

- [Getting Started](getting-started.md) -- install, first message, hook setup
- [Concepts](concepts.md) -- storage, routing, session detection
- [Reference](reference.md) -- full CLI, MCP, and hook documentation
- [Contributing](contributing.md) -- development setup, architecture, code style
