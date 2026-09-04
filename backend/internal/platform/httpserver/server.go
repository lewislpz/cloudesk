package httpserver

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/lewislpz/cloudesk/backend/internal/platform/config"
	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

type Server struct {
	server          *http.Server
	readiness       *health.State
	shutdownTimeout time.Duration
}

func New(configuration config.HTTP, handler http.Handler, readiness *health.State) *Server {
	return &Server{
		server: &http.Server{
			Addr:              configuration.Address,
			Handler:           handler,
			ReadHeaderTimeout: configuration.ReadHeaderTimeout,
			ReadTimeout:       configuration.ReadTimeout,
			IdleTimeout:       configuration.IdleTimeout,
		},
		readiness:       readiness,
		shutdownTimeout: configuration.ShutdownTimeout,
	}
}

func (server *Server) Run(ctx context.Context) error {
	listener, err := net.Listen("tcp", server.server.Addr)
	if err != nil {
		return fmt.Errorf("listen for HTTP traffic: %w", err)
	}
	return server.Serve(ctx, listener)
}

func (server *Server) Serve(ctx context.Context, listener net.Listener) error {
	serveDone := make(chan error, 1)
	go func() {
		serveDone <- server.server.Serve(listener)
	}()
	server.readiness.MarkReady()

	select {
	case err := <-serveDone:
		server.readiness.MarkNotReady()
		if errors.Is(err, http.ErrServerClosed) {
			return nil
		}
		return fmt.Errorf("serve HTTP traffic: %w", err)
	case <-ctx.Done():
		server.readiness.MarkNotReady()
	}

	shutdownContext, cancel := context.WithTimeout(
		context.WithoutCancel(ctx),
		server.shutdownTimeout,
	)
	defer cancel()
	if err := server.server.Shutdown(shutdownContext); err != nil {
		_ = server.server.Close()
		<-serveDone
		return fmt.Errorf("drain HTTP traffic: %w", err)
	}

	if err := <-serveDone; err != nil && !errors.Is(err, http.ErrServerClosed) {
		return fmt.Errorf("serve HTTP traffic: %w", err)
	}
	return nil
}
