# The floor: pre-validation + verdict repair

The server runs a deterministic set of checks on everything you push — no LLM judgment,
no content-quality opinion, just structural gates. Run the same checks locally before you
call `push_records`/`push_collections`: a batch that would fail on the server fails the
same way here, and you find out without burning a round-trip.

## Pre-push checklist

Before calling `push_records`, confirm for every file in the batch:

- It parses as YAML front-matter, a closing `---`, then a body. A file that doesn't
  decode at all, or whose front-matter fails the record schema, never reaches the size or
  path checks — fix decode/schema problems first.
- Front-matter has no keys outside the five-field set (`resources/record-format.md`) —
  fields that don't apply yet (e.g. `stable_id`/`owner_uuid` on a record's first-ever
  push) are simply omitted, not present-but-empty. See `resources/record-format.md` for
  which fields exist at which point in a record's life.
- Body byte length falls within `[limits.min_record_bytes, limits.max_record_bytes]`.
  This window bounds the **body only** — everything below the closing `---` — which is
  also exactly what `content_hash` is computed over. Separately, the server rejects a
  grossly oversized **raw file** (front-matter + body together) before it ever tries to
  parse the front-matter, so don't let a bloated front-matter blob smuggle a file past
  that gate either — keep the whole file lean, not just the body.
- Every path segment matches the slug grammar (`resources/record-format.md`) and the
  path's depth is `<= limits.max_path_depth`.
- The batch is `<= limits.max_records_per_push` records and touches
  `<= limits.max_collections_per_push` distinct collection paths. Chunk a larger push
  instead of sending it all at once.
- No two records in the same batch declare the same `stable_id`.
- No record edits `source_type` or `source_ref` on an id that's already been pushed once
  — those fields are frozen the moment the server first stamps them.

Read `limits` fresh from `whoami` every session; never hardcode any of these numbers.

## Verdict table

Every `push_records`/`push_collections` result carries one of these. On a rejection,
repair per the `Agent action` column, run the edited files back through the same tree
review surface used for authoring (edits flagged, not a silent auto-repush), then
re-push. Content-quality judgment never comes from the server — these codes are all
format/structure, and repair happens in review, where the author lives.

| Verdict/code | Meaning | Agent action |
|---|---|---|
| `accepted` (+`warnings[]`) | landed; id in the result | stamp `record_id` into front-matter |
| `noop` | byte-identical body already stored | nothing |
| `decode_error` / `schema_error` | malformed file / front-matter | fix format locally |
| `too_small` / `too_large` | body outside the size window | merge fragments / split the dump |
| `bad_placement_path` | illegal slug, depth, or unresolvable/cyclic path | rename/re-place, re-check limits |
| `duplicate_of` (+id) | byte-identical record exists elsewhere | drop yours or merge into the existing id |
| `source_origin_immutable` | tried to change stamped provenance | restore the original `source_type`/`source_ref` |
| `unknown_stable_id` | id not found in this org | drop the stale id (server re-matches by content hash) or treat as new |
| `scope_mismatch` | record's `source_ref` != `replace_scope` | remove from batch or fix `source_ref` |
| `missing_name` | collection item without a name | supply the display name |
| `unknown_collection_id` | given `collection_id` not found in this org | drop the stale id and push by path instead, or confirm the id via `list_collections` |
| `bad_batch` | cap breach / in-batch id collision | chunk the batch / dedupe ids |

Other non-blocking warnings you may see on an otherwise-`accepted` record:
`hand_edit_clobbered` — this push overwrote a record whose last write came from the
Publisher UI. It fires on **any** update push that lands on such a record, not only
during **regenerate**'s source-doc sweep — nothing to repair, it's informational, but
don't assume it only ever shows up mid-regeneration. `collection_autocreated` — a
collection in the path didn't exist yet and was auto-created (informational only).

## Warnings + sweep semantics

`push_records` with `replace_scope=<source_ref>` makes the push authoritative for that
scope: any existing record in that scope untouched by the batch is deleted once the push
lands clean.

If **any** record in the batch is rejected — any code, `scope_mismatch` included — the
deletion sweep is skipped entirely for that push: a batch containing a rejection can't be
trusted as the complete set for the scope, so nothing gets deleted. Every accepted verdict
in that same push instead carries a non-blocking `scope_sweep_skipped` warning. Fix the
rejected record(s) and re-push the complete, clean batch to actually trigger the
deletions — a partial re-push of just the fixed record(s) won't do it, since the sweep
needs the whole scope present in one clean call.

## Error envelopes

A tool call can return one of these instead of a normal result — check for `error` before
reading `records`/`collections`:

| `error` | Meaning | Agent action |
|---|---|---|
| `auth_error` | the credential/config behind this MCP call needs attention | tell the contributor their MCP credential/config needs fixing; never ask them to paste a key into the conversation, and never echo one back |
| `org_not_enabled` (HTTP 403) | the org was disabled for contribution after the token was issued (the token itself is still valid) | stop; tell the contributor their organization's contribution access has been turned off and to contact their admin — retrying won't help until it's re-enabled |
| `bad_batch` | this whole call (not one item) exceeded a cap, e.g. too many ids in one `delete_records`/`get_records` | chunk the call and retry |
| `bad_cursor` | a `list_records` cursor wasn't a value the server handed back (treat cursors as opaque; always pass one through unmodified) | drop the cursor and restart pagination from the top |
| `internal_error` | server-side failure | retry once; if it fails again, surface it to the contributor rather than looping |
| `rate_limited` | too many requests for this email, or from this network address, in the current window (surfaced by `/public/v1/auth/request` during the **connect** ceremony, not by the MCP tools above) | stop and tell the contributor to wait before retrying; don't call `request` again immediately — see the **connect** ceremony's shape list in SKILL.md |
