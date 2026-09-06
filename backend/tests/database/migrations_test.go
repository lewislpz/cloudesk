package database_test

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/golang-migrate/migrate/v4"
	migratepgx "github.com/golang-migrate/migrate/v4/database/pgx/v5"
	"github.com/golang-migrate/migrate/v4/source/iofs"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/stdlib"
	"github.com/testcontainers/testcontainers-go"
	testpostgres "github.com/testcontainers/testcontainers-go/modules/postgres"

	dbgen "github.com/lewislpz/cloudesk/backend/internal/gen/sqlc"
	"github.com/lewislpz/cloudesk/backend/internal/platform/database"
)

const (
	postgresImage = "postgres:17.11-alpine3.24@sha256:18cfe3ef5e6815560c98237d6216d1e5119702fb0f3894c8785dd58b8bbe5d73"
	testDatabase  = "clouddesk_test"
	testPassword  = "clouddesk_test_only"
	testUser      = "clouddesk_migrator"
)

func TestMigrationsFromEmpty(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	t.Cleanup(cancel)

	databaseURL := startPostgres(t, ctx)
	runner := newMigrationRunner(t, databaseURL)

	if err := runner.Up(); err != nil {
		t.Fatalf("apply migrations: %v", err)
	}
	assertMigrationVersion(t, runner, 1)
	assertFoundationSchema(t, ctx, databaseURL)

	if err := runner.Up(); !errors.Is(err, migrate.ErrNoChange) {
		t.Fatalf("second migration pass = %v, want ErrNoChange", err)
	}

	if err := runner.Down(); err != nil {
		t.Fatalf("roll back disposable database: %v", err)
	}
	assertFoundationTableExists(t, ctx, databaseURL, false)

	if err := runner.Up(); err != nil {
		t.Fatalf("roll forward after reset: %v", err)
	}
	assertMigrationVersion(t, runner, 1)
	assertFoundationSchema(t, ctx, databaseURL)
}

func TestMigrationMetadataMatchesSQL(t *testing.T) {
	upPath := filepath.Join("..", "..", "migrations", "000001_foundation.up.sql")
	metadataPath := filepath.Join("..", "..", "migrations", "000001_foundation.metadata.json")

	upSQL, err := os.ReadFile(upPath)
	if err != nil {
		t.Fatalf("read migration: %v", err)
	}
	metadataDocument, err := os.ReadFile(metadataPath)
	if err != nil {
		t.Fatalf("read migration metadata: %v", err)
	}

	var metadata struct {
		AffectedTables []string `json:"affected_tables"`
		Checksum       string   `json:"sha256"`
		Owner          string   `json:"owner"`
		Reversible     bool     `json:"reversible"`
		Version        int      `json:"version"`
	}
	if err := json.Unmarshal(metadataDocument, &metadata); err != nil {
		t.Fatalf("decode migration metadata: %v", err)
	}

	digest := sha256.Sum256(upSQL)
	if metadata.Checksum != hex.EncodeToString(digest[:]) {
		t.Fatalf("migration checksum does not match metadata")
	}
	if metadata.Version != 1 || metadata.Owner != "platform" || !metadata.Reversible {
		t.Fatalf("unexpected migration metadata: %+v", metadata)
	}
	if len(metadata.AffectedTables) != 1 || metadata.AffectedTables[0] != "foundation_metadata" {
		t.Fatalf("unexpected affected tables: %v", metadata.AffectedTables)
	}
}

func startPostgres(t *testing.T, ctx context.Context) string {
	t.Helper()

	container, err := testpostgres.Run(
		ctx,
		postgresImage,
		testpostgres.WithDatabase(testDatabase),
		testpostgres.WithUsername(testUser),
		testpostgres.WithPassword(testPassword),
		testpostgres.BasicWaitStrategies(),
	)
	if err != nil {
		t.Fatalf("start disposable PostgreSQL: %v", err)
	}
	t.Cleanup(func() {
		if err := testcontainers.TerminateContainer(container); err != nil {
			t.Errorf("terminate disposable PostgreSQL: %v", err)
		}
	})

	databaseURL, err := container.ConnectionString(
		ctx,
		"sslmode=disable",
		"connect_timeout=5",
		"application_name=clouddesk_database_test",
	)
	if err != nil {
		t.Fatalf("resolve disposable PostgreSQL address: %v", err)
	}
	return databaseURL
}

func newMigrationRunner(t *testing.T, databaseURL string) *migrate.Migrate {
	t.Helper()

	config, err := pgx.ParseConfig(databaseURL)
	if err != nil {
		t.Fatalf("parse disposable database URL: %v", err)
	}
	sqlDatabase := stdlib.OpenDB(*config)
	sqlDatabase.SetMaxOpenConns(1)
	sqlDatabase.SetMaxIdleConns(1)
	sqlDatabase.SetConnMaxLifetime(5 * time.Minute)

	databaseDriver, err := migratepgx.WithInstance(
		sqlDatabase,
		&migratepgx.Config{
			MigrationsTable:  "schema_migrations",
			StatementTimeout: 30 * time.Second,
		},
	)
	if err != nil {
		t.Fatalf("create migration database driver: %v", err)
	}
	sourceDriver, err := iofs.New(os.DirFS(filepath.Join("..", "..")), "migrations")
	if err != nil {
		t.Fatalf("open migration source: %v", err)
	}

	runner, err := migrate.NewWithInstance("iofs", sourceDriver, "pgx5", databaseDriver)
	if err != nil {
		t.Fatalf("create migration runner: %v", err)
	}
	t.Cleanup(func() {
		sourceErr, databaseErr := runner.Close()
		if sourceErr != nil {
			t.Errorf("close migration source: %v", sourceErr)
		}
		if databaseErr != nil {
			t.Errorf("close migration database: %v", databaseErr)
		}
	})
	return runner
}

func assertMigrationVersion(t *testing.T, runner *migrate.Migrate, expected uint) {
	t.Helper()

	version, dirty, err := runner.Version()
	if err != nil {
		t.Fatalf("read migration version: %v", err)
	}
	if dirty || version != expected {
		t.Fatalf("migration state = version %d dirty %t, want version %d clean", version, dirty, expected)
	}
}

func assertFoundationSchema(t *testing.T, ctx context.Context, databaseURL string) {
	t.Helper()

	pool, err := database.OpenPool(ctx, database.PoolConfig{
		URL:            databaseURL,
		MaxConnections: 4,
	})
	if err != nil {
		t.Fatalf("open bounded pool: %v", err)
	}
	t.Cleanup(pool.Close)

	if pool.Config().MaxConns != 4 {
		t.Fatalf("pool max connections = %d, want 4", pool.Config().MaxConns)
	}
	metadata, err := dbgen.New(pool).GetFoundationMetadata(ctx)
	if err != nil {
		t.Fatalf("query generated metadata: %v", err)
	}
	if metadata.Component != "clouddesk" || metadata.SchemaGeneration != 1 {
		t.Fatalf("unexpected foundation metadata: %+v", metadata)
	}

	var applicationTableCount int
	if err := pool.QueryRow(ctx, `
		SELECT count(*)
		FROM information_schema.tables
		WHERE table_schema = 'public'
		  AND table_type = 'BASE TABLE'
		  AND table_name <> 'schema_migrations'
	`).Scan(&applicationTableCount); err != nil {
		t.Fatalf("count application tables: %v", err)
	}
	if applicationTableCount != 1 {
		t.Fatalf("application table count = %d, want metadata table only", applicationTableCount)
	}

	if _, err := pool.Exec(ctx, `
		INSERT INTO foundation_metadata (singleton, component, schema_generation)
		VALUES (false, 'clouddesk', 2)
	`); err == nil {
		t.Fatal("foundation metadata accepted a second non-singleton row")
	}
}

func assertFoundationTableExists(t *testing.T, ctx context.Context, databaseURL string, expected bool) {
	t.Helper()

	config, err := pgx.ParseConfig(databaseURL)
	if err != nil {
		t.Fatalf("parse disposable database URL: %v", err)
	}
	connection, err := pgx.ConnectConfig(ctx, config)
	if err != nil {
		t.Fatalf("connect for schema assertion: %v", err)
	}
	t.Cleanup(func() {
		if err := connection.Close(context.Background()); err != nil {
			t.Errorf("close schema assertion connection: %v", err)
		}
	})

	var exists bool
	if err := connection.QueryRow(
		ctx,
		"SELECT to_regclass('public.foundation_metadata') IS NOT NULL",
	).Scan(&exists); err != nil {
		t.Fatalf("inspect foundation table: %v", err)
	}
	if exists != expected {
		t.Fatalf("foundation table exists = %t, want %t", exists, expected)
	}
}
