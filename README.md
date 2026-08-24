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

## Two things you set once (never bundled — they're per-user)

The plugin ships the MCP registration with **environment-variable references**,
so no secret and no org id are baked into this repo. Set both in your shell
profile or secret manager:

- `LIBRA_CONTRIB_KEY` — your 7-day bearer token, minted by the connect
  ceremony (email one-time code). The skill's **connect** workflow runs this
  for you; you never type or paste the token.
- `LIBRA_ORG_UUID` — your organization's UUID. Sent as the `x-user-org-uuid`
  header so the gateway routes to the correct environment; it must match the
  org your bearer was issued for.

The bundled `.mcp.json` references them as `${LIBRA_CONTRIB_KEY}` and
`${LIBRA_ORG_UUID}` — resolved by your agent at call time, never stored here.

## Getting a credential

Start a session with the skill installed and run **connect** — it asks for your
work email, your org's portal domain, and your org UUID, sends a 6-digit code
to your inbox (5-minute, single-use), and exchanges it for the bearer, which it
writes to `LIBRA_CONTRIB_KEY`. Full flow: `skills/guru-contributor/SKILL.md`.

## Endpoint

- MCP write surface: `https://api.b3networks.com/library/private/v1/mcp`
- Credential issuance: `https://api.b3networks.com/library/public/v1/auth/{request,exchange}`

The `/library` path prefix tells the public gateway which service to forward
to — required on every call. Every request also carries the `x-user-org-uuid`
header for environment routing.

---

© AgentDuet. All rights reserved. Published for distribution and installation;
no license to copy, modify, or redistribute is granted.
