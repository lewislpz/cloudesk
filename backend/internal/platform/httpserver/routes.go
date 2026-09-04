package httpserver

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/google/uuid"
	"github.com/lewislpz/cloudesk/backend/internal/gen/openapi"
	"github.com/lewislpz/cloudesk/backend/internal/platform/health"
)

type healthHandler struct {
	openapi.UnimplementedHandler
	readiness *health.State
}

func NewRoutes(readiness *health.State, requestTimeout time.Duration) (http.Handler, error) {
	generated, err := openapi.NewServer(healthHandler{readiness: readiness}, denySecurity{})
	if err != nil {
		return nil, err
	}

	routes := http.NewServeMux()
	routes.Handle("/health/", generated)
	return withRequestID(withRequestTimeout(requestTimeout, routes)), nil
}

func (handler healthHandler) GetLiveness(
	_ context.Context,
	params openapi.GetLivenessParams,
) (openapi.GetLivenessRes, error) {
	return healthyResponse(requestID(params.XRequestID)), nil
}

func (handler healthHandler) GetReadiness(
	_ context.Context,
	params openapi.GetReadinessParams,
) (openapi.GetReadinessRes, error) {
	requestID := requestID(params.XRequestID)
	if handler.readiness.IsReady() {
		return healthyResponse(requestID), nil
	}
	return &openapi.ServiceUnavailableHeaders{
		XRequestID: requestID,
		Response: openapi.ErrorEnvelope{Error: openapi.Error{
			Code:      "SERVICE_UNAVAILABLE",
			Message:   "The service is temporarily unavailable.",
			RequestId: requestID,
		}},
	}, nil
}

func healthyResponse(requestID openapi.RequestId) *openapi.HealthStatusHeaders {
	return &openapi.HealthStatusHeaders{
		XRequestID: requestID,
		Response: openapi.HealthStatus{
			Status: openapi.HealthStatusStatusOk,
		},
	}
}

func requestID(value openapi.OptRequestId) openapi.RequestId {
	if requestID, ok := value.Get(); ok {
		return requestID
	}
	return openapi.RequestId(uuid.NewString())
}

type denySecurity struct{}

func (denySecurity) HandleCookieSession(
	context.Context,
	openapi.OperationName,
	openapi.CookieSession,
) (context.Context, error) {
	return nil, errors.New("authenticated API operations are not enabled")
}

func withRequestID(next http.Handler) http.Handler {
	return http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		requestID := request.Header.Get("X-Request-ID")
		if openapi.RequestId(requestID).Validate() != nil {
			requestID = uuid.NewString()
			request.Header.Set("X-Request-ID", requestID)
		}
		response.Header().Set("X-Request-ID", requestID)
		next.ServeHTTP(response, request)
	})
}

func withRequestTimeout(timeout time.Duration, next http.Handler) http.Handler {
	return http.HandlerFunc(func(response http.ResponseWriter, request *http.Request) {
		ctx, cancel := context.WithTimeout(request.Context(), timeout)
		defer cancel()
		next.ServeHTTP(response, request.WithContext(ctx))
	})
}
