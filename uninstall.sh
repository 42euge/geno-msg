#!/usr/bin/env bash
# geno-msg uninstaller
# Removes hooks, MCP server, slash command, CLI symlinks, and scripts.
# Does NOT remove ~/.geno/geno-msg/ (message data) or the shared venv.
set -e

GENO_DIR="${HOME}/.geno"
VENV_DIR="${GENO_DIR}/venv"
BIN_DIR="${GENO_DIR}/bin"
SETTINGS="${HOME}/.claude/settings.json"
MCP_CONFIG="${HOME}/.claude/.mcp.json"
SKILLS_DIR="${HOME}/.claude/skills"

echo "=== geno-msg uninstaller ==="

# 1. Remove Claude Code hooks
echo "→ Removing Claude Code hooks..."
if [ -f "${SETTINGS}" ]; then
  python3 -c "
import json

with open('${SETTINGS}') as f:
    settings = json.load(f)

hooks = settings.get('hooks', {})
changed = False

inbox_cmd = '${VENV_DIR}/bin/geno-msg inbox --quiet'
watcher_cmd = '${BIN_DIR}/inbox-watcher.sh'

for event in ['UserPromptSubmit', 'PostToolUse', 'SessionStart']:
    entries = hooks.get(event, [])
    filtered = [
        h for h in entries
        if not any(
            hook.get('command', '') in (inbox_cmd, watcher_cmd)
            for hook in h.get('hooks', [])
        )
    ]
    if len(filtered) != len(entries):
        changed = True
        if filtered:
            hooks[event] = filtered
        else:
            del hooks[event]

if changed:
    with open('${SETTINGS}', 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')
    print('  Hooks removed.')
else:
    print('  No hooks to remove.')
"
fi

# 2. Remove MCP server
echo "→ Removing MCP server..."
if [ -f "${MCP_CONFIG}" ]; then
  python3 -c "
import json

with open('${MCP_CONFIG}') as f:
    config = json.load(f)

servers = config.get('mcpServers', {})
if 'geno-msg' in servers:
    del servers['geno-msg']
    with open('${MCP_CONFIG}', 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    print('  MCP server removed.')
else:
    print('  MCP server not found.')
"
fi

# 3. Remove skill
echo "→ Removing geno-msg skill..."
rm -rf "${SKILLS_DIR}/geno-msg"
# Also clean up legacy slash command if present
rm -f "${HOME}/.claude/commands/geno-msg.md"
echo "  Done."

# 4. Remove CLI symlinks
echo "→ Removing CLI symlinks..."
rm -f "${HOME}/.local/bin/geno-msg"
rm -f "${HOME}/.local/bin/geno-wait"
echo "  Done."

# 5. Remove inbox watcher script
echo "→ Removing inbox watcher..."
rm -f "${BIN_DIR}/inbox-watcher.sh"
echo "  Done."

# 6. Uninstall Python package
echo "→ Uninstalling geno-msg package..."
if [ -f "${VENV_DIR}/bin/pip" ]; then
  "${VENV_DIR}/bin/pip" uninstall -q -y geno-msg 2>/dev/null || true
  echo "  Done."
else
  echo "  Venv not found, skipping."
fi

echo ""
echo "=== Done! ==="
echo "  Removed: hooks, MCP server, skill, CLI symlinks, watcher, package"
echo "  Kept:    ~/.geno/geno-msg/ (message data), ~/.geno/venv/ (shared venv)"
echo ""
echo "Restart Claude Code to apply changes."
