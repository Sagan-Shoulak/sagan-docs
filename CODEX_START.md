# Starting a new official Sagan docs chat

Start read-only. Read `AGENTS.md`, `TECHNOLOGY.md`, `MAINTAINERS.md`,
`README.md`, `docs-sources.lock`, `mkdocs.yml`, the primary repository's
fracture roadmap, and its versioned ecosystem/chat maps. Inspect current
branch, HEAD, status, staged paths, source pins, and concurrent work. Report
what the docs site owns versus what each component owns. This checkout is a
local split candidate; independent deployment is not ready.

Prefer teaching me what to write through small steps, examples, review, and
verification. Do not implement without an explicit request. For authorized
changes, branch from current `dev` as `codex/<request>`, test the affected
work until it passes, commit only intended paths, merge into `dev`, and rerun
relevant tests there. Use the full suite only for `main` promotion or release;
both are currently on owner hold. Do not run unrelated executable examples
for a structural-only documentation edit. Every edited page returns to
`review-needed` and `publication_ready: false` with cleared verification
metadata until a human audits it.

If work belongs to a specialized language, extension, physics, rendering,
workspace, or game chat, recommend that chat using the versioned map and
provide a ready-to-paste handoff with goal, evidence, constraints, pins, and
verification. Do not assume shared chat history. Use Bash, never PowerShell.
Preserve unrelated work and never push, publish, deploy, transfer, or change
remote settings without current authorization.
