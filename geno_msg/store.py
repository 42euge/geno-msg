"""File-based message store.

Messages are stored as individual JSON files under:
  ~/.geno/messages/<recipient-session-id>/<timestamp>-<sender>.json

Each message file contains:
  {
    "from": "<sender-session-id>",
    "to": "<recipient-session-id>",
    "timestamp": "<ISO 8601>",
    "message": "<text>",
    "type": "context",
    "read": false
  }

Message types:
  - context:  Background info — read and absorb, no action required
  - command:  Direct instruction — do this thing
  - question: Asking something — reply expected
  - update:   Status/progress report — FYI, no action required
  - reply:    Response to a previous message
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MESSAGES_DIR = Path.home() / ".geno" / "messages"

MESSAGE_TYPES = ("context", "command", "question", "update", "reply")


@dataclass
class Message:
    from_session: str
    to_session: str
    message: str
    type: str = "context"
    timestamp: str = ""
    read: bool = False
    id: str = ""
    file_path: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.id:
            self.id = uuid.uuid4().hex[:12]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "from": self.from_session,
            "to": self.to_session,
            "timestamp": self.timestamp,
            "type": self.type,
            "message": self.message,
            "read": self.read,
        }


def send_message(from_session: str, to_session: str, message: str, type: str = "context") -> Message:
    """Send a message to a session. Returns the created Message."""
    if type not in MESSAGE_TYPES:
        type = "context"
    msg = Message(from_session=from_session, to_session=to_session, message=message, type=type)

    # Create recipient directory
    recipient_dir = MESSAGES_DIR / to_session
    recipient_dir.mkdir(parents=True, exist_ok=True)

    # Write message file
    filename = f"{msg.id}.json"
    file_path = recipient_dir / filename
    msg.file_path = str(file_path)

    with open(file_path, "w") as f:
        json.dump(msg.to_dict(), f, indent=2)

    return msg


def read_inbox(session_id: str, unread_only: bool = True) -> list[Message]:
    """Read messages for a session."""
    inbox_dir = MESSAGES_DIR / session_id
    if not inbox_dir.exists():
        return []

    messages = []
    for msg_file in sorted(inbox_dir.glob("*.json")):
        try:
            with open(msg_file) as f:
                data = json.load(f)

            if unread_only and data.get("read", False):
                continue

            messages.append(
                Message(
                    from_session=data.get("from", ""),
                    to_session=data.get("to", ""),
                    message=data.get("message", ""),
                    type=data.get("type", "context"),
                    timestamp=data.get("timestamp", ""),
                    read=data.get("read", False),
                    id=data.get("id", msg_file.stem),
                    file_path=str(msg_file),
                )
            )
        except (json.JSONDecodeError, OSError):
            continue

    # Sort by timestamp
    messages.sort(key=lambda m: m.timestamp)
    return messages


def mark_read(session_id: str, message_ids: list[str] | None = None) -> int:
    """Mark messages as read. If message_ids is None, marks all as read. Returns count."""
    inbox_dir = MESSAGES_DIR / session_id
    if not inbox_dir.exists():
        return 0

    count = 0
    for msg_file in inbox_dir.glob("*.json"):
        try:
            with open(msg_file) as f:
                data = json.load(f)

            if data.get("read", False):
                continue

            if message_ids is not None and data.get("id", msg_file.stem) not in message_ids:
                continue

            data["read"] = True
            with open(msg_file, "w") as f:
                json.dump(data, f, indent=2)
            count += 1
        except (json.JSONDecodeError, OSError):
            continue

    return count


def clear_inbox(session_id: str, read_only: bool = True) -> int:
    """Delete messages. If read_only=True, only deletes read messages. Returns count."""
    inbox_dir = MESSAGES_DIR / session_id
    if not inbox_dir.exists():
        return 0

    count = 0
    for msg_file in inbox_dir.glob("*.json"):
        try:
            if read_only:
                with open(msg_file) as f:
                    data = json.load(f)
                if not data.get("read", False):
                    continue

            msg_file.unlink()
            count += 1
        except (json.JSONDecodeError, OSError):
            continue

    # Remove empty directory
    try:
        if inbox_dir.exists() and not any(inbox_dir.iterdir()):
            inbox_dir.rmdir()
    except OSError:
        pass

    return count


def get_current_session_id() -> str | None:
    """Try to detect the current Claude Code session ID.

    Looks at the most recently modified JSONL in ~/.claude/projects/
    that matches the current working directory.
    """
    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return None

    cwd = os.getcwd()

    # Find the project directory that matches our cwd
    best_match = None
    best_mtime = 0.0

    for project_dir in claude_projects.iterdir():
        if not project_dir.is_dir():
            continue

        for jsonl_file in project_dir.glob("*.jsonl"):
            mtime = jsonl_file.stat().st_mtime
            if mtime > best_mtime:
                # Peek at first entry to check cwd
                try:
                    with open(jsonl_file) as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            entry = json.loads(line)
                            entry_cwd = entry.get("cwd", "")
                            if entry_cwd == cwd:
                                best_match = jsonl_file.stem
                                best_mtime = mtime
                            break
                except (json.JSONDecodeError, OSError):
                    continue

    return best_match


def resolve_session(ref: str) -> str:
    """Resolve a partial session reference to a full session ID.

    Accepts full UUID, partial hex prefix, or numeric index.
    """
    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        return ref

    # Collect all session IDs sorted by recency
    sessions = []
    for project_dir in claude_projects.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            sessions.append(
                (jsonl_file.stem, jsonl_file.stat().st_mtime)
            )

    sessions.sort(key=lambda s: s[1], reverse=True)

    # Numeric index
    try:
        idx = int(ref)
        if 1 <= idx <= len(sessions):
            return sessions[idx - 1][0]
    except ValueError:
        pass

    # Partial match
    matches = [s[0] for s in sessions if s[0].startswith(ref)]
    if len(matches) == 1:
        return matches[0]

    # Return as-is if no match (might be a direct session ID)
    return ref
