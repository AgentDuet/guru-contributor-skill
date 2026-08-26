#!/usr/bin/env python3
"""Guru contributor credential store — read/write ~/.guru/credentials.json (stdlib only).

The store maps org_uuid -> { token, expires_at, org_name, owner_name }. This helper
does the read/merge/write safely (chmod 600, never clobbers other orgs) so connect
doesn't hand-edit JSON.

Commands:
    creds.py get  <org_uuid>     print the live token to stdout (exit 1 if absent/expired)
    creds.py show <org_uuid>     print the full entry as JSON minus the token (exit 1 if absent)
    creds.py set  <org_uuid>     read {token,expires_at,org_name,owner_name} JSON from STDIN, merge
    creds.py list                print orgs + expiry (never tokens)

The token is passed on STDIN for `set` (never as a CLI arg) so it can't leak into
shell history or hit quoting issues. `get` prints the raw token by design — that's
its job (the caller wires it into the agent's MCP config); it stays on this machine.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

STORE = os.path.expanduser("~/.guru/credentials.json")


def _load() -> dict:
    try:
        with open(STORE, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except (ValueError, OSError):
        return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, STORE)
    os.chmod(STORE, 0o600)


def _expired(entry: dict) -> bool:
    exp = entry.get("expires_at")
    if not exp:
        return False  # no expiry recorded -> treat as live
    try:
        dt = datetime.fromisoformat(str(exp).replace("Z", "+00:00"))
    except ValueError:
        return False
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    return dt <= now


def cmd_get(org: str) -> int:
    entry = _load().get(org)
    if not entry or not entry.get("token") or _expired(entry):
        return 1
    sys.stdout.write(entry["token"])
    return 0


def cmd_show(org: str) -> int:
    entry = _load().get(org)
    if not entry:
        return 1
    redacted = {k: v for k, v in entry.items() if k != "token"}
    redacted["has_token"] = bool(entry.get("token"))
    redacted["expired"] = _expired(entry)
    print(json.dumps(redacted, indent=2))
    return 0


def cmd_set(org: str) -> int:
    try:
        incoming = json.load(sys.stdin)
    except ValueError as e:
        print(f"creds.py set: invalid JSON on stdin: {e}", file=sys.stderr)
        return 2
    if not isinstance(incoming, dict) or not incoming.get("token"):
        print("creds.py set: stdin must be a JSON object with at least a 'token'", file=sys.stderr)
        return 2
    data = _load()
    entry = data.get(org, {})
    entry.update({k: incoming[k] for k in ("token", "expires_at", "org_name", "owner_name") if k in incoming})
    data[org] = entry
    _save(data)
    print(f"stored credentials for org {org} (expires_at={entry.get('expires_at')})")
    return 0


def cmd_list() -> int:
    data = _load()
    if not data:
        print("(no stored credentials)")
        return 0
    for org, entry in data.items():
        print(f"{org}  expires_at={entry.get('expires_at')}  org_name={entry.get('org_name')}  "
              f"{'EXPIRED' if _expired(entry) else 'live'}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    cmd = argv[1]
    if cmd == "list":
        return cmd_list()
    if cmd in ("get", "show", "set"):
        if len(argv) != 3:
            print(f"creds.py {cmd}: needs <org_uuid>", file=sys.stderr)
            return 2
        return {"get": cmd_get, "show": cmd_show, "set": cmd_set}[cmd](argv[2])
    print(f"creds.py: unknown command {cmd!r}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
