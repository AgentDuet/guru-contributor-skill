# Record & collection marker format

This is the exact file shape the server expects. Read it before you create, edit, or
validate any record or collection marker — don't guess at field names or slug rules.

## Record file

A record is one Markdown file: YAML front-matter, a closing `---`, then the body.

### Front-matter fields

Five fields, no more — the server rejects (`schema_error`) any key outside this set:

- **`stable_id`** — the record's identity, minted by the server. Absent on a record you
  just authored and have never pushed; present once the server has accepted it at least
  once. Shape: `rec_` + 8 lowercase hex chars (collections likewise: `col_` + 8 hex) —
  opaque and never derived from content. Never invent one yourself.
- **`subject`** — the record's one-line thought, ≤150 characters. You author this (the
  atomization step suggests it, the contributor confirms it in batch review); the server
  never derives it from the body.
- **`owner_uuid`** — the identity that pushed the record. The server stamps this from the
  authenticated caller at push time. Before a push, you never *invent* one by hand — it's
  simply absent on a record you haven't pushed yet. After an accepted push, the push
  workflow has you stamp it into the front-matter yourself, from that session's
  `whoami.identity_uuid` (see the push workflow in `SKILL.md`) — that's not inventing a
  value, it's copying back the value the server just told you it used. `owner_uuid` in
  front-matter and `whoami`'s `identity_uuid` are a different label for the same fact, not
  two different concepts: the pushing identity's `identity_uuid`, carried into the record
  as its owner.
- **`source_type`** — present only on a document-derived record: the raw origin kind
  (e.g. `pdf`, `git`). Absent on a hand-authored record — there is no origin to record.
- **`source_ref`** — present only alongside `source_type`: the origin's id (e.g. the
  source filename or doc id). Exactly ONE origin — a single value, never a list or a
  comma-joined pair of filenames; it doubles as the scope key regeneration syncs on, so
  a record with two origins jammed in matches neither and falls out of sync. A thought
  that appears in two documents keeps one chosen primary `source_ref` (see the overlap
  rule in `resources/atomization.md`). Once the server has stamped
  `source_type`/`source_ref` on a record, they're immutable — pushing a change to either
  is rejected (`source_origin_immutable`). If a record didn't come from a document,
  leave both fields out entirely; don't write them as empty or null.

### Body

Everything below the closing `---` is pure content:

- No forced H1 restating the subject — the subject already lives in front-matter.
- No links to other records. Every record must stand alone; a reader who opens only this
  file must get the complete thought with nothing to follow elsewhere.
- The server's `content_hash` for a record is the lowercase-hex SHA-256 digest of the
  body's UTF-8 bytes — everything below the closing `---`, nothing from front-matter.

### Full example

A document-derived record, already pushed once (so `stable_id` and `owner_uuid` are
stamped):

```markdown
---
stable_id: rec_4f9a21bc
subject: Call recordings require prior consent under state wiretap law
owner_uuid: 8f14e45f-ceea-467e-adc3-b9d1a1c2e4a0
source_type: pdf
source_ref: Acceptable-Use-Policy.pdf
---
Before recording a customer call, obtain and log affirmative consent from every
participant in states that require two-party consent. Consent must be captured at
call start, not inferred from continued participation, and the log entry must include
the participant's identity and timestamp.
```

Before its first push, the same record has only the fields you can actually know yet —
`stable_id` and `owner_uuid` are simply absent (not blank, not null: omitted):

```markdown
---
subject: Call recordings require prior consent under state wiretap law
source_type: pdf
source_ref: Acceptable-Use-Policy.pdf
---
Before recording a customer call, obtain and log affirmative consent from every
participant in states that require two-party consent. Consent must be captured at
call start, not inferred from continued participation, and the log entry must include
the participant's identity and timestamp.
```

A hand-authored record never carries `source_type`/`source_ref` at all, pushed or not:

```markdown
---
subject: New laptops must be enrolled in MDM before first login
---
Every laptop issued to a new hire must be enrolled in the MDM profile before the
employee's first login. IT enrolls the device during provisioning; the employee never
performs enrollment themselves.
```

## Filename

The filename is the subject's slug plus `.md` (kebab-case, uniquified on collision) —
`call-recording-consent.md`. It's a display label only:

- Identity NEVER lives in the filename. A record's identity is `stable_id` in its
  front-matter, full stop.
- When the authored subject changes, rename the file to match — but if a rename ever
  leaves the filename and the front-matter's identity disagreeing about anything, the
  front-matter wins. The filename is cosmetic; the header is truth.

## `.collection` marker

Every directory that is a collection holds exactly one `.collection` file: a small JSON
marker, not front-matter, not Markdown.

```json
{ "collection_id": "col_3f9a1c2e", "name": "Compliance Policies" }
```

- **`collection_id`** — server-stamped once the collection has been pushed at least
  once. Absent before that first push, same rule as a record's `stable_id`.
- **`name`** — the authored display name for the collection. This is independent of the
  directory name — the directory name is the collection's *slug*, `name` is its
  human-readable label. Renaming the directory does not change `name`, and vice versa.

The marker is what makes a directory rename identity-preserving: as long as the marker's
`collection_id` survives, the collection is the same collection no matter what the
directory is called.

## Slug & path rules

Every path segment — a directory name in the worktree, standing in for a collection slug
— must match this grammar exactly (the server's path grammar, identical on both sides):

```
^[a-z0-9][a-z0-9-]{0,119}$
```

Lowercase letters, digits, and hyphens only; must start with a letter or digit; max 120
characters. No uppercase, no spaces, no underscores, no leading hyphen. A segment that
fails this grammar — or a path that's empty, or starts/ends with `/`, or has an empty
segment from a double slash — is rejected as `bad_placement_path`.

A record's **path** is the `/`-joined chain of its ancestor collections' slugs, from a
root collection down to (not including) the record's own filename — e.g. a record filed
in `compliance/call-recording/` has path `compliance/call-recording`. Every record file
lives inside at least one collection directory: a record placed at the worktree root has
no ancestor collection, so its path is empty, and an empty path is rejected the same way,
`bad_placement_path`.

**Max depth** = `whoami.limits.max_path_depth` (server default today: 3) — read it fresh
each session from `whoami`, never hardcode it. A path with more segments than the limit
allows is rejected the same way, `bad_placement_path`.

## Example worktree

Two collections, three records, one hand-authored:

```
worktree/
  compliance/
    .collection              # { "collection_id": "col_3f9a1c2e", "name": "Compliance Policies" }
    call-recording-consent.md   # source_type/source_ref: Acceptable-Use-Policy.pdf
    consent-controls.md         # source_type/source_ref: Acceptable-Use-Policy.pdf
  onboarding/
    .collection              # { "collection_id": "col_a17d40b9", "name": "Onboarding" }
    laptop-setup.md             # hand-authored — no source_type, no source_ref
```

`call-recording-consent.md` and `consent-controls.md` both came from the same source
document, so both carry the same `source_ref`; regenerating that document resubmits both
under one `replace_scope`. `laptop-setup.md` has no source fields at all — it was
authored directly, not derived from a document, so there's no origin to track.
