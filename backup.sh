#!/bin/bash

# Prashnakosh Backup Script
# This script creates backups of the database and media files

set -e  # Exit on error

# Load environment variables
source .env

# Variables
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="backups"
DB_BACKUP="$BACKUP_DIR/db_$TIMESTAMP.sql"
MEDIA_BACKUP="$BACKUP_DIR/media_$TIMESTAMP.tar.gz"
RETENTION_DAYS=7

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Database backup
echo "Creating database backup..."
PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U $DB_USER $DB_NAME > $DB_BACKUP
gzip $DB_BACKUP

# Media backup (if files exist)
if [ -d "mediafiles" ] && [ "$(ls -A mediafiles 2>/dev/null)" ]; then
    echo "Creating media files backup..."
    tar -czf $MEDIA_BACKUP mediafiles
fi

# Clean up old backups
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "db_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "media_*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

echo "Backup completed successfully!"
echo "Database: ${DB_BACKUP}.gz"
if [ -f "$MEDIA_BACKUP" ]; then
    echo "Media files: $MEDIA_BACKUP"
fi 