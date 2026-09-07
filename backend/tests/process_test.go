//go:build !windows

package tests

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
	"time"
)

func TestProcessesHandleSIGTERM(t *testing.T) {
	for _, process := range []struct {
		name        string
		packageDir  string
		environment []string
	}{
		{
			name:        "api",
			packageDir:  "./cmd/api",
			environment: []string{"APP_ENV=test", "API_HTTP_ADDRESS=127.0.0.1:0"},
		},
		{
			name:        "worker",
			packageDir:  "./cmd/worker",
			environment: []string{"APP_ENV=test"},
		},
	} {
		t.Run(process.name, func(t *testing.T) {
			binary := filepath.Join(t.TempDir(), process.name)
			build := exec.Command("go", "build", "-o", binary, process.packageDir)
			build.Dir = ".."
			if output, err := build.CombinedOutput(); err != nil {
				t.Fatalf("build %s: %v\n%s", process.name, err, output)
			}

			command := exec.Command(binary)
			command.Env = processEnvironment(process.environment)
			var logs bytes.Buffer
			stderr, err := command.StderrPipe()
			if err != nil {
				t.Fatalf("stderr pipe: %v", err)
			}
			if err := command.Start(); err != nil {
				t.Fatalf("start %s: %v", process.name, err)
			}

			started := make(chan struct{})
			go func() {
				scanner := bufio.NewScanner(stderr)
				for scanner.Scan() {
					logs.WriteString(scanner.Text())
					logs.WriteByte('\n')
					if strings.Contains(scanner.Text(), "process started") {
						select {
						case <-started:
						default:
							close(started)
						}
					}
				}
			}()

			select {
			case <-started:
			case <-time.After(5 * time.Second):
				_ = command.Process.Kill()
				t.Fatalf("%s did not start; logs:\n%s", process.name, logs.String())
			}
			if err := command.Process.Signal(syscall.SIGTERM); err != nil {
				t.Fatalf("signal %s: %v", process.name, err)
			}

			done := make(chan error, 1)
			go func() { done <- command.Wait() }()
			select {
			case err := <-done:
				if err != nil {
					t.Fatalf("%s exit after SIGTERM: %v; logs:\n%s", process.name, err, logs.String())
				}
			case <-time.After(5 * time.Second):
				_ = command.Process.Kill()
				t.Fatalf("%s did not stop after SIGTERM; logs:\n%s", process.name, logs.String())
			}
		})
	}
}

func processEnvironment(overrides []string) []string {
	configurationNames := map[string]struct{}{
		"APP_ENV":                 {},
		"API_HTTP_ADDRESS":        {},
		"API_READ_HEADER_TIMEOUT": {},
		"API_READ_TIMEOUT":        {},
		"API_IDLE_TIMEOUT":        {},
		"API_REQUEST_TIMEOUT":     {},
		"API_SHUTDOWN_TIMEOUT":    {},
		"WORKER_SHUTDOWN_TIMEOUT": {},
	}
	environment := make([]string, 0, len(os.Environ())+len(overrides))
	for _, entry := range os.Environ() {
		name, _, found := strings.Cut(entry, "=")
		if !found {
			continue
		}
		if _, isConfiguration := configurationNames[name]; isConfiguration {
			continue
		}
		environment = append(environment, entry)
	}
	return append(environment, overrides...)
}

func TestProcessesRejectConfigurationWithoutLeakingValues(t *testing.T) {
	for _, process := range []string{"api", "worker"} {
		t.Run(process, func(t *testing.T) {
			binary := filepath.Join(t.TempDir(), process)
			build := exec.Command("go", "build", "-o", binary, "./cmd/"+process)
			build.Dir = ".."
			if output, err := build.CombinedOutput(); err != nil {
				t.Fatalf("build: %v\n%s", err, output)
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			command := exec.CommandContext(ctx, binary)
			const sensitiveValue = "synthetic-private-configuration-value"
			command.Env = processEnvironment([]string{"APP_ENV=" + sensitiveValue})
			output, err := command.CombinedOutput()
			if ctx.Err() != nil {
				t.Fatal("invalid configuration did not fail within the startup deadline")
			}
			var exitError *exec.ExitError
			if !errors.As(err, &exitError) || exitError.ExitCode() != 1 {
				t.Fatalf("startup exit = %v, want exit 1", err)
			}
			if bytes.Contains(output, []byte(sensitiveValue)) {
				t.Fatal("startup log contains the rejected configuration value")
			}
			var event struct {
				Level string `json:"level"`
				Error string `json:"error"`
			}
			if err := json.Unmarshal(bytes.TrimSpace(output), &event); err != nil {
				t.Fatalf("startup error is not a single structured event: %v", err)
			}
			if event.Level != "ERROR" || !strings.Contains(event.Error, "APP_ENV") {
				t.Fatalf("startup error lacks safe diagnostic context: %#v", event)
			}
		})
	}
}
