#!/usr/bin/env python3
"""Generate worktree files (records + .collection markers) from a spec — stdlib only.

Usage:
    python3 gen_records.py <spec.json> [worktree-dir]

The spec is read from a FILE (write it with your editor/agent file tools — never
pass record bodies as shell args; that's the quoting trap this avoids). Writes each
collection directory + its `.collection` marker and each record `.md` with valid
front-matter, under <worktree-dir> (default: current dir). Prints what it wrote.

Spec shape:
{
  "collections": [
    { "path": "compliance", "name": "Compliance Policies", "collection_id": "col_..."(optional) }
  ],
  "records": [
    { "path": "compliance",                     # collection dir chain ("" = root, rejected by server)
      "subject": "one-line thought <=150 chars",
      "body": "the full standalone content",
      "source_type": "pdf"(optional), "source_ref": "file.pdf"(optional, single),
      "stable_id": "rec_..."(optional), "owner_uuid": "..."(optional),
      "filename": "custom-slug"(optional; else slugified from subject) }
  ]
}

Only fields actually present are emitted (never blank/null). Front-matter order is
fixed: stable_id, subject, owner_uuid, source_type, source_ref (record-format.md).
"""
from __future__ import annotations

import json
import os
import re
import sys

_SLUG_OK = re.compile(r"^[a-z0-9][a-z0-9-]{0,119}$")
_FM_ORDER = ["stable_id", "subject", "owner_uuid", "source_type", "source_ref"]


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    s = re.sub(r"-{2,}", "-", s)[:120].strip("-")
    return s or "record"


def _yaml_scalar(v: str) -> str:
    """Emit a YAML-safe scalar. Plain when safe, double-quoted+escaped otherwise."""
    s = str(v)
    plain_safe = (
        s != "" and s == s.strip()
        and not re.search(r'[:#\[\]{}&*!|>\'"%@`,]', s)
        and not s.startswith(("- ", "? "))
        and s.lower() not in ("true", "false", "null", "yes", "no", "~")
    )
    if plain_safe:
        return s
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _front_matter(rec: dict) -> str:
    lines = ["---"]
    for key in _FM_ORDER:
        if key in rec and rec[key] not in (None, ""):
            lines.append(f"{key}: {_yaml_scalar(rec[key])}")
    lines.append("---")
    return "\n".join(lines)


def _validate_path(path: str) -> list[str]:
    segs = [p for p in (path or "").split("/") if p != ""]
    for seg in segs:
        if not _SLUG_OK.match(seg):
            raise SystemExit(f"gen_records.py: bad path segment {seg!r} in {path!r} "
                             f"(must match {_SLUG_OK.pattern})")
    return segs


def main(argv: list[str]) -> int:
    if not (2 <= len(argv) <= 3):
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as f:
        spec = json.load(f)
    base = os.path.abspath(argv[2]) if len(argv) == 3 else os.getcwd()

    written = []
    for col in spec.get("collections", []):
        segs = _validate_path(col.get("path", ""))
        d = os.path.join(base, *segs)
        os.makedirs(d, exist_ok=True)
        marker = {}
        if col.get("collection_id"):
            marker["collection_id"] = col["collection_id"]
        marker["name"] = col.get("name") or (segs[-1] if segs else "")
        with open(os.path.join(d, ".collection"), "w", encoding="utf-8") as fh:
            json.dump(marker, fh)
        written.append(os.path.join(*segs, ".collection"))

    used: set[str] = set()
    for rec in spec.get("records", []):
        if not rec.get("subject"):
            raise SystemExit("gen_records.py: every record needs a 'subject'")
        segs = _validate_path(rec.get("path", ""))
        d = os.path.join(base, *segs)
        os.makedirs(d, exist_ok=True)
        stem = rec.get("filename") or slugify(rec["subject"])
        name, n = stem, 2
        while os.path.join(d, name + ".md") in used or os.path.exists(os.path.join(d, name + ".md")):
            name, n = f"{stem}-{n}", n + 1
        used.add(os.path.join(d, name + ".md"))
        body = rec.get("body", "")
        content = _front_matter(rec) + "\n" + (body if body.endswith("\n") or body == "" else body + "\n")
        fp = os.path.join(d, name + ".md")
        with open(fp, "w", encoding="utf-8") as fh:
            fh.write(content)
        written.append(os.path.join(*segs, name + ".md") if segs else name + ".md")

    for w in written:
        print(w)
    print(f"gen_records.py: wrote {len(written)} file(s) under {base}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
