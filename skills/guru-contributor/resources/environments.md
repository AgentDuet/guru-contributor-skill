# Environments

| env | MCP endpoint URL | routing org-uuid |
|---|---|---|
| prod | `https://api-eks.b3networks.com/library/private/v1/mcp` | `fc312420-0047-49a7-94a8-003f11f115c0` |

`prod` is the default and the only listed environment — **if the contributor
doesn't name one, use it without asking.** `api-eks.b3networks.com` is the public
gateway; the `/library` path prefix tells it which service to forward to
(required on every call). The credential-issuance calls live on the same host +
prefix: `.../library/public/v1/auth/request` and `.../exchange`.

Other environments (e.g. an internal `exp`) are not listed here. To reach one, a
contributor who knows it supplies that env's endpoint URL **and routing
org-uuid** at connect — don't guess or invent either.

Endpoint URLs and routing org-uuids are not secrets — fine to show, share, or
write into config. Two things get set at connect and referenced from MCP config:

- `LIBRA_CONTRIB_KEY` — the issued bearer token (the ONLY secret), referenced as
  `${LIBRA_CONTRIB_KEY}`, resolved at connect time, never typed/pasted/echoed.
  Expires after 7 days; reconnect rather than hand-edit it.
- `LIBRA_ROUTING_ORG` — the routing org-uuid for the chosen env (the column
  above), sent as `x-user-org-uuid` on every call so the gateway routes to the
  right environment. This is a routing value, **NOT** the `ba_uid`: a tenant id
  is not a routable org and fails at the gateway. Contributor identity is the
  bearer token; the `ba_uid` travels only in the `/public/v1/auth/request` body.

**connect** sets both variables, so the contributor manages neither by hand.
