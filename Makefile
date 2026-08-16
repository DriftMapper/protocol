.PHONY: generate verify-generate build vet test

generate:
	./scripts/generate.sh

# Fails if openapi.yaml and the committed types.gen.go have drifted apart.
# Run in CI so a spec change without a matching regenerated commit is caught
# before merge, not discovered by the next consumer.
verify-generate: generate
	git diff --exit-code -- types.gen.go

build:
	go build ./...

vet:
	go vet ./...

test:
	go test ./...
