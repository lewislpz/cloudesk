package app

import (
	"context"

	"github.com/lewislpz/cloudesk/backend/internal/platform/config"
	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
	"github.com/lewislpz/cloudesk/backend/internal/platform/httpserver"
)

type API struct {
	server *httpserver.Server
}

func NewAPI(configuration config.API) (*API, error) {
	readiness := health.NewState()
	routes, err := httpserver.NewRoutes(readiness, configuration.HTTP.RequestTimeout)
	if err != nil {
		return nil, err
	}
	return &API{server: httpserver.New(configuration.HTTP, routes, readiness)}, nil
}

func (api *API) Run(ctx context.Context) error {
	return api.server.Run(ctx)
}
