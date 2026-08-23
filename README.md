# driftmapper/protocol

The Driftmapper wire contract: `openapi.yaml` is the source of truth, and
`types.gen.go` is generated from it and committed. Both the CLI and the
server import this module for request/response types; the dashboard SPA
generates TypeScript types from the same spec. See spec §5.1b.

This repo is deliberately minimal — types and spec, no logic, no
dependencies beyond stdlib. If helpers start accumulating here, something
has leaked in from the wrong side of the CLI/server boundary.

## Versioning

This module has its own semver line, independent of the CLI's. That
independence is what makes the compatibility window below expressible: the
CLI and this contract move on different clocks.

The server supports the current major version and the two preceding majors
(N-2) for `x-stability: public` operations. Within a major version, only
additive changes are permitted — new optional request fields, new response
fields, new enum members in response-only positions. Breaking changes
require a major version bump and are gated in CI (see below).

## Stability tiers

Every operation in `openapi.yaml` declares `x-stability`:

- `public` — the CLI-facing contract. Semver'd and covered by the N-2
  compatibility window above. These are `registerBuild`,
  `authorizeRepository`, `recordDeployment`, `getCurrentDeployment`,
  `getDeployment`, and `recordVerification` (the primary read: keyed by an
  environment name the caller's own deploy step minted, per DRFT-98;
  `getDeployment` is its pinned-row companion).
- `dashboard` — consumed only by the first-party dashboard SPA, which
  deploys in lockstep with the server. Free to change without a major
  version bump.

Promoting an operation from `dashboard` to `public` is additive and safe.
Demoting one is a breaking change to a contract already pinned in customer
CI, and is not permitted. When in doubt, an operation starts `dashboard`.

## Regenerating types

```sh
make generate
```

Runs `oapi-codegen` (types-only mode, pinned version, invoked via
`go run` so it never enters this module's dependency graph) against
`openapi.yaml` and rewrites `types.gen.go`. Commit the result.

`make verify-generate` regenerates into a clean tree and fails if the diff
is non-empty — this is what CI runs to catch a spec change committed
without its matching generated output.

## CI

- **`ci.yml`** — builds, vets, and runs `make verify-generate` on every
  push and PR.
- **`oasdiff.yml`** — runs `oasdiff` breaking-change detection between
  `openapi.yaml` on the PR branch and the previous release tag. A detected
  breaking change fails the check; ship it as a major version bump instead.
- **`release.yml`** — on push of a `vX.Y.Z` tag, re-runs the build/vet/
  verify-generate gate against the tagged commit, then publishes a GitHub
  Release with notes auto-generated from the PRs merged since the previous
  tag.

## Releasing

Tag a release once changes are merged to `main`:

```sh
git tag vX.Y.Z
git push origin vX.Y.Z
```

Bump `X` for any breaking change to a `public`-tier operation (`oasdiff`
enforces this in CI). `dashboard`-tier operations may change freely within
the current major.

Pushing the tag is the release: `release.yml` picks it up and publishes
the GitHub Release page automatically, so there's nothing further to run
by hand.
