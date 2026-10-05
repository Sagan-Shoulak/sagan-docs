# Sagan official docs (local split candidate)

This is a local rehearsal of the future `sagan-docs` repository, not a
published split. It owns site assembly, navigation, styling, versioning,
hosting, and publication; component repositories continue to own the
technical accuracy and source of their sections.

`docs-sources.lock` pins the currently transferred primary `sagan` source at
an exact commit. `scripts/assemble_docs.py` checks that source, copies its
documentation into a new generated tree, and overlays this repository's six
explicitly listed site-owned files. It never alters the source checkout or an
existing output directory. The remaining component sources are not yet
active, and deployment remains paused.

Start with [MAINTAINERS.md](MAINTAINERS.md) for Bash commands and recovery,
[TECHNOLOGY.md](TECHNOLOGY.md) for the ownership model, and
[CODEX_START.md](CODEX_START.md) for a new chat. The broader sequencing lives
in the primary repository's multi-repository fracture roadmap.
