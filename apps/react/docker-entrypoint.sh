#!/bin/sh
set -e

# Substitute only our env vars, leave nginx vars ($host, $uri, etc.) untouched
envsubst '${PORT} ${BACKEND_URL}' \
  < /etc/nginx/nginx.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
