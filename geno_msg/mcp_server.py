"""MCP server for geno-msg inter-agent messaging.

Exposes send_message, read_messages, and list_sessions as MCP tools.
Run with: python -m geno_msg.mcp_server
"""

from __future__ import annotations

import json
import sys
from typing import Any

from .store import (
    get_current_session_id,
    mark_read,
    read_inbox,
    resolve_session,
    send_message,
)


def _read_request() -> dict[str, Any] | None:
    """Read a JSON-RPC request from stdin."""
    line = sys.stdin.readline()
    if not line:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _write_response(response: dict[str, Any]) -> None:
    """Write a JSON-RPC response to stdout."""
    sys.stdout.write(json.dumps(response) + "\n")
    sys.stdout.flush()


def _success(id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id, "result": result}


def _error(id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}}


TOOLS = [
    {
        "name": "send_message",
        "description": "Send a message to another Claude Code session. Use session IDs from list_sessions or partial IDs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient session ID (full, partial, or numeric index)",
                },
                "message": {
                    "type": "string",
                    "description": "Message text to send",
                },
                "from_session": {
                    "type": "string",
                    "description": "Sender session ID (optional, auto-detected if omitted)",
                },
            },
            "required": ["to", "message"],
        },
    },
    {
        "name": "read_messages",
        "description": "Read messages in the inbox for the current or specified session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to check (optional, auto-detected if omitted)",
                },
                "unread_only": {
                    "type": "boolean",
                    "description": "Only show unread messages (default true)",
                    "default": True,
                },
                "mark_read": {
                    "type": "boolean",
                    "description": "Mark returned messages as read (default true)",
                    "default": True,
                },
            },
        },
    },
    {
        "name": "list_sessions",
        "description": "List available Claude Code sessions that can receive messages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Max sessions to return (default 20)",
                    "default": 20,
                },
            },
        },
    },
]


def handle_tool_call(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool call and return the result as text."""
    if name == "send_message":
        to_ref = arguments["to"]
        message = arguments["message"]
        from_session = arguments.get("from_session") or get_current_session_id() or "unknown"

        to_session = resolve_session(to_ref)
        msg = send_message(from_session, to_session, message)

        return json.dumps({
            "status": "sent",
            "to": to_session,
            "from": from_session,
            "message_id": msg.id,
            "file": msg.file_path,
        })

    elif name == "read_messages":
        session_id = arguments.get("session_id") or get_current_session_id()
        if not session_id:
            return json.dumps({"error": "Could not detect session ID. Pass session_id explicitly."})

        unread_only = arguments.get("unread_only", True)
        do_mark_read = arguments.get("mark_read", True)

        messages = read_inbox(session_id, unread_only=unread_only)

        if do_mark_read and messages:
            mark_read(session_id, [m.id for m in messages])

        return json.dumps({
            "session_id": session_id,
            "count": len(messages),
            "messages": [m.to_dict() for m in messages],
        })

    elif name == "list_sessions":
        from pathlib import Path
        from datetime import datetime, timezone

        limit = arguments.get("limit", 20)
        claude_projects = Path.home() / ".claude" / "projects"

        if not claude_projects.exists():
            return json.dumps({"sessions": []})

        sessions = []
        for project_dir in claude_projects.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                sessions.append({
                    "session_id": jsonl_file.stem,
                    "modified": datetime.fromtimestamp(
                        jsonl_file.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                })

        sessions.sort(key=lambda s: s["modified"], reverse=True)
        current = get_current_session_id()

        result = sessions[:limit]
        for s in result:
            s["is_current"] = s["session_id"] == current

        return json.dumps({"sessions": result, "current": current})

    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


def main() -> None:
    """Run the MCP server (JSON-RPC over stdio)."""
    while True:
        request = _read_request()
        if request is None:
            break

        req_id = request.get("id")
        method = request.get("method", "")

        if method == "initialize":
            _write_response(_success(req_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "geno-msg", "version": "0.1.0"},
                "capabilities": {"tools": {}},
            }))

        elif method == "notifications/initialized":
            pass  # No response needed

        elif method == "tools/list":
            _write_response(_success(req_id, {"tools": TOOLS}))

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            try:
                result_text = handle_tool_call(tool_name, arguments)
                _write_response(_success(req_id, {
                    "content": [{"type": "text", "text": result_text}],
                }))
            except Exception as e:
                _write_response(_success(req_id, {
                    "content": [{"type": "text", "text": f"Error: {e}"}],
                    "isError": True,
                }))

        elif method == "ping":
            _write_response(_success(req_id, {}))

        else:
            if req_id is not None:
                _write_response(_error(req_id, -32601, f"Method not found: {method}"))


if __name__ == "__main__":
    main()
