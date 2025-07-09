#!/bin/sh

curl -f http://localhost:${SBNOTE_PORT}${SBNOTE_PATH_PREFIX}/health || exit 1
