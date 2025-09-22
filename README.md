# Instagram Scraper - Production Ready Automation Solution

A comprehensive, dockerized Instagram scraper automation solution designed for production environments. This system provides reliable follower and following list extraction with robust monitoring, automated scheduling, and enterprise-grade features.

## 🚀 Features

### Core Functionality
- 🔐 **Secure Authentication**: Session management with 2FA support and secure credential handling
- 👥 **Complete Data Extraction**: Extract followers, following lists, and profile information
- 📨 **DM Automation**: Automated direct messaging to scraped accounts with templates and campaigns
- ⚡ **Intelligent Rate Limiting**: Built-in rate limiting to avoid Instagram detection and blocks
- 📊 **Multiple Export Formats**: JSON, CSV, and database storage options
- 🎯 **Multi-Target Management**: Configure and manage multiple Instagram accounts to scrape
- ⏰ **Automated Scheduling**: Cron-based scheduling for automated scraping operations

### Production Features
- 🐳 **Dockerized Architecture**: Complete containerization with Docker Compose orchestration
- � **Monitoring & Metrics**: Prometheus metrics, Grafana dashboards, and health checks
- 🔍 **Centralized Logging**: Structured logging with Loki aggregation and log rotation
- 🔄 **Auto Backup & Recovery**: Automated database backups with configurable retention
- 🌐 **Reverse Proxy**: Nginx reverse proxy with SSL termination and load balancing
- 🛡️ **Security Hardened**: Non-root containers, secret management, and security best practices
- 📱 **RESTful API**: FastAPI-based REST API for programmatic access and integration
- 🎛️ **Environment Management**: Separate configurations for development, staging, and production

### Reliability & Performance
- � **Error Handling**: Comprehensive error handling with automatic retries and fallbacks
- 💾 **Data Persistence**: PostgreSQL database with Redis caching for optimal performance
- 🔄 **High Availability**: Multi-service architecture with health checks and auto-restart
- 📊 **Performance Monitoring**: Real-time performance metrics and alerting capabilities

## 📋 Requirements

### System Requirements
- **Operating System**: Linux/macOS/Windows with WSL2
- **Memory**: Minimum 4GB RAM (8GB recommended for production)
- **Storage**: Minimum 10GB free space (more for data storage)
- **Network**: Stable internet connection

### Software Prerequisites
- **Docker**: Version 20.10+ ([Installation Guide](https://docs.docker.com/get-docker/))
- **Docker Compose**: Version 2.0+ ([Installation Guide](https://docs.docker.com/compose/install/))
- **Git**: For cloning the repository

## 🛠 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd instagram-scraper-automation

# Run the setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 2. Configure Credentials

Edit the environment files with your Instagram credentials:

```bash
# Development environment
nano .env.development

# Production environment  
nano .env.production
```

**Required Configuration:**
```env
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password
POSTGRES_PASSWORD=change_this_password
GRAFANA_PASSWORD=change_this_password
```

### 3. Deploy

```bash
# Development deployment
./scripts/deploy.sh development deploy

# Production deployment
./scripts/deploy.sh production deploy
```

### 4. Verify Installation

```bash
# Check service status
./scripts/deploy.sh production status

# View logs
./scripts/deploy.sh production logs

# Access health check
curl http://localhost:8080/health
```

## 🎯 Usage

### Command Line Interface

```bash
# Interactive mode
python src/main.py --interactive

# Scrape single account
python src/main.py --target username --max-followers 1000

# Scrape all configured targets
python src/main.py --scrape-targets

# Add new target
python src/main.py --add-target username

# List all targets
python src/main.py --list-targets
```

### REST API

The application provides a comprehensive REST API for programmatic access:

```bash
# API Documentation
http://localhost:8080/docs

# Health Check
curl http://localhost:8080/health

# Start scraping job
curl -X POST http://localhost:8080/scrape \
  -H "Content-Type: application/json" \
  -d '{"username": "target_username", "max_followers": 1000}'

# Check job status
curl http://localhost:8080/scrape/{job_id}

# Get metrics
curl http://localhost:8080/metrics
```

### Target Configuration

Create or modify `data/targets.json`:

```json
{
  "targets": [
    {
      "username": "target_account",
      "description": "Description of target",
      "active": true,
      "max_followers": 5000,
      "max_following": 5000,
      "scrape_interval_hours": 24
    }
  ],
  "settings": {
    "default_max_followers": 5000,
    "default_max_following": 5000
  }
}
```

## 🐳 Docker Architecture

### Services

| Service | Purpose | Port | Dependencies |
|---------|---------|------|--------------|
| **instagram-scraper** | Main application | 8080 | postgres, redis |
| **instagram-scheduler** | Automated scheduling | - | postgres, redis |
| **postgres** | Primary database | 5432 | - |
| **redis** | Caching & sessions | 6379 | - |
| **prometheus** | Metrics collection | 9090 | - |
| **grafana** | Monitoring dashboard | 3000 | prometheus |
| **loki** | Log aggregation | 3100 | - |
| **nginx** | Reverse proxy | 80/443 | instagram-scraper |

### Network Architecture

```
Internet → Nginx (80/443) → Instagram Scraper (8080)
                         ↘ Grafana (3000)
                         
Instagram Scraper ↔ PostgreSQL (5432)
                 ↔ Redis (6379)
                 
Prometheus ← All Services (metrics)
Loki ← All Services (logs)
```

## 📊 Monitoring & Observability

### Grafana Dashboards

Access monitoring dashboards at `http://localhost:3000`:

- **Application Overview**: Key performance metrics and health status
- **System Resources**: CPU, memory, disk, and network usage
- **Scraping Analytics**: Success rates, completion times, and error analysis
- **Database Performance**: PostgreSQL connection pools and query performance

### Prometheus Metrics

Key metrics available at `http://localhost:9090`:

```
# Application Metrics
scraper_uptime_seconds                    # Application uptime
scraper_active_scrapes                    # Currently running scrape operations
scraper_total_scrapes                     # Total scrapes completed
scraper_api_requests_total                # API request count by endpoint

# System Metrics  
scraper_memory_usage_mb                   # Memory consumption
scraper_cpu_percent                       # CPU utilization
system_disk_percent                       # Disk space usage
redis_connected                           # Redis connection status
postgres_connected                        # PostgreSQL connection status
```

### Log Aggregation

Centralized logging with Loki integration:

- **Structured JSON logs** for easy parsing and analysis
- **Log levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Automatic log rotation** to prevent disk space issues
- **Query interface** through Grafana for log exploration

## 🔒 Security Considerations

### Authentication & Authorization
- Instagram credentials stored in environment variables
- Database passwords configurable per environment
- API endpoints can be secured with authentication middleware

### Network Security
- Services communicate over internal Docker networks
- Exposed ports configurable per environment
- SSL/TLS termination at the reverse proxy level

### Data Protection
- Session files encrypted and stored in secure volumes
- Regular automated backups with configurable retention
- Sensitive data excluded from logs and metrics

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `INSTAGRAM_USERNAME` | Instagram account username | - | ✅ |
| `INSTAGRAM_PASSWORD` | Instagram account password | - | ✅ |
| `ENVIRONMENT` | Deployment environment | production | ❌ |
| `LOG_LEVEL` | Logging verbosity | INFO | ❌ |
| `POSTGRES_PASSWORD` | Database password | - | ✅ |
| `REDIS_HOST` | Redis server hostname | redis | ❌ |
| `BACKUP_RETENTION_DAYS` | Backup retention period | 30 | ❌ |

### Rate Limiting Configuration

```env
# Delays between requests (seconds)
MIN_DELAY=2.0
MAX_DELAY=5.0

# Maximum requests per minute
REQUESTS_PER_MINUTE=30

# Retry configuration
MAX_RETRIES=3
RETRY_DELAY=10.0
```

### Scraping Limits

```env
# Default limits for follower/following extraction
DEFAULT_MAX_FOLLOWERS=5000
DEFAULT_MAX_FOLLOWING=5000

# Enable profile picture downloads
SAVE_PROFILE_PICS=false
```

## 🔄 Backup & Recovery

### Automated Backups

```bash
# Manual backup
./scripts/backup.sh

# View backup status
ls -la backups/

# Restore from backup (example)
docker-compose down
# Restore volume data
docker-compose up -d
```

### Backup Contents

- **PostgreSQL database dumps** (compressed)
- **Application data volumes** (user data, sessions)
- **Configuration files** and environment settings
- **Metadata** with backup timestamps and integrity checksums

## 🚀 Deployment

### Development Environment

```bash
# Start development environment
./scripts/deploy.sh development deploy

# Enable hot reload for development
# Set HOT_RELOAD=true in .env.development
```

### Staging Environment

```bash
# Deploy to staging
./scripts/deploy.sh staging deploy

# Run integration tests
# curl http://staging-server:8080/health
```

### Production Environment

```bash
# Deploy to production
./scripts/deploy.sh production deploy

# Scale services if needed
./scripts/deploy.sh production scale instagram-scraper 3

# Monitor deployment
./scripts/deploy.sh production status
```

## 🔧 Maintenance

### Regular Maintenance Tasks

```bash
# Update application
./scripts/deploy.sh production update

# Clean up old Docker images
./scripts/deploy.sh production cleanup

# Database maintenance
./scripts/deploy.sh production migrate

# Create manual backup
./scripts/deploy.sh production backup
```

### Health Monitoring

```bash
# Check overall system health
curl http://localhost:8080/health

# Detailed metrics
curl http://localhost:8080/metrics/json

# View application info
curl http://localhost:8080/info
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Instagram Login Failed
```bash
# Check credentials in environment file
grep INSTAGRAM .env.production

# Verify 2FA is not enabled or handle it properly
docker-compose logs instagram-scraper
```

#### 2. Rate Limiting / IP Blocked
```bash
# Increase delays in configuration
# MIN_DELAY=5.0
# MAX_DELAY=10.0
# REQUESTS_PER_MINUTE=15

# Check if proxy configuration is needed
# USE_PROXY=true
# PROXY_URL=http://proxy-server:port
```

#### 3. Database Connection Issues
```bash
# Check PostgreSQL service status
docker-compose ps postgres

# Verify database credentials
docker-compose logs postgres

# Test database connection
docker-compose exec postgres psql -U scraper_user -d instagram_scraper
```

#### 4. Memory Issues
```bash
# Check memory usage
docker stats

# Reduce scraping limits in configuration
# DEFAULT_MAX_FOLLOWERS=1000
# DEFAULT_MAX_FOLLOWING=1000
```

### Debug Mode

Enable detailed debugging:

```bash
# Set debug level logging
LOG_LEVEL=DEBUG

# Enable debug mode
DEBUG=true

# View detailed logs
./scripts/deploy.sh production logs
```

### Log Analysis

```bash
# Follow logs in real-time
docker-compose logs -f instagram-scraper

# Search for specific errors
docker-compose logs instagram-scraper | grep ERROR

# Check specific service logs
docker-compose logs postgres
docker-compose logs redis
```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check and system status |
| `GET` | `/health/live` | Kubernetes liveness probe |
| `GET` | `/health/ready` | Kubernetes readiness probe |

### Scraping Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/scrape` | Start new scraping job |
| `GET` | `/scrape/{job_id}` | Get job status |
| `GET` | `/scrape` | List all jobs |

### Monitoring Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/metrics` | Prometheus metrics |
| `GET` | `/metrics/json` | JSON formatted metrics |
| `GET` | `/info` | Application information |

### API Examples

```bash
# Start scraping job
curl -X POST http://localhost:8080/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "username": "target_account",
    "max_followers": 1000,
    "max_following": 500
  }'

# Response
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "queued",
  "message": "Scraping job started"
}

# Check job status
curl http://localhost:8080/scrape/123e4567-e89b-12d3-a456-426614174000

# Response
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "progress": 100.0,
  "message": "Successfully scraped @target_account",
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:05:00Z"
}
```

## 🔮 Advanced Configuration

### Kubernetes Deployment

For Kubernetes deployment, use the provided health check endpoints:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 30

readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Custom Monitoring

Add custom metrics to Prometheus:

```python
from prometheus_client import Counter, Histogram

# Custom metric example
CUSTOM_METRIC = Counter('scraper_custom_events', 'Custom events', ['event_type'])
CUSTOM_METRIC.labels(event_type='user_action').inc()
```

### Database Scaling

For high-volume operations:

```yaml
# docker-compose.yml
postgres:
  environment:
    - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '2.0'
```

## 📖 Client Delivery Checklist

### Pre-Delivery
- [ ] Update all credentials and passwords
- [ ] Test deployment in staging environment
- [ ] Verify all monitoring dashboards
- [ ] Create production backup schedule
- [ ] Document any custom configurations

### Delivery Package
- [ ] Complete source code with documentation
- [ ] Environment configuration templates
- [ ] Deployment and maintenance scripts
- [ ] Monitoring and alerting setup
- [ ] Backup and recovery procedures
- [ ] Troubleshooting guide and FAQ

### Post-Delivery Support
- [ ] Initial deployment assistance
- [ ] Monitoring setup verification
- [ ] Staff training on operations
- [ ] Documentation of any customizations
- [ ] Maintenance schedule recommendations

## 📞 Support

For technical support and questions:

1. **Documentation**: Check this README and inline code documentation
2. **Logs**: Review application logs for error details
3. **Health Checks**: Use built-in health endpoints for diagnostics
4. **Monitoring**: Check Grafana dashboards for performance insights

## 📄 License

This project is proprietary software developed for specific client requirements. All rights reserved.

---

**Instagram Scraper Automation Solution v1.0**  
*Production-ready, dockerized Instagram scraping platform*

# Scrape all configured targets
python src/main.py --scrape-targets
```

### Command Line Options

```bash
# Basic usage
python src/main.py [options]

Options:
  -u, --username        Instagram username
  -p, --password        Instagram password
  -t, --target          Target username to scrape
  --max-followers       Maximum followers to scrape
  --max-following       Maximum following to scrape
  --scrape-targets      Scrape all active targets
  --add-target          Add a new target username
  --list-targets        List all configured targets
  -i, --interactive     Run in interactive mode
  --setup               Create .env file for credentials
  
  # DM Automation Options
  --dm-stats            Show DM automation statistics
  --dm-scraped          Send DMs to scraped accounts
  --dm-user             Send single DM to specified user
  --dm-message          Message content for single DM
  --dm-template         Template ID to use for DM campaign
  --dm-campaign         Campaign ID to run
```

### Examples

```bash
# Scrape specific user with limits
python src/main.py -t "example_user" --max-followers 500 --max-following 500

# Add a new target
python src/main.py --add-target "new_user"

# List all configured targets
python src/main.py --list-targets

# Run scheduler
python config/scheduler.py --run
```

## 📨 DM Automation

The system includes comprehensive DM automation capabilities for engaging with scraped accounts.

### Features
- **Template Management**: Create reusable message templates with variables
- **Campaign System**: Organize targets into campaigns with tracking
- **Rate Limiting**: Built-in safety limits to prevent spam detection
- **Analytics**: Comprehensive statistics and success tracking

### Quick Start with DM Automation

```bash
# Show DM statistics
python src/main.py -u username -p password --dm-stats

# Send DMs to scraped accounts
python src/main.py -u username -p password --dm-scraped --dm-template intro_1

# Send single DM
python src/main.py -u username -p password --dm-user target_user --dm-message "Hello!"

# Interactive DM management
python src/main.py --interactive
# Choose option 5: DM Automation Menu
```

### DM API Endpoints

Access DM features via REST API:

```bash
# Get DM statistics
curl http://localhost:8080/api/v1/dm/stats

# Create template
curl -X POST "http://localhost:8080/api/v1/dm/templates" \
  -H "Content-Type: application/json" \
  -d '{"name": "Intro", "subject": "Hello", "message": "Hi {username}!"}'

# Create campaign
curl -X POST "http://localhost:8080/api/v1/dm/campaigns" \
  -H "Content-Type: application/json" \
  -d '{"name": "Q4 Campaign", "template_id": "intro_1", "target_list": ["user1", "user2"]}'
```

### Safety & Compliance

⚠️ **Important**: DM automation operates in simulation mode by default. Review `docs/DM_AUTOMATION.md` for detailed safety guidelines and compliance information.

## Configuration

### Target Configuration

Edit `data/targets.json` to configure accounts to scrape:

```json
{
  "targets": [
    {
      "username": "example_user",
      "description": "Example account",
      "active": true,
      "max_followers": 1000,
      "max_following": 1000,
      "scrape_interval_hours": 24
    }
  ]
}
```

### Environment Variables

Key configuration options in `.env`:

```bash
# Authentication
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Rate Limiting
MIN_DELAY=1.0
MAX_DELAY=3.0
REQUESTS_PER_MINUTE=60

# Scraping Limits
DEFAULT_MAX_FOLLOWERS=5000
DEFAULT_MAX_FOLLOWING=5000
```

## Output Format

Scraped data is saved in JSON format with the following structure:

```json
{
  "profile": {
    "username": "example_user",
    "full_name": "Example User",
    "followers": 1000,
    "following": 500,
    "posts": 100,
    "is_private": false,
    "is_verified": false
  },
  "followers": [
    {
      "username": "follower1",
      "full_name": "Follower One",
      "is_private": false,
      "is_verified": false,
      "follower_count": 100,
      "following_count": 200,
      "scraped_at": "2024-01-01T12:00:00"
    }
  ],
  "following": [...],
  "stats": {
    "followers_scraped": 1000,
    "following_scraped": 500
  }
}
```

## Scheduling

Run automatic scheduled scraping:

```bash
# Start scheduler (runs daily at 2 AM)
python config/scheduler.py --run

# Manual one-time scrape
python config/scheduler.py --manual

# List scheduled jobs
python config/scheduler.py --list-jobs
```

## File Structure

```
Ig-Scraper/
├── src/
│   ├── main.py          # Main application entry
│   ├── auth.py          # Authentication module
│   └── scraper.py       # Core scraping logic
├── config/
│   ├── settings.py      # Configuration settings
│   └── scheduler.py     # Task scheduler
├── data/
│   ├── targets.json     # Target configuration
│   └── [output files]   # Scraped data
├── requirements.txt     # Python dependencies
├── .env.example        # Environment template
└── README.md           # This file
```

## Rate Limiting

The scraper includes built-in rate limiting to avoid Instagram's anti-bot measures:

- Configurable delays between requests (1-3 seconds default)
- Maximum requests per minute limit (60 default)
- Automatic retry with exponential backoff
- Session management to maintain login state

## Legal Notice

⚠️ **Important**: This tool is for educational and research purposes only. Make sure to:

- Comply with Instagram's Terms of Service
- Respect users' privacy and data protection laws
- Use appropriate rate limiting to avoid overloading Instagram's servers
- Only scrape public information
- Consider ethical implications of data collection

## Troubleshooting

### Common Issues

1. **Login Failed**: Check credentials and 2FA settings
2. **Rate Limited**: Increase delays in configuration
3. **Private Profiles**: Cannot scrape private accounts you don't follow
4. **Module Import Errors**: Install dependencies with `pip install -r requirements.txt`

### Logs

Check logs for detailed error information:
- Application logs: `data/scraper.log`
- Scheduler logs: `data/scheduler.log`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Disclaimer

This tool is provided as-is for educational purposes. Users are responsible for ensuring their use complies with applicable laws and Instagram's Terms of Service. The authors are not responsible for any misuse or legal issues arising from the use of this tool.
