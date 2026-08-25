# guru-contributor-skill

Contribute knowledge to the **Guru** knowledge base straight from your coding
agent. Point it at your documents and the skill turns them into atomic,
reviewed knowledge records and publishes them for you — you work in plain
language, it takes care of the rest.

## Install

### Claude Code
```
/plugin marketplace add AgentDuet/guru-contributor-skill
/plugin install guru-contributor@agentduet
```

### Antigravity (agy)
```
agy plugin install guru-contributor@agentduet
```
(or `agy plugin import` from a Claude marketplace already added.)

### Other agents
Copy `skills/guru-contributor/` into your agent's skills directory
(`~/.claude/skills/` for Claude Code, `~/.gemini/config/skills/` or a project
`.agents/skills/` for Antigravity).

## Get started

Start a session and run **connect**. It asks you three things, once:

1. your work email
2. your organization's portal domain
3. your organization

connect emails you a 6-digit code, verifies you, and sets everything up. When
your access later expires, just run **connect** again.

That's all you do. Connection, credentials, and security are handled for you —
there's nothing to configure and nothing to keep secret on your side.

---

© AgentDuet. All rights reserved. Published for distribution and installation;
no license to copy, modify, or redistribute is granted.
