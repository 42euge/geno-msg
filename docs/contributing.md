# Contributing & Development

## Getting started

```bash
geno-tools install geno-msg
```

For development, clone manually and install in editable mode:

```bash
git clone https://github.com/42euge/geno-msg.git
cd geno-msg
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Project structure

```
geno-msg/
├── pyproject.toml              # Package config, entry point
├── mkdocs.yml                  # Documentation site
├── geno_msg/
│   ├── __init__.py
│   ├── store.py                # File-based message storage (core)
│   ├── cli.py                  # CLI commands (send, inbox, sessions)
│   └── mcp_server.py           # MCP server (JSON-RPC over stdio)
├── tests/
│   └── __init__.py
└── docs/                       # This website
```

## Architecture

```
store.py          ← core: read/write message files
  ↑         ↑
cli.py    mcp_server.py
  ↑
hook (just cli with --quiet)
```

**`store.py`** is the only module that touches the filesystem. It provides:

- `send_message()` — write a message file
- `read_inbox()` — list messages for a session
- `mark_read()` — update read status
- `clear_inbox()` — delete read messages
- `get_current_session_id()` — auto-detect current session
- `resolve_session()` — partial ID / index resolution

**`cli.py`** dispatches subcommands (`send`, `inbox`, `sessions`) and formats output.

**`mcp_server.py`** wraps the same store functions as MCP tools over JSON-RPC stdio.

## Key design decisions

**Files over databases.** Each message is a separate JSON file. This makes the system inspectable (`ls`, `cat`), debuggable, and impossible to corrupt from concurrent writes.

**Three interfaces, one store.** CLI, MCP, and hooks all use the same `store.py`. No data duplication, no sync issues.

**Auto-detect, but don't require it.** Session detection works by matching cwd to JSONL logs. If it fails, every command accepts an explicit session ID. No magic that blocks the user.

**Quiet mode for hooks.** `--quiet` produces minimal output and auto-marks messages as read. This keeps hook output clean and prevents message repetition.

## Extension ideas

**Message types.** Add a `type` field to messages (e.g., `"info"`, `"request"`, `"error"`) so agents can prioritize.

**Channels.** Group messages by topic rather than just by session. Useful for multi-agent workflows.

**TTL / expiry.** Auto-delete messages older than N hours. Prevents stale inbox buildup.

**Delivery confirmation.** Track whether the recipient actually read the message.

## Reporting issues

Open an issue on [GitHub](https://github.com/42euge/geno-msg/issues). Include:

- Command you ran
- Expected vs actual behavior
- Contents of the relevant message file if applicable

## Pull requests

Good contributions:

- New store backends (e.g., SQLite for high-volume scenarios)
- Message filtering (by sender, age, content)
- Improved session auto-detection
- Bug fixes in edge cases (concurrent reads/writes, missing directories)

Before submitting:

1. Test with real agent sessions
2. Verify all three interfaces (CLI, MCP, hook) still work
3. Keep the diff focused

## Code style

- Type hints on all function signatures
- Keep store.py dependency-free (stdlib only)
- CLI uses click, MCP uses raw JSON-RPC — no heavy frameworks
