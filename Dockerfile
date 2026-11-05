FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY index.html multicuenta-reel.mp4 favicon.svg icon-32.png icon-180.png /usr/share/nginx/html/
COPY img/*.webp /usr/share/nginx/html/img/
EXPOSE 80
