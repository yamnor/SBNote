#!/bin/bash

: "${EXEC_TOOL:=gosu}"
: "${APP_HOST:=0.0.0.0}"
: "${APP_PORT:=8080}"

set -euo pipefail

printf '\n%s\n' "🚀 Starting SBNote on ${APP_HOST}:${APP_PORT}"

sbnote_command="python -m \
                  uvicorn \
                  main:app \
                  --app-dir server \
                  --host ${APP_HOST} \
                  --port ${APP_PORT} \
                  --proxy-headers \
                  --forwarded-allow-ips '*'"

if [ $(id -u) -eq 0 ] && [ $(id -g) -eq 0 ]; then
    printf '🔧 %s\n' "Setting file permissions..."
    chown -R "${PUID}:${PGID}" "${SBNOTE_PATH}"

    printf '👤 %s\n' "Starting SBNote as user ${PUID}..."
    exec ${EXEC_TOOL} ${PUID}:${PGID} ${sbnote_command}

else
    printf 'ℹ️  %s\n' "A user was set by docker, skipping file permission changes."
    printf '👤 %s\n' "Starting SBNote as user $(id -u)..."
    exec ${sbnote_command}
fi
