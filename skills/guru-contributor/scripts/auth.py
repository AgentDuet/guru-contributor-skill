#!/usr/bin/env python3
"""Guru contributor auth helper — the OTP ceremony + header injection (stdlib only).

Wraps the two public auth endpoints so the ceremony is one tested code path
instead of per-session hand-rolled HTTP, and so the minted bearer goes straight
into the credential store (~/.guru/credentials.json, via creds.py) without ever
passing through the agent's context.

Commands:
    auth.py request  <email> <domain> <org_uuid> <env_mcp_url>
        POST <auth-base>/request. Prints the server's JSON verdict verbatim
        ({"status": "sent", ...} or {"error": ...}) — nothing secret in it.
        Exit 0 on "sent", 1 on any other shape.

    auth.py exchange <email> <otp> <org_uuid> <env_mcp_url>
        POST <auth-base>/exchange. On success the bearer is written straight
        to the store under <org_uuid>; stdout gets a REDACTED receipt only
        ({"status": "issued", "owner_name": ..., "expires_at": ...}) — the
        token itself is never printed. Exit 0 issued, 1 otherwise.

    auth.py headers  <org_uuid>
        Print the MCP auth headers as JSON from the stored live token:
        {"Authorization": "Bearer <token>", "x-user-org-uuid": "<org_uuid>"}.
        This is the ONE sanctioned way to materialize the credential for MCP
        config injection (same job as `creds.py get`, plus the org header, so
        every consumer builds identical headers). Exit 1 if absent/expired.

The <env_mcp_url> is the environment's MCP URL from resources/environments.md.
The auth base is DERIVED from it — the trailing `/private/v1/mcp` is replaced
with `/public/v1/auth` — which preserves any gateway path prefix. A URL that
does not end in /private/v1/mcp is refused rather than guessed at.

The OTP is fine as a CLI argument: it is single-use, 5-minute, and burns on
exchange — worthless in shell history. The bearer is the secret, and it never
leaves the store.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

import creds  # sibling module — the credential store (read/merge/write, 0600)

_MCP_TAIL = "/private/v1/mcp"
_TIMEOUT_S = 30


def _auth_base(env_mcp_url: str) -> str:
    url = env_mcp_url.rstrip("/")
    if not url.endswith(_MCP_TAIL):
        raise ValueError(
            f"env url must end with {_MCP_TAIL} (got {env_mcp_url!r}) — "
            "refusing to guess the auth base from a bare host"
        )
    return url[: -len(_MCP_TAIL)] + "/public/v1/auth"


def _post(url: str, org_uuid: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-user-org-uuid": org_uuid,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        raw = e.read()
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        return {"error": "unreachable", "detail": str(e)}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"error": "bad_response"}
    except ValueError:
        return {"error": "bad_response", "detail": raw[:200].decode("utf-8", "replace")}


def cmd_request(email: str, domain: str, org_uuid: str, env_mcp_url: str) -> int:
    result = _post(_auth_base(env_mcp_url) + "/request", org_uuid,
                   {"email": email, "domain": domain, "org_uuid": org_uuid})
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "sent" else 1


def cmd_exchange(email: str, otp: str, org_uuid: str, env_mcp_url: str) -> int:
    result = _post(_auth_base(env_mcp_url) + "/exchange", org_uuid,
                   {"email": email, "otp": otp})
    token = result.get("token")
    if not token:
        print(json.dumps(result, indent=2))
        return 1
    # Bearer goes straight to the store — never to stdout, never into context.
    data = creds._load()
    entry = data.get(org_uuid, {})
    entry.update({k: result[k] for k in ("token", "expires_at", "owner_name") if k in result})
    data[org_uuid] = entry
    creds._save(data)
    receipt = {
        "status": "issued",
        "org_uuid": org_uuid,
        "owner_name": result.get("owner_name"),
        "expires_at": result.get("expires_at"),
        "stored": creds.STORE,
    }
    print(json.dumps(receipt, indent=2))
    return 0


def cmd_headers(org_uuid: str) -> int:
    entry = creds._load().get(org_uuid)
    if not entry or not entry.get("token") or creds._expired(entry):
        print(f"auth.py headers: no live token for org {org_uuid} — run the "
              "connect ceremony (request + exchange) first", file=sys.stderr)
        return 1
    print(json.dumps({
        "Authorization": f"Bearer {entry['token']}",
        "x-user-org-uuid": org_uuid,
    }, indent=2))
    return 0


def main(argv: list[str]) -> int:
    usage = {
        "request": (4, "auth.py request <email> <domain> <org_uuid> <env_mcp_url>"),
        "exchange": (4, "auth.py exchange <email> <otp> <org_uuid> <env_mcp_url>"),
        "headers": (1, "auth.py headers <org_uuid>"),
    }
    if len(argv) < 2 or argv[1] not in usage:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[1]
    nargs, hint = usage[cmd]
    if len(argv) != 2 + nargs:
        print(f"usage: {hint}", file=sys.stderr)
        return 2
    try:
        if cmd == "request":
            return cmd_request(*argv[2:6])
        if cmd == "exchange":
            return cmd_exchange(*argv[2:6])
        return cmd_headers(argv[2])
    except ValueError as e:
        print(f"auth.py {cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
