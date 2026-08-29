#!/bin/bash
# Backup script for LegalLens India

set -e

# Configuration
BACKUP_DIR="/backups/legallens"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "Starting backup at $(date)"

# Database backup
echo "Backing up database..."
docker compose exec -T db pg_dump -U postgres legallens | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# MinIO backup
echo "Backing up MinIO data..."
docker run --rm -v legallens_minio_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/minio_$DATE.tar.gz /data

# Remove old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed at $(date)"
echo "Backup location: $BACKUP_DIR"
