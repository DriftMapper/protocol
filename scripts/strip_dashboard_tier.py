#!/usr/bin/env python3
"""Strip dashboard-tier paths from an OpenAPI spec before an oasdiff breaking-
change comparison (DRFT-32).

Dashboard-tier operations (x-stability: dashboard) are, per openapi.yaml's
compatibility policy, free to change without a version bump. oasdiff's own
--filter-extension flag can't express that: it matches by extension *name*,
not by an x-stability *value*, so it can't tell `x-stability: dashboard` from
`x-stability: public` with a single extension name. Introducing a second,
presence-only marker extension for this was tried and rejected — confirmed
empirically that oasdiff excludes a path only when the marker is already
present on *both* sides of the diff, which means the very first comparison
against a tag that predates the marker's introduction flags every dashboard
path as newly "removed" (a false positive, not a fix).

Stripping dashboard-tier paths out of each spec file independently, using
that file's own x-stability *values*, avoids both problems and needs no new
marker: the value-based x-stability field has existed on every operation
since the tiering scheme was introduced, so it's already present on old
release tags, not just the current revision.

Only strips a path when EVERY operation on it is dashboard-tier — a path
mixing public and dashboard operations is left untouched (none exist today;
if one is ever added, its dashboard-tier operation's breaking changes will
need a manual override note on the PR, the same "handle the rare case by
hand" fallback this policy already accepts elsewhere).
"""
import sys

import yaml

METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def strip(spec: dict) -> dict:
    paths = spec.get("paths", {})
    for path, item in list(paths.items()):
        if not isinstance(item, dict):
            continue
        ops = [v for k, v in item.items() if k in METHODS and isinstance(v, dict)]
        if ops and all(op.get("x-stability") == "dashboard" for op in ops):
            del paths[path]
    return spec


def main() -> None:
    if len(sys.argv) != 3:
        sys.exit(f"usage: {sys.argv[0]} <in.yaml> <out.yaml>")
    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path) as f:
        spec = yaml.safe_load(f)

    strip(spec)

    with open(out_path, "w") as f:
        yaml.safe_dump(spec, f, sort_keys=False)


if __name__ == "__main__":
    main()
