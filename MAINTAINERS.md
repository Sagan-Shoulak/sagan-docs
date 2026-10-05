---
title: Maintaining the official Sagan docs
status: review-needed
publication_ready: false
verified_in: null
verified_on: null
verified_by: null
---

# Maintaining the official Sagan docs

This is a local extraction candidate, not a published or independently
deployed repository. The existing site automation still targets monorepo
layout. Do not run `deploy/`, `scripts/docs_versions.sh`, or a release command
from this candidate. The project-wide release and `main` promotion hold stays
in force until the owner explicitly reopens it and decides publication policy.

## Reproduce the pinned aggregate

Install Git, Python 3.11+, and the pinned packages in `requirements-docs.txt`.
Use Git Bash and point `sagan_checkout` at a clean ordinary clone whose origin
and HEAD match `docs-sources.lock`:

```bash
python -m venv build/docs-venv
build/docs-venv/Scripts/python.exe -m pip install -r requirements-docs.txt
sagan_checkout=/path/to/verified/sagan
python scripts/assemble_docs.py --sagan "$sagan_checkout" --output build/assembled-check
build/docs-venv/Scripts/python.exe -m mkdocs build --strict --clean -f build/assembled-check/mkdocs.yml
python -m unittest discover -s tests -p assemble_docs_test.py -v
```

On Linux/macOS, use `build/docs-venv/bin/python` in place of the Windows
virtual-environment path. `--output` must name a new directory; the assembler
never replaces an existing one. It does not clone or update the source on its
own. The generated tree includes `sources.json` as provenance. Its built site
is under `build/assembled-check/build/docs-site/` because the copied config
retains the current `site_dir` contract. Keep generated trees under ignored
`build/`; never edit them as source.

This rehearsal passed five offline assembler tests and a strict MkDocs build
against the public Sagan commit
`4132c8c37f99dc5f89c7141f5780b583b64d192e` on Windows. The strict
build reported the existing unlisted
`contributing/late-bound-face-defaults-checkpoint.md` page but exited zero.
Linux/macOS and independent hosted CI are not yet verified.

## Component documentation mounts

`docs-sources.lock` lists VS Code, physics, and rendering page/asset paths as
`planned`. They are not fetched or published from nonexistent split remotes.
After a component repository exists and passes its extraction gate, change
only its reviewed lock entry to `state = "active"`, add its exact `commit`,
and supply a clean checkout at that URL and commit. For all three active
components, the assembly syntax is:

```bash
python scripts/assemble_docs.py \
  --sagan "$sagan_checkout" \
  --component sagan-vscode="$vscode_checkout" \
  --component sagan-physics="$physics_checkout" \
  --component sagan-render="$render_checkout" \
  --output build/assembled-components
build/docs-venv/Scripts/python.exe -m mkdocs build --strict --clean \
  -f build/assembled-components/mkdocs.yml
```

Use `build/docs-venv/bin/python` on Linux/macOS. Exactly the active
components must be supplied; a planned component must not be supplied.
Each component's full `docs/` file set must equal its listed paths, with no
symlinks, dirty checkout, wrong origin, or wrong HEAD. The generated
`sources.json` records URL, commit, and paths for every mounted component.
The local ignored-lock rehearsal mounted all three extracted candidates,
passed eight offline tests and a strict Windows MkDocs build. It did not
activate their canonical entries or deploy the site. The existing unlisted
contributor checkpoint page warning remained unchanged.

The draft `.github/workflows/docs-checks.yml` runs offline contracts and
strictly builds the pinned primary-source aggregate on Linux, Windows, and
macOS. It has not run in an independent destination. When any component
becomes active, update this workflow to check out that exact locked source;
the assembler will otherwise fail closed for the missing component.

## Ownership, editing, and tests

`docs-sources.lock` pins the consumed source. The six paths in its
`site.overlay_paths` must match every tracked file in this repository's
`docs/` tree. To add a site-owned file, update the lock and explain why the
site, rather than a component, owns it. Component-authored pages must remain
in their owning repository. Any documentation edit resets that page to
`status: review-needed`, `publication_ready: false`, and null verification
metadata; a human audit is required before publication.

For an authorized request, inspect branch, HEAD, status, and staged paths;
start a fresh `codex/<request>` branch from current `dev`; make the scoped
change and run focused tests until they pass. Commit only intended paths,
merge into `dev`, then rerun relevant tests against integrated `dev`. A
structural-only docs change need not execute unrelated Sagan examples. Run
affected examples when their source or supporting behavior changes. The full
suite is reserved for reviewed `dev`-to-`main` promotion or release, both
currently held.

The current `scripts/docs.sh` still expects monorepo paths. Do not claim its
`check`, `check-structure`, or `check-examples` commands validate this split
candidate until they are rewired to exact component checkouts. The separate
assembler tests and strict aggregate build are the present focused checks.

## Failure and recovery

- A wrong origin, commit, or dirty source is rejected before copying. Verify
  `git -C "$sagan_checkout" remote -v`, `git -C "$sagan_checkout" rev-parse HEAD`,
  and `git -C "$sagan_checkout" status --short`; preserve local work rather
  than resetting it to satisfy the lock.
- An overlay mismatch means ownership changed. Compare
  `docs-sources.lock` with the six site-owned paths; do not auto-copy new
  pages into this repository.
- An existing output directory is preserved. Choose a new output path after
  inspecting it; the assembler does not delete previous builds.
- A strict MkDocs failure belongs to the aggregate at the exact source pin.
  Inspect `sources.json` and the reported file; route a component page fix to
  its owning chat and reset its review status when changed.

Before a real split, document exact CI, deployment credentials by name only,
cross-repository preview triggers, version/rollback semantics, HP1/frontdoor
ownership, clean-machine recovery, and an owner handoff drill. No credential
value belongs in this repository. The existing local-only primary backup does
not survive loss of this machine or restore GitHub settings and discussions.
