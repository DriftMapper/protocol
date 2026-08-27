# `build-info.html` format

The output of `driftmapper` (no subcommand) — one HTML file written into a
deployed build, alongside `driftmapper/protocol`'s OpenAPI spec, as this
org's other public contract (spec §5.1b). It isn't API-shaped so it doesn't
belong in `openapi.yaml`, but it's consumed by third parties independent of
either the CLI or the server — anything that wants to parse a deployed
build's identity, today or years from now — so it gets the same documented,
versioned treatment.

Reference implementation: `driftmapper/cli`'s `internal/buildinfo` package
(`Generate` writes this shape; `Parse` reads it) — this format is the
product (DRFT-124), not a byproduct of a verification feature, so both
halves ship and are maintained regardless of what else the CLI does.
Third-party tooling (synthetic monitoring, uptime checks, a future
`driftmapper probe <url>` — see DRFT-131) is the primary audience for
`Parse`. This document is the contract; `internal/buildinfo` is one
conforming producer and parser of it, not the source of truth for what any
parser is allowed to assume.

## Contract vs. presentation

The file has two independent layers. Only the first is the contract:

1. **Machine-readable — namespaced, versioned meta tags.** This is what a
   parser reads. Stable across CLI versions, evolved only per the
   compatibility rules below.
2. **Human-facing — visible content plus a click-only sign-in link.** The
   build ID and built-at timestamp rendered as ordinary page text (DRFT-52
   — no request required to see them), and a link (plus `<noscript>`
   fallback) to sign in for the full authenticated record. No auto-redirect
   on page load. Free to change shape (copy, styling, link target) without
   a version bump — a parser must never depend on anything in this layer.

All representations in the file are written from one build-instance
ID/resolution-URL pair in a single generation step, so they can never
disagree with each other.

## Meta tags

```html
<meta name="driftmapper:schema-version" content="1">
<meta name="driftmapper:build-id" content="<build-instance-id>">
<meta name="driftmapper:built-at" content="<built-at>">
<meta name="driftmapper:resolution-url" content="<resolution-url>">
```

| Tag | Required | Meaning |
|---|---|---|
| `driftmapper:schema-version` | Yes | See "Schema version semantics" below. |
| `driftmapper:build-id` | Yes | Opaque, server-issued. Content-addressed over `repository_id + commit_sha + ref + workflow + run_id + run_attempt` server-side — **treat this as opaque and do not parse it**; the derivation is an implementation detail that may change without a schema-version bump. |
| `driftmapper:built-at` | Yes | RFC 3339 timestamp of build registration. Added additively (no schema-version bump) alongside DRFT-52's visible unauth-tier content — matches the resolution page's own `driftmapper:built-at` tag (spec §2.7) exactly, so a parser sees the same value whichever surface it reads. |
| `driftmapper:resolution-url` | Yes | The build's resolution page. Server-provided; the CLI constructs no URL of its own. |

A tag not listed here may appear in a future schema version. A parser built
against version `1` should ignore unrecognized tags rather than reject the
file for their presence — see below.

## Schema version semantics

`driftmapper:schema-version` exists because this file is a public contract
consumed by third-party parsers (synthetic monitoring, uptime tooling — see
"Reference implementation" above; the scheduled pinger that originally
motivated this was cancelled, DRFT-27) built against CLI versions that may
be years old by the time they read a given file, and there's no other
unambiguous way to evolve the format later.

- **A new tag is additive, not a version bump.** Parsers must tolerate
  unknown `driftmapper:*` tags. This is the same "clients tolerate unknown
  fields" posture `openapi.yaml`'s N-2 compatibility window applies to the
  wire protocol, restated here for this contract.
- **Removing or changing the meaning of an existing tag is a breaking
  change** and requires a version bump.
- **On an unrecognized `schema-version`: fail loudly, don't guess.** A
  parser that doesn't recognize the version number must report an explicit
  "unsupported build-info schema version `<N>`" error rather than attempt
  to interpret the file under assumptions from a version it does
  understand. A silent best-effort parse that's wrong is worse than a
  parser that stops and says so — this is the same failure mode
  `internal/oidc` avoids on an unrecognized issuer, applied to file parsing
  instead of token verification.

## Filename

Default, zero-config: `build-info.html` at the deploy root. Configurable
per-project via `DRIFTMAPPER_BUILD_INFO_FILE` (CLI env var) or `--output`
(CLI flag) — the *filename* is configurable, the *format* is not; see the
CLI's own `--help` for the current flag surface.

## Compatibility window

This format tracks the same N-2 compatibility posture as
`driftmapper/protocol`'s `public`-tier API operations (see this repo's main
README) — a parser should expect to encounter files written by CLI versions
several majors old, in the wild, indefinitely. `schema-version` is what
makes that expectation safe to build against.

## Documents CLI v1.x

This describes the file as written by `driftmapper/cli` v1.x
(`internal/buildinfo`, schema version `1`). If the CLI's major version
surface grows enough to need it, this document should version alongside it
rather than silently drifting out of sync with what v2+ actually emits.
