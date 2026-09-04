package app

import (
	"context"

	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

type Worker struct {
	readiness *health.State
}

func NewWorker(readiness *health.State) *Worker {
	return &Worker{readiness: readiness}
}

func (worker *Worker) Run(ctx context.Context) error {
	worker.readiness.MarkReady()
	defer worker.readiness.MarkNotReady()
	<-ctx.Done()
	return nil
}
