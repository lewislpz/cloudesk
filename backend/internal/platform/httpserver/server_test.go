package httpserver

import (
	"context"
	"net"
	"net/http"
	"testing"
	"time"

	"github.com/lewislpz/cloudesk/backend/internal/platform/config"
	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

func TestServerWithdrawsReadinessBeforeDrainingInflightRequest(t *testing.T) {
	t.Parallel()

	readiness := health.NewState()
	requestStarted := make(chan struct{})
	releaseRequest := make(chan struct{})
	handler := http.HandlerFunc(func(response http.ResponseWriter, _ *http.Request) {
		close(requestStarted)
		<-releaseRequest
		response.WriteHeader(http.StatusNoContent)
	})
	server := New(config.HTTP{
		Address:           "127.0.0.1:0",
		ReadHeaderTimeout: time.Second,
		ReadTimeout:       time.Second,
		IdleTimeout:       time.Second,
		ShutdownTimeout:   time.Second,
	}, handler, readiness)

	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	serveDone := make(chan error, 1)
	go func() { serveDone <- server.Serve(ctx, listener) }()
	waitFor(t, readiness.IsReady)

	responseDone := make(chan error, 1)
	go func() {
		response, requestErr := http.Get("http://" + listener.Addr().String())
		if requestErr == nil {
			_ = response.Body.Close()
		}
		responseDone <- requestErr
	}()
	select {
	case <-requestStarted:
	case <-time.After(time.Second):
		t.Fatal("request did not reach handler")
	}

	cancel()
	waitFor(t, func() bool { return !readiness.IsReady() })
	close(releaseRequest)

	if err := <-responseDone; err != nil {
		t.Fatalf("in-flight request failed during graceful drain: %v", err)
	}
	select {
	case err := <-serveDone:
		if err != nil {
			t.Fatalf("Serve() error = %v", err)
		}
	case <-time.After(2 * time.Second):
		t.Fatal("server did not stop within shutdown timeout")
	}
}

func TestServerForcesCloseAfterShutdownDeadline(t *testing.T) {
	t.Parallel()

	readiness := health.NewState()
	requestStarted := make(chan struct{})
	releaseRequest := make(chan struct{})
	handler := http.HandlerFunc(func(response http.ResponseWriter, _ *http.Request) {
		close(requestStarted)
		<-releaseRequest
		response.WriteHeader(http.StatusNoContent)
	})
	server := New(config.HTTP{
		Address:           "127.0.0.1:0",
		ReadHeaderTimeout: time.Second,
		ReadTimeout:       time.Second,
		IdleTimeout:       time.Second,
		ShutdownTimeout:   20 * time.Millisecond,
	}, handler, readiness)
	listener, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatalf("listen: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	serveDone := make(chan error, 1)
	go func() { serveDone <- server.Serve(ctx, listener) }()
	waitFor(t, readiness.IsReady)

	requestDone := make(chan struct{})
	go func() {
		response, _ := http.Get("http://" + listener.Addr().String())
		if response != nil {
			_ = response.Body.Close()
		}
		close(requestDone)
	}()
	select {
	case <-requestStarted:
	case <-time.After(time.Second):
		t.Fatal("request did not reach handler")
	}

	cancel()
	select {
	case err := <-serveDone:
		if err == nil {
			t.Fatal("Serve() error = nil, want shutdown deadline error")
		}
	case <-time.After(time.Second):
		t.Fatal("server did not enforce shutdown deadline")
	}
	if readiness.IsReady() {
		t.Fatal("server remains ready after forced close")
	}
	close(releaseRequest)
	select {
	case <-requestDone:
	case <-time.After(time.Second):
		t.Fatal("forced-close request did not return")
	}
}

func waitFor(t *testing.T, condition func() bool) {
	t.Helper()
	deadline := time.Now().Add(time.Second)
	for !condition() {
		if time.Now().After(deadline) {
			t.Fatal("condition was not reached before deadline")
		}
		time.Sleep(time.Millisecond)
	}
}
