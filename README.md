# guru-contributor-skill

Contribute knowledge to the **Guru** knowledge base straight from your coding
agent. Point it at your documents and the skill turns them into atomic,
reviewed knowledge records and publishes them for you — you work in plain
language, it takes care of the rest.

## Install

Works on **Antigravity desktop (AG)** and the **`agy` CLI**. One install serves
both — it lands globally in `~/.gemini/config/plugins/`. Install once, then run
**connect** (below).

### Antigravity desktop (AG)
No terminal needed. Paste this into an AG chat:

> Install this skill: https://github.com/AgentDuet/guru-contributor-skill

AG clones the repo and installs it for you. Approve the permission prompts; it
may take a couple of attempts to get there — let it work through them. When it
reports success: fully **quit + reopen** the app (plugins load at startup), run
**connect**, then quit + reopen once more (MCP config also loads at startup).

### agy CLI (AGY)
```
git clone https://github.com/AgentDuet/guru-contributor-skill.git
agy plugin install ./guru-contributor-skill
```
Open a new session, run **connect**, then open a new session again.

## Get started

Start a session and run **connect**. It walks you through everything — verifies
who you are, wires up the connection, and tells you exactly what to do if
anything is missing. When your access later expires, just run **connect** again.

Connection, credentials, and security are handled for you — there's nothing to
configure and nothing to keep secret on your side.

Every session, before it writes anything, the skill shows you which workspace
you're contributing into and asks you to confirm — so a mistaken workspace is
caught before anything lands.

## Your documents

Point the skill at your files — Markdown, text, and PDF work as-is. For Office
files (`.docx`, `.pptx`, `.xlsx`) it reads them using converter tools already on
your machine if present (`pandoc`, `python3`, `textutil`, …); **you don't need
to install anything**. If none are available, it simply asks you to **Save As
PDF** and continues. Nothing to set up.

---

© AgentDuet. All rights reserved. Published for distribution and installation;
no license to copy, modify, or redistribute is granted.
