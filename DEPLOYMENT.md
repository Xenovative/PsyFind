# PsyFind Deployment Guide

This guide covers multiple deployment options for the PsyFind application.

## Prerequisites

- Linux server (Ubuntu 20.04+ or CentOS 8+ recommended)
- Root or sudo access
- Domain name (optional, can use IP address)
- SSL certificate (optional, for HTTPS)

## Deployment Options

### 1. Traditional Server Deployment

#### Quick Start
```bash
# Make deployment script executable
chmod +x deploy.sh

# Run full deployment
sudo ./deploy.sh

# Or with custom domain and ports
sudo DOMAIN=your-domain.com ./deploy.sh
sudo DOMAIN=your-domain.com APP_PORT=8000 HTTP_PORT=8080 ./deploy.sh
```

#### Manual Steps
1. **Prepare the server:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install required packages
   sudo apt install -y python3 python3-pip python3-venv nginx supervisor git curl
   ```

2. **Deploy the application:**
   ```bash
   sudo ./deploy.sh deploy
   ```

3. **Configure environment:**
   - Edit `/opt/psyfind/.env.production`
   - Set your API keys and passwords
   - Restart the service: `sudo systemctl restart psyfind`

#### Service Management
```bash
# Start services
sudo ./deploy.sh start

# Stop services
sudo ./deploy.sh stop

# Restart services
sudo ./deploy.sh restart

# Check status
sudo ./deploy.sh status

# View logs
sudo ./deploy.sh logs

# Update application
sudo ./deploy.sh update
```

### 2. Docker Deployment

#### Quick Start
```bash
# Make deployment script executable
chmod +x deploy-docker.sh

# Deploy with Docker
./deploy-docker.sh deploy

# Or with custom ports
APP_PORT=8000 HTTP_PORT=8080 ./deploy-docker.sh deploy
```

#### Prerequisites
- Docker and Docker Compose installed
- `.env.production` file configured

#### Docker Commands
```bash
# Deploy
./deploy-docker.sh deploy

# Start/stop services
./deploy-docker.sh start
./deploy-docker.sh stop

# View logs
./deploy-docker.sh logs

# Update application
./deploy-docker.sh update
```

## Configuration

### Port Configuration

Both deployment scripts support custom port configuration through environment variables:

- **APP_PORT** - Internal application port (default: 5000)
- **HTTP_PORT** - External HTTP port (default: 80)  
- **HTTPS_PORT** - External HTTPS port (default: 443)

**Examples:**
```bash
# Traditional deployment with custom ports
sudo APP_PORT=8000 HTTP_PORT=8080 HTTPS_PORT=8443 ./deploy.sh deploy

# Docker deployment with custom ports
APP_PORT=3000 HTTP_PORT=3080 ./deploy-docker.sh deploy

# Non-standard HTTP port (useful for development/testing)
HTTP_PORT=8080 ./deploy-docker.sh deploy
```

### Environment Variables

Edit `.env.production` with your settings:

```bash
# LLM Configuration
LLM_PROVIDER=auto
OPENAI_API_KEY=your_openai_api_key_here
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Security (IMPORTANT: Change these!)
FLASK_SECRET_KEY=your_secure_random_key_here
ADMIN_PASSWORD=your_admin_password
DOCTOR_PASSWORD=your_doctor_password
PASSWORD_SALT=your_unique_salt
```

### SSL/HTTPS Setup

#### Option 1: Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Option 2: Custom Certificate
1. Place your certificate files in `/etc/ssl/certs/`
2. Update nginx configuration
3. Restart nginx: `sudo systemctl restart nginx`

### Database Backup

```bash
# Create backup
sudo -u psyfind cp /opt/psyfind/psyfind.db /opt/psyfind/backups/psyfind_$(date +%Y%m%d_%H%M%S).db

# Automated backup (add to crontab)
0 2 * * * /opt/psyfind/backup.sh
```

## Monitoring

### System Monitoring
```bash
# Check service status
sudo systemctl status psyfind
sudo systemctl status nginx

# View resource usage
htop
df -h
free -h

# Check logs
sudo journalctl -u psyfind -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Application Health
- Health check endpoint: `http://your-domain.com/health`
- Admin panel: `http://your-domain.com/admin`

## Security Considerations

### Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Firewalld (CentOS)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### Security Checklist
- [ ] Change default passwords in `.env.production`
- [ ] Generate secure Flask secret key
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall rules
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup database regularly

## Troubleshooting

### Common Issues

1. **Service won't start:**
   ```bash
   sudo journalctl -u psyfind -n 50
   # Check for Python errors or missing dependencies
   ```

2. **Nginx 502 Bad Gateway:**
   ```bash
   # Check if PsyFind service is running
   sudo systemctl status psyfind
   
   # Check nginx configuration
   sudo nginx -t
   ```

3. **Permission errors:**
   ```bash
   # Fix ownership
   sudo chown -R psyfind:psyfind /opt/psyfind
   ```

4. **Database issues:**
   ```bash
   # Check database file permissions
   ls -la /opt/psyfind/psyfind.db
   
   # Recreate database if corrupted
   sudo -u psyfind python3 /opt/psyfind/app.py
   ```

### Performance Tuning

1. **Increase worker processes:**
   Edit `/etc/systemd/system/psyfind.service`:
   ```
   ExecStart=/opt/psyfind/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 5 --timeout 120 app:app
   ```

2. **Nginx optimization:**
   - Enable gzip compression
   - Configure caching headers
   - Increase worker connections

3. **Database optimization:**
   - Regular VACUUM operations
   - Index optimization
   - Consider PostgreSQL for high load

## Scaling

### Horizontal Scaling
- Use load balancer (nginx, HAProxy)
- Multiple application instances
- Shared database (PostgreSQL/MySQL)
- Redis for session storage

### Vertical Scaling
- Increase server resources
- Optimize application code
- Database tuning
- Caching strategies

## Support

For issues and questions:
1. Check logs first
2. Review this deployment guide
3. Check the main README.md
4. Create an issue in the project repository

## Maintenance

### Regular Tasks
- Update system packages monthly
- Backup database weekly
- Monitor disk space
- Review access logs
- Update SSL certificates
- Security patches

### Update Process
```bash
# Traditional deployment
sudo ./deploy.sh update

# Docker deployment
./deploy-docker.sh update
```
