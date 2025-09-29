#!/bin/bash

# Test script to check nginx configuration setup

echo "Testing nginx directory structure..."

# Check if nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "ERROR: nginx is not installed"
    exit 1
fi

echo "✓ nginx is installed"

# Check main nginx.conf
if [ -f /etc/nginx/nginx.conf ]; then
    echo "✓ nginx.conf exists"
else
    echo "ERROR: nginx.conf not found"
    exit 1
fi

# Check directory structure
if [ -d /etc/nginx/sites-available ]; then
    echo "✓ sites-available directory exists"
    NGINX_AVAILABLE="/etc/nginx/sites-available"
    NGINX_ENABLED="/etc/nginx/sites-enabled"
elif [ -d /etc/nginx/conf.d ]; then
    echo "✓ conf.d directory exists (using conf.d structure)"
    NGINX_AVAILABLE="/etc/nginx/conf.d"
    NGINX_ENABLED="/etc/nginx/conf.d"
else
    echo "Creating sites-available and sites-enabled directories..."
    mkdir -p /etc/nginx/sites-available
    mkdir -p /etc/nginx/sites-enabled
    NGINX_AVAILABLE="/etc/nginx/sites-available"
    NGINX_ENABLED="/etc/nginx/sites-enabled"
fi

# Check if sites-enabled is included in nginx.conf
if grep -q "sites-enabled" /etc/nginx/nginx.conf; then
    echo "✓ sites-enabled is included in nginx.conf"
elif grep -q "conf.d" /etc/nginx/nginx.conf; then
    echo "✓ conf.d is included in nginx.conf"
else
    echo "Adding sites-enabled include to nginx.conf..."
    sed -i '/http {/a\\tinclude /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
    echo "✓ Added sites-enabled include"
fi

# Test nginx configuration
if nginx -t; then
    echo "✓ nginx configuration test passed"
else
    echo "ERROR: nginx configuration test failed"
    exit 1
fi

echo ""
echo "Nginx setup is ready for deployment!"
echo "Available: $NGINX_AVAILABLE"
echo "Enabled: $NGINX_ENABLED"
