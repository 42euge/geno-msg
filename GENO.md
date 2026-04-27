# geno-msg — Inter-Agent Messaging

Inter-agent messaging for the geno ecosystem. Send messages between coding agent sessions using file-based storage, CLI, MCP tools, or automatic hooks.

## Skills

| Skill | Sub-skillset | Slash command |
|-------|-------------|---------------|
| geno-msg | -- | -- (umbrella) |

## Repo structure

```
geno-msg/
├── GENO.md              # agent instructions (this file)
├── SKILL.md             # umbrella skill manifest (symlink)
├── genotools.yaml       # geno-tools manifest
├── pyproject.toml       # Python package config
├── skills/
│   └── geno-msg/        # umbrella skill
│       └── SKILL.md
├── geno_msg/            # Python package
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py           # CLI commands (send, inbox, sessions)
│   ├── store.py         # file-based message storage (core)
│   ├── mcp_server.py    # MCP server (JSON-RPC over stdio)
│   ├── wait.py          # geno-wait entry point
│   └── inbox_watcher.sh # background inbox watcher script
├── docs/                # MkDocs Material site
├── tests/
└── mkdocs.yml
```

## Conventions

- **Single store**: `store.py` is the only module that touches the filesystem. CLI, MCP, and hooks all use it.
- **Message storage**: JSON files at `~/.geno/messages/<recipient-session-id>/`.
- **Session references**: full UUID, partial ID prefix, or numeric index (1 = most recent).
- **Three interfaces**: CLI (`geno-msg`), MCP tools (`send_message`, `read_messages`, `list_sessions`), and hook (`inbox --quiet`).

## Architecture

```
store.py          <- core: read/write message files
  ^         ^
cli.py    mcp_server.py
  ^
hook (just cli with --quiet)
```

**`store.py`** provides: `send_message()`, `read_inbox()`, `mark_read()`, `clear_inbox()`, `get_current_session_id()`, `resolve_session()`.

**`cli.py`** dispatches subcommands (`send`, `inbox`, `sessions`, `join`, `broadcast`) and formats output. Uses `click`.

**`mcp_server.py`** wraps the same store functions as MCP tools over JSON-RPC stdio.

## Dependencies

- Python 3.10+
- `click>=8.0` (CLI framework)
- No other runtime dependencies. `store.py` is stdlib-only.
