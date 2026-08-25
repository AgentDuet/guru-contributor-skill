# guru-contributor-skill

Contribute knowledge to the **Guru** knowledge base straight from your coding
agent. Point it at your documents and the skill turns them into atomic,
reviewed knowledge records and publishes them for you — you work in plain
language, it takes care of the rest.

## Install

Works on four hosts. Install once, then run **connect** (below) — it wires up
the right config for whichever host you're on.

### Claude Code (CLI)
```
/plugin marketplace add AgentDuet/guru-contributor-skill
/plugin install guru-contributor@agentduet
```

### Antigravity (agy) — CLI or 2.x desktop
Clone, then install the plugin (one command; installs globally to
`~/.gemini/config/plugins/`, shared by the `agy` CLI **and** the Antigravity
desktop app):
```
git clone https://github.com/AgentDuet/guru-contributor-skill.git
agy plugin install ./guru-contributor-skill
```
On the **desktop app**, fully quit + reopen after installing (it loads plugins
at startup), then run **connect**, then restart once more (MCP config also loads
at startup). The CLI just needs a new session.

### Claude Cowork (Claude desktop app)
In the app: **Customize → Skills → ➕ → Upload a skill**, and choose a ZIP of the
`skills/guru-contributor/` folder. (Or drop it under `.claude/skills/`.) Then run
**connect** and fully restart the app.

### Other Agent-Skills agents
Copy `skills/guru-contributor/` into the agent's skills directory; run
**connect** and let it write that agent's MCP config.

## Get started

Start a session and run **connect**. It asks you three things, once:

1. your work email
2. your organization's portal domain
3. your organization

connect emails you a 6-digit code, verifies you, and sets everything up. When
your access later expires, just run **connect** again.

That's all you do. Connection, credentials, and security are handled for you —
there's nothing to configure and nothing to keep secret on your side.

Every session, before it writes anything, the skill shows you which
organization you're contributing into and asks you to confirm — so a mistaken
org is caught before anything lands.

## Your documents

Point the skill at your files — Markdown, text, and PDF work as-is. For Office
files (`.docx`, `.pptx`, `.xlsx`) it reads them using converter tools already on
your machine if present (`pandoc`, `python3`, `textutil`, …); **you don't need
to install anything**. If none are available, it simply asks you to **Save As
PDF** and continues. Nothing to set up.

---

© AgentDuet. All rights reserved. Published for distribution and installation;
no license to copy, modify, or redistribute is granted.
