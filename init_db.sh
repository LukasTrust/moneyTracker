#!/bin/bash
# Database Management Script for Money Tracker
# Provides manual database operations: init, backup, restore, migration status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="moneytracker"
COMPOSE_FILE="docker-compose.yml"
COMPOSE_FILE_PROD="docker-compose.prod.yml"
DB_VOLUME="moneytracker_sqlite-data"
DB_VOLUME_PROD="moneytracker_sqlite-data-prod"
BACKUP_DIR="./backups"
DB_PATH="/app/data/moneytracker.db"

# Helper functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running!"
        exit 1
    fi
}

# ============================================
# Command: init
# Initialize database and run migrations
# ============================================
cmd_init() {
    print_header "Initializing Database"
    
    local env="${1:-dev}"
    local compose_file="$COMPOSE_FILE"
    
    if [ "$env" = "prod" ]; then
        compose_file="$COMPOSE_FILE_PROD"
    fi
    
    print_info "Environment: $env"
    print_info "Compose file: $compose_file"
    echo ""
    
    # Start backend container (will run migrations via entrypoint)
    print_info "Starting backend container..."
    docker-compose -f "$compose_file" up -d backend
    
    # Wait for initialization
    print_info "Waiting for initialization..."
    sleep 5
    
    # Check logs
    print_info "Checking initialization logs..."
    docker-compose -f "$compose_file" logs backend | grep -A 20 "Money Tracker Backend"
    
    print_success "Database initialization complete!"
}

# ============================================
# Command: status
# Show migration status
# ============================================
cmd_status() {
    print_header "Migration Status"
    
    local env="${1:-dev}"
    local container="${PROJECT_NAME}-backend"
    
    if [ "$env" = "prod" ]; then
        container="${PROJECT_NAME}-backend-prod"
    fi
    
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        print_error "Container '$container' is not running!"
        print_info "Start it with: docker-compose up -d backend"
        exit 1
    fi
    
    # Show applied migrations
    print_info "Applied migrations:"
    docker exec "$container" sqlite3 "$DB_PATH" \
        "SELECT version, description, datetime(applied_at, 'localtime') as applied, execution_time_ms || 'ms' as duration 
         FROM schema_migrations 
         ORDER BY version" \
        -header -column 2>/dev/null || {
        print_warning "No migrations table found (database may not be initialized)"
    }
    
    echo ""
    
    # Show available migration files
    print_info "Available migration files:"
    docker exec "$container" find /app/migrations -name "*.py" -o -name "*.sql" | \
        grep -v __pycache__ | \
        grep -E "^/app/migrations/[0-9]" | \
        sort
    
    echo ""
    
    # Show database stats
    print_info "Database statistics:"
    docker exec "$container" sqlite3 "$DB_PATH" \
        "SELECT 
            (SELECT COUNT(*) FROM sqlite_master WHERE type='table') as tables,
            (SELECT COUNT(*) FROM data_rows) as data_rows,
            (SELECT COUNT(*) FROM accounts) as accounts,
            (SELECT COUNT(*) FROM categories) as categories" \
        -header -column
}

# ============================================
# Command: backup
# Create database backup
# ============================================
cmd_backup() {
    print_header "Creating Database Backup"
    
    local env="${1:-dev}"
    local container="${PROJECT_NAME}-backend"
    local description="$2"
    
    if [ "$env" = "prod" ]; then
        container="${PROJECT_NAME}-backend-prod"
    fi
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/${PROJECT_NAME}_${env}_${timestamp}.db"
    
    if [ -n "$description" ]; then
        backup_file="$BACKUP_DIR/${PROJECT_NAME}_${env}_${timestamp}_${description}.db"
    fi
    
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        print_error "Container '$container' is not running!"
        exit 1
    fi
    
    # Create backup
    print_info "Creating backup: $(basename $backup_file)"
    docker exec "$container" sqlite3 "$DB_PATH" ".backup /tmp/backup.db"
    docker cp "${container}:/tmp/backup.db" "$backup_file"
    docker exec "$container" rm /tmp/backup.db
    
    # Get backup size
    local size=$(du -h "$backup_file" | cut -f1)
    
    print_success "Backup created: $backup_file ($size)"
    
    # Show recent backups
    echo ""
    print_info "Recent backups:"
    ls -lht "$BACKUP_DIR" | head -6
}

# ============================================
# Command: restore
# Restore database from backup
# ============================================
cmd_restore() {
    print_header "Restoring Database Backup"
    
    local backup_file="$1"
    local env="${2:-dev}"
    local container="${PROJECT_NAME}-backend"
    
    if [ "$env" = "prod" ]; then
        container="${PROJECT_NAME}-backend-prod"
    fi
    
    # Check if backup file exists
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        print_info "Available backups:"
        ls -lh "$BACKUP_DIR" 2>/dev/null || print_warning "No backups found"
        exit 1
    fi
    
    # Confirm restore
    print_warning "This will replace the current database!"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Restore cancelled"
        exit 0
    fi
    
    # Stop container
    print_info "Stopping container..."
    docker-compose stop backend
    
    # Copy backup to container
    print_info "Restoring backup..."
    docker cp "$backup_file" "${container}:/tmp/restore.db"
    
    # Start container temporarily to restore
    docker-compose start backend
    sleep 3
    
    # Restore database
    docker exec "$container" cp /tmp/restore.db "$DB_PATH"
    docker exec "$container" rm /tmp/restore.db
    
    # Restart container
    print_info "Restarting container..."
    docker-compose restart backend
    
    print_success "Database restored from: $backup_file"
}

# ============================================
# Command: migrate
# Run migrations manually
# ============================================
cmd_migrate() {
    print_header "Running Migrations Manually"
    
    local env="${1:-dev}"
    local container="${PROJECT_NAME}-backend"
    
    if [ "$env" = "prod" ]; then
        container="${PROJECT_NAME}-backend-prod"
    fi
    
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        print_error "Container '$container' is not running!"
        exit 1
    fi
    
    # Run migrations
    print_info "Executing migration runner..."
    docker exec "$container" python /app/migrations/run_migrations.py
    
    print_success "Migrations completed!"
}

# ============================================
# Command: shell
# Open SQLite shell
# ============================================
cmd_shell() {
    print_header "Opening SQLite Shell"
    
    local env="${1:-dev}"
    local container="${PROJECT_NAME}-backend"
    
    if [ "$env" = "prod" ]; then
        container="${PROJECT_NAME}-backend-prod"
    fi
    
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${container}$"; then
        print_error "Container '$container' is not running!"
        exit 1
    fi
    
    print_info "Opening database shell..."
    print_info "Type .quit to exit"
    echo ""
    
    docker exec -it "$container" sqlite3 "$DB_PATH"
}

# ============================================
# Command: clean
# Clean database volume
# ============================================
cmd_clean() {
    print_header "Cleaning Database Volume"
    
    local env="${1:-dev}"
    local volume="$DB_VOLUME"
    
    if [ "$env" = "prod" ]; then
        volume="$DB_VOLUME_PROD"
    fi
    
    print_warning "This will DELETE all data in the database!"
    print_warning "Volume: $volume"
    read -p "Are you sure? (yes/no): " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        print_info "Clean cancelled"
        exit 0
    fi
    
    # Stop containers
    print_info "Stopping containers..."
    docker-compose down
    
    # Remove volume
    print_info "Removing volume..."
    docker volume rm "$volume" 2>/dev/null || print_warning "Volume not found"
    
    print_success "Volume cleaned!"
    print_info "Start containers again to initialize fresh database"
}

# ============================================
# Command: help
# Show usage information
# ============================================
cmd_help() {
    cat << EOF
Database Management Script for Money Tracker

Usage: $0 <command> [options]

Commands:
    init [dev|prod]              Initialize database and run migrations
    status [dev|prod]            Show migration status and database stats
    backup [dev|prod] [desc]     Create database backup
    restore <file> [dev|prod]    Restore database from backup
    migrate [dev|prod]           Run migrations manually
    shell [dev|prod]             Open SQLite shell
    clean [dev|prod]             Clean database volume (destructive!)
    help                         Show this help message

Examples:
    $0 init                      Initialize development database
    $0 status                    Show migration status
    $0 backup dev "before_update" Create backup with description
    $0 restore backups/moneytracker_dev_20231116.db
    $0 migrate prod              Run migrations in production
    $0 shell                     Open database shell
    
Environment:
    dev (default) - Development environment
    prod          - Production environment

EOF
}

# ============================================
# Main
# ============================================
main() {
    check_docker
    
    local command="${1:-help}"
    shift || true
    
    case "$command" in
        init)
            cmd_init "$@"
            ;;
        status)
            cmd_status "$@"
            ;;
        backup)
            cmd_backup "$@"
            ;;
        restore)
            cmd_restore "$@"
            ;;
        migrate)
            cmd_migrate "$@"
            ;;
        shell)
            cmd_shell "$@"
            ;;
        clean)
            cmd_clean "$@"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        *)
            print_error "Unknown command: $command"
            echo ""
            cmd_help
            exit 1
            ;;
    esac
}

main "$@"
