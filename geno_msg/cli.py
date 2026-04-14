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

    if do_mark_read:
        mark_read(session_id, [m.id for m in messages])


def _get_project_path(jsonl_file) -> str:
    """Extract the real project path from a session's first JSONL entry."""
    try:
        with open(jsonl_file) as f:
            for i, line in enumerate(f):
                if i > 10:  # only check first few lines
                    break
                line = line.strip()
                if not line:
                    continue
                entry = json.loads(line)
                cwd = entry.get("cwd", "")
                if cwd:
                    return cwd
    except (json.JSONDecodeError, OSError):
        pass
    return ""


def _shorten_path(path: str, max_len: int = 40) -> str:
    """Shorten a project path for display."""
    from pathlib import Path

    if not path:
        return ""

    home = str(Path.home())
    if path.startswith(home):
        path = "~" + path[len(home):]

    if len(path) <= max_len:
        return path

    # Show last components that fit
    parts = path.split("/")
    result = parts[-1]
    for part in reversed(parts[:-1]):
        candidate = part + "/" + result
        if len(candidate) > max_len - 3:
            break
        result = candidate
    return ".../" + result


def _find_live_sessions() -> set[str]:
    """Find session IDs with a running claude process.

    Matches claude PIDs to sessions by checking the parent shell's cwd
    against each session's project path (from the JSONL).
    """
    import subprocess
    from pathlib import Path

    live: set[str] = set()

    try:
        # Find all claude CLI processes (not Claude.app, not subprocesses)
        ps_out = subprocess.run(
            ["ps", "-eo", "pid,ppid,args"], capture_output=True, text=True
        ).stdout

        claude_procs = []  # (pid, ppid)
        for line in ps_out.splitlines():
            parts = line.strip().split(None, 2)
            if len(parts) < 3:
                continue
            if "Claude.app" in parts[2] or "grep" in parts[2]:
                continue
            args = parts[2]
            if args.startswith("claude") or args.endswith("/claude"):
                try:
                    claude_procs.append((int(parts[0]), int(parts[1])))
                except ValueError:
                    pass

        if not claude_procs:
            return live

        # Get parent shell cwd for each claude process
        live_cwds: list[str] = []
        for pid, ppid in claude_procs:
            try:
                lsof_out = subprocess.run(
                    ["lsof", "-a", "-p", str(ppid), "-d", "cwd"],
                    capture_output=True, text=True
                ).stdout
                # Second line has the cwd in the last column
                lines = lsof_out.strip().splitlines()
                if len(lines) >= 2:
                    cwd = lines[1].rsplit(None, 1)[-1]
                    live_cwds.append(cwd)
            except (OSError, subprocess.SubprocessError):
                pass

        if not live_cwds:
            return live

        # Match cwds against session project paths.
        # Only the most recent session per project directory gets marked LIVE,
        # since that's the one the running claude process is using.
        claude_projects = Path.home() / ".claude" / "projects"
        if not claude_projects.exists():
            return live

        # Group sessions by project dir, sorted by recency
        from collections import defaultdict
        project_sessions: dict[str, list[tuple[float, str, str]]] = defaultdict(list)

        for project_dir in claude_projects.iterdir():
            if not project_dir.is_dir():
                continue
            for jsonl_file in project_dir.glob("*.jsonl"):
                session_cwd = _get_project_path(jsonl_file)
                if session_cwd:
                    mtime = jsonl_file.stat().st_mtime
                    project_sessions[session_cwd].append(
                        (mtime, jsonl_file.stem, session_cwd)
                    )

        # For each live cwd, mark only the most recent matching session
        for cwd in live_cwds:
            for session_cwd, sessions_list in project_sessions.items():
                if session_cwd.endswith(cwd) or cwd.endswith(session_cwd.split("/")[-1]):
                    sessions_list.sort(reverse=True)  # most recent first
                    live.add(sessions_list[0][1])  # mark only the newest
                    break

    except (OSError, subprocess.SubprocessError):
        pass

    return live


def _handle_sessions(args: list[str]) -> None:
    """List active sessions with project names and live/dead status."""
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
            sessions.append({
                "id": jsonl_file.stem,
                "mtime": jsonl_file.stat().st_mtime,
                "path": jsonl_file,
            })

    sessions.sort(key=lambda s: s["mtime"], reverse=True)

    current = get_current_session_id()
    live = _find_live_sessions()

    # Read project paths (only for displayed sessions)
    display = sessions[:20]
    for s in display:
        s["project"] = _get_project_path(s["path"])

    click.echo()
    click.secho("  Sessions:", bold=True)
    click.echo()
    for i, s in enumerate(display, 1):
        dt = datetime.fromtimestamp(s["mtime"], tz=timezone.utc)
        age = _format_age(dt.isoformat())
        project = _shorten_path(s["project"])

        is_current = s["id"] == current
        is_live = s["id"] in live

        if is_current:
            status = click.style(" *", fg="green", bold=True)
        elif is_live:
            status = click.style(" LIVE", fg="cyan", bold=True)
        else:
            status = ""

        click.echo(f"  {i:>3}. {s['id'][:8]}  {project:<40} ({age}){status}")
    click.echo()
    click.echo("  * = this session  LIVE = recently active")
    click.echo()


def _handle_join(args: list[str]) -> None:
    """Live chat mode — watch inbox and send messages interactively.

    Usage: geno-msg join [session-id-to-watch] [--as <my-session-id>]
    """
    import select
    import time

    from .store import MESSAGES_DIR

    # Parse args
    watch_session = None
    my_session = get_current_session_id() or "cli"
    i = 0
    while i < len(args):
        if args[i] == "--as" and i + 1 < len(args):
            my_session = args[i + 1]
            i += 2
            continue
        elif not args[i].startswith("-"):
            watch_session = resolve_session(args[i])
        i += 1

    if not watch_session:
        # Default: watch our own inbox
        watch_session = my_session
        if watch_session == "cli":
            click.echo("Can't auto-detect session. Pass a session ID:")
            click.echo("  geno-msg join <session-id>")
            click.echo("  geno-msg join <session-id> --as <my-id>")
            raise SystemExit(1)

    inbox_dir = MESSAGES_DIR / watch_session
    inbox_dir.mkdir(parents=True, exist_ok=True)

    # Track known files
    known_files: set[str] = set()
    if inbox_dir.exists():
        for f in inbox_dir.glob("*.json"):
            known_files.add(f.name)

    click.echo()
    click.secho(f"  Joined as {my_session[:8]} — watching {watch_session[:8]}", fg="cyan", bold=True)
    click.secho("  Type a message and press Enter to broadcast.", dim=True)
    click.secho("  Ctrl+C to quit.", dim=True)
    click.echo()

    def check_new_messages() -> None:
        nonlocal known_files
        if not inbox_dir.exists():
            return
        current = set()
        for f in inbox_dir.glob("*.json"):
            current.add(f.name)
            if f.name not in known_files:
                try:
                    with open(f) as fh:
                        data = json.load(fh)
                    if not data.get("read", False):
                        sender = data.get("from", "unknown")[:8]
                        ts = data.get("timestamp", "")
                        try:
                            dt = datetime.fromisoformat(ts)
                            ts_str = dt.strftime("%H:%M:%S")
                        except (ValueError, TypeError):
                            ts_str = "??:??:??"
                        msg = data.get("message", "")
                        click.secho(f"  [{ts_str}] {sender}: ", fg="yellow", bold=True, nl=False)
                        click.echo(msg)
                except (json.JSONDecodeError, OSError):
                    pass
        known_files = current

    try:
        while True:
            # Check for new messages
            check_new_messages()

            # Non-blocking stdin check (wait up to 2 seconds)
            if select.select([sys.stdin], [], [], 2)[0]:
                line = sys.stdin.readline().strip()
                if not line:
                    continue
                # Send to all live sessions (broadcast)
                # For now, send to the watched session
                # The user can specify a target with @session_id prefix
                if line.startswith("@"):
                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        target = resolve_session(parts[0][1:])
                        msg_text = parts[1]
                    else:
                        click.echo("  Usage: @session-id message")
                        continue
                else:
                    # Broadcast to all live sessions
                    target = None
                    msg_text = line

                if target:
                    msg = send_message(my_session, target, msg_text)
                    click.secho(f"  → {target[:8]}: ", fg="green", nl=False)
                    click.echo(msg_text)
                else:
                    # Find live sessions and send to all of them
                    live = _find_live_sessions()
                    live.discard(watch_session)  # don't send to ourselves
                    if not live:
                        click.secho("  No live sessions to broadcast to.", dim=True)
                        continue
                    for sid in live:
                        send_message(my_session, sid, msg_text)
                    click.secho(f"  → broadcast ({len(live)} sessions): ", fg="green", nl=False)
                    click.echo(msg_text)

    except KeyboardInterrupt:
        click.echo()
        click.secho("  Left chat.", dim=True)


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
        click.echo("  geno-msg join [session-id]           Live chat (watch inbox + send)")
        click.echo("  geno-msg sessions                    List available sessions")
        click.echo()
        click.echo("Session references:")
        click.echo("  Full UUID:     9a004367-5e0d-41e1-...")
        click.echo("  Partial ID:    9a004367")
        click.echo("  Index:         1 (most recent), 2, 3, ...")
        click.echo()
        click.echo("Join mode:")
        click.echo("  Type messages to broadcast to all live sessions")
        click.echo("  @session-id message   — send to specific session")
        click.echo("  Ctrl+C to quit")
        return

    cmd = args[0]
    cmd_args = args[1:]

    if cmd == "send":
        _handle_send(cmd_args)
    elif cmd == "inbox":
        _handle_inbox(cmd_args)
    elif cmd == "sessions":
        _handle_sessions(cmd_args)
    elif cmd == "join":
        _handle_join(cmd_args)
    else:
        click.echo(f"Unknown command: {cmd}")
        click.echo("Run geno-msg --help for usage.")
        raise SystemExit(1)


if __name__ == "__main__":
    entry_point()
