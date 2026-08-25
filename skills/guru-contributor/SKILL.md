---
name: guru-contributor
description: Contribute knowledge to the libra KB. Atomize documents into records in a local worktree, review as a batch, push through the libra MCP tools. Use when the user wants to add, update, regenerate, or sync knowledge records with the libra library.
---

## Vocabulary

Use these two words exactly as defined, and no others, when you talk about libra
knowledge:

- **record** — the atomic unit of knowledge: one complete thought.
- **collection** — a folder in the knowledge tree that holds records (and nested
  collections).

Two more words describe *actions*, and you must not blur them:

- **push** — submitting your work to the libra server through the libra MCP tools.
  This is the only "remote" that exists in this system.
- **commit** — a local git checkpoint inside your worktree. It never leaves your
  machine and the server never sees it.

The worktree's local git repository has **no origin, by design**. Do not run `git
push` inside it — there is no remote configured, so it has nowhere to go. If you
reach for `git push` out of habit, stop: the action you want is push-via-MCP (see
Session start / Workflows), not a git push.

## Principles

Follow these four rules on every task in this skill:

1. **Propose everything, interrogate nothing.** Always produce a complete draft
   before asking the contributor anything. Every record gets a suggested subject;
   every collection gets a suggested name. Never block on a clarifying question when
   you could instead draft your best guess and let the contributor correct it. You
   present the contributor a tree to review, not a questionnaire: silence on any
   given record means they accept it as drafted; you only need one confirmation for
   the whole batch before you push.
2. **The worktree is canonical and self-describing.** Never invent side-state (a
   separate tracking file, a database, your own notes) to remember what a record or
   collection is — identity, subject, and provenance live in the files themselves
   (front-matter and collection markers). Read them back from the files, not from
   memory of what you wrote.
3. **The MCP surface is the only door.** Nothing you do in the worktree reaches the
   server except an explicit push through the libra MCP tools. Do not try to sync,
   mirror, or publish the worktree any other way.
4. **Every destructive state is one revert away — when git is available.** With
   git, you commit locally at each checkpoint, so a bad regeneration, review
   edit, or structural experiment is always recoverable with `git revert` or
   `git reset` — no server involvement needed; commit often so this stays true.
   Without git (see the Git section), there is no local undo — make a `.bak`
   copy before any risky rewrite and tell the contributor the safety net is
   reduced.

## The worktree

Your worktree is a directory where each directory is a collection and each file
is a record; identity and provenance live in front-matter and collection
markers, not in filenames or any external store. Read `resources/record-format.md`
before you create or edit any record or collection marker — it defines the exact
file shape the server expects. When `git` is available (see below) the worktree
is also a local git repo, which adds checkpoints and undo — but git is not
required to contribute.

## Git — recommended, not required

Git powers the worktree's **local safety net**: checkpoint commits and undo
(`git revert`/`git reset`). It is **not** required to contribute — the core path
(author files → push via MCP) works without it. On the FIRST session (and in
`init`), run `git --version` and handle three cases:

1. **git present** → full mode: the worktree is a git repo, you commit at each
   checkpoint, and any bad state is one revert away. Proceed normally.
2. **git missing** → tell the contributor plainly, then:
   - **Recommend they install it themselves** — the best option: one-time,
     machine-wide, no admin questions for you to handle.
   - **Offer to install it for them, ONLY if they say yes.** Installing system
     software changes their machine and may need admin — never do it silently.
     On an explicit yes, detect OS + package manager and run the exact command;
     never assume `sudo` without telling them:
     - macOS: `brew install git` (or `xcode-select --install`)
     - Debian/Ubuntu: `sudo apt-get install -y git`
     - Fedora/RHEL: `sudo dnf install -y git`
     - Windows: `winget install --id Git.Git` (or `choco install git` /
       `scoop install git`)
   - **If they decline both → no-git mode.** State the trade-off (below) and
     continue — never dead-end on a missing git.
3. **no-git mode trade-off** (say it, don't bury it):
   - **Lost:** local checkpoints and local undo — a bad regeneration or review
     edit **can't be rolled back** with git.
   - **Still works:** authoring, review, **push via MCP**, reading records back
     (identity/provenance live in the files), and the **server keeps its own
     history** of what you push.
   - **Safety substitute:** before any risky local rewrite or regeneration,
     copy the file to `<name>.bak` first so you can restore it by hand.
   - Suggest installing git later for the full safety net.

## Session start

Before doing anything else in a session, call the `whoami` MCP tool. It returns:

```
{ org_name, org_uuid, identity_uuid, owner_name, limits }
```

### Org confirmation — MANDATORY, no exception

Contributions are org-scoped and irreversible-ish (they land in a real shared
knowledge base). A contributor working across several orgs/environments can
easily have the wrong one active. So **before any contribution action in a
session — push_records, push_collections, delete_records, or an edit — you MUST
show the contributor the active org and get an explicit yes/no confirmation.**

Show it plainly, name first (a UUID is not something a human can eyeball):

```
You are connected to:  <org_name>   (<org_uuid>)
Contributing as:       <owner_name>
Proceed with this organization? (yes / no)
```

Rules, no exceptions:
- Do this once per session, at the start (or immediately after a **connect** /
  org switch), and always before the first write.
- Require an explicit **yes**. Silence, "go ahead with the task", or any
  instruction that isn't a clear yes to *this* question does NOT count — ask
  again. Read-only calls (whoami, list_*, get_records) are fine before the
  confirm; nothing that writes is.
- On **no**: stop. Do not push anything. Offer **connect** to switch org, or
  end. Never proceed to a write on an unconfirmed org.
- If `org_name` equals `org_uuid` (the server couldn't resolve a display name),
  say so explicitly and still require the yes/no — do not pretend you have a
  friendly name you don't.

### Limits

Treat `limits` as live server configuration, not a constant — read it fresh each
session and use its values directly instead of hardcoding numbers. It carries:

- `max_path_depth`
- `min_record_bytes`
- `max_record_bytes`
- `max_records_per_push`
- `max_collections_per_push`

Never hardcode any of these; the server can change them at any time.

If `whoami` is absent or fails outright, the libra MCP tools aren't reachable
in this session yet — run **connect** (below) before anything else in this
skill. (After connect succeeds, run the org confirmation above before writing.)

## Workflows

Call `whoami` once at session start (see Session start above) before any of these —
every workflow below reads `limits` from that call, never a hardcoded number.
**connect** is the one exception: it's what you run precisely when `whoami`
doesn't work yet.

**connect** — Register (or switch) the libra MCP server itself. This is what
session start hands you off to when the libra tools aren't reachable, and it's
also the answer whenever the contributor asks to connect or switch
environments.

1. Read `resources/environments.md` and pick the endpoint:
   - Exactly ONE concrete (non-placeholder) environment listed → **use it, no
     confirmation** — just tell the contributor which endpoint you're connecting
     to as you proceed.
   - Several listed → ask which one.
   - Empty, all placeholders, or the contributor's environment isn't listed →
     ask them for the URL directly. Never guess or invent one.
2. Check for an existing `libra` registration. If one exists, show its current
   URL and offer keep or switch; switch means rewriting that entry with the
   new URL, nothing more.
3. Ensure a live token for the target org, via the local **token store** — so
   the contributor logs in once *per org*, not once per folder:
   - The store is `~/.guru/credentials.json` (`chmod 600` — it holds secrets).
     Shape: a map `org_uuid -> { token, expires_at, org_name, owner_name }`.
   - Look up the target org. If it has a token whose `expires_at` is still in
     the future, **reuse it** — no ceremony, no re-login. This is what makes
     the same org work across folders and lets you switch between already-known
     orgs login-free.
   - Otherwise run the **ceremony** (below) to mint one, then save it to the
     store under that org_uuid (`chmod 600`). Never store a token anywhere else
     in plaintext, never echo it.
4. Register the server for the host you're running in, using the token from
   step 3. **First determine the host** — Claude Code CLI, Antigravity (agy,
   CLI or desktop), Claude Cowork (the Claude desktop app), or another
   Agent-Skills agent — and pick the matching target below; if you can't tell,
   ask the contributor. State exactly what you're about to write first — the
   permission prompt on the write IS the consent gate; connect never registers
   silently. Each target ends with a reload the contributor must perform (see
   step 5) — the config never hot-loads.

   **Claude Code (CLI) — two modes; ask which, default global:**
   - *Global* (the comfortable default for a one-org contributor): a
     **user-scoped** `.mcp.json` with env-var references, plus the two env vars
     set from the store:
     ```json
     { "mcpServers": { "libra": { "type": "http", "url": "<env-url>",
       "headers": { "Authorization": "Bearer ${LIBRA_CONTRIB_KEY}",
                    "x-user-org-uuid": "${LIBRA_ORG_UUID}" } } } }
     ```
     Set `LIBRA_CONTRIB_KEY` (the store's token) and `LIBRA_ORG_UUID` (the org)
     in the contributor's shell profile / secret manager. One active org per
     machine; works in every folder.
   - *Per-folder* (for testing several orgs/envs at once): a **project-scoped**
     `.mcp.json` in THIS folder with the org and token **inline as literals**
     from the store, so each folder pins its own org:
     ```json
     { "mcpServers": { "libra": { "type": "http", "url": "<env-url>",
       "headers": { "Authorization": "Bearer <token literal>",
                    "x-user-org-uuid": "<org_uuid literal>" } } } }
     ```
     The token is a secret in a project file — **ensure `.mcp.json` is
     gitignored in that repo before writing it**, and tell the contributor it
     must never be committed.

   In both modes the `libra` entry nests under the top-level `mcpServers` —
   merge into an existing one; never write `libra` at the top level.
   *Per-folder is a Claude Code CLI-only capability* — the other three hosts
   have a single global config (see below).

   **Antigravity (agy) — CLI AND desktop 2.x, one command — switch-active-org:**
   agy keeps ONE global registration at `~/.gemini/config/mcp_config.json`
   which **both the CLI and the 2.x desktop app read**, and bakes header values
   as literals (no runtime env expansion) — so exactly one org is active per
   machine; you *switch* it, you don't scope it per folder. Run:
   `agy mcp add -H "Authorization: Bearer <token literal>" -H
   "x-user-org-uuid: <org_uuid literal>" libra <env-url>` (both literals from
   the store), then `chmod 600 ~/.gemini/config/mcp_config.json` (it holds the
   token and agy leaves it world-readable). One command covers CLI + desktop.
   Tell the contributor agy is now globally pointed at THIS org until switched
   again — two orgs are never active on agy at once.

   **Claude Cowork (Claude desktop app) — global, one active org:**
   Cowork reads `claude_desktop_config.json` (macOS:
   `~/Library/Application Support/Claude/claude_desktop_config.json`; Windows:
   `%APPDATA%\Claude\claude_desktop_config.json`). It expects **literal**
   header values. Merge this into its top-level `mcpServers` (never overwrite an
   existing `mcpServers` — read, merge the `libra` key, write back):
   ```json
   { "mcpServers": { "libra": { "url": "<env-url>",
     "headers": { "Authorization": "Bearer <token literal>",
                  "x-user-org-uuid": "<org_uuid literal>" } } } }
   ```
   One active org per machine (like agy) — to switch org, rewrite this entry.
   The skill itself installs into Cowork separately from this MCP wiring — the
   contributor adds it via **Customize → Skills → ➕ → Upload a skill** (a ZIP),
   or drops it under `.claude/skills/`; connect only writes the MCP config.

   **Any other Agent-Skills-standard agent:** its own MCP config file, same
   entry shape (inline literals from the store), at the path its install README
   names; if none, ask the contributor to locate its MCP settings — never
   invent a path.

**Ceremony** — mint a fresh bearer. Run by step 3 ONLY when the store has no
live token for the target org (a hand-issued admin/break-glass key is the other
way in — save that straight to the store under its org and skip the ceremony):
   1. Ask the contributor for THREE things together, in the same ask — the
      request call needs all three:
      - their work email
      - the org's **portal** domain (e.g. `portal.hoiio.net`) — explain this
        is the domain their org's portal uses, NOT necessarily the domain
        their email address is on; the two are often different
      - their org_uuid
      Never guess any of the three, never pull them from git config, the
      environment registry, or any other ambient source — ask. (domain and
      org_uuid in chat are both fine — neither is a credential, unlike the
      bearer itself.)
   2. Derive the auth base from the env-url, don't rebuild it from the host:
      take the env's MCP URL and replace its `/private/v1/mcp` tail with
      `/public/v1/auth/request`. This preserves any gateway path prefix (prod
      is `.../library/private/v1/mcp` → `.../library/public/v1/auth/request`;
      local has no prefix). Never strip back to the bare host — you'd drop the
      prefix and hit the wrong service. Call `POST <that URL> {email, domain,
      org_uuid}` — and set the header `x-user-org-uuid: <org_uuid>` on this
      call (same value as the body's org_uuid; the public gateway routes to
      the right environment by that header). Its shapes:
      - `sent` — tell the contributor a 6-digit code is on its way to that
        inbox, single-use, expires in 5 minutes, and ask them to read it back
        to you when it arrives. Saying the code itself in chat is fine and
        expected — it burns the moment it's used (or in 5 minutes,
        whichever's first), so it's worthless to anyone after that.
      - `otp_pending` — a live code for this email already exists. Tell them
        to check their inbox for the one already sent, or wait for it to
        expire before requesting a new one.
      - `not_a_member` — either the (email, domain) pair didn't resolve to a
        known identity, or the identity it resolved to isn't a member of that
        org_uuid. Stop here and tell the contributor to double-check all
        three values (email, portal domain, and org_uuid), or contact their
        admin if they're confident all three are right; don't retry
        automatically.
      - `org_not_enabled` — the org itself hasn't been enabled for
        contribution yet (this is separate from membership — the org must be
        opened on the Libra side first). Stop; tell the contributor their
        organization isn't enabled to contribute yet and to ask their admin to
        have it provisioned/opened. Don't retry — re-requesting won't change
        it until the org is opened.
      - `send_failed` — the code was minted but delivery failed (a notification-
        service hiccup). Nothing is pending, so it's safe to just retry step 2
        — tell the contributor delivery failed and you're trying again. If
        this keeps happening on retry, don't loop indefinitely: repeated
        attempts (successful sends and failed ones alike) count against the
        same request budget below, so a few retries in a row can tip you into
        `rate_limited` — treat that as your cue to stop and tell the
        contributor, not to keep retrying automatically.
      - `rate_limited` — too many requests for this email, or from this
        network address, in the current window. This is not an error to
        retry through: stop, tell the contributor plainly that requests are
        being throttled and to wait before trying again, and don't call
        `request` again immediately — a fresh attempt right away will almost
        certainly hit the same limit.
      - `internal_error` — an unexpected server-side fault (never a
        credential leak). Tell the contributor something went wrong on the
        server and to try again shortly; if it repeats, that's one to escalate
        rather than keep retrying blindly.
   3. Once the contributor gives you the code, call `POST <auth base>/exchange
      {email, otp}` — the same base you derived in step 2 (env-url with
      `/private/v1/mcp` swapped for `/public/v1/auth`), NOT the bare host —
      also with the header
      `x-user-org-uuid: <org_uuid>` (same routing rule as the request call).
      Its shapes:
      - a bearer token — this is the one moment the credential is in your
        context. Save it to the **token store** (`~/.guru/credentials.json`,
        `chmod 600`) under this org_uuid, with `expires_at` and, if you have
        them, `org_name`/`owner_name`. Never print, log, or repeat it back in
        chat. Then continue to step 4 (register) — global mode also copies it
        into the `LIBRA_CONTRIB_KEY`/`LIBRA_ORG_UUID` env vars; per-folder and
        agy modes read the literal straight from the store.
      - `otp_invalid` — wrong code. Ask the contributor to retype it
        carefully (typos, transposed digits) and retry the exchange with the
        same code before it expires. Five wrong attempts burn the OTP outright
        — if that happens, go back to step 2 and request a fresh one.
   4. Confirm the token landed in the store under the right org_uuid, then
      return to step 4 (register) to wire it into the agent — never ask for the
      key value back, never echo it.

   If a contributor already has a hand-issued key from an admin (break-glass /
   dev convenience), skip the ceremony: save that key to the store under its
   org (ask them for the value privately — never in chat, never echoed), then
   register as usual. Either path ends the same way: the token lives only in
   the store (and, in global mode, the env var), and never transits chat.
5. Finish by telling the contributor to reload — newly registered MCP servers
   never hot-load. The reload depends on the host:
   - **Claude Code CLI / agy CLI:** start a new session.
   - **agy desktop / Claude Cowork (desktop apps):** fully quit and reopen the
     app (a new chat/tab is not enough — the whole app must restart to re-read
     the config).
   Then call `whoami` to verify — the org name/limits echoing back means you're
   connected. Then run the **session-start org confirmation** before any write.

**Reconnecting after expiry:** any tool call that comes back as an auth
failure (a bare 401, or a tool result carrying an auth-shaped error) after a
prior successful connect most likely means the 7-day bearer expired. Don't
guess or retry blindly — tell the contributor their session credential has
expired and offer to re-run the ceremony (a fresh email round trip, ~30
seconds) to mint a new one; the new token overwrites the expired entry in the
token store under that org, and re-registers per the mode they're using.

**init** — Create the worktree directory and write `README-worktree.md`: a short
notice that this repo has no remote (see Vocabulary above — push happens through
the MCP tools, not `git push`). Then check git (see the **Git** section):
- **git present:** `git init` the directory and make the first commit
  `"init worktree"`; commit at each checkpoint from here on.
- **git missing:** run the Git-section flow (recommend self-install → offer to
  install on consent → else no-git mode). In no-git mode, skip `git init`/commit
  entirely — it's a plain folder; use `.bak` copies before risky rewrites.

**ingest <documents>** — The core authoring workflow:

1. Read the source document(s). Formats your Read tool handles natively
   (markdown, text, PDF) need nothing. Binary formats (.docx, .pptx, .xlsx)
   you convert YOURSELF — the contributor is never asked to be technical.
   Try, in order, whatever this machine has:
   - `pandoc <file> -t markdown`
   - plain `python3` with the standard library only — a .docx is a zip:
     read `word/document.xml` via `zipfile` and strip the XML tags to text
     (no packages to install)
   - macOS: `textutil -convert txt <file>`
   - Windows with Word installed: PowerShell COM —
     `(New-Object -ComObject Word.Application)` open + save as text
   - LAST resort only, when every rung above is unavailable: ask the
     contributor to open the file and **File → Save As** PDF or plain text
     into the docs folder — say exactly that, one step, no jargon.
   Extracted text loses layout — that's fine; atomization needs the words,
   not the formatting. Tables that carry real knowledge: transcribe the
   content into prose or a small markdown table in the record body.
2. Atomize each one per `resources/atomization.md` — one complete thought per
   record, subjects, provenance, what to skip (and why).
3. Write the draft records and their `.collection` markers into the worktree.
   Follow `resources/record-format.md` exactly for file shape: a fresh record's
   front-matter has only `subject` plus `source_type`/`source_ref` (both stamped
   verbatim from the document) — no `stable_id`, no `owner_uuid` yet. A fresh
   collection's marker has only `name` — no `collection_id` yet.
4. Commit `"atomized <source_ref>"`. Ingesting several documents in one call
   still gets one commit per document, each tagged with that document's own
   `source_ref`.
5. Present the tree review (S1): the full map of collections and their record
   counts, every record's suggested subject, and what you skipped and why. Hand
   off to **review** (below) for the contributor's edits and confirmation —
   nothing here has touched the server yet.

**review** — Show the collection/subject/count map plus `git diff` against the
last checkpoint, so the contributor sees exactly what changed since then. The
contributor edits files and markers directly in the worktree (front-matter,
body, `.collection` names) — you don't collect edits through a form. On their
one confirmation for the batch, commit `"reviewed <scope>"`. This is also the
surface a rejected push comes back to: fix the flagged files, run them through
this same review, then re-push (one review surface for authoring and
repair, never a silent auto-repush).

**push** — Land the reviewed batch on the server:

1. Pre-validate every file locally against `resources/floor-rules.md`'s
   pre-push checklist — catch what would be rejected before spending a
   round-trip on it.
2. Call `push_collections(collections=[{path, name, collection_id?}])` for
   every collection touched by this batch. Include `collection_id` whenever the
   `.collection` marker already has one — that's what lets a rename or move
   resolve as the *same* collection instead of creating a new one; omit it only
   for a collection that has never been pushed. Always send `name`, even
   unchanged (a blank `name` is rejected, not treated as "leave as-is"). Read
   back `{"collections": [{path, collection_id, outcome: created|renamed|moved
   |noop|rejected, code?, detail?}]}` and stamp `collection_id` into each
   `.collection` marker (every outcome except `rejected` carries one).
3. Call `push_records(records=[{path, content}], replace_scope?)` — `content`
   is the record's full file text, front-matter and body together. `path` is
   the record's COLLECTION path only (`compliance/call-recording`), never the
   filename — including the `.md` name gets `bad_placement_path`.
   `replace_scope=<source_ref>` ONLY belongs on a regeneration push (see
   **regenerate** below) — never set it on an ordinary ingest push. Read back
   `{"records": [{path, verdict: accepted|noop|rejected, record_id?, code?,
   detail?, suggestion?, warnings}], "removed": [{record_id, subject}]}` —
   `warnings` is always present, an empty list when there's nothing to flag —
   it's the other fields marked `?` that are absent when they don't apply,
   never `warnings`. `removed` is only ever populated by a `replace_scope` push (the sweep), and
   each entry names the record that was retired: its `record_id` and its
   `subject`, nothing else. The `records` results come back one per submitted
   record, in the same order you submitted them — match each verdict back to
   its file by that position, never by `path`: paths repeat within a
   collection (nothing stops two records sharing a directory), so a
   path-based match can stamp the wrong file's id and silently cross-write it
   on the next push.
4. Stamp results back: on `accepted`, write `record_id` into that record's
   `stable_id` and this session's `whoami.identity_uuid` into `owner_uuid`
   (front-matter's `owner_uuid` and `whoami`'s `identity_uuid` are the same
   fact — see `resources/record-format.md`). `noop` already carries its
   existing `stable_id`, nothing to stamp. `rejected` carries neither.
5. Handle every verdict per the `resources/floor-rules.md` table: repair
   rejections in the review surface above and re-push; surface `warnings`
   (clobbered hand-edit, auto-created collection, skipped deletion sweep) to
   the contributor as informational, not blocking.
6. Chunk both calls to `limits.max_records_per_push` /
   `limits.max_collections_per_push` — send as many chunks as the batch needs,
   tally `accepted`/`noop`/`rejected` across all of them, then make ONE commit
   once the whole logical push has landed: `"pushed: N accepted, M noop, K
   rejected"`.

If any MCP call comes back as a bare HTTP 401 (`{"error": "unauthorized"}`)
instead of a normal tool result, that happened before your call ever reached a
tool — it means the MCP client's own credential/config is wrong, not that a
record was rejected. Treat it exactly like an `auth_error`: tell the contributor
their MCP configuration needs fixing, and never ask them to paste a key into
the chat.

**checkout [subtree]** — Materialize the worktree from server state:

1. `list_collections()` → `{"collections": [{collection_id, name, path,
   parent_collection_id, record_count, sub_collection_count}]}`. This call
   always returns every collection in the org, flat — there's no server-side
   subtree filter. With no `[subtree]` given, create a directory + `.collection`
   marker (from `collection_id` + `name`) for every entry. With `[subtree]`
   given, first find the entry matching that subtree, then keep only it and
   its descendants — walk the flat list by `parent_collection_id` (a
   collection belongs to the subtree if its `parent_collection_id` is the
   subtree root or any collection already included) — and create directories
   /markers for only that filtered set.
2. `list_records(collection_id?, source_ref?, cursor?, limit?)`. The
   `collection_id` filter is **non-recursive**: it returns only records filed
   directly in that one collection, not in its sub-collections too. For a
   whole-org checkout, call it once with no `collection_id` filter. For a
   subtree checkout, there is no single call that covers the subtree — call it
   once per collection id in the filtered set from step 1, unioning the
   results. Paginate each call: keep passing its response's `next_cursor` back
   as `cursor` until a response omits it. (`limit` is clamped server-side to
   `limits.max_records_per_push` regardless of what you pass.)
3. `get_records(record_ids, include_content=true)`, chunked to
   `limits.max_records_per_push` — the same per-call cap the server enforces
   on this and `delete_records`. The `record_id`s step 2 just listed are what
   you pass in as this call's `record_ids`. Each returned entry carries
   `subject`, `owner`, `collection`, `path`, `source_type`/`source_ref`, and
   `content` (body only, front-matter already stripped) — its `path` names the
   worktree directory the reconstructed file lands in (the same collection
   directory step 1 created). Reconstruct the record file per
   `resources/record-format.md` from those fields (`stable_id` = `record_id`,
   `owner_uuid` = `owner.owner_uuid`) plus the fetched `content` as the body.
   Anything in `skipped` (`not_found` / `off_shelf` / `content_missing`) has no
   file to write — note it instead of failing the checkout.
4. Commit `"checkout <scope>"`.

Invariant: pushing a freshly-checked-out worktree back should produce all
`noop` verdicts and `"removed": []` — that's the sanity check that the
checkout faithfully reproduced server state.

**regenerate <source_ref>** — Re-derive a source document's records after the
document itself changed. Warn the contributor before starting: this clobbers
any hand-edits made to that source's derived records — the source document
wins by design.

1. Checkout that scope first (remote truth, not the local copy): this is the
   same mechanics and commit (`"checkout <scope>"`) as **checkout** above,
   scoped via `list_records(source_ref=<source_ref>)` — a flat filter across
   the whole org, not a collection subtree walk, so (unlike a subtree
   checkout) one paginated `list_records` call already covers the full scope;
   there's no need to iterate per collection id here. This one commit serves
   double duty as both the checkout checkpoint and the "before regenerate"
   checkpoint — regeneration begins by re-pulling remote truth.
2. Re-atomize the (possibly changed) document per `resources/atomization.md`,
   carrying forward identity and subject from what you just checked out:
   a thought that's unchanged keeps both its `stable_id` and its previously
   confirmed `subject`; a thought that materially changed keeps its
   `stable_id` but gets a NEW suggested `subject`, flagged "subject changed"
   for the contributor's attention in review. A thought with no prior match is
   new (no `stable_id` yet, same as ingest); a previously-derived record with
   no matching thought anymore simply isn't in the batch — the push's sweep
   (next step) retires it.
3. Run **review**, then **push** with `replace_scope=<source_ref>` — mandatory
   here, unlike an ordinary ingest push. The server completes the sync: every
   record still under that `source_ref` and not present in this batch is
   deleted once the push lands clean, reported in the push response's
   `removed`. Report each retired record to the contributor by its `subject`
   (that's what the field is for) — not by `record_id` — and delete its local
   file too, if a copy from the pre-regeneration checkout is still sitting in
   the worktree.

**status** — Compare three views, read-only (no MCP writes, no commit):

1. Local vs last checkpoint: `git status` / `git diff` against the most recent
   checkpoint commit — what's new or edited since then.
2. Local vs remote-known: `list_records(...)` (paginated, per **checkout**
   above) over the relevant scope, diffed against local front-matter: a
   record's local `stable_id` matches an entry's remote `record_id`, and a
   locally recomputed body hash matches that entry's `content_hash`. Classify
   each record as new (no local `stable_id`, no remote match), changed
   (`stable_id` matches a `record_id` but the recomputed local body hash
   disagrees with that entry's `content_hash`), or server-only (a remote
   `record_id` with no corresponding local file — a candidate for a fresh
   checkout). "Unpushed" is not a fourth, overlapping bucket — it's a
   refinement of the first two: a record is unpushed when it's new or changed
   AND has not yet gone through a `"pushed: ..."` checkpoint. New/changed
   describe *what* differs from remote-known; unpushed describes *whether*
   that difference has actually been sent yet.

## Checkpoints and the revert footgun

Commit at five points: after atomization, after a review confirm, immediately
after a push lands (before anything else happens, so a revert target still
carries the ids the push just stamped), after checkout, and before
regeneration (regenerate's opening checkout commit covers this one too, as
noted above).

The footgun: reverting PAST a push checkpoint strips the ids that push
stamped, and a naive re-push of the reverted files would ask the server to
mint fresh ids for content it already has — silent duplicates. Two nets catch
this: the server's own content-hash floor re-matches an id-less file against
an unchanged body already stored under the same `source_ref` scope and adopts
the existing id rather than minting a new one — the same re-match behavior
`resources/floor-rules.md`'s verdict table describes for a dropped/unknown id;
and the skill itself must warn the contributor before pushing any id-less file
at a path it knows was stamped in an earlier checkpoint — that combination is
exactly the shape a bad revert leaves behind.

## Delete

A hand-authored record dies by an explicit `delete_records(record_ids)` call —
idempotent per id, so an already-gone id just reports `not_found`, never an
error. A document-derived record dies as a side effect of **regenerate**'s
`replace_scope` sweep, not by a direct delete call. There is no
`delete_collections` tool; an empty collection left behind by either path is
the server's concern, not the worktree's.

## Resources

- `resources/environments.md` — the env → MCP endpoint URL registry. Read it
  before you run **connect**.
- `resources/record-format.md` — the exact record and collection-marker file
  format. Read it before you create, edit, or validate any record or marker.
- `resources/atomization.md` — how to turn a source document into records (what
  makes one complete thought, subject conventions, what to skip). Read it before
  you atomize a document.
- `resources/floor-rules.md` — the deterministic checks the server runs on push,
  and how to pre-validate locally so you catch rejections before you push. Read it
  before you push, and when repairing a rejected record.
