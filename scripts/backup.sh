#!/bin/bash
# Backup script for Instagram Scraper
# Creates comprehensive backups of application data

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="instagram-scraper"
BACKUP_BASE_DIR="backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_BASE_DIR/$TIMESTAMP"

echo -e "${BLUE}Instagram Scraper Backup Script${NC}"
echo -e "${BLUE}===============================${NC}"
echo "Backup directory: $BACKUP_DIR"
echo "Retention period: $RETENTION_DAYS days"
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Function to backup PostgreSQL database
backup_postgres() {
    log "Backing up PostgreSQL database..."
    
    local db_user=${POSTGRES_USER:-scraper_user}
    local db_name=${POSTGRES_DB:-instagram_scraper}
    
    # Create database dump using docker-compose
    docker-compose exec -T postgres pg_dump -U "$db_user" -d "$db_name" > "$BACKUP_DIR/postgres_dump.sql"
    
    # Compress dump
    gzip "$BACKUP_DIR/postgres_dump.sql"
    
    log "PostgreSQL backup completed"
}

# Function to backup application data volumes
backup_volumes() {
    log "Backing up application data volumes..."
    
    local volumes=(
        "${PROJECT_NAME}_scraper_data"
        "${PROJECT_NAME}_scraper_sessions"
        "${PROJECT_NAME}_redis_data"
    )
    
    for volume in "${volumes[@]}"; do
        if docker volume ls | grep -q "$volume"; then
            log "Backing up volume: $volume"
            
            # Create tar archive of volume
            docker run --rm \
                -v "$volume":/data:ro \
                -v "$(pwd)/$BACKUP_DIR":/backup \
                alpine \
                tar czf "/backup/${volume}.tar.gz" -C /data .
        fi
    done
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    find "$BACKUP_BASE_DIR" -maxdepth 1 -type d -name "20*" -mtime +$RETENTION_DAYS -exec rm -rf {} \;
}

# Main function
main() {
    log "Starting backup..."
    backup_postgres
    backup_volumes
    cleanup_old_backups
    log "Backup completed successfully!"
}

# Run main function
main "$@"