#!/usr/bin/env python3
"""Guru contributor MCP client helper — for hosts without a native MCP harness
(stdlib only).

Some agent hosts cannot register a streamable-HTTP MCP server with custom auth
headers (or improvise raw HTTP when their MCP support is weak). This helper is
the ONE tested client for those hosts: it speaks the MCP handshake
(initialize -> initialized -> request), carries the `mcp-session-id`, injects
the auth headers from the credential store, and parses both JSON and SSE
response framings. On hosts WITH working native MCP tools, use those — this
script is the fallback, not a replacement.

Commands:
    mcp.py tools <ba_uid> <env_mcp_url>
        List the server's tools: prints {"tools": [{name, description,
        inputSchema}, ...]}.

    mcp.py call <tool_name> <ba_uid> <env_mcp_url>
        Call one tool. Arguments are a JSON object on STDIN (empty stdin = {})
        — never CLI args (quoting breaks). Prints the tool result:
        structuredContent when the server provides it, otherwise the text
        content blocks. Exit 0 on success, 1 on a tool/protocol error.

Credentials come from the token store (~/.guru/credentials.json) — run the
connect ceremony (scripts/auth.py) first. A 401 here means the bearer expired:
re-run the ceremony, don't retry blindly.
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

import creds  # sibling module — the credential store

_PROTOCOL_VERSION = "2025-03-26"
_TIMEOUT_S = 120


class McpError(Exception):
    pass


def _auth_headers(ba_uid: str) -> dict:
    entry = creds._load().get(ba_uid)
    if not entry or not entry.get("token") or creds._expired(entry):
        raise McpError(
            f"no live token for workspace {ba_uid} — run the connect ceremony "
            "(scripts/auth.py request + exchange) first"
        )
    routing_org = entry.get("routing_org")
    if not routing_org:
        raise McpError(
            f"stored credential for {ba_uid} has no routing_org — re-run connect "
            "(exchange) to record it"
        )
    return {
        "Authorization": f"Bearer {entry['token']}",
        # ROUTING only — the env's routing org-uuid recorded at exchange, NOT the
        # ba_uid (a tenant id is not a routable org and fails at the gateway).
        "x-user-org-uuid": routing_org,
    }


def _parse_response(raw: bytes, content_type: str) -> dict:
    """FastMCP streamable-http answers a POST either as plain JSON or as an
    SSE stream whose `data:` lines carry the JSON-RPC messages. Return the
    LAST data payload (the response; earlier ones are progress/log events)."""
    if "text/event-stream" in content_type:
        last = None
        for line in raw.decode("utf-8", "replace").splitlines():
            if line.startswith("data:"):
                candidate = line[len("data:"):].strip()
                if candidate:
                    last = candidate
        if last is None:
            raise McpError("SSE response carried no data payload")
        return json.loads(last)
    return json.loads(raw)


class Session:
    """One MCP session per invocation: initialize -> initialized -> use.
    Best-effort DELETE on close so the server can reap the session."""

    def __init__(self, url: str, ba_uid: str) -> None:
        self._url = url.rstrip("/")
        self._headers = _auth_headers(ba_uid)
        self._session_id: str | None = None
        self._next_id = 1

    def _post(self, payload: dict, *, expect_response: bool) -> dict | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **self._headers,
        }
        if self._session_id:
            headers["mcp-session-id"] = self._session_id
        req = urllib.request.Request(
            self._url, data=json.dumps(payload).encode("utf-8"),
            headers=headers, method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
                sid = resp.headers.get("mcp-session-id")
                if sid:
                    self._session_id = sid
                if not expect_response:
                    resp.read()
                    return None
                return _parse_response(resp.read(), resp.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise McpError(
                    "401 unauthorized — the bearer likely expired; re-run the "
                    "connect ceremony (scripts/auth.py)"
                ) from e
            body = e.read()[:300].decode("utf-8", "replace")
            raise McpError(f"HTTP {e.code} from MCP endpoint: {body}") from e
        except (urllib.error.URLError, OSError, TimeoutError) as e:
            raise McpError(f"MCP endpoint unreachable: {e}") from e

    def _rpc(self, method: str, params: dict | None = None) -> dict:
        payload = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        self._next_id += 1
        if params is not None:
            payload["params"] = params
        msg = self._post(payload, expect_response=True)
        if msg is None or msg.get("id") is None and "error" not in msg:
            raise McpError(f"no JSON-RPC response for {method}")
        if "error" in msg:
            raise McpError(f"{method} failed: {json.dumps(msg['error'])}")
        return msg.get("result", {})

    def open(self) -> None:
        self._rpc("initialize", {
            "protocolVersion": _PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "guru-contributor-mcp-helper", "version": "1.0"},
        })
        self._post({"jsonrpc": "2.0", "method": "notifications/initialized"},
                   expect_response=False)

    def close(self) -> None:
        if not self._session_id:
            return
        req = urllib.request.Request(
            self._url, headers={**self._headers, "mcp-session-id": self._session_id},
            method="DELETE",
        )
        try:
            urllib.request.urlopen(req, timeout=10).read()
        except Exception:
            pass  # reaping is the server's problem; never fail the command on it

    def tools(self) -> dict:
        result = self._rpc("tools/list")
        return {"tools": [
            {"name": t.get("name"), "description": t.get("description"),
             "inputSchema": t.get("inputSchema")}
            for t in result.get("tools", [])
        ]}

    def call(self, name: str, arguments: dict) -> tuple[dict | list | str, bool]:
        result = self._rpc("tools/call", {"name": name, "arguments": arguments})
        is_error = bool(result.get("isError"))
        structured = result.get("structuredContent")
        if structured is not None:
            return structured, is_error
        texts = [c.get("text", "") for c in result.get("content", [])
                 if c.get("type") == "text"]
        joined = "\n".join(t for t in texts if t)
        # Tool results are often JSON serialized into a text block — surface
        # the object itself when it parses, so callers get one shape.
        try:
            return json.loads(joined), is_error
        except ValueError:
            return joined, is_error


def cmd_tools(ba_uid: str, url: str) -> int:
    s = Session(url, ba_uid)
    s.open()
    try:
        print(json.dumps(s.tools(), indent=2))
        return 0
    finally:
        s.close()


def cmd_call(tool: str, ba_uid: str, url: str) -> int:
    stdin = sys.stdin.read().strip()
    try:
        arguments = json.loads(stdin) if stdin else {}
    except ValueError as e:
        print(f"mcp.py call: stdin must be a JSON object of arguments: {e}", file=sys.stderr)
        return 2
    if not isinstance(arguments, dict):
        print("mcp.py call: stdin JSON must be an object", file=sys.stderr)
        return 2
    s = Session(url, ba_uid)
    s.open()
    try:
        result, is_error = s.call(tool, arguments)
        print(result if isinstance(result, str) else json.dumps(result, indent=2))
        return 1 if is_error else 0
    finally:
        s.close()


def main(argv: list[str]) -> int:
    try:
        if len(argv) >= 2 and argv[1] == "tools" and len(argv) == 4:
            return cmd_tools(argv[2], argv[3])
        if len(argv) >= 2 and argv[1] == "call" and len(argv) == 5:
            return cmd_call(argv[2], argv[3], argv[4])
    except McpError as e:
        print(f"mcp.py: {e}", file=sys.stderr)
        return 1
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
