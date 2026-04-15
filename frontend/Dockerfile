FROM nginx:alpine

# Copy static assets
COPY . /usr/share/nginx/html

# Copy Nginx template (to be processed at startup)
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template

# Copy entrypoint for env var injection
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
