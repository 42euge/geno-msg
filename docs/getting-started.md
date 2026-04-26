# Getting Started

## Prerequisites

- Python 3.10+
- A supported coding CLI (Claude Code, Gemini CLI, Codex, or OpenCode)
- [geno-tools](https://github.com/42euge/geno-tools) installed

## Installation

```bash
geno-tools install geno-msg
```

Or from within an agent session:

```
/geno-tools install geno-msg
```

This clones the repo, creates a venv, installs the CLI, registers the MCP server, and configures hooks.

## Send your first message

Find out which sessions are available:

```bash
geno-msg sessions
```

```
  Sessions:

    1. 9a004367  (just now) <-
    2. d2cf72cc  (2h ago)
    3. 38444d75  (5h ago)
```

The `<-` marks your current session. Send a message to another one:

```bash
geno-msg send d2cf72cc "hey, the refactor is done -- pull main and rerun tests"
```

```
Sent to d2cf72cc: hey, the refactor is done -- pull main and rerun tests
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
    hey, the refactor is done -- pull main and rerun tests
```

Messages are marked as read after viewing.

## MCP server

The MCP server is registered automatically by `geno-tools install`. It provides three tools to agent sessions: `send_message`, `read_messages`, and `list_sessions`.

Restart your coding agent after installation to activate the MCP server.

## Hook (auto-check inbox)

The hook is configured automatically by `geno-tools install`. It runs `geno-msg inbox --quiet` at the start of each turn. If there are unread messages, they appear in the conversation context:

```
[msg from 9a004367] the refactor is done -- pull main and rerun tests
```

No polling, no manual checking. The agent sees the message and can act on it.

## Next steps

- [**Concepts**](concepts.md) -- how the storage, routing, and session detection work
- [**Reference**](reference.md) -- full CLI, MCP, and hook documentation
