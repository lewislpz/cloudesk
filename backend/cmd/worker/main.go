package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/lewislpz/cloudesk/backend/internal/app"
	"github.com/lewislpz/cloudesk/backend/internal/platform/config"
	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	if err := run(logger); err != nil {
		logger.Error("worker process stopped", "error", err)
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	configuration, err := config.LoadWorker(os.LookupEnv)
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	worker := app.NewWorker(health.NewState())
	logger.Info("worker process started", "environment", configuration.Environment)
	return worker.Run(ctx)
}
