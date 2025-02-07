#!/bin/bash
# sqlserver_backup.sh
sqlserver_backup() {
    HOST=$1
    PORT=$2
    DB_NAME=$3
    USERNAME=$4
    PASSWORD=$5
    BACKUP_DIR=$6
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    BACKUP_PATH="${BACKUP_DIR}/sqlserver_${DB_NAME}_${TIMESTAMP}.bak"

    # Create backup directory if it doesn't exist
    mkdir -p $BACKUP_DIR

    # Create the backup using sqlcmd
    sqlcmd -S "$HOST,$PORT" -U $USERNAME -P $PASSWORD -Q "BACKUP DATABASE [$DB_NAME] TO DISK = '$BACKUP_PATH' WITH FORMAT"

    if [ $? -eq 0 ]; then
        echo "SQL Server backup created successfully at $BACKUP_PATH"
        return 0
    else
        echo "Error creating SQL Server backup"
        return 1
    fi
}
