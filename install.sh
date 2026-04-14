#!/usr/bin/env bash
# geno-msg installer
# Sets up the venv, installs the package, configures Claude Code hooks,
# and registers the MCP server.
set -e

GENO_DIR="${HOME}/.geno"
VENV_DIR="${GENO_DIR}/venv"
BIN_DIR="${GENO_DIR}/bin"
SETTINGS="${HOME}/.claude/settings.json"
MCP_CONFIG="${HOME}/.claude/.mcp.json"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== geno-msg installer ==="

# 1. Create venv and install
echo "→ Setting up Python venv at ${VENV_DIR}..."
python3 -m venv "${VENV_DIR}" 2>/dev/null || true
"${VENV_DIR}/bin/pip" install -q -e "${SCRIPT_DIR}"

# 2. Install inbox watcher script
echo "→ Installing inbox watcher..."
mkdir -p "${BIN_DIR}"
cp "${SCRIPT_DIR}/geno_msg/inbox_watcher.sh" "${BIN_DIR}/inbox-watcher.sh"
chmod +x "${BIN_DIR}/inbox-watcher.sh"

# 3. Install skill (symlink for single source of truth)
echo "→ Installing geno-msg skill..."
SKILLS_DIR="${HOME}/.claude/skills"
mkdir -p "${SKILLS_DIR}"
ln -sfn "${SCRIPT_DIR}/skills/geno-msg" "${SKILLS_DIR}/geno-msg"
echo "  Symlinked to ${SKILLS_DIR}/geno-msg"

# 5. Symlink CLI
echo "→ Creating CLI symlinks..."
mkdir -p "${HOME}/.local/bin"
ln -sf "${VENV_DIR}/bin/geno-msg" "${HOME}/.local/bin/geno-msg"
ln -sf "${VENV_DIR}/bin/geno-wait" "${HOME}/.local/bin/geno-wait"

# 6. Configure Claude Code hooks
echo "→ Configuring Claude Code hooks..."
if [ -f "${SETTINGS}" ]; then
  # Add hooks if not already present
  python3 -c "
import json, sys

with open('${SETTINGS}') as f:
    settings = json.load(f)

hooks = settings.setdefault('hooks', {})
changed = False

# UserPromptSubmit hook
inbox_cmd = '${VENV_DIR}/bin/geno-msg inbox --quiet'
ups = hooks.get('UserPromptSubmit', [])
if not any(h.get('hooks', [{}])[0].get('command', '') == inbox_cmd for h in ups if h.get('hooks')):
    ups.append({'hooks': [{'type': 'command', 'command': inbox_cmd, 'timeout': 3}]})
    hooks['UserPromptSubmit'] = ups
    changed = True

# PostToolUse hook
ptu = hooks.get('PostToolUse', [])
if not any(h.get('hooks', [{}])[0].get('command', '') == inbox_cmd for h in ptu if h.get('hooks')):
    ptu.append({'hooks': [{'type': 'command', 'command': inbox_cmd, 'timeout': 3}]})
    hooks['PostToolUse'] = ptu
    changed = True

# SessionStart hook (background watcher)
watcher_cmd = '${BIN_DIR}/inbox-watcher.sh'
ss = hooks.get('SessionStart', [])
if not any(h.get('hooks', [{}])[0].get('command', '') == watcher_cmd for h in ss if h.get('hooks')):
    ss.append({'hooks': [{'type': 'command', 'command': watcher_cmd, 'async': True}]})
    hooks['SessionStart'] = ss
    changed = True

if changed:
    with open('${SETTINGS}', 'w') as f:
        json.dump(settings, f, indent=2)
        f.write('\n')
    print('  Hooks configured.')
else:
    print('  Hooks already configured.')
"
else
  echo "  Warning: ${SETTINGS} not found. Create it or configure hooks manually."
fi

# 7. Register MCP server
echo "→ Registering MCP server..."
if [ -f "${MCP_CONFIG}" ]; then
  python3 -c "
import json

with open('${MCP_CONFIG}') as f:
    config = json.load(f)

servers = config.setdefault('mcpServers', {})
if 'geno-msg' not in servers:
    servers['geno-msg'] = {
        'command': '${VENV_DIR}/bin/python',
        'args': ['-m', 'geno_msg.mcp_server']
    }
    with open('${MCP_CONFIG}', 'w') as f:
        json.dump(config, f, indent=2)
        f.write('\n')
    print('  MCP server registered.')
else:
    print('  MCP server already registered.')
"
else
  mkdir -p "$(dirname "${MCP_CONFIG}")"
  cat > "${MCP_CONFIG}" <<MCPEOF
{
  "mcpServers": {
    "geno-msg": {
      "command": "${VENV_DIR}/bin/python",
      "args": ["-m", "geno_msg.mcp_server"]
    }
  }
}
MCPEOF
  echo "  MCP config created."
fi

echo ""
echo "=== Done! ==="
echo "  CLI:     geno-msg (in ~/.local/bin)"
echo "  MCP:     geno-msg server registered"
echo "  Hooks:   inbox check on prompt/tool, watcher on session start"
echo ""
echo "Restart Claude Code to activate the MCP server and hooks."
