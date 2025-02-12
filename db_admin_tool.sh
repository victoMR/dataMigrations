#!/bin/bash

# Colores para mejorar la interfaz
green='\033[0;32m'
blue='\033[0;34m'
red='\033[0;31m'
yellow='\033[1;33m'
purple='\033[0;35m'
reset='\033[0m'

# Rutas y directorios BASE relativos al directorio de ejecución
BASE_DIR="$(pwd)"
BACKUP_DIR="$BASE_DIR/backups"
EXPORT_DIR="$BASE_DIR/exports"
LOG_DIR="$BASE_DIR/logs"
POSTGRES_DIR="$BASE_DIR/postgres"
SQLSERVER_DIR="$BASE_DIR/sqlServer"
LOG_FILE="$LOG_DIR/operations.log"

# Variables de configuración
POSTGRES_CONTAINER="postgres_db"
SQLSERVER_CONTAINER="sqlserver"
POSTGRES_USER="my_user"
POSTGRES_DB="my_database"
SQLSERVER_DB="TestDB"
SQLSERVER_PASSWORD="Batmanlol1"

# Crear directorios si no existen
mkdir -p "$BACKUP_DIR" "$EXPORT_DIR" "$LOG_DIR"

function log_operation() {
    echo -e "${green}[INFO]${reset} $1" | tee -a "$LOG_FILE"
}

function error_log() {
    echo -e "${red}[ERROR]${reset} $1" | tee -a "$LOG_FILE"
}

function warning_log() {
    echo -e "${yellow}[WARNING]${reset} $1" | tee -a "$LOG_FILE"
}

# Función para verificar si SQL Server está listo
function check_sqlserver_ready() {
    for i in {1..30}; do
        if docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" -Q "SELECT 1;" &>/dev/null; then
            return 0
        fi
        echo "Esperando a que SQL Server esté listo... ($i/30)"
        sleep 1
    done
    return 1
}

function show_menu() {
    clear
    ## Add ANSI ASCII art to the menu
    echo -e "${purple}
    ⠄⠄⠄⠄⢠⣿⣿⣿⣿⣿⢻⣿⣿⣿⣿⣿⣿⣿⣿⣯⢻⣿⣿⣿⣿⣆⠄⠄⠄
    ⠄⠄⣼⢀⣿⣿⣿⣿⣏⡏⠄⠹⣿⣿⣿⣿⣿⣿⣿⣿⣧⢻⣿⣿⣿⣿⡆⠄⠄
    ⠄⠄⡟⣼⣿⣿⣿⣿⣿⠄⠄⠄⠈⠻⣿⣿⣿⣿⣿⣿⣿⣇⢻⣿⣿⣿⣿⠄⠄
    ⠄⢰⠃⣿⣿⠿⣿⣿⣿⠄⠄⠄⠄⠄⠄⠙⠿⣿⣿⣿⣿⣿⠄⢿⣿⣿⣿⡄⠄
    ⠄⢸⢠⣿⣿⣧⡙⣿⣿⡆⠄⠄⠄⠄⠄⠄⠄⠈⠛⢿⣿⣿⡇⠸⣿⡿⣸⡇⠄
    ⠄⠈⡆⣿⣿⣿⣿⣦⡙⠳⠄⠄⠄⠄⠄⠄⢀⣠⣤⣀⣈⠙⠃⠄⠿⢇⣿⡇⠄
    ⠄⠄⡇⢿⣿⣿⣿⣿⡇⠄⠄⠄⠄⠄⣠⣶⣿⣿⣿⣿⣿⣿⣷⣆⡀⣼⣿⡇⠄
    ⠄⠄⢹⡘⣿⣿⣿⢿⣷⡀⠄⢀⣴⣾⣟⠉⠉⠉⠉⣽⣿⣿⣿⣿⠇⢹⣿⠃⠄
    ⠄⠄⠄⢷⡘⢿⣿⣎⢻⣷⠰⣿⣿⣿⣿⣦⣀⣀⣴⣿⣿⣿⠟⢫⡾⢸⡟⠄.
    ⠄⠄⠄⠄⠻⣦⡙⠿⣧⠙⢷⠙⠻⠿⢿⡿⠿⠿⠛⠋⠉⠄⠂⠘⠁⠞⠄⠄⠄
    ⠄⠄⠄⠄⠄⠈⠙⠑⣠⣤⣴⡖⠄⠿⣋⣉⣉⡁⠄⢾⣦⠄⠄⠄⠄⠄⠄⠄⠄"
    echo -e "${blue}========================================="
    echo -e "${blue}========================================="
    echo -e "     Administración de Bases de Datos      "
    echo -e "=========================================${reset}"
    echo -e "${green}1) Levantar contenedores Docker${reset}"
    echo -e "${green}2) Verificar estado de contenedores${reset}"
    echo -e "${green}3) Backup de PostgreSQL${reset}"
    echo -e "${green}4) Backup de SQL Server${reset}"
    echo -e "${green}5) Restaurar PostgreSQL${reset}"
    echo -e "${green}6) Restaurar SQL Server${reset}"
    echo -e "${green}7) Crear usuario solo lectura (PostgreSQL)${reset}"
    echo -e "${green}8) Crear usuario solo lectura (SQL Server)${reset}"
    echo -e "${green}9) Importar datos CSV a PostgreSQL${reset}"
    echo -e "${green}10) Exportar datos CSV desde PostgreSQL${reset}"
    echo -e "${green}11) Importar datos CSV a SQL Server${reset}"
    echo -e "${green}12) Exportar datos CSV desde SQL Server${reset}"
    echo -e "${green}13) Migrar datos de PostgreSQL a SQL Server${reset}"
    echo -e "${green}14) Migrar datos de SQL Server a PostgreSQL${reset}"
    echo -e "${green}15) Exportar datos de SQL Server a JSON${reset}"
    echo -e "${green}16) Subir backup de PostgreSQL a Google Cloud${reset}"
    echo -e "${green}17) Subir backup de SQL Server a Google Cloud${reset}"
    echo -e "${green}18) Restaurar PostgreSQL desde Google Cloud${reset}"
    echo -e "${green}19) Restaurar SQL Server desde Google Cloud${reset}"
    echo -e "${red}0) Salir${reset}"
    echo -e "${blue}=========================================${reset}"
    echo -n "Selecciona una opción: "
}

function start_containers() {
    echo -e "${green}Levantando contenedores Docker...${reset}"
    docker compose -f "$POSTGRES_DIR/docker-compose.yml" up -d
    docker compose -f "$SQLSERVER_DIR/docker-compose.yml" up -d

    # Esperar a que SQL Server esté listo
    if check_sqlserver_ready; then
        log_operation "Contenedores levantados exitosamente."

        # Crear la base de datos TestDB si no existe
        docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
            -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '${SQLSERVER_DB}') CREATE DATABASE ${SQLSERVER_DB};"
    else
        error_log "Tiempo de espera agotado para SQL Server"
    fi
}

function check_containers() {
    echo -e "${blue}Estado actual de los contenedores:${reset}"
    docker ps --format "table {{.Names}}\t{{.Status}}"
}

function backup_postgres() {
    local backup_file="$BACKUP_DIR/backup_postgres_$(date +%Y%m%d).sql"
    echo -e "${green}Realizando backup de PostgreSQL...${reset}"
    if docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file"; then
        log_operation "Backup de PostgreSQL completado: $backup_file"
    else
        error_log "Error al realizar backup de PostgreSQL"
    fi
}

function backup_sqlserver() {
    local backup_file="$BACKUP_DIR/my_database_$(date +%Y%m%d).bak"
    echo -e "${green}Realizando backup de SQL Server...${reset}"

    # Crear directorio de backups si no existe en el contenedor
    docker exec "$SQLSERVER_CONTAINER" mkdir -p /var/opt/mssql/backup

    # Verificar que el directorio de backups se creó correctamente
    if ! docker exec "$SQLSERVER_CONTAINER" test -d /var/opt/mssql/backup; then
        error_log "No se pudo crear el directorio de backups en el contenedor."
        return 1
    fi

    # Realizar el backup de la base de datos
    if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
        -Q "BACKUP DATABASE [$SQLSERVER_DB] TO DISK = N'/var/opt/mssql/backup/my_database.bak' WITH INIT, FORMAT, COMPRESSION;"; then
        # Copiar el archivo de backup al host
        if docker cp "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/my_database.bak" "$backup_file"; then
            log_operation "Backup de SQL Server completado: $backup_file"
        else
            error_log "Error al copiar el archivo de backup al host."
        fi
    else
        error_log "Error al realizar backup de SQL Server."
    fi
}

function restore_postgres() {
    local backup_file="$BACKUP_DIR/$(ls -t "$BACKUP_DIR" | grep -E '\.sql$' | head -n 1)"

    if [ -f "$backup_file" ]; then
        echo -e "${green}Restaurando PostgreSQL desde $backup_file...${reset}"
        if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$backup_file"; then
            log_operation "Restauración de PostgreSQL completada desde $backup_file"
        else
            error_log "Error al restaurar PostgreSQL"
        fi
    else
        error_log "No se encontró ningún archivo de backup (.sql) en $BACKUP_DIR"
    fi
}

function restore_sqlserver() {
    local backup_file="$BACKUP_DIR/$(ls -t "$BACKUP_DIR" | grep -E '\.bak$' | head -n 1)"

    if [ -f "$backup_file" ]; then
        echo -e "${green}Restaurando SQL Server desde $backup_file...${reset}"

        # Restaurar la base de datos desde el volumen montado
        if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
            -Q "RESTORE DATABASE [$SQLSERVER_DB] FROM DISK = N'/backups/$(basename "$backup_file")' \
        WITH MOVE '$SQLSERVER_DB' TO '/var/opt/mssql/data/my_database.mdf', \
        MOVE '${SQLSERVER_DB}_log' TO '/var/opt/mssql/data/my_database.ldf', \
        REPLACE;"; then
            log_operation "Restauración de SQL Server completada desde $backup_file"
        else
            error_log "Error al restaurar SQL Server"
        fi
    else
        error_log "No se encontró ningún archivo de backup (.bak) en $BACKUP_DIR"
    fi
}

function create_readonly_user_postgres() {
    echo -e "${green}Creando usuario solo lectura en PostgreSQL...${reset}"
    if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
CREATE USER read_only_user WITH PASSWORD 'ReadonlyPass1';
GRANT CONNECT ON DATABASE $POSTGRES_DB TO read_only_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO read_only_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO read_only_user;
EOF
    then
        log_operation "Usuario solo lectura creado en PostgreSQL."
    else
        error_log "Error al crear usuario de solo lectura en PostgreSQL"
    fi
}

function create_readonly_user_sqlserver() {
    echo -e "${green}Creando usuario solo lectura en SQL Server...${reset}"
    if docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
        -Q "CREATE LOGIN ReadOnlyUser WITH PASSWORD='ReadonlyPass1'; \
    USE $SQLSERVER_DB; CREATE USER ReadOnlyUser FOR LOGIN ReadOnlyUser; \
    EXEC sp_addrolemember N'db_datareader', N'ReadOnlyUser';"; then
        log_operation "Usuario solo lectura creado en SQL Server."
    else
        error_log "Error al crear usuario de solo lectura en SQL Server"
    fi
}

function import_csv_postgres() {
    echo -n "Ingresa la ruta del archivo CSV a importar: "
    read file
    echo -n "Ingresa el nombre de la tabla destino: "
    read table

    # Verificar que el archivo existe
    if [ ! -f "$file" ]; then
        error_log "Archivo no encontrado: $file"
        return 1
    fi

    # Preprocesar el archivo CSV
    echo -e "${green}Preprocesando archivo CSV...${reset}"
    sed -i 's/\\"/""/g' "$file"  # Escapar comillas dobles
    sed -i 's/\\,/,/g' "$file"   # Escapar comas
    sed -i 's/\\r//g' "$file"    # Eliminar retornos de carro (CR)
    sed -i 's/\\n/ /g' "$file"   # Reemplazar saltos de línea con espacios

    # Copiar el archivo CSV al contenedor de PostgreSQL
    echo -e "${green}Copiando archivo CSV al contenedor...${reset}"
    docker cp "$file" "$POSTGRES_CONTAINER:/tmp/"

    # Verificar que el archivo se copió correctamente
    if ! docker exec "$POSTGRES_CONTAINER" test -f "/tmp/$(basename "$file")"; then
        error_log "No se pudo copiar el archivo CSV al contenedor."
        return 1
    fi

    # Obtener la primera línea del archivo CSV (encabezados)
    echo -e "${green}Obteniendo encabezados del archivo CSV...${reset}"
    headers=$(head -n 1 "$file")
    IFS=',' read -r -a columns <<< "$headers"

    # Verificar si la tabla ya existe en PostgreSQL
    echo -e "${green}Verificando si la tabla existe en PostgreSQL...${reset}"
    table_exists=$(docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '$table');")

    if [[ "$table_exists" == *"f"* ]]; then
        echo -e "${green}La tabla no existe. Creando tabla en PostgreSQL...${reset}"

        # Generar la consulta CREATE TABLE
        create_table_sql="CREATE TABLE $table ("
        for column in "${columns[@]}"; do
            # Limpiar el nombre de la columna (eliminar comillas y espacios)
            column=$(echo "$column" | tr -d '"' | tr -d '\r' | xargs)
            # Asignar un tipo de dato predeterminado (por ejemplo, VARCHAR)
            create_table_sql+="$column VARCHAR, "
        done
        create_table_sql="${create_table_sql%, });"

        # Crear la tabla en PostgreSQL
        if ! docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -c "$create_table_sql"; then
            error_log "Error al crear la tabla en PostgreSQL."
            return 1
        fi
    else
        echo -e "${green}La tabla ya existe. No es necesario crearla.${reset}"
    fi

    # Importar el archivo CSV a PostgreSQL
    echo -e "${green}Importando datos a PostgreSQL...${reset}"
    if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "\\COPY $table FROM '/tmp/$(basename "$file")' WITH CSV HEADER;"; then
        log_operation "Importación de CSV completada en PostgreSQL desde $file hacia $table."
    else
        error_log "Error al importar CSV a PostgreSQL."
        return 1
    fi
}

function export_csv_postgres() {
    echo -n "Ingresa el nombre de la tabla a exportar: "
    read table
    local export_file="$EXPORT_DIR/salida_postgres_$(date +%Y%m%d).csv"
    if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "\\COPY $table TO '/tmp/salida.csv' WITH CSV HEADER;"; then
        docker cp "$POSTGRES_CONTAINER:/tmp/salida.csv" "$export_file"
        log_operation "Exportación de PostgreSQL completada: $export_file"
    else
        error_log "Error al exportar datos de PostgreSQL"
    fi
}

function import_csv_sqlserver() {
    echo -n "Ingresa la ruta del archivo CSV a importar: "
    read file
    echo -n "Ingresa el nombre de la tabla destino: "
    read table
    if [ -f "$file" ]; then
        docker cp "$file" "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/"
        if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/bcp "$SQLSERVER_DB.dbo.$table" \
            in "/var/opt/mssql/backup/$(basename "$file")" -c -t',' -S localhost -U SA -P "$SQLSERVER_PASSWORD" -C; then
            log_operation "Importación de CSV completada en SQL Server desde $file hacia $table."
        else
            error_log "Error al importar CSV a SQL Server"
        fi
    else
        error_log "Archivo no encontrado: $file"
    fi
}

function export_csv_sqlserver() {
    echo -n "Ingresa el nombre de la tabla a exportar: "
    read table
    local export_file="$EXPORT_DIR/salida_sqlserver_$(date +%Y%m%d).csv"
    if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/bcp "SELECT * FROM $SQLSERVER_DB.dbo.$table" \
        queryout "/var/opt/mssql/backup/salida.csv" -c -t',' -S localhost -U SA -P "$SQLSERVER_PASSWORD" -C; then
        docker cp "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/salida.csv" "$export_file"
        log_operation "Exportación de SQL Server completada: $export_file"
    else
        error_log "Error al exportar datos de SQL Server"
    fi
}

function export_json_sqlserver() {
    echo -n "Ingresa el nombre de la tabla a exportar: "
    read table
    local export_file="$EXPORT_DIR/salida_sqlserver_$(date +%Y%m%d).json"
    local temp_csv="$EXPORT_DIR/temp_sqlserver_export.csv"

    # Exportar datos desde SQL Server a CSV
    if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/bcp "SELECT * FROM $SQLSERVER_DB.dbo.$table" \
        queryout "/var/opt/mssql/backup/temp.csv" -c -t',' -S localhost -U SA -P "$SQLSERVER_PASSWORD" -C; then
        docker cp "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/temp.csv" "$temp_csv"
    else
        error_log "Error al exportar datos de SQL Server a CSV"
        return 1
    fi

    # Convertir CSV a JSON usando Python
    if python3 -c "import csv, json; print(json.dumps([dict(r) for r in csv.DictReader(open('$temp_csv'))], indent=4))" > "$export_file"; then
        log_operation "Exportación de SQL Server a JSON completada: $export_file"
    else
        error_log "Error al convertir CSV a JSON"
    fi
}

function migrate_postgres_to_sqlserver() {
    echo -n "Ingresa el nombre de la tabla en PostgreSQL a migrar: "
    read table
    local temp_csv="$EXPORT_DIR/migration_postgres_to_sqlserver.csv"

    # Exportar datos desde PostgreSQL
    echo -e "${green}Exportando datos desde PostgreSQL...${reset}"
    if ! docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "\\COPY $table TO '/tmp/migration.csv' WITH CSV HEADER;"; then
        error_log "Error al exportar datos desde PostgreSQL."
        return 1
    fi

    # Copiar el archivo CSV al host
    docker cp "$POSTGRES_CONTAINER:/tmp/migration.csv" "$temp_csv"

    # Verificar que el archivo CSV se copió correctamente
    if [ ! -f "$temp_csv" ]; then
        error_log "No se pudo copiar el archivo CSV desde el contenedor de PostgreSQL."
        return 1
    fi

    # Preprocesar el archivo CSV para eliminar comillas dobles
    echo -e "${green}Preprocesando archivo CSV...${reset}"
    sed -i 's/"//g' "$temp_csv"  # Eliminar comillas dobles

    # Crear directorio de backups en el contenedor de SQL Server si no existe
    docker exec "$SQLSERVER_CONTAINER" mkdir -p /var/opt/mssql/backup

    # Copiar el archivo CSV al contenedor de SQL Server
    docker cp "$temp_csv" "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/migration.csv"

    # Obtener la estructura de la tabla en PostgreSQL
    echo -e "${green}Obteniendo estructura de la tabla en PostgreSQL...${reset}"
    local columns=$(docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c \
        "SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = '$table';")

    if [ -z "$columns" ]; then
        error_log "No se pudo obtener la estructura de la tabla en PostgreSQL."
        return 1
    fi

    # Mapear tipos de datos
    declare -A type_mapping=(
        ["integer"]="INT"
        ["bigint"]="BIGINT"
        ["smallint"]="SMALLINT"
        ["numeric"]="DECIMAL"
        ["real"]="FLOAT"
        ["double precision"]="FLOAT"
        ["varchar"]="VARCHAR"
        ["text"]="VARCHAR(MAX)"
        ["date"]="DATE"
        ["timestamp"]="DATETIME"
        ["boolean"]="BIT"
    )

    # Generar la consulta CREATE TABLE para SQL Server
    local create_table_sql="CREATE TABLE $table ("

    while IFS='|' read -r column_name data_type character_maximum_length; do
        column_name=$(echo "$column_name" | xargs)
        data_type=$(echo "$data_type" | xargs)

        # Mapeo de tipos de datos
        local sqlserver_type="${type_mapping[$data_type]}"
        if [ -z "$sqlserver_type" ]; then
            warning_log "Tipo de datos no mapeado: $data_type. Usando VARCHAR(MAX) como predeterminado."
            sqlserver_type="VARCHAR(MAX)"
        fi

        if [[ "$sqlserver_type" == "VARCHAR" && -n "$character_maximum_length" ]]; then
            sqlserver_type="VARCHAR($character_maximum_length)"
        fi

        create_table_sql+="$column_name $sqlserver_type, "
    done <<< "$columns"

    create_table_sql="${create_table_sql%, });"

    # Verificar y crear la tabla en SQL Server
    echo -e "${green}Creando tabla en SQL Server...${reset}"
    if ! docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
        -Q "USE $SQLSERVER_DB; IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '$table') $create_table_sql"; then
        error_log "Error al crear la tabla en SQL Server."
        return 1
    fi

    # Importar datos a SQL Server
    echo -e "${green}Importando datos a SQL Server...${reset}"
    if docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/bcp "$SQLSERVER_DB.dbo.$table" \
        in "/var/opt/mssql/backup/migration.csv" -c -t',' -S localhost -U SA -P "$SQLSERVER_PASSWORD" -C -F 2 -e /var/opt/mssql/backup/error.log -m 1; then
        log_operation "Migración de PostgreSQL a SQL Server completada para la tabla $table."
    else
        error_log "Error al importar datos a SQL Server. Revisa error.log para más detalles."
        docker exec "$SQLSERVER_CONTAINER" cat /var/opt/mssql/backup/error.log
    fi
}

function migrate_sqlserver_to_postgres() {
    echo -n "Ingresa el nombre de la tabla en SQL Server a migrar: "
    read table
    local temp_csv="$EXPORT_DIR/migration_sqlserver_to_postgres.csv"

    # Exportar datos desde SQL Server
    echo -e "${green}Exportando datos desde SQL Server...${reset}"
    if ! docker exec "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/bcp "SELECT * FROM $SQLSERVER_DB.dbo.$table" \
        queryout "/var/opt/mssql/backup/migration.csv" -c -t',' -S localhost -U SA -P "$SQLSERVER_PASSWORD" -C; then
        error_log "Error al exportar datos desde SQL Server"
        return 1
    fi
    docker cp "$SQLSERVER_CONTAINER:/var/opt/mssql/backup/migration.csv" "$temp_csv"

    # Verificar que la tabla existe en PostgreSQL y crear si no existe
    echo -e "${green}Verificando tabla en PostgreSQL...${reset}"
    if ! docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "SELECT 1 FROM information_schema.tables WHERE table_name = '$table'" | grep -q 1; then
        if ! docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
            -c "CREATE TABLE $table (id SERIAL PRIMARY KEY);"; then
            error_log "Error al crear la tabla en PostgreSQL"
            return 1
        fi
    fi

    # Importar datos a PostgreSQL
    echo -e "${green}Importando datos a PostgreSQL...${reset}"
    docker cp "$temp_csv" "$POSTGRES_CONTAINER:/tmp/"
    if docker exec -i "$POSTGRES_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
        -c "\\COPY $table FROM '/tmp/migration.csv' WITH CSV HEADER;"; then
        log_operation "Migración de SQL Server a PostgreSQL completada para la tabla $table."
    else
        error_log "Error al importar datos a PostgreSQL"
    fi
}
function upload_postgres_backup_to_gcloud() {
    local backup_file="$BACKUP_DIR/$(ls -t "$BACKUP_DIR" | grep -E 'backup_postgres_.*\.sql$' | head -n 1)"
    local bucket_name="backups-postgres_ubuntu"  # Nombre del bucket para PostgreSQL

    if [ -f "$backup_file" ]; then
        echo -e "${green}Subiendo $backup_file a Google Cloud Storage...${reset}"
        if gsutil cp "$backup_file" "gs://$bucket_name/$(basename "$backup_file")"; then
            log_operation "Backup de PostgreSQL subido exitosamente a Google Cloud Storage: $backup_file"
        else
            error_log "Error al subir $backup_file a Google Cloud Storage"
        fi
    else
        error_log "No se encontró ningún archivo de backup de PostgreSQL en $BACKUP_DIR"
    fi
}

function restore_postgres_from_gcloud() {
    echo -n "Ingresa el nombre del archivo de backup en Google Cloud: "
    read file_name
    local bucket_name="backups-postgres_ubuntu"  # Nombre del bucket para PostgreSQL
    local backup_file="$BACKUP_DIR/$file_name"

    echo -e "${green}Descargando $file_name desde Google Cloud Storage...${reset}"
    if gsutil cp "gs://$bucket_name/$file_name" "$backup_file"; then
        log_operation "Archivo $file_name descargado exitosamente desde Google Cloud Storage."
        restore_postgres "$backup_file"
    else
        error_log "Error al descargar $file_name desde Google Cloud Storage"
    fi
}
function upload_sqlserver_backup_to_gcloud() {
    local backup_file="$BACKUP_DIR/$(ls -t "$BACKUP_DIR" | grep -E 'my_database_.*\.bak$' | head -n 1)"
    local bucket_name="backups-sqlserver_ubuntu"  # Nombre del bucket para SQL Server

    if [ -f "$backup_file" ]; then
        echo -e "${green}Subiendo $backup_file a Google Cloud Storage...${reset}"
        if gsutil cp "$backup_file" "gs://$bucket_name/$(basename "$backup_file")"; then
            log_operation "Backup de SQL Server subido exitosamente a Google Cloud Storage: $backup_file"
        else
            error_log "Error al subir $backup_file a Google Cloud Storage"
        fi
    else
        error_log "No se encontró ningún archivo de backup de SQL Server en $BACKUP_DIR"
    fi
}

function restore_sqlserver_from_gcloud() {
    echo -n "Ingresa el nombre del archivo de backup en Google Cloud: "
    read file_name
    local bucket_name="backups-sqlserver_ubuntu"  # Nombre del bucket para SQL Server
    local backup_file="$BACKUP_DIR/$file_name"

    echo -e "${green}Descargando $file_name desde Google Cloud Storage...${reset}"
    if gsutil cp "gs://$bucket_name/$file_name" "$backup_file"; then
        log_operation "Archivo $file_name descargado exitosamente desde Google Cloud Storage."
        restore_sqlserver "$backup_file"
    else
        error_log "Error al descargar $file_name desde Google Cloud Storage"
    fi
}

while true; do
    show_menu
    read option
    case $option in
        1) start_containers;;
        2) check_containers;;
        3) backup_postgres;;
        4) backup_sqlserver;;
        5) restore_postgres;;
        6) restore_sqlserver;;
        7) create_readonly_user_postgres;;
        8) create_readonly_user_sqlserver;;
        9) import_csv_postgres;;
        10) export_csv_postgres;;
        11) import_csv_sqlserver;;
        12) export_csv_sqlserver;;
        13) migrate_postgres_to_sqlserver;;
        14) migrate_sqlserver_to_postgres;;
        15) export_json_sqlserver;;
        16) upload_postgres_backup_to_gcloud;;
        17) upload_sqlserver_backup_to_gcloud;;
        18) restore_postgres_from_gcloud;;
        19) restore_sqlserver_from_gcloud;;
        0) break;;
        *) warning_log "Opción inválida";;
    esac
    read -p "Presiona Enter para continuar..."
done
