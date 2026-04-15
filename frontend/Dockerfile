FROM nginx:alpine

# Copy static assets
COPY . /usr/share/nginx/html

# Official Nginx Docker images (since 1.19) support environment variables in templates.
# Files ending in .template in /etc/nginx/templates/ will be processed with envsubst
# and the output written to /etc/nginx/conf.d/ when the container starts.
COPY nginx.conf.template /etc/nginx/templates/default.conf.template

EXPOSE 8080

# The default Nginx entrypoint handles the template processing.
# We don't need a custom entrypoint script anymore.
CMD ["nginx", "-g", "daemon off;"]
