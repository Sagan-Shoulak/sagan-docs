# Official documentation cutover readiness

Issue [Sagan-Shoulak/sagan-docs#7](https://github.com/Sagan-Shoulak/sagan-docs/issues/7)
tracks the evidence and owner decision required before this repository may
publish the official site. This document is a rehearsal contract, not
authorization to deploy.

## Confirmed preview path

The `Documentation preview` workflow performs only read operations against the
exact commits in `docs-sources.lock`. It tests the source and ownership
contracts, bootstraps clean detached checkouts, assembles the aggregate,
strictly builds it, records `sources.json` plus SHA-256 evidence for every
built file, and uploads a short-lived workflow artifact. It has no content
write permission, publication job, HP1 runner, environment, or deployment
step.

Assembly rejects a wrong origin, wrong commit, dirty checkout, missing or
extra component-owned path, duplicate destination owner, unsafe path, or
existing output directory. The strict MkDocs build rejects broken navigation
and link errors. Together these checks prevent a preview with silently missing
or multiply owned sections. The evidence artifact makes the exact source pins
and resulting file set reviewable without changing the live site.

The October 5, 2026 local rehearsal at the current lock assembled 114 source
files into 159 built files. Its normalized sitemap contained 90 routes, exactly
matching the 90 routes exposed by the live experimental sitemap: neither side
had an unmatched route. The live site did not expose `sources.json` (HTTP 404),
so source-pin provenance can be confirmed for the candidate artifact but not
retrospectively for the currently deployed files. That provenance gap must be
recorded rather than inferred away.

## Required comparison before cutover

For the reviewed candidate commit:

1. Download the `exact-lock-docs-preview` artifact from its passing workflow.
2. Confirm `sources.json` matches the reviewed `docs-sources.lock` in URLs,
   commits, component paths, and site overlays.
3. Compare `preview-evidence.json` with a read-only inventory of the current
   live experimental site. Classify every added, removed, or changed route;
   unexplained differences block cutover.
4. Inspect navigation, search, styling, version selection, component pages,
   images, redirects, and provenance in an isolated preview location. A local
   artifact inspection is acceptable; uploading it to HP1 is not authorized
   by this rehearsal.
5. Record the comparison and owner approval in issue #7. Approval must name the
   candidate commit and exact source pins.

## Proposed cutover sequence

These steps remain proposals until the owner explicitly authorizes them:

1. Freeze both the primary publisher and candidate docs commit long enough to
   prevent competing writes.
2. Capture the current live release/version pointers and a complete recoverable
   copy of the currently served site.
3. Re-run the exact-lock workflow at the approved commit and verify its
   evidence against the approved comparison.
4. Change publication ownership in a separately reviewed PR. Do not combine
   that change with source-pin, content, navigation, or release changes.
5. Deploy once, verify representative routes and assets through the public
   endpoint, and confirm only one publisher can write the target.
6. Keep the captured prior site and publisher configuration until the owner
   closes the observation window.

## Rollback drill and stop conditions

The non-production drill uses two local directories: an immutable copy of the
current-site inventory and the extracted candidate artifact. Switching a
temporary `current` pointer to the candidate demonstrates the cutover;
switching it back to the immutable prior copy demonstrates rollback. Hash both
inventories before and after the drill. The prior copy must remain unchanged,
and restoration must not require rebuilding either version. The October 5,
2026 local drill switched from the captured live headers, redirect page, and
sitemap to the 159-file candidate and back; all three prior evidence files
retained their hashes and the pointer ended on the prior inventory. This proves
the rehearsal mechanism, not HP1 deployment or production recovery.

During a future authorized production cutover, stop and restore the captured
prior site if provenance differs from the approved pins, a required route or
asset is absent, navigation/search/version selection fails, more than one
publisher can write, deployment is partial, or public verification cannot be
completed. Restoration means re-pointing the live target to the captured prior
site and restoring the former publisher configuration; do not attempt an
in-place repair under live traffic.

The `main` promotion, stable release, deployment, and publication holds remain
in force until the owner approves a separate cutover change.
