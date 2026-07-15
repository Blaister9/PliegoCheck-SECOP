#!/usr/bin/env sh
set -eu
: "${PLIEGOCHECK_RESTRICTED_ENV_FILE:?Define PLIEGOCHECK_RESTRICTED_ENV_FILE}"
exec python3 "$(dirname "$0")/controller.py" --env-file "$PLIEGOCHECK_RESTRICTED_ENV_FILE" "$@"
