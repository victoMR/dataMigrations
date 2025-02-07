#!/bin/bash
# mongodb_backup.sh
mongodb_backup() {
    HOST=$1
    PORT=$2
    DB_NAME=$3
    USERNAME=$4
    PASSWORD=$5
    BACKUP_DIR=$6
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    BACKUP_PATH="${BACKUP_DIR}/mongodb_${DB_NAME}_${TIMESTAMP}"

    # Create backup directory if it doesn't exist
    mkdir -p $BACKUP_DIR

    # Perform backup using mongodump
    mongodump --host $HOST --port $PORT --db $DB_NAME \
        --username $USERNAME --password $PASSWORD \
        --out $BACKUP_PATH

    if [ $? -eq 0 ]; then
        # Compress the backup
        tar -czf "${BACKUP_PATH}.tar.gz" -C $BACKUP_DIR "mongodb_${DB_NAME}_${TIMESTAMP}"
        rm -rf $BACKUP_PATH
        echo "MongoDB backup created successfully at ${BACKUP_PATH}.tar.gz"
        return 0
    else
        echo "Error creating MongoDB backup"
        return 1
    fi
}
