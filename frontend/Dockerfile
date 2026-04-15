FROM nginx:alpine

COPY . /usr/share/nginx/html

# Expose port 8080 (Cloud Run standard for many, but we can config Nginx to listen there)
RUN sed -i 's/listen       80;/listen       8080;/g' /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
