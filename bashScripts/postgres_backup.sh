#!/bin/bash
# postgres_backup.sh
postgres_backup() {
    HOST=$1
    PORT=$2
    DB_NAME=$3
    USERNAME=$4
    PASSWORD=$5
    BACKUP_DIR=$6
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    export PGPASSWORD=$PASSWORD

    BACKUP_PATH="${BACKUP_DIR}/postgres_${DB_NAME}_${TIMESTAMP}.sql"

    # Create backup directory if it doesn't exist
    mkdir -p $BACKUP_DIR

    # Perform backup
    pg_dump -h $HOST -p $PORT -U $USERNAME -d $DB_NAME > $BACKUP_PATH

    if [ $? -eq 0 ]; then
        echo "PostgreSQL backup created successfully at $BACKUP_PATH"
        return 0
    else
        echo "Error creating PostgreSQL backup"
        return 1
    fi
}
