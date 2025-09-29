#!/bin/bash

# PsyFind Docker Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
APP_PORT="${APP_PORT:-5000}"
HTTP_PORT="${HTTP_PORT:-80}"
HTTPS_PORT="${HTTPS_PORT:-443}"

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

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_success "Docker and Docker Compose are available"
}

setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f ".env.production" ]; then
        log_error ".env.production file not found. Please create it first."
        exit 1
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Create SSL directory (for future HTTPS setup)
    mkdir -p ssl
    
    log_success "Environment setup complete"
}

build_and_deploy() {
    log_info "Building and deploying PsyFind with Docker..."
    
    # Export port variables for docker-compose
    export APP_PORT HTTP_PORT HTTPS_PORT
    
    # Build and start services
    docker-compose up --build -d
    
    log_success "PsyFind deployed successfully"
}

show_status() {
    echo
    log_info "Deployment Status:"
    echo "=================="
    
    docker-compose ps
    
    echo
    if [ "$HTTP_PORT" = "80" ]; then
        log_info "Application URL: http://localhost"
    else
        log_info "Application URL: http://localhost:$HTTP_PORT"
    fi
    log_info "View logs: docker-compose logs -f"
    log_info "Stop services: docker-compose down"
    echo
}

wait_for_health() {
    log_info "Waiting for application to be healthy..."
    
    for i in {1..30}; do
        if curl -f http://localhost:$HTTP_PORT/health &>/dev/null; then
            log_success "Application is healthy"
            return 0
        fi
        sleep 2
    done
    
    log_warning "Health check timeout. Check logs with: docker-compose logs"
}

# Main deployment process
main() {
    log_info "Starting PsyFind Docker deployment..."
    
    check_docker
    setup_environment
    build_and_deploy
    wait_for_health
    show_status
    
    log_success "PsyFind Docker deployment completed!"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "start")
        docker-compose start
        log_success "Services started"
        ;;
    "stop")
        docker-compose stop
        log_success "Services stopped"
        ;;
    "restart")
        docker-compose restart
        log_success "Services restarted"
        ;;
    "down")
        docker-compose down
        log_success "Services stopped and removed"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "status")
        docker-compose ps
        ;;
    "build")
        docker-compose build --no-cache
        log_success "Images rebuilt"
        ;;
    "update")
        log_info "Updating application..."
        docker-compose down
        docker-compose pull
        docker-compose up --build -d
        log_success "Application updated"
        ;;
    *)
        echo "Usage: $0 {deploy|start|stop|restart|down|logs|status|build|update}"
        echo
        echo "Commands:"
        echo "  deploy   - Full deployment (default)"
        echo "  start    - Start services"
        echo "  stop     - Stop services"
        echo "  restart  - Restart services"
        echo "  down     - Stop and remove services"
        echo "  logs     - Show live logs"
        echo "  status   - Show service status"
        echo "  build    - Rebuild images"
        echo "  update   - Update and redeploy"
        echo
        echo "Environment Variables:"
        echo "  APP_PORT    - Application port (default: 5000)"
        echo "  HTTP_PORT   - HTTP port (default: 80)"
        echo "  HTTPS_PORT  - HTTPS port (default: 443)"
        echo
        echo "Examples:"
        echo "  APP_PORT=8000 HTTP_PORT=8080 ./deploy-docker.sh deploy"
        echo "  HTTP_PORT=3000 ./deploy-docker.sh deploy"
        exit 1
        ;;
esac
