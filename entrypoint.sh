#!/bin/sh

[ "$EXEC_TOOL" ] || EXEC_TOOL=gosu
[ "$SBNOTE_HOST" ] || SBNOTE_HOST=0.0.0.0
[ "$SBNOTE_PORT" ] || SBNOTE_PORT=8080

set -e

echo "\
======== Welcome to SBNote ========
"

sbnote_command="python -m \
                  uvicorn \
                  main:app \
                  --app-dir server \
                  --host ${SBNOTE_HOST} \
                  --port ${SBNOTE_PORT} \
                  --proxy-headers \
                  --forwarded-allow-ips '*'"

if [ `id -u` -eq 0 ] && [ `id -g` -eq 0 ]; then
    echo Setting file permissions...
    chown -R ${PUID}:${PGID} ${SBNOTE_PATH}

    echo Starting SBNote as user ${PUID}...
    exec ${EXEC_TOOL} ${PUID}:${PGID} ${sbnote_command}

else
    echo "A user was set by docker, skipping file permission changes."
    echo Starting SBNote as user $(id -u)...
    exec ${sbnote_command}
fi
