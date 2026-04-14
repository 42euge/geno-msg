---
name: geno-msg
description: >-
  Inter-agent messaging — send messages, check inbox, join live chat, list sessions.
  Use when user says /geno-msg, asks to message another session, check inbox, or join live chat.
allowed-tools: "Bash(~/.geno/venv/bin/geno-msg *) Bash(~/.geno/bin/inbox-watcher.sh *)"
argument-hint: "[send|inbox|sessions|join|broadcast] [args...]"
---

# geno-msg — Inter-Agent Messaging

```!
which ~/.geno/venv/bin/geno-msg >/dev/null 2>&1 || echo "⚠️ geno-msg is not installed. Run: bash <repo>/install.sh"
```

You have access to geno-msg MCP tools (`send_message`, `read_messages`, `list_sessions`) and the CLI at `~/.geno/venv/bin/geno-msg`.

## Commands

Parse the user's arguments to determine the action:

### `/geno-msg` (no args) or `/geno-msg inbox`
Check the inbox for unread messages using the `read_messages` MCP tool.

### `/geno-msg send <session> <message>`
Send a message to another session using the `send_message` MCP tool. Session can be a partial ID or numeric index.

### `/geno-msg sessions`
List available sessions with live/dead status. Run:
```bash
~/.geno/venv/bin/geno-msg sessions
```

### `/geno-msg join [session-id]`
Start live message monitoring. The watcher uses a **detect-and-exit** pattern:

1. Run the inbox watcher as a **background Bash command** (`run_in_background: true`):
   ```bash
   ~/.geno/bin/inbox-watcher.sh --force
   ```
2. The watcher polls the inbox **without consuming messages** (peek only).
3. When a message arrives, the watcher **exits** — this triggers a task-completion notification.
4. On notification, react to the message. The PostToolUse hook (`inbox --quiet`) will inject it into the conversation on your next tool use (peek only — the message stays unread).
5. After processing the message, mark it as read:
   ```bash
   ~/.geno/venv/bin/geno-msg inbox --mark-read
   ```
6. **Restart the watcher** by running the same background command again.

Repeat steps 3–6 for each incoming message. Always restart the watcher after handling a message.

If no session-id is given, watch the current session's inbox.

### `/geno-msg broadcast <message>`
Send a message to ALL live sessions. Run:
```bash
~/.geno/venv/bin/geno-msg sessions
```
Then use the `send_message` MCP tool to send to each LIVE session.

## Auto-Join Behavior

On session start, check `~/.geno/geno-msg/settings.json`. If `autoJoin` is `true`, automatically start the background inbox watcher (same as `/geno-msg join`).

## Settings

Settings file: `~/.geno/geno-msg/settings.json`
- `autoJoin` (bool): automatically start inbox watcher on session start
- `watchInterval` (int): seconds between inbox checks (default 5)
- `broadcastOnSend` (bool): when true, `/geno-msg send` without a target broadcasts to all live sessions
