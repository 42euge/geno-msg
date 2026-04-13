"""CLI for geno-msg inter-agent messaging."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

import click

from .store import (
    clear_inbox,
    get_current_session_id,
    mark_read,
    read_inbox,
    resolve_session,
    send_message,
)


def _format_age(ts_str: str) -> str:
    try:
        ts = datetime.fromisoformat(ts_str)
        now = datetime.now(timezone.utc)
        seconds = (now - ts).total_seconds()
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{int(seconds // 60)}m ago"
        if seconds < 86400:
            return f"{int(seconds // 3600)}h ago"
        return f"{int(seconds // 86400)}d ago"
    except (ValueError, TypeError):
        return ts_str


def _handle_send(args: list[str]) -> None:
    """geno-msg send <session> <message...>"""
    if len(args) < 2:
        click.echo("Usage: geno-msg send <session-id> <message>")
        raise SystemExit(1)

    to_ref = args[0]
    message = " ".join(args[1:])

    to_session = resolve_session(to_ref)
    from_session = get_current_session_id() or "unknown"

    msg = send_message(from_session, to_session, message)

    click.echo(f"Sent to {to_session[:8]}: {message[:80]}")
    click.echo(f"  File: {msg.file_path}")


def _handle_inbox(args: list[str]) -> None:
    """geno-msg inbox [--all] [--json] [--quiet] [--mark-read] [--clear]"""
    show_all = "--all" in args
    as_json = "--json" in args
    quiet = "--quiet" in args
    do_mark_read = "--mark-read" in args
    do_clear = "--clear" in args
    session_id = None

    for a in args:
        if not a.startswith("-"):
            session_id = a
            break

    if session_id is not None:
        session_id = resolve_session(session_id)
    else:
        session_id = get_current_session_id()

    if session_id is None:
        if quiet:
            return
        click.echo("Could not detect current session ID.")
        click.echo("Pass a session ID: geno-msg inbox <session-id>")
        raise SystemExit(1)

    if do_clear:
        count = clear_inbox(session_id, read_only=True)
        if not quiet:
            click.echo(f"Cleared {count} read message(s).")
        return

    messages = read_inbox(session_id, unread_only=not show_all)

    if not messages:
        if not quiet:
            click.echo("No messages.")
        return

    if as_json:
        click.echo(json.dumps([m.to_dict() for m in messages], indent=2))
    else:
        if not quiet:
            click.echo()
            label = "All" if show_all else "Unread"
            click.secho(f"  {label} messages for {session_id[:8]}:", bold=True)
            click.echo()

        for msg in messages:
            age = _format_age(msg.timestamp)
            prefix = "  " if not quiet else ""
            from_label = msg.from_session[:8] if msg.from_session else "unknown"

            if quiet:
                # Minimal output for hooks — just the message content
                click.secho(f"[msg from {from_label}] ", fg="yellow", bold=True, nl=False)
                click.echo(msg.message)
            else:
                status = " " if not msg.read else "✓"
                click.echo(f"  {status} [{age}] from {from_label}:")
                click.echo(f"    {msg.message}")
                click.echo()

    if do_mark_read or quiet:
        mark_read(session_id, [m.id for m in messages])


def _handle_sessions(args: list[str]) -> None:
    """List active sessions (delegates to geno-mon if available)."""
    from pathlib import Path

    claude_projects = Path.home() / ".claude" / "projects"
    if not claude_projects.exists():
        click.echo("No sessions found.")
        return

    sessions = []
    for project_dir in claude_projects.iterdir():
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            sessions.append(
                (jsonl_file.stem, jsonl_file.stat().st_mtime)
            )

    sessions.sort(key=lambda s: s[1], reverse=True)

    current = get_current_session_id()

    click.echo()
    click.secho("  Sessions:", bold=True)
    click.echo()
    for i, (sid, mtime) in enumerate(sessions[:20], 1):
        dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
        age = _format_age(dt.isoformat())
        marker = " ←" if sid == current else ""
        click.echo(f"  {i:>3}. {sid[:8]}  ({age}){marker}")
    click.echo()


def entry_point() -> None:
    """Entry point — dispatch subcommands."""
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        click.echo("geno-msg — inter-agent messaging")
        click.echo()
        click.echo("Usage:")
        click.echo("  geno-msg send <session> <message>   Send a message")
        click.echo("  geno-msg inbox                      Check inbox (current session)")
        click.echo("  geno-msg inbox <session-id>          Check inbox for a session")
        click.echo("  geno-msg inbox --quiet               Minimal output (for hooks)")
        click.echo("  geno-msg inbox --all                 Include read messages")
        click.echo("  geno-msg inbox --json                JSON output")
        click.echo("  geno-msg inbox --mark-read           Mark messages as read")
        click.echo("  geno-msg inbox --clear               Delete read messages")
        click.echo("  geno-msg sessions                    List available sessions")
        click.echo()
        click.echo("Session references:")
        click.echo("  Full UUID:     9a004367-5e0d-41e1-...")
        click.echo("  Partial ID:    9a004367")
        click.echo("  Index:         1 (most recent), 2, 3, ...")
        return

    cmd = args[0]
    cmd_args = args[1:]

    if cmd == "send":
        _handle_send(cmd_args)
    elif cmd == "inbox":
        _handle_inbox(cmd_args)
    elif cmd == "sessions":
        _handle_sessions(cmd_args)
    else:
        click.echo(f"Unknown command: {cmd}")
        click.echo("Run geno-msg --help for usage.")
        raise SystemExit(1)


if __name__ == "__main__":
    entry_point()
