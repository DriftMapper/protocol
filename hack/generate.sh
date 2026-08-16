#!/usr/bin/env bash
# Regenerates types.gen.go from openapi.yaml. Run via `make generate`.
#
# oapi-codegen is invoked with a pinned version through `go run pkg@version`
# rather than a go.mod tool dependency, so it never enters this module's
# dependency graph (spec §5.1b: no dependencies beyond stdlib).
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

OAPI_CODEGEN_VERSION="v2.8.0"

go run "github.com/oapi-codegen/oapi-codegen/v2/cmd/oapi-codegen@${OAPI_CODEGEN_VERSION}" \
  -config oapi-codegen-config.yaml openapi.yaml

# oapi-codegen emits Merge* helpers for oneOf schemas that call into
# github.com/oapi-codegen/runtime for JSON merge-patch semantics. Nothing in
# this repo needs merge-patch behavior over a discriminated union — As*/From*
# already cover full-replace access — so strip those methods and the import
# they pull in rather than accept a non-stdlib dependency for unused code.
perl -0777 -pe 's/\n\/\/ Merge\w+ performs a merge.*?\nfunc \(t \*\w+\) Merge\w+\(v \w+\) error \{.*?\n\}\n//gs' \
  types.gen.go > types.gen.go.tmp
mv types.gen.go.tmp types.gen.go

if ! grep -q 'runtime\.' types.gen.go; then
  perl -0777 -pi -e 's/\n\t"github\.com\/oapi-codegen\/runtime"\n/\n/' types.gen.go
fi

gofmt -w types.gen.go
