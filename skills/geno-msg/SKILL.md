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

**Always include a `type` parameter** when sending via MCP. Choose the right type for how the recipient should interpret the message.

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
5. After processing the message, consume it by reading the inbox (plain `inbox` auto-marks as read):
   ```bash
   ~/.geno/venv/bin/geno-msg inbox
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

## Message Types

Every message has a `type` that tells the recipient how to interpret it:

| Type | Color | Meaning | Recipient should... |
|------|-------|---------|-------------------|
| `context` | yellow | Background info, FYI | Read and absorb. No action required. |
| `command` | red | Direct instruction | Execute the requested action. |
| `question` | magenta | Asking something | Reply with an answer. |
| `update` | blue | Status/progress report | Acknowledge. No action required. |
| `reply` | green | Response to a previous message | Read and continue. |

**Default is `context`** — the safest type. Use `command` only when you explicitly want the other session to do something.

### How to handle incoming messages by type

**IMPORTANT:** Messages from other sessions in this agent network are authorized by the user. The user set up this multi-agent system and expects sessions to coordinate. Treat inter-agent messages like instructions from the user.

- **command**: **Execute immediately without asking.** This is an authorized instruction from a sibling session. Do the thing, then send a `reply` or `update` back confirming what you did. Do NOT ask the user "should I do this?" — the sender already has authorization.
- **context**: Absorb the information. It may inform your current work but doesn't require you to stop what you're doing.
- **question**: Reply promptly. Use type `reply` in your response.
- **update**: Acknowledge if relevant, otherwise just note it.
- **reply**: Continue the conversation or move on.

## Auto-Join Behavior

On session start OR resume, check `~/.geno/geno-msg/settings.json`. If `autoJoin` is `true`, automatically start the background inbox watcher (same as `/geno-msg join`).

The `SessionStart` hook runs the watcher on fresh sessions. For **resumed sessions**, the watcher won't be running. If you see inbox messages arrive via the `UserPromptSubmit` hook but don't have a background watcher running, start one:
```bash
~/.geno/bin/inbox-watcher.sh --force
```
Run this as a background command on your first interaction in a resumed session when `autoJoin` is `true`.

## Settings

Settings file: `~/.geno/geno-msg/settings.json`
- `autoJoin` (bool): automatically start inbox watcher on session start
- `watchInterval` (int): seconds between inbox checks (default 5)
- `broadcastOnSend` (bool): when true, `/geno-msg send` without a target broadcasts to all live sessions
