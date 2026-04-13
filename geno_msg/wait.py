"""geno-wait: Interruptible sleep that checks inbox.

Replaces `sleep N && command` with inbox-aware waiting.
When a message arrives, prints it and exits early so the
Claude Code turn fires immediately.

Usage:
    geno-wait 600                    # sleep 600s, check inbox every 10s
    geno-wait 600 --interval 5       # check every 5s
    geno-wait 600 -- kaggle status   # after wait, run command
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from .store import MESSAGES_DIR, get_current_session_id, read_inbox, mark_read


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help"):
        print("Usage: geno-wait <seconds> [--interval N] [-- command...]")
        print("  Sleeps with periodic inbox checks. Exits early on new messages.")
        return

    # Parse args
    duration = 0
    interval = 10
    command: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
            i += 2
            continue
        elif args[i] == "--":
            command = args[i + 1:]
            break
        elif duration == 0:
            try:
                duration = int(args[i])
            except ValueError:
                # Assume everything from here is the command
                command = args[i:]
                break
        i += 1

    if duration <= 0:
        print("Invalid duration", file=sys.stderr)
        sys.exit(1)

    session_id = get_current_session_id()

    # Record existing unread count so we only trigger on NEW messages
    existing_unread = 0
    if session_id:
        existing_unread = len(read_inbox(session_id, unread_only=True))

    elapsed = 0
    interrupted = False

    while elapsed < duration:
        sleep_time = min(interval, duration - elapsed)
        time.sleep(sleep_time)
        elapsed += sleep_time

        # Check for new messages
        if session_id:
            unread = read_inbox(session_id, unread_only=True)
            if len(unread) > existing_unread:
                # New messages arrived — print them and break
                new_msgs = unread[existing_unread:]
                for msg in new_msgs:
                    sender = msg.from_session[:8] if msg.from_session else "unknown"
                    print(f"[geno-msg from {sender}] {msg.message}")
                interrupted = True
                break

    if not interrupted:
        print(f"Wait complete ({duration}s)")

    # Run the command if provided
    if command:
        result = subprocess.run(command, capture_output=False)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
