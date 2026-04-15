#!/bin/sh
# frontend/docker-entrypoint.sh

# Use envsubst to replace $BACKEND_URL in the Nginx template with the real env var
# Then write the result to the final Nginx config file.
# Note: we only replace $BACKEND_URL to avoid breaking other Nginx variables.
envsubst '$BACKEND_URL' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start Nginx
exec "$@"
