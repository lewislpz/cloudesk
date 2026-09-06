#!/bin/sh

set -eu

api_image=${CLOUDESK_API_TEST_IMAGE:-clouddesk-api:test}
web_image=${CLOUDESK_WEB_TEST_IMAGE:-clouddesk-web:test}
api_container=clouddesk-image-test-api-$$
web_container=clouddesk-image-test-web-$$
temporary_directory=$(mktemp -d)

cleanup() {
  docker rm --force "$api_container" "$web_container" >/dev/null 2>&1 || true
  rm -r -- "$temporary_directory"
}
trap cleanup EXIT
trap 'exit 130' INT TERM

docker build --check backend
docker build --check --file frontend/Dockerfile .
docker build --build-arg IMAGE_REVISION=verification --tag "$api_image" backend
docker build --build-arg IMAGE_REVISION=verification --file frontend/Dockerfile --tag "$web_image" .

test "$(docker image inspect "$api_image" --format '{{.Config.User}}')" = "65532:65532"
test "$(docker image inspect "$web_image" --format '{{.Config.User}}')" = "node"
test "$(docker image inspect "$api_image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "verification"
test "$(docker image inspect "$web_image" --format '{{index .Config.Labels "org.opencontainers.image.revision"}}')" = "verification"
api_size=$(docker image inspect "$api_image" --format '{{.Size}}')
web_size=$(docker image inspect "$web_image" --format '{{.Size}}')
test "$api_size" -lt 10485760
test "$web_size" -lt 104857600

for image in "$api_image" "$web_image"; do
  if docker image inspect "$image" --format '{{range .Config.Env}}{{println .}}{{end}}' |
    grep -Eiq '(password|secret|token|database_url|oidc_client)'; then
    echo "runtime image environment contains a secret-like name: $image" >&2
    exit 1
  fi
  if docker history --no-trunc "$image" |
    grep -Eiq '(password|secret|token|database_url|oidc_client)'; then
    echo "image history contains a secret-like name: $image" >&2
    exit 1
  fi
done

docker run --detach --name "$api_container" --publish 127.0.0.1::8080 \
  --read-only --cap-drop ALL --security-opt no-new-privileges:true "$api_image" >/dev/null
docker run --detach --name "$web_container" --publish 127.0.0.1::3000 \
  --read-only --tmpfs /tmp:rw,nosuid,noexec,size=64m \
  --cap-drop ALL --security-opt no-new-privileges:true "$web_image" >/dev/null

api_port=$(docker port "$api_container" 8080/tcp | sed 's/.*://')
web_port=$(docker port "$web_container" 3000/tcp | sed 's/.*://')

for attempt in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:$api_port/health/ready" >/dev/null 2>&1 &&
    curl -fsS "http://127.0.0.1:$web_port/" >/dev/null 2>&1; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "container startup exceeded 30 seconds" >&2
    exit 1
  fi
  sleep 1
done

for attempt in $(seq 1 30); do
  if [ "$(docker inspect "$web_container" --format '{{.State.Health.Status}}')" = "healthy" ]; then
    break
  fi
  if [ "$attempt" -eq 30 ]; then
    echo "web image health check exceeded 30 seconds" >&2
    exit 1
  fi
  sleep 1
done

curl -fsS -H 'X-Request-ID: container-smoke' \
  -D "$temporary_directory/api.headers" \
  "http://127.0.0.1:$api_port/health/live" |
  jq -e '.status == "ok"' >/dev/null
grep -Eiq '^X-Request-Id: container-smoke' "$temporary_directory/api.headers"

for route in / /onboarding /acme-consulting; do
  curl -fsS "http://127.0.0.1:$web_port$route" | grep -Fq 'ClouDesk'
done

for container in "$api_container" "$web_container"; do
  test "$(docker inspect "$container" --format '{{.HostConfig.ReadonlyRootfs}}')" = "true"
  test "$(docker inspect "$container" --format '{{json .HostConfig.CapDrop}}')" = '["ALL"]'
  docker inspect "$container" --format '{{json .HostConfig.SecurityOpt}}' |
    jq -e 'index("no-new-privileges:true") != null' >/dev/null
done
test "$(docker exec "$web_container" id -u)" -ne 0

web_files=$(docker export "$web_container" | tar -tf -)
if printf '%s\n' "$web_files" |
  grep -Eiq '(^|/)(\.env[^/]*|Dockerfile|pnpm-lock\.yaml|[^/]+\.(ts|tsx))$'; then
  echo "web runtime image contains a forbidden build/source file" >&2
  exit 1
fi

docker stop --time 10 "$api_container" "$web_container" >/dev/null
test "$(docker inspect "$api_container" --format '{{.State.ExitCode}}')" -eq 0
# The upstream Next standalone server exits directly from SIGTERM (128 + 15).
test "$(docker inspect "$web_container" --format '{{.State.ExitCode}}')" -eq 143

printf 'ClouDesk container image smoke: PASS\n'
