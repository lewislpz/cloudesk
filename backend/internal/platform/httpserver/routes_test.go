package httpserver

import (
	"encoding/json"
	"mime"
	"net/http"
	"net/http/httptest"
	"regexp"
	"testing"
	"time"

	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

var requestIDPattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$`)

func TestHealthRoutesExposeLiveAndReadySemantics(t *testing.T) {
	t.Parallel()

	readiness := health.NewState()
	handler, err := NewRoutes(readiness, 10*time.Second)
	if err != nil {
		t.Fatalf("NewRoutes() error = %v", err)
	}

	t.Run("liveness is independent of readiness", func(t *testing.T) {
		request := httptest.NewRequest(http.MethodGet, "/health/live", nil)
		request.Header.Set("X-Request-ID", "caller-123")
		response := httptest.NewRecorder()

		handler.ServeHTTP(response, request)

		assertJSONResponse(t, response, http.StatusOK, "ok", "")
		if got := response.Header().Get("X-Request-ID"); got != "caller-123" {
			t.Errorf("X-Request-ID = %q, want caller-123", got)
		}
	})

	t.Run("readiness withdraws traffic while draining", func(t *testing.T) {
		response := httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/health/ready", nil))

		assertJSONResponse(t, response, http.StatusServiceUnavailable, "", "SERVICE_UNAVAILABLE")

		readiness.MarkReady()
		response = httptest.NewRecorder()
		handler.ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/health/ready", nil))

		assertJSONResponse(t, response, http.StatusOK, "ok", "")
	})
}

func TestRequestIDMiddlewareReplacesInvalidInputAndCoversNotFound(t *testing.T) {
	t.Parallel()

	handler, err := NewRoutes(health.NewState(), 10*time.Second)
	if err != nil {
		t.Fatalf("NewRoutes() error = %v", err)
	}

	for _, path := range []string{"/health/live", "/not-found"} {
		response := httptest.NewRecorder()
		request := httptest.NewRequest(http.MethodGet, path, nil)
		request.Header.Set("X-Request-ID", "invalid request id with spaces")

		handler.ServeHTTP(response, request)

		requestID := response.Header().Get("X-Request-ID")
		if requestID == "invalid request id with spaces" || !requestIDPattern.MatchString(requestID) {
			t.Errorf("%s X-Request-ID = %q, want generated valid value", path, requestID)
		}
	}
}

func TestM1OrganizationFixtureIsNotExposed(t *testing.T) {
	t.Parallel()

	handler, err := NewRoutes(health.NewState(), 10*time.Second)
	if err != nil {
		t.Fatalf("NewRoutes() error = %v", err)
	}
	request := httptest.NewRequest(
		http.MethodGet,
		"/api/v1/organizations/2e4cf420-792d-4c89-a768-0d68e9235a7e",
		nil,
	)
	request.AddCookie(&http.Cookie{Name: "__Host-cloudesk_session", Value: "not-a-session"})
	response := httptest.NewRecorder()

	handler.ServeHTTP(response, request)

	if response.Code != http.StatusNotFound {
		t.Fatalf("status = %d, want 404", response.Code)
	}
}

func TestRequestTimeoutReachesHandlerContext(t *testing.T) {
	t.Parallel()

	var remaining time.Duration
	next := http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		deadline, ok := request.Context().Deadline()
		if !ok {
			t.Error("request context has no deadline")
			return
		}
		remaining = time.Until(deadline)
		response.WriteHeader(http.StatusNoContent)
	})

	withRequestTimeout(250*time.Millisecond, next).ServeHTTP(
		httptest.NewRecorder(),
		httptest.NewRequest(http.MethodGet, "/", nil),
	)

	if remaining <= 0 || remaining > 250*time.Millisecond {
		t.Errorf("remaining deadline = %s, want within (0, 250ms]", remaining)
	}
}

func assertJSONResponse(
	t *testing.T,
	response *httptest.ResponseRecorder,
	wantStatus int,
	wantHealth string,
	wantErrorCode string,
) {
	t.Helper()

	if response.Code != wantStatus {
		t.Fatalf("status = %d, want %d; body = %s", response.Code, wantStatus, response.Body)
	}
	mediaType, _, err := mime.ParseMediaType(response.Header().Get("Content-Type"))
	if err != nil || mediaType != "application/json" {
		t.Errorf("Content-Type = %q, want application/json media type", response.Header().Get("Content-Type"))
	}
	if requestID := response.Header().Get("X-Request-ID"); !requestIDPattern.MatchString(requestID) {
		t.Errorf("X-Request-ID = %q, want valid request ID", requestID)
	}

	var body struct {
		Status string `json:"status"`
		Error  struct {
			Code      string `json:"code"`
			RequestID string `json:"requestId"`
		} `json:"error"`
	}
	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if body.Status != wantHealth || body.Error.Code != wantErrorCode {
		t.Errorf("body = %#v, want status %q and error code %q", body, wantHealth, wantErrorCode)
	}
	if wantErrorCode != "" && body.Error.RequestID != response.Header().Get("X-Request-ID") {
		t.Errorf("body request ID = %q, want response header value", body.Error.RequestID)
	}
}
