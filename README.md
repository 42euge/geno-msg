# geno-msg

Inter-agent messaging for the geno ecosystem. Send messages between coding agent sessions using file-based storage, CLI, MCP tools, or automatic hooks.

## Install

```bash
geno-tools install geno-msg
```

Or from within an agent session:

```
/geno-tools install geno-msg
```

## Usage

### CLI

```bash
# Send a message to another session
geno-msg send <session-id> "check the test results"

# Check your inbox
geno-msg inbox

# List available sessions
geno-msg sessions
```

Session references work like geno-mon: full UUID, partial ID (`d2cf72cc`), or numeric index (`1` = most recent).

### MCP Server

The MCP server gives every agent session three tools: `send_message`, `read_messages`, `list_sessions`. It is configured automatically by `geno-tools install`.

### Hook (auto-check inbox)

A hook checks the inbox at the start of each turn. If there are unread messages, they appear in the conversation context automatically. Hooks are configured by `geno-tools install`.

## How it works

Messages are JSON files stored at `~/.geno/messages/<session-id>/`:

```json
{
  "id": "a1b2c3d4e5f6",
  "from": "9a004367-...",
  "to": "d2cf72cc-...",
  "timestamp": "2026-04-13T08:00:00+00:00",
  "message": "check the test results",
  "read": false
}
```

Transparent and traceable -- `ls ~/.geno/messages/` to see everything.

## Documentation

Full documentation at [42euge.github.io/geno-msg](https://42euge.github.io/geno-msg/).

## Part of the geno ecosystem

| Project | Role |
|---|---|
| [geno](https://github.com/42euge/geno) | Agent orchestrator |
| [geno-tools](https://github.com/42euge/geno-tools) | Skillset manager |
| [geno-mon](https://github.com/42euge/geno-mon) | Agent observability |
| **geno-msg** | Inter-agent messaging |

## License

[MIT](LICENSE)
