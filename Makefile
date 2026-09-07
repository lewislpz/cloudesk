.PHONY: docs-check test-foundation

docs-check:
	python3 scripts/check-docs.py

test-foundation:
	pnpm check
	go -C backend test -race -count=1 ./...
	pnpm build
	pnpm --dir frontend test:e2e
	python3 scripts/test-ci.py
	$(MAKE) docs-check
