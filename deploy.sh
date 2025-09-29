#!/bin/bash

# PsyFind Deployment Script
# Supports Ubuntu/Debian and CentOS/RHEL systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="psyfind"
APP_USER="psyfind"
APP_DIR="/opt/psyfind"
SERVICE_NAME="psyfind"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
DOMAIN="${DOMAIN:-localhost}"
APP_PORT="${APP_PORT:-5000}"
HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="${HTTPS_PORT:-443}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    else
        log_error "Cannot detect OS"
        exit 1
    fi
    
    if [[ "$OS" == *"Ubuntu"* ]] || [[ "$OS" == *"Debian"* ]]; then
        PACKAGE_MANAGER="apt"
        INSTALL_CMD="apt-get install -y"
        UPDATE_CMD="apt-get update"
    elif [[ "$OS" == *"CentOS"* ]] || [[ "$OS" == *"Red Hat"* ]] || [[ "$OS" == *"Rocky"* ]]; then
        PACKAGE_MANAGER="yum"
        INSTALL_CMD="yum install -y"
        UPDATE_CMD="yum update"
    else
        log_error "Unsupported OS: $OS"
        exit 1
    fi
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root"
        exit 1
    fi
}

fix_apt_repositories() {
    log_info "Fixing APT repository issues..."
    
    # Accept changed repository labels for common PPAs
    if [ -f /etc/apt/sources.list.d/ondrej-ubuntu-apache2-jammy.list ]; then
        log_info "Accepting Apache2 PPA label change"
        apt-get update --allow-releaseinfo-change -o Acquire::AllowInsecureRepositories=true 2>/dev/null || true
    fi
    
    if [ -f /etc/apt/sources.list.d/ondrej-ubuntu-php-jammy.list ]; then
        log_info "Accepting PHP PPA label change"
        apt-get update --allow-releaseinfo-change -o Acquire::AllowInsecureRepositories=true 2>/dev/null || true
    fi
    
    # Remove problematic nginx repository
    if [ -f /etc/apt/sources.list.d/nginx.list ]; then
        log_warning "Removing problematic nginx repository"
        rm -f /etc/apt/sources.list.d/nginx.list
    fi
    
    # Clean apt cache
    apt-get clean
    rm -rf /var/lib/apt/lists/*
    
    log_success "Repository issues fixed"
}

install_dependencies() {
    log_info "Installing system dependencies..."
    
    if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
        # Fix repository issues first
        fix_apt_repositories
        
        # Update package lists
        apt-get update
        
        # Install dependencies
        $INSTALL_CMD python3 python3-pip python3-venv nginx supervisor git curl
    else
        $UPDATE_CMD
        $INSTALL_CMD python3 python3-pip nginx supervisor git curl
        # Install python3-venv equivalent for CentOS/RHEL
        python3 -m pip install virtualenv
    fi
    
    log_success "System dependencies installed"
}

create_user() {
    log_info "Creating application user..."
    
    if ! id "$APP_USER" &>/dev/null; then
        useradd --system --shell /bin/bash --home-dir $APP_DIR --create-home $APP_USER
        log_success "User $APP_USER created"
    else
        log_warning "User $APP_USER already exists"
    fi
}

setup_application() {
    log_info "Setting up application..."
    
    # Create application directory
    mkdir -p $APP_DIR
    
    # Copy application files
    if [ -d "$(pwd)" ]; then
        cp -r . $APP_DIR/
        # Remove git directory and other unnecessary files
        rm -rf $APP_DIR/.git $APP_DIR/venv $APP_DIR/deploy.sh
    else
        log_error "Please run this script from the PsyFind project directory"
        exit 1
    fi
    
    # Set ownership
    chown -R $APP_USER:$APP_USER $APP_DIR
    
    log_success "Application files copied"
}

setup_python_environment() {
    log_info "Setting up Python virtual environment..."
    
    # Switch to app user and setup venv
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        python3 -m venv venv
        source venv/bin/activate
        pip install --upgrade pip
        pip install -r requirements.txt
        pip install gunicorn
    "
    
    log_success "Python environment setup complete"
}

setup_production_config() {
    log_info "Setting up production configuration..."
    
    # Create production .env file
    sudo -u $APP_USER bash -c "
        cd $APP_DIR
        cp .env.example .env.production
        sed -i 's/FLASK_ENV=development/FLASK_ENV=production/' .env.production
        sed -i 's/FLASK_DEBUG=True/FLASK_DEBUG=False/' .env.production
        sed -i 's/dev-secret-key-change-in-production/$(openssl rand -hex 32)/' .env.production
    "
    
    log_success "Production configuration created"
}

setup_systemd_service() {
    log_info "Setting up systemd service..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=PsyFind - Psychiatry Analysis Application
After=network.target

[Service]
Type=notify
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
EnvironmentFile=$APP_DIR/.env.production
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 127.0.0.1:$APP_PORT --workers 3 --timeout 120 --access-logfile - --error-logfile - app:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    log_success "Systemd service created and enabled"
}

setup_nginx() {
    log_info "Setting up Nginx configuration..."
    
    cat > $NGINX_AVAILABLE/$SERVICE_NAME << EOF
server {
    listen $HTTP_PORT;
    server_name $DOMAIN;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;
    
    location / {
        proxy_pass http://127.0.0.1:$APP_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        
        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /static {
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # Enable site
    ln -sf $NGINX_AVAILABLE/$SERVICE_NAME $NGINX_ENABLED/
    
    # Test nginx configuration
    nginx -t
    
    log_success "Nginx configuration created"
}

setup_firewall() {
    log_info "Configuring firewall..."
    
    if command -v ufw &> /dev/null; then
        ufw allow 22/tcp
        ufw allow $HTTP_PORT/tcp
        ufw allow $HTTPS_PORT/tcp
        ufw --force enable
    elif command -v firewall-cmd &> /dev/null; then
        firewall-cmd --permanent --add-service=ssh
        firewall-cmd --permanent --add-port=$HTTP_PORT/tcp
        firewall-cmd --permanent --add-port=$HTTPS_PORT/tcp
        firewall-cmd --reload
    fi
    
    log_success "Firewall configured"
}

start_services() {
    log_info "Starting services..."
    
    systemctl start $SERVICE_NAME
    systemctl restart nginx
    
    log_success "Services started"
}

show_status() {
    echo
    log_info "Deployment Status:"
    echo "=================="
    
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "PsyFind service is running"
    else
        log_error "PsyFind service is not running"
    fi
    
    if systemctl is-active --quiet nginx; then
        log_success "Nginx is running"
    else
        log_error "Nginx is not running"
    fi
    
    echo
    if [ "$HTTP_PORT" = "80" ]; then
        log_info "Application URL: http://$DOMAIN"
    else
        log_info "Application URL: http://$DOMAIN:$HTTP_PORT"
    fi
    log_info "Service logs: journalctl -u $SERVICE_NAME -f"
    log_info "Nginx logs: tail -f /var/log/nginx/access.log"
    echo
}

# Main deployment process
main() {
    log_info "Starting PsyFind deployment..."
    
    check_root
    detect_os
    
    log_info "Detected OS: $OS"
    log_info "Package Manager: $PACKAGE_MANAGER"
    
    install_dependencies
    create_user
    setup_application
    setup_python_environment
    setup_production_config
    setup_systemd_service
    setup_nginx
    setup_firewall
    start_services
    show_status
    
    log_success "PsyFind deployment completed successfully!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "start")
        systemctl start $SERVICE_NAME
        systemctl start nginx
        log_success "Services started"
        ;;
    "stop")
        systemctl stop $SERVICE_NAME
        log_success "PsyFind service stopped"
        ;;
    "restart")
        systemctl restart $SERVICE_NAME
        systemctl restart nginx
        log_success "Services restarted"
        ;;
    "status")
        show_status
        ;;
    "logs")
        journalctl -u $SERVICE_NAME -f
        ;;
    "update")
        log_info "Updating application..."
        systemctl stop $SERVICE_NAME
        # Backup current version
        cp -r $APP_DIR $APP_DIR.backup.$(date +%Y%m%d_%H%M%S)
        # Update code (assumes git repository)
        sudo -u $APP_USER bash -c "cd $APP_DIR && git pull"
        # Update dependencies
        sudo -u $APP_USER bash -c "cd $APP_DIR && source venv/bin/activate && pip install -r requirements.txt"
        systemctl start $SERVICE_NAME
        log_success "Application updated"
        ;;
    "fix-repos")
        if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
            fix_apt_repositories
            apt-get update
            log_success "Repository issues fixed"
        else
            log_warning "Repository fix only available for APT-based systems"
        fi
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|status|logs|update|fix-repos}"
        echo
        echo "Commands:"
        echo "  deploy     - Full deployment (default)"
        echo "  start      - Start services"
        echo "  stop       - Stop PsyFind service"
        echo "  restart    - Restart services"
        echo "  status     - Show service status"
        echo "  logs       - Show live logs"
        echo "  update     - Update application code"
        echo "  fix-repos  - Fix APT repository issues"
        echo
        echo "Environment Variables:"
        echo "  DOMAIN      - Domain name (default: localhost)"
        echo "  APP_PORT    - Application port (default: 5000)"
        echo "  HTTP_PORT   - HTTP port (default: 80)"
        echo "  HTTPS_PORT  - HTTPS port (default: 443)"
        echo
        echo "Examples:"
        echo "  sudo DOMAIN=example.com ./deploy.sh deploy"
        echo "  sudo APP_PORT=8000 HTTP_PORT=8080 ./deploy.sh deploy"
        exit 1
        ;;
esac
