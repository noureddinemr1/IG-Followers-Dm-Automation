#!/bin/bash
# Setup script for Instagram Scraper
# Initializes the environment and prepares for deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Instagram Scraper Setup Script${NC}"
echo -e "${BLUE}=============================${NC}"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed${NC}"
        echo "Please install Docker from https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Error: Docker Compose is not installed${NC}"
        echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker daemon is not running${NC}"
        echo "Please start Docker daemon"
        exit 1
    fi
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}Creating necessary directories...${NC}"
    
    local directories=(
        "data"
        "logs"
        "sessions"
        "backups"
        "volumes/data"
        "volumes/dev-data"
        "volumes/staging-data"
        "docker/nginx/ssl"
        "docker/loki"
        "docker/redis"
        "docker/postgres/init"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        echo "Created: $dir"
    done
    
    echo -e "${GREEN}✓ Directories created${NC}"
}

# Function to set up environment files
setup_environment() {
    echo -e "${YELLOW}Setting up environment configuration...${NC}"
    
    # Create default .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        cp ".env.development" ".env"
        echo "Created default .env file from development template"
    fi
    
    echo -e "${GREEN}✓ Environment configuration ready${NC}"
    echo -e "${YELLOW}⚠ Remember to update credentials in .env files before deployment${NC}"
}

# Function to generate SSL certificates (self-signed for development)
generate_ssl_certs() {
    echo -e "${YELLOW}Generating self-signed SSL certificates for development...${NC}"
    
    local ssl_dir="docker/nginx/ssl"
    
    if [[ ! -f "$ssl_dir/cert.pem" ]]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$ssl_dir/key.pem" \
            -out "$ssl_dir/cert.pem" \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost" \
            2>/dev/null || echo "OpenSSL not available, skipping SSL certificate generation"
        
        if [[ -f "$ssl_dir/cert.pem" ]]; then
            echo -e "${GREEN}✓ SSL certificates generated${NC}"
        else
            echo -e "${YELLOW}⚠ SSL certificates not generated (OpenSSL not available)${NC}"
        fi
    else
        echo -e "${GREEN}✓ SSL certificates already exist${NC}"
    fi
}

# Function to create nginx configuration
create_nginx_config() {
    echo -e "${YELLOW}Creating Nginx configuration...${NC}"
    
    cat > docker/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream app {
        server instagram-scraper:8080;
    }
    
    upstream grafana {
        server grafana:3000;
    }
    
    server {
        listen 80;
        server_name _;
        
        location /health {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /metrics {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
    
    echo -e "${GREEN}✓ Nginx configuration created${NC}"
}

# Function to create Redis configuration
create_redis_config() {
    echo -e "${YELLOW}Creating Redis configuration...${NC}"
    
    cat > docker/redis/redis.conf << 'EOF'
# Redis configuration for Instagram Scraper
bind 0.0.0.0
port 6379
timeout 0
tcp-keepalive 300
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./
maxmemory 256mb
maxmemory-policy allkeys-lru
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
aof-load-truncated yes
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
EOF
    
    echo -e "${GREEN}✓ Redis configuration created${NC}"
}

# Function to create Loki configuration
create_loki_config() {
    echo -e "${YELLOW}Creating Loki configuration...${NC}"
    
    cat > docker/loki/loki.yml << 'EOF'
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

ingester:
  wal:
    enabled: true
    dir: /loki/wal
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s
  max_transfer_retries: 0

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s

ruler:
  storage:
    type: local
    local:
      directory: /loki/rules
  rule_path: /loki/rules-temp
  alertmanager_url: http://localhost:9093
  ring:
    kvstore:
      store: inmemory
  enable_api: true
EOF
    
    echo -e "${GREEN}✓ Loki configuration created${NC}"
}

# Function to set permissions
set_permissions() {
    echo -e "${YELLOW}Setting file permissions...${NC}"
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    # Set appropriate permissions for data directories
    chmod 755 data logs sessions backups volumes
    
    echo -e "${GREEN}✓ Permissions set${NC}"
}

# Function to validate setup
validate_setup() {
    echo -e "${YELLOW}Validating setup...${NC}"
    
    # Check if essential files exist
    local required_files=(
        "docker-compose.yml"
        "Dockerfile"
        ".env.production"
        ".env.development"
        ".env.staging"
        "requirements.txt"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            echo -e "${RED}Error: Required file missing: $file${NC}"
            exit 1
        fi
    done
    
    # Test Docker Compose configuration
    if ! docker-compose config > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker Compose configuration is invalid${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Setup validation passed${NC}"
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo -e "${BLUE}Setup completed successfully!${NC}"
    echo -e "${BLUE}=====================${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update Instagram credentials in .env files:"
    echo "   - .env.development"
    echo "   - .env.staging"  
    echo "   - .env.production"
    echo ""
    echo "2. For development:"
    echo "   ./scripts/deploy.sh development deploy"
    echo ""
    echo "3. For production:"
    echo "   ./scripts/deploy.sh production deploy"
    echo ""
    echo "4. Check application status:"
    echo "   ./scripts/deploy.sh production status"
    echo ""
    echo "5. View logs:"
    echo "   ./scripts/deploy.sh production logs"
    echo ""
    echo -e "${GREEN}Happy scraping!${NC}"
}

# Main setup function
main() {
    check_prerequisites
    create_directories
    setup_environment
    generate_ssl_certs
    create_nginx_config
    create_redis_config
    create_loki_config
    set_permissions
    validate_setup
    show_next_steps
}

# Run main function
main "$@"