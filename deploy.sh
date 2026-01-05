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

# Configuration (can be overridden by env vars or interactive mode)
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
DRY_RUN="${DRY_RUN:-false}"
INTERACTIVE="${INTERACTIVE:-false}"

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

log_dry() {
    echo -e "${YELLOW}[DRY-RUN]${NC} Would: $1"
}

confirm() {
    local prompt="$1"
    local default="${2:-y}"
    if [[ "$INTERACTIVE" != "true" ]]; then
        return 0
    fi
    read -p "$prompt [Y/n] " response
    response=${response:-$default}
    [[ "$response" =~ ^[Yy]$ ]]
}

show_banner() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║         PsyFind Deployment Tool           ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

show_config() {
    echo -e "${BLUE}Current Configuration:${NC}"
    echo "  Domain:     $DOMAIN"
    echo "  App Port:   $APP_PORT"
    echo "  HTTP Port:  $HTTP_PORT"
    echo "  HTTPS Port: $HTTPS_PORT"
    echo "  App Dir:    $APP_DIR"
    echo "  App User:   $APP_USER"
    echo "  Skip Nginx: ${SKIP_NGINX:-false}"
    echo
}

interactive_config() {
    show_banner
    echo -e "${GREEN}Interactive Configuration${NC}"
    echo "Press Enter to accept defaults shown in brackets."
    echo
    
    read -p "Domain name [$DOMAIN]: " input
    DOMAIN="${input:-$DOMAIN}"
    
    read -p "Application port [$APP_PORT]: " input
    APP_PORT="${input:-$APP_PORT}"
    
    read -p "HTTP port [$HTTP_PORT]: " input
    HTTP_PORT="${input:-$HTTP_PORT}"
    
    read -p "Skip Nginx setup? (y/N) [${SKIP_NGINX:-n}]: " input
    if [[ "$input" =~ ^[Yy]$ ]]; then
        SKIP_NGINX="true"
    fi
    
    echo
    show_config
    read -p "Proceed with these settings? [Y/n] " confirm
    if [[ "$confirm" =~ ^[Nn]$ ]]; then
        log_error "Deployment cancelled by user"
        exit 0
    fi
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    local errors=0
    
    # Check if running from project directory
    if [ ! -f "app.py" ] && [ ! -f "requirements.txt" ]; then
        log_error "Not in PsyFind project directory (missing app.py or requirements.txt)"
        errors=$((errors + 1))
    fi
    
    # Check for required files
    if [ ! -f ".env.example" ]; then
        log_warning ".env.example not found - will need manual configuration"
    fi
    
    # Check internet connectivity
    if ! ping -c 1 google.com &>/dev/null 2>&1; then
        log_warning "No internet connection detected - package installation may fail"
    fi
    
    if [ $errors -gt 0 ]; then
        log_error "Prerequisites check failed with $errors error(s)"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
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
        
        # Ensure nginx directories exist
        mkdir -p /etc/nginx/sites-available
        mkdir -p /etc/nginx/sites-enabled
        
        # Check if sites-enabled is included in nginx.conf
        if ! grep -q "sites-enabled" /etc/nginx/nginx.conf; then
            log_info "Adding sites-enabled include to nginx.conf"
            sed -i '/http {/a\\tinclude /etc/nginx/sites-enabled/*;' /etc/nginx/nginx.conf
        fi
        
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
ExecStart=$APP_DIR/venv/bin/gunicorn --bind 0.0.0.0:$APP_PORT --workers 3 --timeout 120 --access-logfile - --error-logfile - app:app
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
    
    # Create nginx directories if they don't exist
    mkdir -p $NGINX_AVAILABLE
    mkdir -p $NGINX_ENABLED
    
    # Check if we're using sites-available/enabled structure or conf.d
    if [ ! -d "$NGINX_AVAILABLE" ] && [ -d "/etc/nginx/conf.d" ]; then
        log_info "Using nginx conf.d structure instead of sites-available"
        NGINX_AVAILABLE="/etc/nginx/conf.d"
        NGINX_ENABLED="/etc/nginx/conf.d"
        NGINX_CONFIG_FILE="$NGINX_AVAILABLE/${SERVICE_NAME}.conf"
    else
        NGINX_CONFIG_FILE="$NGINX_AVAILABLE/$SERVICE_NAME"
    fi
    
    cat > $NGINX_CONFIG_FILE << EOF
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
    
    # Enable site (only if using sites-available/enabled structure)
    if [ "$NGINX_AVAILABLE" != "$NGINX_ENABLED" ]; then
        ln -sf $NGINX_CONFIG_FILE $NGINX_ENABLED/
        log_info "Site enabled in sites-enabled"
    else
        log_info "Configuration placed in conf.d (auto-enabled)"
    fi
    
    # Remove default nginx site if it exists and conflicts
    if [ -f "$NGINX_ENABLED/default" ] && [ "$NGINX_AVAILABLE" != "$NGINX_ENABLED" ]; then
        rm -f $NGINX_ENABLED/default
        log_info "Removed default nginx site"
    fi
    
    # Test nginx configuration
    if nginx -t; then
        log_success "Nginx configuration created and tested successfully"
    else
        log_error "Nginx configuration test failed"
        log_info "Configuration file location: $NGINX_CONFIG_FILE"
        log_info "Please check the configuration manually"
        exit 1
    fi
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
    
    if [[ "${SKIP_NGINX:-false}" != "true" ]]; then
        systemctl restart nginx
    fi
    
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
    
    if [[ "${SKIP_NGINX:-false}" != "true" ]]; then
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
    else
        log_info "Direct application URL: http://$DOMAIN:$APP_PORT"
    fi
    log_info "Service logs: journalctl -u $SERVICE_NAME -f"
    if [[ "${SKIP_NGINX:-false}" != "true" ]]; then
        log_info "Nginx logs: tail -f /var/log/nginx/access.log"
    fi
    echo
}

# Main deployment process
main() {
    show_banner
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY-RUN MODE - No changes will be made"
        echo
    fi
    
    check_root
    detect_os
    
    if [[ "$INTERACTIVE" == "true" ]]; then
        interactive_config
    fi
    
    check_prerequisites
    
    log_info "Detected OS: $OS"
    log_info "Package Manager: $PACKAGE_MANAGER"
    
    if [[ "$DRY_RUN" != "true" ]]; then
        show_config
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_dry "Install system dependencies"
        log_dry "Create user $APP_USER"
        log_dry "Copy application to $APP_DIR"
        log_dry "Setup Python virtual environment"
        log_dry "Create production config"
        log_dry "Setup systemd service"
        if [[ "${SKIP_NGINX:-false}" != "true" ]]; then
            log_dry "Setup Nginx reverse proxy"
            log_dry "Configure firewall"
        fi
        log_dry "Start services"
        log_success "Dry run complete - no changes made"
        exit 0
    fi
    
    install_dependencies
    create_user
    setup_application
    setup_python_environment
    setup_production_config
    setup_systemd_service
    
    # Skip nginx and firewall for testing
    if [[ "${SKIP_NGINX:-false}" == "true" ]]; then
        log_info "Skipping nginx and firewall setup (testing mode)"
    else
        setup_nginx
        setup_firewall
    fi
    
    start_services
    show_status
    
    log_success "PsyFind deployment completed successfully!"
}

uninstall() {
    log_info "Uninstalling PsyFind..."
    
    check_root
    
    # Stop services
    if systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
        systemctl stop $SERVICE_NAME
        log_info "Stopped $SERVICE_NAME service"
    fi
    
    # Disable and remove service
    if [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
        systemctl disable $SERVICE_NAME 2>/dev/null || true
        rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
        systemctl daemon-reload
        log_info "Removed systemd service"
    fi
    
    # Remove nginx config
    if [ -f "$NGINX_AVAILABLE/$SERVICE_NAME" ]; then
        rm -f "$NGINX_AVAILABLE/$SERVICE_NAME"
        rm -f "$NGINX_ENABLED/$SERVICE_NAME"
        systemctl reload nginx 2>/dev/null || true
        log_info "Removed Nginx configuration"
    fi
    if [ -f "/etc/nginx/conf.d/${SERVICE_NAME}.conf" ]; then
        rm -f "/etc/nginx/conf.d/${SERVICE_NAME}.conf"
        systemctl reload nginx 2>/dev/null || true
        log_info "Removed Nginx configuration"
    fi
    
    # Remove application directory
    if [ -d "$APP_DIR" ]; then
        read -p "Remove application directory $APP_DIR? [y/N] " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            rm -rf "$APP_DIR"
            log_info "Removed application directory"
        fi
    fi
    
    # Remove user
    if id "$APP_USER" &>/dev/null; then
        read -p "Remove user $APP_USER? [y/N] " confirm
        if [[ "$confirm" =~ ^[Yy]$ ]]; then
            userdel -r $APP_USER 2>/dev/null || userdel $APP_USER
            log_info "Removed user $APP_USER"
        fi
    fi
    
    log_success "PsyFind uninstalled"
}

show_help() {
    show_banner
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo
    echo -e "${GREEN}Commands:${NC}"
    echo "  deploy      Full deployment (default)"
    echo "  start       Start services"
    echo "  stop        Stop PsyFind service"
    echo "  restart     Restart services"
    echo "  status      Show service status"
    echo "  logs        Show live logs (Ctrl+C to exit)"
    echo "  update      Update application code from git"
    echo "  uninstall   Remove PsyFind completely"
    echo "  fix-repos   Fix APT repository issues"
    echo "  config      Show current configuration"
    echo
    echo -e "${GREEN}Options:${NC}"
    echo "  -h, --help        Show this help message"
    echo "  -i, --interactive Run in interactive mode (prompts for config)"
    echo "  -n, --dry-run     Show what would be done without making changes"
    echo
    echo -e "${GREEN}Environment Variables:${NC}"
    echo "  DOMAIN       Domain name (default: localhost)"
    echo "  APP_PORT     Application port (default: 5000)"
    echo "  HTTP_PORT    HTTP port (default: 80)"
    echo "  HTTPS_PORT   HTTPS port (default: 443)"
    echo "  SKIP_NGINX   Skip nginx setup (default: false)"
    echo
    echo -e "${GREEN}Examples:${NC}"
    echo "  sudo ./deploy.sh deploy              # Basic deployment"
    echo "  sudo ./deploy.sh -i deploy           # Interactive deployment"
    echo "  sudo ./deploy.sh --dry-run deploy    # Preview deployment"
    echo "  sudo DOMAIN=example.com ./deploy.sh deploy"
    echo "  sudo SKIP_NGINX=true ./deploy.sh deploy"
    echo
}

# Parse options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--interactive)
            INTERACTIVE="true"
            shift
            ;;
        -n|--dry-run)
            DRY_RUN="true"
            shift
            ;;
        -*)
            log_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
        *)
            break
            ;;
    esac
done

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
        detect_os
        if [[ "$PACKAGE_MANAGER" == "apt" ]]; then
            fix_apt_repositories
            apt-get update
            log_success "Repository issues fixed"
        else
            log_warning "Repository fix only available for APT-based systems"
        fi
        ;;
    "uninstall")
        uninstall
        ;;
    "config")
        show_banner
        show_config
        ;;
    *)
        show_help
        exit 1
        ;;
esac
