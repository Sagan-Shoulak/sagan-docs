# Sagan official docs (local split candidate)

This is a local rehearsal of the future `sagan-docs` repository, not a
published split. It owns site assembly, navigation, styling, versioning,
hosting, and publication; component repositories continue to own the
technical accuracy and source of their sections.

`docs-sources.lock` pins the currently transferred primary `sagan` source at
an exact commit. `scripts/assemble_docs.py` checks that source, copies its
documentation into a new generated tree, and overlays this repository's six
explicitly listed site-owned files. It never alters the source checkout or an
existing output directory. The lock also lists exact future mount paths for
extension, physics, and rendering docs, all still `planned`. An active
component must have a full pinned commit and a clean, exact-origin checkout;
the assembler then replaces only its explicitly owned pages/assets and
records that provenance. No split remote is active, and deployment remains
paused.

`scripts/bootstrap_docs_sources.py` clones only active lock entries to
ordinary ignored checkouts and refuses to move or overwrite an existing
checkout. The draft CI uses those exact sources and assembles them with
`--source-root`; hosted CI has not been run in an independent docs repo.

Start with [MAINTAINERS.md](MAINTAINERS.md) for Bash commands and recovery,
[TECHNOLOGY.md](TECHNOLOGY.md) for the ownership model, and
[CODEX_START.md](CODEX_START.md) for a new chat. The broader sequencing lives
in the primary repository's multi-repository fracture roadmap.
