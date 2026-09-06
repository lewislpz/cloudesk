package database

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

const (
	DefaultMaxConnections int32 = 8
	MaximumConnections    int32 = 64
)

type PoolConfig struct {
	URL            string
	MaxConnections int32
}

func OpenPool(ctx context.Context, config PoolConfig) (*pgxpool.Pool, error) {
	if strings.TrimSpace(config.URL) == "" {
		return nil, errors.New("database URL is required")
	}
	if config.MaxConnections < 0 || config.MaxConnections > MaximumConnections {
		return nil, fmt.Errorf("database max connections must be zero or between 1 and %d", MaximumConnections)
	}

	maxConnections := config.MaxConnections
	if maxConnections == 0 {
		maxConnections = DefaultMaxConnections
	}

	poolConfig, err := pgxpool.ParseConfig(config.URL)
	if err != nil {
		return nil, errors.New("parse database pool configuration")
	}
	poolConfig.MaxConns = maxConnections
	poolConfig.MinConns = 0
	poolConfig.MaxConnLifetime = 30 * time.Minute
	poolConfig.MaxConnIdleTime = 5 * time.Minute
	poolConfig.HealthCheckPeriod = 30 * time.Second
	poolConfig.ConnConfig.ConnectTimeout = 5 * time.Second

	pool, err := pgxpool.NewWithConfig(ctx, poolConfig)
	if err != nil {
		return nil, fmt.Errorf("open database pool: %w", err)
	}
	if err := pool.Ping(ctx); err != nil {
		pool.Close()
		return nil, fmt.Errorf("ping database: %w", err)
	}
	return pool, nil
}
