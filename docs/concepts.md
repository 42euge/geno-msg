# Concepts

## File-based storage

Every message is a JSON file at `~/.geno/messages/<recipient-session-id>/`:

```
~/.geno/messages/
└── d2cf72cc-48a9-426c-98fb-6211e71430cf/
    ├── a1b2c3d4e5f6.json
    └── f7e8d9c0b1a2.json
```

Each file:

```json
{
  "id": "a1b2c3d4e5f6",
  "from": "9a004367-5e0d-41e1-a461-f567688fc1d0",
  "to": "d2cf72cc-48a9-426c-98fb-6211e71430cf",
  "timestamp": "2026-04-13T08:00:00+00:00",
  "message": "the auth test is fixed, pull and rerun",
  "read": false
}
```

This design is intentional:

- **Traceable** — `ls ~/.geno/messages/` shows everything. `cat` any file to read it. No databases, no daemons.
- **Debuggable** — if a message isn't arriving, you can inspect the file directly.
- **Atomic** — each message is its own file. No corruption risk from concurrent writes.
- **Cleanable** — `rm` a file to delete a message. `rm -r` a directory to clear an inbox.

## Session identification

Claude Code sessions are identified by UUIDs (e.g., `9a004367-5e0d-41e1-a461-f567688fc1d0`). These correspond to JSONL log files at `~/.claude/projects/<project-slug>/<session-id>.jsonl`.

geno-msg accepts multiple reference formats:

| Format | Example | How it resolves |
|---|---|---|
| Full UUID | `9a004367-5e0d-41e1-...` | Direct match |
| Partial ID | `9a004367` | Prefix match against known sessions |
| Numeric index | `1`, `2`, `3` | Nth most recent session |

## Auto-detection

When you run `geno-msg inbox` without specifying a session, it tries to auto-detect the current session by:

1. Getting the current working directory
2. Scanning `~/.claude/projects/` for the most recently modified JSONL whose `cwd` matches

This works well when you're running geno-msg from the same directory as the Claude Code session. If auto-detection fails, pass the session ID explicitly.

## Message lifecycle

```
send_message()
  → writes JSON file to ~/.geno/messages/<to>/
  → file has "read": false

inbox (or hook checks)
  → reads all *.json in ~/.geno/messages/<session>/
  → displays unread messages
  → marks them "read": true (in quiet/hook mode)

clear
  → deletes read message files
  → removes empty directories
```

Messages persist until explicitly cleared. The `--quiet` flag (used by hooks) automatically marks messages as read after displaying them, so you won't see the same message twice.

## How the three layers interact

```
                    ┌─────────────┐
                    │  ~/.geno/   │
                    │  messages/  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────┴────┐  ┌────┴────┐  ┌────┴────┐
         │   CLI   │  │   MCP   │  │  Hook   │
         │  send   │  │  tools  │  │  auto   │
         │  inbox  │  │  agent  │  │  check  │
         └─────────┘  └─────────┘  └─────────┘
```

All three read and write the same files. You can send a message via CLI and receive it via MCP, or vice versa. The hook is just the CLI's `inbox --quiet` running automatically.

## Security considerations

Messages are stored as plain-text JSON in the user's home directory. They are:

- Readable by any process running as the same user
- Not encrypted
- Not authenticated (any process can write to any session's inbox)

This is appropriate for a single-user development environment. For multi-user or production scenarios, additional access controls would be needed.
