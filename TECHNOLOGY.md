---
title: Official documentation technology overview
status: review-needed
publication_ready: false
verified_in: null
verified_on: null
verified_by: null
---

# Official documentation technology overview

The official site is one publication surface assembled from several owners.
The `sagan` repository currently owns language, toolchain, math, and
project-development documentation; future component repositories will own
their own technical pages. This repository owns the MkDocs theme,
cross-component navigation, versions, previews, deployment, and publication
policy. It must not silently become the second author of a component page.

For the first local split rehearsal, `docs-sources.lock` names the primary
source URL and full tested commit. The assembler verifies the source checkout
is exactly that commit, clean, and from the expected origin. It then copies
its `docs/` tree into a fresh generated site and overlays the exact six
site-owned paths listed in the lock. Any unlisted site file or missing overlay
fails assembly. This prevents a new page from silently entering the wrong
repository. The generated tree carries its source URL, commit, and overlay
list in `sources.json`; it is build output, not an independently edited source.

The copied `mkdocs.yml` retains the existing navigation and hooks, while
the generated tree includes the two required site hooks. A strict MkDocs
build can therefore test a pinned aggregate without moving component pages
out of their source repository. The existing `docs.sh` and deployment scripts
still assume monorepo layout and are not yet wired to the aggregate. This
candidate does not implement component-PR previews, cross-repository version
selection, approved publication gating, or a hosting cutover.

The dependency direction is one-way: the docs site consumes component docs
and exact source locks; a language, extension, physics, rendering, or game
build must not depend on this repository to compile. A workspace lock may
coordinate the same commits, but this docs lock independently records what
was assembled for a site build. See [MAINTAINERS.md](MAINTAINERS.md) for
commands, failure handling, and release hold.
