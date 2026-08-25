# guru-contributor-skill

The **guru-contributor** skill, packaged for one-command install on any
MCP-capable coding agent. It turns a contributor's documents into atomic
knowledge records in a local git worktree, walks them through one batch review,
and pushes the result to the Guru knowledge base through the libra MCP tools.

This repo is a distribution package — the authoring source lives in the Libra
monorepo. Nothing here is secret: the endpoint is the public
`api.b3networks.com` gateway, and the per-user credential is never included.

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

### Plain copy (any Agent-Skills-standard agent)
Copy `skills/guru-contributor/` into your agent's skills directory
(`~/.claude/skills/` for Claude Code, `~/.gemini/config/skills/` or a project
`.agents/skills/` for Antigravity) and register the MCP server from
`.mcp.json` yourself.

## Get connected

After installing, start a session and run **connect**. It asks you for three
things, once:

1. your work email
2. your org's portal domain (e.g. `portal.hoiio.net`)
3. your org UUID

connect emails you a 6-digit code (5-minute, single-use), exchanges it for a
7-day access token, and wires up the MCP server for you. That's it — you don't
type, paste, or manage any token, and you don't set any environment variables
by hand. When the token expires, run **connect** again.

<details>
<summary>Under the hood (only matters if you register the server manually)</summary>

The bundled `.mcp.json` carries no secret and no org id — it references two
per-user environment variables that **connect** sets for you:

- `LIBRA_CONTRIB_KEY` — your access token (the credential). connect mints and
  stores it; it is never printed or committed.
- `LIBRA_ORG_UUID` — your org UUID, sent as the `x-user-org-uuid` routing
  header. Not a secret, but must match the org your token was issued for.

If you skip the plugin and copy the skill by hand, set both yourself (shell
profile or secret manager) before the first tool call. Full flow:
`skills/guru-contributor/SKILL.md`.
</details>

## Endpoint

- MCP write surface: `https://api.b3networks.com/library/private/v1/mcp`
- Credential issuance: `https://api.b3networks.com/library/public/v1/auth/{request,exchange}`

The `/library` path prefix tells the public gateway which service to forward
to — required on every call. Every request also carries the `x-user-org-uuid`
header for environment routing.

---

© AgentDuet. All rights reserved. Published for distribution and installation;
no license to copy, modify, or redistribute is granted.
