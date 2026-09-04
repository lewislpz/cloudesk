package config

import (
	"strings"
	"testing"
	"time"
)

func TestLoadAPIUsesBoundedDefaults(t *testing.T) {
	t.Parallel()

	got, err := LoadAPI(mapLookup(nil))
	if err != nil {
		t.Fatalf("LoadAPI() error = %v", err)
	}

	if got.Environment != "development" {
		t.Errorf("Environment = %q, want development", got.Environment)
	}
	if got.HTTP.Address != ":8080" {
		t.Errorf("HTTP.Address = %q, want :8080", got.HTTP.Address)
	}
	if got.HTTP.ReadHeaderTimeout != 5*time.Second {
		t.Errorf("HTTP.ReadHeaderTimeout = %s, want 5s", got.HTTP.ReadHeaderTimeout)
	}
	if got.HTTP.ReadTimeout != 15*time.Second {
		t.Errorf("HTTP.ReadTimeout = %s, want 15s", got.HTTP.ReadTimeout)
	}
	if got.HTTP.IdleTimeout != 60*time.Second {
		t.Errorf("HTTP.IdleTimeout = %s, want 1m", got.HTTP.IdleTimeout)
	}
	if got.HTTP.RequestTimeout != 10*time.Second {
		t.Errorf("HTTP.RequestTimeout = %s, want 10s", got.HTTP.RequestTimeout)
	}
	if got.HTTP.ShutdownTimeout != 30*time.Second {
		t.Errorf("HTTP.ShutdownTimeout = %s, want 30s", got.HTTP.ShutdownTimeout)
	}
}

func TestLoadAPIRejectsInvalidValuesWithoutEchoingThem(t *testing.T) {
	t.Parallel()

	tests := map[string]struct {
		name  string
		value string
	}{
		"environment":         {name: "APP_ENV", value: "prod"},
		"address":             {name: "API_HTTP_ADDRESS", value: "8080"},
		"named port":          {name: "API_HTTP_ADDRESS", value: "localhost:http"},
		"port zero":           {name: "API_HTTP_ADDRESS", value: "localhost:0"},
		"read header timeout": {name: "API_READ_HEADER_TIMEOUT", value: "0s"},
		"read timeout":        {name: "API_READ_TIMEOUT", value: "31s"},
		"idle timeout":        {name: "API_IDLE_TIMEOUT", value: "1s"},
		"request timeout":     {name: "API_REQUEST_TIMEOUT", value: "0s"},
		"shutdown timeout":    {name: "API_SHUTDOWN_TIMEOUT", value: "3m"},
	}

	for name, test := range tests {
		t.Run(name, func(t *testing.T) {
			t.Parallel()
			_, err := LoadAPI(mapLookup(map[string]string{test.name: test.value}))
			if err == nil {
				t.Fatal("LoadAPI() error = nil, want validation error")
			}
			if !strings.Contains(err.Error(), test.name) {
				t.Errorf("error %q does not name %s", err, test.name)
			}
			if strings.Contains(err.Error(), test.value) {
				t.Errorf("error %q echoes rejected value", err)
			}
		})
	}
}

func TestLoadAPIAllowsEphemeralPortInTests(t *testing.T) {
	t.Parallel()

	got, err := LoadAPI(mapLookup(map[string]string{
		"APP_ENV":          "test",
		"API_HTTP_ADDRESS": "127.0.0.1:0",
	}))
	if err != nil {
		t.Fatalf("LoadAPI() error = %v", err)
	}
	if got.HTTP.Address != "127.0.0.1:0" {
		t.Errorf("HTTP.Address = %q, want ephemeral test address", got.HTTP.Address)
	}
}

func TestLoadWorkerValidatesShutdownTimeout(t *testing.T) {
	t.Parallel()

	got, err := LoadWorker(mapLookup(map[string]string{
		"APP_ENV":                 "test",
		"WORKER_SHUTDOWN_TIMEOUT": "45s",
	}))
	if err != nil {
		t.Fatalf("LoadWorker() error = %v", err)
	}
	if got.Environment != "test" || got.ShutdownTimeout != 45*time.Second {
		t.Fatalf("LoadWorker() = %#v, want test environment and 45s timeout", got)
	}

	_, err = LoadWorker(mapLookup(map[string]string{"WORKER_SHUTDOWN_TIMEOUT": "11m"}))
	if err == nil || !strings.Contains(err.Error(), "WORKER_SHUTDOWN_TIMEOUT") {
		t.Fatalf("LoadWorker() error = %v, want named bounds error", err)
	}
}

func mapLookup(values map[string]string) LookupEnv {
	return func(name string) (string, bool) {
		value, ok := values[name]
		return value, ok
	}
}
