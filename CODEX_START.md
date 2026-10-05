# Starting a new official Sagan docs chat

Start read-only. Read `AGENTS.md`, `TECHNOLOGY.md`, `MAINTAINERS.md`,
`README.md`, `docs-sources.lock`, `mkdocs.yml`, the primary repository's
fracture roadmap, and its versioned ecosystem/chat maps. Inspect current
branch, HEAD, status, staged paths, source pins, and concurrent work. Report
what the docs site owns versus what each component owns. This checkout is a
public split repository; independent deployment and component aggregation
still need validation.

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

This tracked prompt is a one-time bootstrap. After reading it and orienting
read-only, delete `CODEX_START.md` on a short-lived branch, commit that
deletion and any required contract updates, then open a PR into `dev` linked
to an onboarding issue. Do not
recreate it; `AGENTS.md`, `TECHNOLOGY.md`, and `MAINTAINERS.md` remain the
durable instructions.

Use existing or new GitHub issues for substantive work, PRs into `dev` for
review, and the organization Project for cross-repo milestones when access
permits. Link each PR to its issue, record focused checks, source pins, and
integration impact, and update Project status. If Project access is
unavailable, record that in the issue and continue safe local verification.
The split is tracked by Sagan-Shoulak/sagan#6.
