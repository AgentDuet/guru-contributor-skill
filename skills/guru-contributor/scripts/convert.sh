#!/usr/bin/env sh
# Convert an Office document to plain text WITHOUT python — macOS / Linux fallback.
# Prefer convert.py when python3 exists; use this only when it doesn't.
#
# Usage: sh convert.sh <input-file>   (text -> stdout)
# Tries, in order: pandoc -> textutil(macOS, docx) -> unzip+strip-tags.
# Exit: 0 ok, 2 unsupported/missing, 3 no usable converter.
set -eu

in="${1:-}"
[ -n "$in" ] && [ -f "$in" ] || { echo "convert.sh: file not found: $in" >&2; exit 2; }
ext=$(printf '%s' "${in##*.}" | tr '[:upper:]' '[:lower:]')
case "$ext" in docx|pptx|xlsx) : ;; *) echo "convert.sh: unsupported .$ext" >&2; exit 2 ;; esac

# 1. pandoc handles all three cleanly if present.
if command -v pandoc >/dev/null 2>&1; then
  pandoc "$in" -t plain 2>/dev/null && exit 0 || true
fi

# 2. macOS textutil (docx/older Office formats).
if [ "$ext" = docx ] && command -v textutil >/dev/null 2>&1; then
  textutil -convert txt -stdout "$in" 2>/dev/null && exit 0 || true
fi

# 3. Last resort: unzip the parts and strip XML tags (loses layout; words survive).
command -v unzip >/dev/null 2>&1 || { echo "convert.sh: need pandoc, textutil, or unzip" >&2; exit 3; }
strip() { sed -e 's/<[^>]*>/ /g' -e 's/&amp;/\&/g' -e 's/&lt;/</g' -e 's/&gt;/>/g' -e 's/[[:space:]]\{2,\}/ /g'; }
case "$ext" in
  docx) unzip -p "$in" word/document.xml 2>/dev/null | strip ;;
  pptx) for s in $(unzip -Z1 "$in" 2>/dev/null | grep '^ppt/slides/slide.*\.xml$' | sort); do
          unzip -p "$in" "$s" 2>/dev/null | strip; echo; done ;;
  xlsx) unzip -p "$in" xl/sharedStrings.xml 2>/dev/null | strip ;;
esac
