#!/bin/sh
set -e

if [ -f /app/env.yaml ]; then
    eval "$(python /app/scripts/yaml_to_env.py /app/env.yaml)"
fi

exec "$@"
