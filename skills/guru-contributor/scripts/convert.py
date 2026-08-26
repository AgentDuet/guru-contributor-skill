#!/usr/bin/env python3
"""Convert an Office document (.docx / .pptx / .xlsx) to plain text — stdlib only.

Usage:
    python3 convert.py <input-file> [output-file]

Prints the extracted text to stdout (or writes <output-file> if given). Layout is
not preserved — atomization needs the words, not the formatting. No pip installs:
Office files are ZIPs of XML, parsed with the standard library.

Exit codes: 0 ok · 2 unsupported/missing file · 3 parse error. On failure the
reason goes to stderr, so the caller can fall back (convert.sh / .ps1 / Save-As).
"""
from __future__ import annotations

import sys
import zipfile
from xml.etree import ElementTree as ET


def _local(tag: str) -> str:
    """Strip the XML namespace: '{ns}tag' -> 'tag'."""
    return tag.rsplit("}", 1)[-1]


def _text_of(elem) -> str:
    """All descendant <t> text (docx/pptx share the <t> convention)."""
    return "".join(n.text or "" for n in elem.iter() if _local(n.tag) == "t")


def _docx(z: zipfile.ZipFile) -> str:
    root = ET.fromstring(z.read("word/document.xml"))
    lines = []
    for p in root.iter():
        if _local(p.tag) == "p":          # one paragraph per line
            lines.append(_text_of(p))
    return "\n".join(lines)


def _pptx(z: zipfile.ZipFile) -> str:
    slides = sorted(
        (n for n in z.namelist()
         if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
        key=lambda n: int("".join(c for c in n if c.isdigit()) or 0),
    )
    out = []
    for i, name in enumerate(slides, 1):
        root = ET.fromstring(z.read(name))
        paras = [_text_of(p) for p in root.iter() if _local(p.tag) == "p"]
        body = "\n".join(x for x in paras if x.strip())
        out.append(f"--- Slide {i} ---\n{body}" if body else f"--- Slide {i} ---")
    return "\n\n".join(out)


def _xlsx(z: zipfile.ZipFile) -> str:
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sroot = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in sroot:
            shared.append("".join(t.text or "" for t in si.iter() if _local(t.tag) == "t"))
    sheets = sorted(
        (n for n in z.namelist()
         if n.startswith("xl/worksheets/sheet") and n.endswith(".xml")),
        key=lambda n: int("".join(c for c in n if c.isdigit()) or 0),
    )
    out = []
    for si, name in enumerate(sheets, 1):
        root = ET.fromstring(z.read(name))
        rows = []
        for row in (r for r in root.iter() if _local(r.tag) == "row"):
            cells = []
            for c in (x for x in row if _local(x.tag) == "c"):
                v = next((e for e in c if _local(e.tag) == "v"), None)
                is_val = next((e for e in c if _local(e.tag) == "is"), None)
                if c.get("t") == "s" and v is not None and v.text is not None:
                    idx = int(v.text)
                    cells.append(shared[idx] if 0 <= idx < len(shared) else "")
                elif is_val is not None:
                    cells.append("".join(t.text or "" for t in is_val.iter() if _local(t.tag) == "t"))
                elif v is not None:
                    cells.append(v.text or "")
                else:
                    cells.append("")
            rows.append("\t".join(cells))
        body = "\n".join(rows)
        out.append(f"--- Sheet {si} ---\n{body}" if body else f"--- Sheet {si} ---")
    return "\n\n".join(out)


_HANDLERS = {"docx": _docx, "pptx": _pptx, "xlsx": _xlsx}


def convert(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    handler = _HANDLERS.get(ext)
    if handler is None:
        print(f"convert.py: unsupported extension .{ext} (want docx/pptx/xlsx)", file=sys.stderr)
        sys.exit(2)
    try:
        with zipfile.ZipFile(path) as z:
            return handler(z)
    except FileNotFoundError:
        print(f"convert.py: file not found: {path}", file=sys.stderr)
        sys.exit(2)
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        print(f"convert.py: could not parse {path}: {e}", file=sys.stderr)
        sys.exit(3)


def main(argv: list[str]) -> int:
    if not (2 <= len(argv) <= 3):
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)  # the Usage line
        return 2
    text = convert(argv[1])
    if len(argv) == 3:
        with open(argv[2], "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
