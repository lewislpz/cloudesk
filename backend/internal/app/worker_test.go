package app

import (
	"context"
	"testing"
	"time"

	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

func TestWorkerStopsOnCancellationAndWithdrawsReadiness(t *testing.T) {
	t.Parallel()

	readiness := health.NewState()
	worker := NewWorker(readiness)
	ctx, cancel := context.WithCancel(context.Background())
	done := make(chan error, 1)
	go func() { done <- worker.Run(ctx) }()

	deadline := time.Now().Add(time.Second)
	for !readiness.IsReady() && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if !readiness.IsReady() {
		t.Fatal("worker did not become ready")
	}

	cancel()
	select {
	case err := <-done:
		if err != nil {
			t.Fatalf("Run() error = %v", err)
		}
	case <-time.After(time.Second):
		t.Fatal("worker did not stop after cancellation")
	}
	if readiness.IsReady() {
		t.Fatal("worker remains ready after stopping")
	}
}
