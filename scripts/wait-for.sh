#!/usr/bin/env sh
set -e
HOST="$1"; SHIFTED=${1#*:}; PORT=${SHIFTED:-80}
until nc -z $(echo "$HOST" | cut -d: -f1) $(echo "$HOST" | cut -d: -f2); do
echo "Waiting for $HOST..."; sleep 2;
done
echo "$HOST is up"