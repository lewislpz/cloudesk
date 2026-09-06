#!/bin/sh

set -eu

action=${1:-up}
profile=${2:-persistent}

case "$profile" in
  persistent | ephemeral) ;;
  *)
    echo "profile must be persistent or ephemeral" >&2
    exit 2
    ;;
esac

project_prefix=${CLOUDESK_COMPOSE_PROJECT_PREFIX:-clouddesk-local}
if [ "$profile" = "persistent" ]; then
  project=$project_prefix
else
  project=${project_prefix}-ephemeral
fi

compose() {
  docker compose --project-name "$project" "$@"
}

case "$action" in
  up)
    if [ "$profile" = "persistent" ]; then
      compose up --detach --wait
    else
      compose --profile ephemeral up --detach --wait postgres-ephemeral oidc-ephemeral
    fi
    ;;
  down)
    if [ "$profile" = "persistent" ]; then
      compose down --remove-orphans
    else
      compose --profile ephemeral down --remove-orphans
    fi
    ;;
  status)
    if [ "$profile" = "persistent" ]; then
      compose ps
    else
      compose --profile ephemeral ps
    fi
    ;;
  reset)
    if [ "$profile" != "persistent" ]; then
      echo "reset is only meaningful for the persistent profile" >&2
      exit 2
    fi
    compose down --volumes --remove-orphans
    ;;
  *)
    echo "usage: $0 {up|down|status|reset} [persistent|ephemeral]" >&2
    exit 2
    ;;
esac
