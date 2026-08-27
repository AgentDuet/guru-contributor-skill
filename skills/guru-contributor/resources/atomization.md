# Atomization: turning a document into records

This is how you turn a source document into records during `ingest` and
`regenerate`. Read it before you atomize anything — it's the judgment calls, not
a file format (that's `resources/record-format.md`).

## One record, one complete thought

A record is one complete thought a reader could act on alone. Records carry no
links to each other, so a record that leans on a neighbor to make sense is
broken, not just poorly styled — treat this as a correctness bar, not a style
preference.

- When a stretch of source text covers more than one topic, split it into
  separate records — one per thought.
- When a single thought is scattered across sections, merge the pieces back
  into one record.
- When a stretch of text is too small to be a complete thought on its own —
  a fragment — don't force it into its own record: fold it into the record it
  actually belongs to, or drop it (see the skip-list below).
- Keep the source's factual wording. Atomizing is about finding the
  boundaries between thoughts, not rewriting or embellishing them — carry the
  facts over faithfully, trimming only the surrounding meta-talk (see below).

## Self-containment test

Before you finalize a record, ask: would this survive being read with nothing
else on screen? If understanding it depends on something the reader would only
know from a neighboring section, inline the minimum context it needs —
expand the acronym, name the system, restate the precondition — right there in
the record. Don't rely on the reader having read anything else.

## Subjects

Every record needs a subject: one sentence, ≤150 characters, specific enough
to distinguish it from every other record — "How we rotate DNS keys", not
"DNS". You suggest the subject during atomization; the contributor confirms
or edits it during batch review — you never derive it from the body after the
fact, and it never becomes a forced heading in the body itself. Field
mechanics (character limit, where it lives, how it's validated) are in
`resources/record-format.md`; this is only about what makes a subject good.

## What isn't knowledge (skip it, and say why)

Some of what's in a source document isn't a record candidate at all. Skip
these, and when you present the draft tree for review, tell the contributor
what you skipped and why — don't silently drop content:

- **Boilerplate** — disclaimers, headers/footers, legal filler that repeats
  across documents and carries no document-specific fact.
- **Navigation text** — tables of contents, "see section X below", breadcrumb
  trails — text whose only job is to point somewhere else in the same
  document.
- **The document's own changelog** — "v2: added section 3", revision
  histories of the document itself. This describes the document, not the
  knowledge inside it.
- **Fragments** — text too small or too incomplete to stand as a complete
  thought (see above), once you've tried to merge it into something.

## Structure: proposing collections

Propose collections that mirror the content's own organization — the source
document's own sections and headings are usually your best signal for where
the boundaries are. Prefer shallow trees over deep ones: a flatter structure
is easier for the contributor to review and easier for a reader to navigate.

**One tree per batch, never one tree per document.** When ingesting several
documents together, read ALL of them before proposing any structure, then
propose a SINGLE tree for the whole batch. Document boundaries are provenance
(`source_ref`), not structure: overlapping or related topics from different
documents share collections. Do not mirror the input folder as one
collection-per-file — atomize the combined content and let its topics, not its
filenames, draw the boundaries.

**A new root collection is a structural decision, not a filing convenience.**
A batch of related documents almost always belongs under ONE root (or inside
an existing collection the contributor names). If your draft proposes more
than one new root from a single ingest, treat that as a smell: re-examine
whether the roots are really independent subtrees, and if you keep them,
call the choice out explicitly in the tree review rather than letting it
pass silently.

The server enforces a hard cap on how deep a collection tree can go. Read the
live value from `whoami.limits.max_path_depth` every session — never hardcode
a number, the server can change it.

Extremes are a smell worth reconsidering: a collection holding a single
record probably didn't need to be its own collection; a collection holding
fifty records probably has an internal structure you haven't surfaced yet;
one root (or one collection) per source document means you atomized documents
independently instead of atomizing the batch.

## Provenance

Every record you derive from a source document carries that document's
`source_type`/`source_ref`, verbatim, so its origin is traceable. A record you
author directly, with no source document behind it, carries neither field —
there's no origin to record. This is the same provenance contract described in
`resources/record-format.md`; that's where the field mechanics and immutability
rule live. Nothing about how you propose structure or subjects changes based on
whether a record is document-derived or hand-authored.

**Exactly one `source_ref` per record — never a list.** `source_ref` is a
single origin id, and it is also the scope key the server syncs on: a
regeneration replaces records by their one `source_ref`. Never join two
filenames into one field (`"a.docx, b.docx"` is wrong) — a record stamped that
way matches neither document's regeneration scope and is stranded from sync.

**When the same thought appears in two source documents,** don't merge their
provenance. Surface the overlap in the tree review and let the contributor
choose one of:
- **Keep one, drop the other** — the record keeps the chosen document's single
  `source_ref`; the duplicate from the other document is dropped.
- **Merge the wording into one record, under one chosen primary source** — the
  contributor picks which document is the origin; the merged record carries that
  one `source_ref` only.

Either way the surviving record ends with exactly one `source_ref`. Present the
choice; never decide it silently, and never keep both origins on one record.

---

This guidance grew out of an earlier ingest-pipeline prompt for spotting one
complete thought in a source document. Only that judgment survived — the old
pipeline's structured output format, and everything it tagged onto each
extracted thought beyond a subject, is gone.
