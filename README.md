# geno-msg

Inter-agent messaging for the geno ecosystem. Send messages between Claude Code sessions using file-based storage, CLI, MCP tools, or automatic hooks.

## Install

```bash
git clone https://github.com/42euge/geno-msg.git
cd geno-msg
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
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

Add to `~/.claude/.mcp.json`:

```json
{
  "mcpServers": {
    "geno-msg": {
      "command": "/path/to/geno-msg/.venv/bin/python",
      "args": ["-m", "geno_msg.mcp_server"]
    }
  }
}
```

This gives every Claude Code session three tools: `send_message`, `read_messages`, `list_sessions`.

### Hook (auto-check inbox)

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "/path/to/geno-msg/.venv/bin/geno-msg inbox --quiet",
        "timeout": 3000
      }
    ]
  }
}
```

This checks for unread messages at the start of each turn. If there are messages, they appear in the conversation context automatically.

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

Transparent and traceable — `ls ~/.geno/messages/` to see everything.

## Part of the geno ecosystem

| Project | Role |
|---|---|
| [geno](https://github.com/42euge/geno) | Agent orchestrator |
| [geno-tools](https://github.com/42euge/geno-tools) | Skills package |
| [geno-mon](https://github.com/42euge/geno-mon) | Agent observability |
| **geno-msg** | Inter-agent messaging |
