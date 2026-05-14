#!/usr/bin/env sh
set -e

host="$1"
shift

until nc -z ${host%:*} ${host#*:}; do
  echo "Waiting for $host..."
  sleep 1
done

exec "$@"
