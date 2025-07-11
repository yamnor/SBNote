#!/bin/sh

: "${APP_PORT:=8080}"
: "${SBNOTE_PATH_PREFIX:=}"

curl -f http://localhost:${APP_PORT}${SBNOTE_PATH_PREFIX}/health || exit 1
