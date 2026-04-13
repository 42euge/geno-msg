# Reference

## CLI

### `geno-msg send <session> <message>`

Send a message to another session.

```bash
geno-msg send d2cf72cc "pull main and rerun the tests"
geno-msg send 2 "check the latest commit"        # by index
```

The sender is auto-detected from the current working directory. If detection fails, the sender is recorded as `"unknown"`.

### `geno-msg inbox [session-id] [options]`

Check the inbox for the current or specified session.

```bash
geno-msg inbox                    # current session, unread only
geno-msg inbox d2cf72cc           # specific session
geno-msg inbox --all              # include read messages
geno-msg inbox --json             # JSON output
geno-msg inbox --quiet            # minimal output, auto-marks read (for hooks)
geno-msg inbox --mark-read        # mark displayed messages as read
geno-msg inbox --clear            # delete read messages
```

**Output modes:**

| Flag | Behavior |
|---|---|
| (default) | Formatted display with timestamps and sender |
| `--quiet` | One-line per message, marks as read. Designed for hook output. |
| `--json` | JSON array of message objects |

### `geno-msg sessions`

List available Claude Code sessions.

```bash
geno-msg sessions
```

```
  Sessions:

    1. 9a004367  (just now) ←
    2. d2cf72cc  (2h ago)
    3. 38444d75  (5h ago)
```

The `←` marks the auto-detected current session.

## MCP Server

### Setup

Add to `~/.claude/.mcp.json`:

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

Restart Claude Code to pick up the new server.

### Tools

#### `send_message`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `to` | string | yes | Recipient session ID (full, partial, or index) |
| `message` | string | yes | Message text |
| `from_session` | string | no | Sender session ID (auto-detected if omitted) |

Returns:

```json
{
  "status": "sent",
  "to": "d2cf72cc-...",
  "from": "9a004367-...",
  "message_id": "a1b2c3d4e5f6",
  "file": "/Users/you/.geno/messages/d2cf72cc-.../a1b2c3d4e5f6.json"
}
```

#### `read_messages`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `session_id` | string | no | Session to check (auto-detected if omitted) |
| `unread_only` | boolean | no | Only unread messages (default: true) |
| `mark_read` | boolean | no | Mark returned messages as read (default: true) |

Returns:

```json
{
  "session_id": "d2cf72cc-...",
  "count": 1,
  "messages": [
    {
      "id": "a1b2c3d4e5f6",
      "from": "9a004367-...",
      "to": "d2cf72cc-...",
      "timestamp": "2026-04-13T08:00:00+00:00",
      "message": "pull main and rerun the tests",
      "read": false
    }
  ]
}
```

#### `list_sessions`

| Parameter | Type | Required | Description |
|---|---|---|---|
| `limit` | integer | no | Max sessions to return (default: 20) |

Returns:

```json
{
  "current": "9a004367-...",
  "sessions": [
    {"session_id": "9a004367-...", "modified": "2026-04-13T08:00:00+00:00", "is_current": true},
    {"session_id": "d2cf72cc-...", "modified": "2026-04-13T06:00:00+00:00", "is_current": false}
  ]
}
```

## Hook

### Setup

Add to `~/.claude/settings.json`:

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

### Behavior

The hook runs `geno-msg inbox --quiet` at the start of each user turn. If there are unread messages:

1. Each message is printed as `[msg from <sender>] <message>`
2. Messages are marked as read so they don't repeat
3. The output appears in the conversation context, so the agent can see and act on it

If there are no messages, the hook produces no output and adds no overhead.

### Timeout

The 3000ms timeout ensures the hook doesn't block the session if something goes wrong. The inbox check is a local file read and should complete in under 50ms.

## File format

Message files at `~/.geno/messages/<session-id>/<message-id>.json`:

```json
{
  "id": "a1b2c3d4e5f6",
  "from": "9a004367-5e0d-41e1-a461-f567688fc1d0",
  "to": "d2cf72cc-48a9-426c-98fb-6211e71430cf",
  "timestamp": "2026-04-13T08:00:00.000000+00:00",
  "message": "the auth test is fixed, pull and rerun",
  "read": false
}
```

| Field | Type | Description |
|---|---|---|
| `id` | string | 12-char hex identifier |
| `from` | string | Sender session UUID |
| `to` | string | Recipient session UUID |
| `timestamp` | string | ISO 8601 with timezone |
| `message` | string | Message content |
| `read` | boolean | Whether the message has been read |
