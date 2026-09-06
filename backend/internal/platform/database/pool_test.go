package database

import (
	"context"
	"strings"
	"testing"
)

func TestOpenPoolRejectsMissingURL(t *testing.T) {
	t.Parallel()

	pool, err := OpenPool(context.Background(), PoolConfig{})
	if pool != nil {
		pool.Close()
		t.Fatal("OpenPool returned a pool for missing URL")
	}
	if err == nil || !strings.Contains(err.Error(), "URL is required") {
		t.Fatalf("OpenPool error = %v, want missing URL error", err)
	}
}

func TestOpenPoolRejectsUnboundedPool(t *testing.T) {
	t.Parallel()

	pool, err := OpenPool(context.Background(), PoolConfig{
		URL:            "postgres://user:secret@example.invalid/clouddesk",
		MaxConnections: MaximumConnections + 1,
	})
	if pool != nil {
		pool.Close()
		t.Fatal("OpenPool returned an unbounded pool")
	}
	if err == nil || !strings.Contains(err.Error(), "max connections") {
		t.Fatalf("OpenPool error = %v, want connection bound error", err)
	}
	if strings.Contains(err.Error(), "secret") {
		t.Fatal("OpenPool error exposed a database credential")
	}
}

func TestOpenPoolRedactsMalformedURL(t *testing.T) {
	t.Parallel()

	const secret = "do-not-log-this"
	pool, err := OpenPool(context.Background(), PoolConfig{
		URL: "postgres://user:" + secret + "@%zz",
	})
	if pool != nil {
		pool.Close()
		t.Fatal("OpenPool returned a pool for malformed URL")
	}
	if err == nil {
		t.Fatal("OpenPool accepted a malformed URL")
	}
	if strings.Contains(err.Error(), secret) {
		t.Fatal("OpenPool error exposed a database credential")
	}
}
