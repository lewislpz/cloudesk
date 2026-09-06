SQLC_VERSION := v1.31.1
SQLC := go run github.com/sqlc-dev/sqlc/cmd/sqlc@$(SQLC_VERSION)

.PHONY: db-test-reset sqlc-check sqlc-generate

db-test-reset:
	go test -count=1 ./tests/database -run '^TestMigrationsFromEmpty$$'

sqlc-generate:
	$(SQLC) generate -f sqlc.yaml

sqlc-check:
	../scripts/check-sqlc.sh
