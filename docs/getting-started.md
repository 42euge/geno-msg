# Getting Started

## Installation

```bash
git clone https://github.com/42euge/geno-msg.git
cd geno-msg
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

Requires Python 3.10+. The only runtime dependency is `click`.

## Send your first message

Find out which sessions are available:

```bash
geno-msg sessions
```

```
  Sessions:

    1. 9a004367  (just now) ←
    2. d2cf72cc  (2h ago)
    3. 38444d75  (5h ago)
```

The `←` marks your current session. Send a message to another one:

```bash
geno-msg send d2cf72cc "hey, the refactor is done — pull main and rerun tests"
```

```
Sent to d2cf72cc: hey, the refactor is done — pull main and rerun tests
  File: /Users/you/.geno/messages/d2cf72cc-.../a1b2c3d4e5f6.json
```

## Check your inbox

From the receiving session:

```bash
geno-msg inbox
```

```
  Unread messages for d2cf72cc:

    [2m ago] from 9a004367:
    hey, the refactor is done — pull main and rerun tests
```

Messages are marked as read after viewing.

## Set up the MCP server

Add to `~/.claude/.mcp.json` so every future session gets messaging tools:

```json
{
  "mcpServers": {
    "geno-msg": {
      "command": "/absolute/path/to/geno-msg/.venv/bin/python",
      "args": ["-m", "geno_msg.mcp_server"]
    }
  }
}
```

After restarting Claude Code, agents can use `send_message`, `read_messages`, and `list_sessions` as native tools.

## Set up the hook

Add to `~/.claude/settings.json` so sessions auto-check for messages:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "command": "/absolute/path/to/geno-msg/.venv/bin/geno-msg inbox --quiet",
        "timeout": 3000
      }
    ]
  }
}
```

Now at the start of each turn, any unread messages appear automatically:

```
[msg from 9a004367] the refactor is done — pull main and rerun tests
```

No polling, no manual checking. The agent sees the message and can act on it.

## Next steps

- [**Concepts**](concepts.md) — how the storage, routing, and session detection work
- [**Reference**](reference.md) — full CLI, MCP, and hook documentation
