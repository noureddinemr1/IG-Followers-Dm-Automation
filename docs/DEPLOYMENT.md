# Deployment Guide

This guide provides comprehensive instructions for deploying the Instagram Scraper automation solution across different environments.

## Overview

The Instagram Scraper is designed as a multi-service Docker application that can be deployed in development, staging, and production environments with appropriate configurations for each.

## Prerequisites

### System Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **RAM** | 4 GB | 8 GB | 16+ GB |
| **Storage** | 10 GB | 50 GB | 100+ GB |
| **Network** | 10 Mbps | 100 Mbps | 1 Gbps |

### Software Requirements

- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Git**: Latest version
- **Operating System**: Linux (Ubuntu 20.04+), macOS 10.15+, or Windows 10+ with WSL2

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

### 2. Directory Structure

```bash
# Create application directory
sudo mkdir -p /opt/instagram-scraper
sudo chown $USER:$USER /opt/instagram-scraper
cd /opt/instagram-scraper

# Clone repository
git clone <repository-url> .

# Set permissions
chmod +x scripts/*.sh
```

### 3. Environment Configuration

```bash
# Run setup script
./scripts/setup.sh

# Configure environment files
cp .env.production .env
nano .env
```

## Environment-Specific Deployments

### Development Environment

Development environment is optimized for testing and development with:
- Debug logging enabled
- Hot reload capabilities
- Relaxed rate limiting
- Local database connections

```bash
# Deploy development environment
./scripts/deploy.sh development deploy

# Verify deployment
./scripts/deploy.sh development status

# View logs
./scripts/deploy.sh development logs
```

**Development Configuration:**
```env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
REQUESTS_PER_MINUTE=60
DEFAULT_MAX_FOLLOWERS=100
HOT_RELOAD=true
DEBUG=true
```

### Staging Environment

Staging environment mirrors production settings but with:
- Test credentials
- Moderate resource allocation
- Full monitoring enabled
- SSL certificates for testing

```bash
# Deploy staging environment
./scripts/deploy.sh staging deploy

# Run health checks
curl -k https://staging-server/health

# Monitor deployment
watch ./scripts/deploy.sh staging status
```

**Staging Configuration:**
```env
ENVIRONMENT=staging
LOG_LEVEL=INFO
REQUESTS_PER_MINUTE=40
SSL_ENABLED=true
NOTIFICATIONS_ENABLED=true
```

### Production Environment

Production environment provides:
- Maximum security hardening
- Resource optimization
- Comprehensive monitoring
- Automated backups
- High availability setup

```bash
# Deploy production environment
./scripts/deploy.sh production deploy

# Verify all services
./scripts/deploy.sh production status

# Setup monitoring
# Access Grafana at https://your-domain/grafana
```

**Production Configuration:**
```env
ENVIRONMENT=production
LOG_LEVEL=INFO
REQUESTS_PER_MINUTE=30
SSL_ENABLED=true
BACKUP_RETENTION_DAYS=30
NOTIFICATIONS_ENABLED=true
```

## Docker Compose Configuration

### Service Architecture

```yaml
# Core Services
instagram-scraper:        # Main application
instagram-scheduler:      # Automated scheduling
postgres:                # Primary database
redis:                   # Caching and sessions

# Monitoring Stack
prometheus:              # Metrics collection
grafana:                # Dashboards
loki:                   # Log aggregation

# Infrastructure
nginx:                  # Reverse proxy and load balancer
```

### Resource Allocation

```yaml
# Production resource limits
services:
  instagram-scraper:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  postgres:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Volume Management

```yaml
volumes:
  scraper_data:           # Application data
  scraper_sessions:       # Instagram sessions
  postgres_data:          # Database storage
  redis_data:            # Cache storage
  grafana_data:          # Dashboard configs
  prometheus_data:       # Metrics storage
```

## Network Configuration

### Internal Networks

```yaml
networks:
  scraper-network:        # Application services
    subnet: 172.20.0.0/16
  
  monitoring-network:     # Monitoring services
    subnet: 172.21.0.0/16
```

### Port Mapping

| Service | Internal Port | External Port | Purpose |
|---------|---------------|---------------|----------|
| nginx | 80/443 | 80/443 | HTTP/HTTPS access |
| instagram-scraper | 8080 | 8080 | API access |
| grafana | 3000 | 3000 | Monitoring dashboard |
| prometheus | 9090 | 9090 | Metrics endpoint |

### Firewall Configuration

```bash
# Allow necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

## SSL/TLS Configuration

### Automatic SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Manual SSL Certificate

```bash
# Generate self-signed certificate (development)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout docker/nginx/ssl/key.pem \
  -out docker/nginx/ssl/cert.pem

# Update nginx configuration
# ssl_certificate /etc/nginx/ssl/cert.pem;
# ssl_certificate_key /etc/nginx/ssl/key.pem;
```

## Database Setup

### PostgreSQL Configuration

```bash
# Access database
docker-compose exec postgres psql -U scraper_user -d instagram_scraper

# Create additional databases (if needed)
CREATE DATABASE instagram_scraper_staging;
CREATE USER staging_user WITH PASSWORD 'staging_password';
GRANT ALL PRIVILEGES ON DATABASE instagram_scraper_staging TO staging_user;
```

### Database Migrations

```bash
# Run migrations
./scripts/deploy.sh production migrate

# Backup before migration
./scripts/backup.sh

# Restore if needed
# docker-compose exec postgres psql -U scraper_user -d instagram_scraper < backup.sql
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'instagram-scraper'
    static_configs:
      - targets: ['instagram-scraper:8080']
    metrics_path: '/metrics'
```

### Grafana Dashboard Import

```bash
# Access Grafana
# http://localhost:3000
# Default: admin/admin

# Import dashboard
# Use dashboard ID: 12345 (custom dashboard)
# Or import from JSON file
```

### Alerting Configuration

```yaml
# Alert rules (example)
groups:
  - name: instagram-scraper-alerts
    rules:
      - alert: HighMemoryUsage
        expr: scraper_memory_usage_mb > 800
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
```

## Security Hardening

### Container Security

```dockerfile
# Use non-root user
USER appuser

# Remove unnecessary packages
RUN apt-get remove -y build-essential && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Set read-only filesystem
docker run --read-only --tmpfs /tmp
```

### Secret Management

```bash
# Use Docker secrets
echo "password123" | docker secret create postgres_password -

# Reference in compose file
secrets:
  postgres_password:
    external: true
```

### Network Security

```yaml
# Disable external access to internal services
services:
  postgres:
    ports: []  # No external ports
    networks:
      - scraper-network
```

## Load Balancing and High Availability

### Multiple Application Instances

```bash
# Scale application
./scripts/deploy.sh production scale instagram-scraper 3

# Verify scaling
docker-compose ps
```

### Database High Availability

```yaml
# PostgreSQL with replication
services:
  postgres-primary:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: master
  
  postgres-replica:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_MODE: slave
      POSTGRES_MASTER_SERVICE: postgres-primary
```

### Health Check Configuration

```yaml
healthcheck:
  test: ["CMD", "/app/healthcheck.sh"]
  interval: 30s
  timeout: 10s
  start_period: 60s
  retries: 3
```

## Backup and Recovery

### Automated Backup Setup

```bash
# Setup cron job for automated backups
crontab -e

# Add line for daily backup at 2 AM
0 2 * * * /opt/instagram-scraper/scripts/backup.sh

# Setup log rotation
sudo logrotate -d /etc/logrotate.d/instagram-scraper
```

### Disaster Recovery

```bash
# Complete system backup
tar -czf /backup/instagram-scraper-$(date +%Y%m%d).tar.gz \
  /opt/instagram-scraper \
  --exclude=/opt/instagram-scraper/volumes

# Restore procedure
cd /opt
tar -xzf /backup/instagram-scraper-20240101.tar.gz
cd instagram-scraper
./scripts/deploy.sh production deploy
```

## Performance Optimization

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Check disk usage
df -h
du -sh /opt/instagram-scraper/volumes/*

# Memory optimization
echo 'vm.swappiness=10' >> /etc/sysctl.conf
sysctl -p
```

### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

### Application Tuning

```env
# Optimize rate limiting for performance
REQUESTS_PER_MINUTE=45
MIN_DELAY=1.5
MAX_DELAY=3.0

# Connection pooling
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Troubleshooting

### Common Deployment Issues

#### 1. Port Conflicts
```bash
# Check port usage
sudo netstat -tulpn | grep :8080

# Kill process using port
sudo kill -9 $(sudo lsof -t -i:8080)
```

#### 2. Docker Daemon Issues
```bash
# Restart Docker service
sudo systemctl restart docker

# Check Docker status
sudo systemctl status docker

# View Docker logs
sudo journalctl -u docker.service
```

#### 3. Memory Issues
```bash
# Increase swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 4. Database Connection Failures
```bash
# Check database logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres pg_isready -U scraper_user

# Reset database
docker-compose down
docker volume rm instagram-scraper_postgres_data
docker-compose up -d postgres
```

### Log Analysis

```bash
# Application logs
docker-compose logs -f instagram-scraper

# System logs
sudo journalctl -f

# Error logs only
docker-compose logs instagram-scraper | grep ERROR

# Performance logs
docker-compose logs instagram-scraper | grep "Performance:"
```

## Maintenance Procedures

### Regular Maintenance Tasks

```bash
# Weekly maintenance script
#!/bin/bash

# Update images
docker-compose pull

# Clean up unused resources
docker system prune -f

# Backup data
./scripts/backup.sh

# Check logs for errors
docker-compose logs --since 7d | grep ERROR > weekly_errors.log

# Update SSL certificates
sudo certbot renew
```

### Update Procedures

```bash
# Application update
git pull origin main
./scripts/deploy.sh production update

# Rolling update (zero downtime)
docker-compose up -d --no-deps instagram-scraper
```

## Monitoring and Alerting

### Key Metrics to Monitor

- **Application Health**: Response time, error rates, uptime
- **System Resources**: CPU, memory, disk usage
- **Database Performance**: Connection count, query performance
- **Network**: Bandwidth usage, connection failures
- **Business Metrics**: Scraping success rate, data volume

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | 70% | 90% |
| Memory Usage | 80% | 95% |
| Disk Usage | 80% | 90% |
| Error Rate | 5% | 10% |
| Response Time | 2s | 5s |

## Compliance and Legal Considerations

### Data Protection
- Implement data retention policies
- Ensure GDPR compliance for EU users
- Regular data purging procedures
- Audit logging for data access

### Rate Limiting Compliance
- Respect Instagram's terms of service
- Implement conservative rate limits
- Monitor for 429 responses
- Use proxy rotation if necessary

### Security Auditing
- Regular security scans
- Dependency vulnerability checks
- Access log monitoring
- Incident response procedures

## Conclusion

This deployment guide provides a comprehensive framework for deploying the Instagram Scraper in various environments. For production deployments, always:

1. Follow security best practices
2. Implement proper monitoring
3. Test in staging first
4. Have backup and recovery procedures
5. Monitor compliance with platform terms
6. Maintain regular updates and patches

For additional support or custom deployment requirements, refer to the troubleshooting section or contact the development team.