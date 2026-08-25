# Environments

| env | MCP endpoint URL |
|---|---|
| prod | `https://api-eks.b3networks.com/library/private/v1/mcp` |

`prod` is the public gateway. The `/library` path prefix tells the gateway
which service to forward to — it is required on every call. The
credential-issuance calls live on the same host, same prefix —
`https://api-eks.b3networks.com/library/public/v1/auth/request` and `.../exchange`.
Every request (issuance and MCP alike) must carry the `x-user-org-uuid` header
so the gateway routes to the correct environment. If the contributor's
environment isn't in this table, **connect** asks for the URL directly — never
guess one.

Endpoint URLs are not secrets — a URL is fine to show, share, or write into
config. The credential is: it exists only as the `LIBRA_CONTRIB_KEY`
environment variable on the contributor's own machine (set in their shell
profile or a secret manager), referenced from MCP config as
`${LIBRA_CONTRIB_KEY}`, and resolved by the agent at connect time — it is
never typed, pasted, or echoed anywhere else. The routing header reads a
second variable, `LIBRA_ORG_UUID` (the contributor's org UUID — not a secret);
**connect** sets both, so the contributor manages neither by hand.
