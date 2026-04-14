#!/usr/bin/env bash
# Background inbox watcher for geno-msg.
# Polls inbox and outputs messages as JSON with hookSpecificOutput
# so Claude Code injects them into the model's context.
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

while true; do
  output=$("$GENO_MSG" inbox --quiet 2>/dev/null)
  if [ -n "$output" ]; then
    escaped=$(echo "$output" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"Notification\",\"additionalContext\":$escaped}}"
  fi
  sleep "$INTERVAL"
done
