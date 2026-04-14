#!/usr/bin/env bash
# Background inbox watcher for geno-msg.
# Polls inbox every 5s and outputs new messages.
# Intended to run as an async SessionStart hook in Claude Code.

GENO_MSG="$(dirname "$0")/../bin/geno-msg"
# Fallback to well-known path
if [ ! -x "$GENO_MSG" ]; then
  GENO_MSG="${HOME}/.geno/venv/bin/geno-msg"
fi

while true; do
  output=$("$GENO_MSG" inbox --quiet 2>/dev/null)
  if [ -n "$output" ]; then
    escaped=$(echo "$output" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"Notification\",\"additionalContext\":$escaped}}"
  fi
  sleep 5
done
