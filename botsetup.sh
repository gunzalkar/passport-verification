#!/bin/bash

# Update and upgrade the system
apt update && apt -y dist-upgrade

# Install required packages
apt install -y nginx tesseract-ocr

# Install required Python packages
pip3 install easyocr mrz fastapi uvicorn gunicorn numpy==1.26.3 opencv-python python-multipart

# Create Nginx configuration for the app
NGINX_CONF="/etc/nginx/sites-enabled/my_app"
echo "server {
    listen 8020;

    location / {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host \$host;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }
}" > $NGINX_CONF

# Remove the default Nginx site configuration
#unlink /etc/nginx/sites-enabled/default

# Restart Nginx to apply the changes
systemctl restart nginx

echo "Done"
