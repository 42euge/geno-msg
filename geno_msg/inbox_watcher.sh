#!/usr/bin/env bash
# Background inbox watcher for geno-msg.
# Polls inbox WITHOUT consuming messages (no --quiet/--mark-read).
# Exits as soon as a message is detected so the task-completion
# notification wakes the agent. The PostToolUse hook then consumes
# the message via "inbox --quiet".
#
# When run as a SessionStart hook, checks ~/.geno/geno-msg/settings.json
# for autoJoin=true before starting. Pass --force to skip the check.

GENO_MSG="${HOME}/.geno/venv/bin/geno-msg"
SETTINGS="${HOME}/.geno/geno-msg/settings.json"
INTERVAL=5

# Check autoJoin setting unless --force is passed
if [ "$1" != "--force" ]; then
  if [ -f "$SETTINGS" ]; then
    auto_join=$(python3 -c "import json; print(json.load(open('$SETTINGS')).get('autoJoin', False))" 2>/dev/null)
    if [ "$auto_join" != "True" ]; then
      exit 0
    fi
    # Read custom interval
    custom_interval=$(python3 -c "import json; print(json.load(open('$SETTINGS')).get('watchInterval', 5))" 2>/dev/null)
    if [ -n "$custom_interval" ] && [ "$custom_interval" -gt 0 ] 2>/dev/null; then
      INTERVAL=$custom_interval
    fi
  else
    # No settings file = no auto-join
    exit 0
  fi
fi

# Poll without consuming (--quiet = peek only) — exit on first message
# so task completion notification wakes the agent.
while true; do
  output=$("$GENO_MSG" inbox --quiet 2>/dev/null)
  if [ -n "$output" ] && [ "$output" != "No messages." ]; then
    echo "New message detected"
    exit 0
  fi
  sleep "$INTERVAL"
done
