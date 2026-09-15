#!/usr/bin/env python3
"""Guru contributor auth helper — the OTP ceremony + header injection (stdlib only).

Wraps the two public auth endpoints so the ceremony is one tested code path
instead of per-session hand-rolled HTTP, and so the minted bearer goes straight
into the credential store (~/.guru/credentials.json, via creds.py) without ever
passing through the agent's context.

Commands:
    auth.py request  <email> <ba_uid> <routing_org> <env_mcp_url>
        POST <auth-base>/request with body {"ba_uid": ..., "email": ...} (no
        portal domain — there is no domain input in this ceremony). Prints the
        server's JSON verdict verbatim, then a plain-language line for the
        agent to relay:
          - "sent"                 -> a code is on its way; proceed to exchange.
          - "first_contact_required" -> the C2 instruction, verbatim; do NOT
            proceed to the OTP prompt.
          - "not_available"        -> the workspace isn't set up yet.
          - "otp_pending" / "rate_limited" / "send_failed" / "internal_error"
            -> their own short message.
        Exit 0 on "sent", 1 on any other shape.

    auth.py exchange <email> <otp> <ba_uid> <routing_org> <env_mcp_url>
        POST <auth-base>/exchange. On success the bearer is written straight
        to the store under <ba_uid> (together with <routing_org>, so later MCP
        calls reuse the same routing header); stdout gets a REDACTED receipt
        only ({"status": "issued", "display_name": ..., "expires_at": ...}) —
        the token itself is never printed. Exit 0 issued, 1 otherwise.

    auth.py headers  <ba_uid>
        Print the MCP auth headers as JSON from the stored live token:
        {"Authorization": "Bearer <token>", "x-user-org-uuid": "<routing_org>"}.
        This is the ONE sanctioned way to materialize the credential for MCP
        config injection (same job as `creds.py get`, plus the routing
        header, so every consumer builds identical headers). Exit 1 if
        absent/expired.

The <env_mcp_url> is the environment's MCP URL from resources/environments.md.
The auth base is DERIVED from it — the trailing `/private/v1/mcp` is replaced
with `/public/v1/auth` — which preserves any gateway path prefix. A URL that
does not end in /private/v1/mcp is refused rather than guessed at.

`x-user-org-uuid` is the gateway ROUTING header (b3 internal-gateway routing),
NOT an identity claim. It must carry the environment's ROUTING org-uuid (the
`routing org-uuid` column in resources/environments.md, chosen by env=exp|prod)
— NOT the ba_uid. The ba_uid is a tenant id, not a routable org, so routing by
it fails at the gateway. Contributor identity comes from the bearer token
(the server resolves it); the ba_uid travels in the /request body, never the
routing header.

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

# Human-facing lines for each `request` outcome code. The C2 instruction is
# verbatim per the spec (impl/specs/2026-09-14-contributor-first-contact-otp.md §2.1/§5)
# — do not paraphrase it.
_REQUEST_MESSAGES = {
    "sent": (
        "A 6-digit code is on its way to that inbox, single-use, expires in "
        "5 minutes. Ask the contributor to read it back to you, then run exchange."
    ),
    "first_contact_required": (
        "You haven't reached this workspace's librarian yet. Open a chat "
        "with it on agentduet.com from your own account, then run connect again."
    ),
    "not_available": "This workspace isn't set up for contribution.",
    "otp_pending": (
        "A live code for this email already exists. Check the inbox for the "
        "one already sent, or wait for it to expire before requesting a new one."
    ),
    "rate_limited": (
        "Too many requests for this email or network address in the current "
        "window. Wait before trying again — don't retry immediately."
    ),
    "send_failed": (
        "The code was minted but delivery failed. Safe to retry request once; "
        "repeated failures can tip into rate_limited."
    ),
    "internal_error": (
        "Unexpected server-side fault. Try again shortly; escalate if it repeats."
    ),
}

# Codes that mean the ceremony should continue on to prompt for the OTP.
_PROCEED_TO_OTP = {"sent"}


def _auth_base(env_mcp_url: str) -> str:
    url = env_mcp_url.rstrip("/")
    if not url.endswith(_MCP_TAIL):
        raise ValueError(
            f"env url must end with {_MCP_TAIL} (got {env_mcp_url!r}) — "
            "refusing to guess the auth base from a bare host"
        )
    return url[: -len(_MCP_TAIL)] + "/public/v1/auth"


def _post(url: str, routing_org: str, body: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            # ROUTING only — the env's routing org-uuid, not the ba_uid.
            "x-user-org-uuid": routing_org,
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


def _outcome_code(result: dict) -> str | None:
    """The machine code the skill branches on. Success is {"status": "sent"};
    every other outcome is {"error": "<code>"} (spec §2.1). Read both."""
    return result.get("status") or result.get("error")


def cmd_request(email: str, ba_uid: str, routing_org: str, env_mcp_url: str) -> int:
    result = _post(_auth_base(env_mcp_url) + "/request", routing_org,
                   {"ba_uid": ba_uid, "email": email})
    print(json.dumps(result, indent=2))
    code = _outcome_code(result)
    message = _REQUEST_MESSAGES.get(code)
    if message:
        print(message, file=sys.stderr)
    return 0 if code in _PROCEED_TO_OTP else 1


def cmd_exchange(email: str, otp: str, ba_uid: str, routing_org: str, env_mcp_url: str) -> int:
    result = _post(_auth_base(env_mcp_url) + "/exchange", routing_org,
                   {"email": email, "otp": otp})
    token = result.get("token")
    if not token:
        print(json.dumps(result, indent=2))
        return 1
    # Bearer goes straight to the store — never to stdout, never into context.
    # Persist routing_org alongside it so `headers`/mcp.py reuse the SAME routing
    # header on every MCP call (the ba_uid is not the routing value).
    data = creds._load()
    entry = data.get(ba_uid, {})
    entry.update({k: result[k] for k in ("token", "expires_at", "display_name", "owner_name") if k in result})
    entry["routing_org"] = routing_org
    data[ba_uid] = entry
    creds._save(data)
    receipt = {
        "status": "issued",
        "ba_uid": ba_uid,
        "display_name": result.get("display_name"),
        "owner_name": result.get("owner_name"),
        "expires_at": result.get("expires_at"),
        "stored": creds.STORE,
    }
    print(json.dumps(receipt, indent=2))
    return 0


def cmd_headers(ba_uid: str) -> int:
    entry = creds._load().get(ba_uid)
    if not entry or not entry.get("token") or creds._expired(entry):
        print(f"auth.py headers: no live token for workspace {ba_uid} — run the "
              "connect ceremony (request + exchange) first", file=sys.stderr)
        return 1
    routing_org = entry.get("routing_org")
    if not routing_org:
        print(f"auth.py headers: stored credential for {ba_uid} has no routing_org "
              "— re-run connect (exchange) to record it", file=sys.stderr)
        return 1
    print(json.dumps({
        "Authorization": f"Bearer {entry['token']}",
        "x-user-org-uuid": routing_org,
    }, indent=2))
    return 0


def main(argv: list[str]) -> int:
    usage = {
        "request": (4, "auth.py request <email> <ba_uid> <routing_org> <env_mcp_url>"),
        "exchange": (5, "auth.py exchange <email> <otp> <ba_uid> <routing_org> <env_mcp_url>"),
        "headers": (1, "auth.py headers <ba_uid>"),
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
            return cmd_exchange(*argv[2:7])
        return cmd_headers(argv[2])
    except ValueError as e:
        print(f"auth.py {cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
