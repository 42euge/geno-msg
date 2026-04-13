# geno-msg

## AI agents can't talk to each other

You have two Claude Code sessions open. One is debugging a test failure. The other just finished a refactor that fixes it. Right now, the only way to connect them is you — copy-pasting context between windows.

**geno-msg** gives your agents a shared inbox. Send a message from one session, receive it in another — through files, CLI, MCP tools, or automatic hooks.

---

## Three layers, one storage

All three interfaces read and write the same files at `~/.geno/messages/`. Pick whichever fits your workflow — or use all of them.

### CLI — for humans and scripts

```bash
geno-msg send d2cf72cc "the auth test is fixed, pull and rerun"
geno-msg inbox
```

### MCP — for agents

Agents call `send_message` and `read_messages` as native tools. No Bash needed.

```json
{
  "name": "send_message",
  "arguments": {
    "to": "d2cf72cc",
    "message": "the auth test is fixed, pull and rerun"
  }
}
```

### Hook — automatic notifications

A Claude Code hook checks the inbox at the start of every turn. Messages arrive without anyone asking.

```
[msg from 9a004367] the auth test is fixed, pull and rerun
```

## Quick start

```bash
git clone https://github.com/42euge/geno-msg.git
cd geno-msg
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
geno-msg --help
```

[:material-rocket-launch: Getting Started](getting-started.md){ .md-button .md-button--primary }
[:material-book-open-variant: Concepts](concepts.md){ .md-button }
[:material-github: View on GitHub](https://github.com/42euge/geno-msg){ .md-button }
