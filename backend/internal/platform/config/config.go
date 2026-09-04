package config

import (
	"fmt"
	"net"
	"strconv"
	"time"
)

type LookupEnv func(string) (string, bool)

type API struct {
	Environment string
	HTTP        HTTP
}

type HTTP struct {
	Address           string
	ReadHeaderTimeout time.Duration
	ReadTimeout       time.Duration
	IdleTimeout       time.Duration
	RequestTimeout    time.Duration
	ShutdownTimeout   time.Duration
}

type Worker struct {
	Environment     string
	ShutdownTimeout time.Duration
}

func LoadAPI(lookup LookupEnv) (API, error) {
	environment, err := loadEnvironment(lookup)
	if err != nil {
		return API{}, err
	}
	address := valueOrDefault(lookup, "API_HTTP_ADDRESS", ":8080")
	if err := validateAddress(address, environment); err != nil {
		return API{}, err
	}

	readHeaderTimeout, err := loadDuration(
		lookup, "API_READ_HEADER_TIMEOUT", 5*time.Second, time.Second, 30*time.Second,
	)
	if err != nil {
		return API{}, err
	}
	readTimeout, err := loadDuration(
		lookup, "API_READ_TIMEOUT", 15*time.Second, time.Second, 30*time.Second,
	)
	if err != nil {
		return API{}, err
	}
	idleTimeout, err := loadDuration(
		lookup, "API_IDLE_TIMEOUT", time.Minute, 5*time.Second, 5*time.Minute,
	)
	if err != nil {
		return API{}, err
	}
	requestTimeout, err := loadDuration(
		lookup, "API_REQUEST_TIMEOUT", 10*time.Second, 100*time.Millisecond, 30*time.Second,
	)
	if err != nil {
		return API{}, err
	}
	shutdownTimeout, err := loadDuration(
		lookup, "API_SHUTDOWN_TIMEOUT", 30*time.Second, time.Second, 2*time.Minute,
	)
	if err != nil {
		return API{}, err
	}

	return API{
		Environment: environment,
		HTTP: HTTP{
			Address:           address,
			ReadHeaderTimeout: readHeaderTimeout,
			ReadTimeout:       readTimeout,
			IdleTimeout:       idleTimeout,
			RequestTimeout:    requestTimeout,
			ShutdownTimeout:   shutdownTimeout,
		},
	}, nil
}

func validateAddress(address string, environment string) error {
	_, port, err := net.SplitHostPort(address)
	if err != nil {
		return fmt.Errorf("API_HTTP_ADDRESS must be a host:port address")
	}
	portNumber, err := strconv.Atoi(port)
	if err != nil || portNumber < 0 || portNumber > 65535 {
		return fmt.Errorf("API_HTTP_ADDRESS must use a numeric port")
	}
	if portNumber == 0 && environment != "test" {
		return fmt.Errorf("API_HTTP_ADDRESS may use port zero only in test")
	}
	return nil
}

func LoadWorker(lookup LookupEnv) (Worker, error) {
	environment, err := loadEnvironment(lookup)
	if err != nil {
		return Worker{}, err
	}
	shutdownTimeout, err := loadDuration(
		lookup, "WORKER_SHUTDOWN_TIMEOUT", time.Minute, time.Second, 10*time.Minute,
	)
	if err != nil {
		return Worker{}, err
	}
	return Worker{Environment: environment, ShutdownTimeout: shutdownTimeout}, nil
}

func loadEnvironment(lookup LookupEnv) (string, error) {
	environment := valueOrDefault(lookup, "APP_ENV", "development")
	switch environment {
	case "development", "test", "staging", "production":
		return environment, nil
	default:
		return "", fmt.Errorf("APP_ENV must name a supported environment")
	}
}

func loadDuration(
	lookup LookupEnv,
	name string,
	fallback time.Duration,
	minimum time.Duration,
	maximum time.Duration,
) (time.Duration, error) {
	raw, ok := lookup(name)
	if !ok {
		return fallback, nil
	}
	value, err := time.ParseDuration(raw)
	if err != nil {
		return 0, fmt.Errorf("%s must be a duration", name)
	}
	if value < minimum || value > maximum {
		return 0, fmt.Errorf("%s is outside its allowed bounds", name)
	}
	return value, nil
}

func valueOrDefault(lookup LookupEnv, name string, fallback string) string {
	if value, ok := lookup(name); ok {
		return value
	}
	return fallback
}
