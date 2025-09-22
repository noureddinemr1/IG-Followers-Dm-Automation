#!/bin/bash
# Deployment script for Instagram Scraper
# Usage: ./deploy.sh [environment] [action]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT=${1:-production}
ACTION=${2:-deploy}
PROJECT_NAME="instagram-scraper"

echo -e "${BLUE}Instagram Scraper Deployment Script${NC}"
echo -e "${BLUE}====================================${NC}"
echo "Environment: $ENVIRONMENT"
echo "Action: $ACTION"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    exit 1
fi

# Set environment file
ENV_FILE=".env.$ENVIRONMENT"
if [[ ! -f "$ENV_FILE" ]]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found${NC}"
    exit 1
fi

echo -e "${GREEN}Using environment file: $ENV_FILE${NC}"

# Export environment for docker-compose
export ENVIRONMENT=$ENVIRONMENT

# Function to wait for service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1

    echo -e "${YELLOW}Waiting for $service to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps $service | grep -q "healthy"; then
            echo -e "${GREEN}$service is healthy${NC}"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 10
        ((attempt++))
    done
    
    echo -e "${RED}$service failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Function to backup data
backup_data() {
    echo -e "${YELLOW}Creating backup before deployment...${NC}"
    
    # Create backup directory with timestamp
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup volumes if they exist
    if docker volume ls | grep -q "${PROJECT_NAME}_scraper_data"; then
        echo "Backing up scraper data..."
        docker run --rm -v ${PROJECT_NAME}_scraper_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/scraper_data.tar.gz -C /data .
    fi
    
    if docker volume ls | grep -q "${PROJECT_NAME}_postgres_data"; then
        echo "Backing up PostgreSQL data..."
        docker-compose exec -T postgres pg_dumpall -U ${POSTGRES_USER:-scraper_user} > "$BACKUP_DIR/postgres_dump.sql"
    fi
    
    echo -e "${GREEN}Backup created in $BACKUP_DIR${NC}"
}

# Function to deploy application
deploy() {
    echo -e "${YELLOW}Starting deployment...${NC}"
    
    # Pull latest images
    echo "Pulling latest images..."
    docker-compose pull
    
    # Build application image
    echo "Building application image..."
    docker-compose build --no-cache
    
    # Start services
    echo "Starting services..."
    docker-compose up -d
    
    # Wait for core services
    wait_for_service postgres
    wait_for_service redis
    wait_for_service instagram-scraper
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
}

# Function to stop application
stop() {
    echo -e "${YELLOW}Stopping application...${NC}"
    docker-compose down
    echo -e "${GREEN}Application stopped${NC}"
}

# Function to restart application
restart() {
    echo -e "${YELLOW}Restarting application...${NC}"
    docker-compose restart
    echo -e "${GREEN}Application restarted${NC}"
}

# Function to show logs
logs() {
    echo -e "${YELLOW}Showing application logs...${NC}"
    docker-compose logs -f --tail=100
}

# Function to show status
status() {
    echo -e "${YELLOW}Application Status:${NC}"
    docker-compose ps
    echo ""
    echo -e "${YELLOW}Health Check:${NC}"
    curl -s http://localhost:8080/health | jq . || echo "Health check failed"
}

# Function to cleanup old images and volumes
cleanup() {
    echo -e "${YELLOW}Cleaning up old Docker images and volumes...${NC}"
    
    # Remove dangling images
    docker image prune -f
    
    # Remove unused volumes (be careful with this)
    read -p "Remove unused volumes? This may delete data! (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    echo -e "${GREEN}Cleanup completed${NC}"
}

# Function to update application
update() {
    echo -e "${YELLOW}Updating application...${NC}"
    
    # Create backup first
    backup_data
    
    # Pull latest changes
    if [[ -d ".git" ]]; then
        git pull origin main
    fi
    
    # Deploy
    deploy
    
    echo -e "${GREEN}Update completed successfully!${NC}"
}

# Function to scale services
scale() {
    local service=$1
    local replicas=$2
    
    if [[ -z "$service" || -z "$replicas" ]]; then
        echo -e "${RED}Usage: $0 $ENVIRONMENT scale <service> <replicas>${NC}"
        exit 1
    fi
    
    echo -e "${YELLOW}Scaling $service to $replicas replicas...${NC}"
    docker-compose up -d --scale $service=$replicas
    echo -e "${GREEN}Scaling completed${NC}"
}

# Function to run database migrations
migrate() {
    echo -e "${YELLOW}Running database migrations...${NC}"
    
    # Wait for database to be ready
    wait_for_service postgres
    
    # Run migrations (if using Alembic or similar)
    docker-compose exec instagram-scraper python -c "
    import sys
    sys.path.append('/app/src')
    # Add your migration code here
    print('Migration completed')
    "
    
    echo -e "${GREEN}Database migrations completed${NC}"
}

# Main script logic
case $ACTION in
    deploy)
        backup_data
        deploy
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    cleanup)
        cleanup
        ;;
    update)
        update
        ;;
    scale)
        scale $3 $4
        ;;
    migrate)
        migrate
        ;;
    backup)
        backup_data
        ;;
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        echo ""
        echo "Available actions:"
        echo "  deploy  - Deploy the application"
        echo "  stop    - Stop the application"
        echo "  restart - Restart the application"
        echo "  logs    - Show application logs"
        echo "  status  - Show application status"
        echo "  cleanup - Clean up old Docker images and volumes"
        echo "  update  - Update and redeploy the application"
        echo "  scale   - Scale a service (requires service name and replica count)"
        echo "  migrate - Run database migrations"
        echo "  backup  - Create a backup of application data"
        echo ""
        echo "Usage: $0 [environment] [action]"
        echo "Example: $0 production deploy"
        exit 1
        ;;
esac