FROM nginx:alpine

# Копируем все статические файлы в директорию, которую обслуживает nginx
COPY index.html /usr/share/nginx/html
COPY style.css /usr/share/nginx/html
COPY script.js /usr/share/nginx/html

EXPOSE 80