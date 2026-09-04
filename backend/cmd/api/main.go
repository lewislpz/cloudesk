package main

import (
	"context"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/lewislpz/cloudesk/backend/internal/app"
	"github.com/lewislpz/cloudesk/backend/internal/platform/config"
)

func main() {
	logger := slog.New(slog.NewJSONHandler(os.Stderr, nil))
	if err := run(logger); err != nil {
		logger.Error("api process stopped", "error", err)
		os.Exit(1)
	}
}

func run(logger *slog.Logger) error {
	configuration, err := config.LoadAPI(os.LookupEnv)
	if err != nil {
		return err
	}
	api, err := app.NewAPI(configuration)
	if err != nil {
		return err
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	logger.Info("api process started", "environment", configuration.Environment)
	return api.Run(ctx)
}
