
# Explicación Detallada del Script de Administración de Bases de Datos

## Configuración Inicial

```bash
green='\033[0;32m'
blue='\033[0;34m'
red='\033[0;31m'
yellow='\033[1;33m'
purple='\033[0;35m'
reset='\033[0m'
```

Estas variables definen códigos de color ANSI para mejorar la interfaz de usuario. Los códigos de escape `\033` permiten cambiar el color del texto en la terminal:
- `green`: Se usa para mensajes de éxito y operaciones completadas
- `blue`: Para títulos y elementos del menú
- `red`: Para errores y advertencias críticas
- `yellow`: Para advertencias y mensajes de precaución
- `purple`: Para elementos decorativos
- `reset`: Regresa el color al valor predeterminado

## Estructura de Directorios

```bash
BASE_DIR="$(pwd)"
BACKUP_DIR="$BASE_DIR/backups"
EXPORT_DIR="$BASE_DIR/exports"
LOG_DIR="$BASE_DIR/logs"
POSTGRES_DIR="$BASE_DIR/postgres"
SQLSERVER_DIR="$BASE_DIR/sqlServer"
LOG_FILE="$LOG_DIR/operations.log"
```

Esta sección establece la estructura de directorios del proyecto:
- `$(pwd)` obtiene el directorio actual donde se ejecuta el script
- Cada variable define una ruta específica para diferentes operaciones
- La estructura separa claramente los respaldos, exportaciones y logs
- Los archivos de configuración de cada base de datos tienen su propio directorio

## Variables de Configuración

```bash
POSTGRES_CONTAINER="postgres_db"
SQLSERVER_CONTAINER="sqlserver"
POSTGRES_USER="my_user"
POSTGRES_DB="my_database"
SQLSERVER_DB="TestDB"
SQLSERVER_PASSWORD="Batmanlol1"
```

Estas variables contienen la configuración básica para ambas bases de datos:
- Nombres de los contenedores Docker
- Credenciales de acceso
- Nombres de las bases de datos
- En un ambiente de producción, estas credenciales deberían estar en un archivo .env

## Funciones de Registro (Logging)

```bash
function log_operation() {
    echo -e "${green}[INFO]${reset} $1" | tee -a "$LOG_FILE"
}

function error_log() {
    echo -e "${red}[ERROR]${reset} $1" | tee -a "$LOG_FILE"
}

function warning_log() {
    echo -e "${yellow}[WARNING]${reset} $1" | tee -a "$LOG_FILE"
}
```

Estas funciones manejan el registro de eventos:
- `log_operation`: Registra operaciones exitosas en verde
- `error_log`: Registra errores en rojo
- `warning_log`: Registra advertencias en amarillo
- `tee -a` envía la salida tanto a la pantalla como al archivo de log
- El parámetro `$1` representa el mensaje que se va a registrar

## Verificación de SQL Server

```bash
function check_sqlserver_ready() {
    for i in {1..30}; do
        if docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd \
            -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" -Q "SELECT 1;" &>/dev/null; then
            return 0
        fi
        echo "Esperando a que SQL Server esté listo... ($i/30)"
        sleep 1
    done
    return 1
}
```

Esta función verifica si SQL Server está listo para aceptar conexiones:
- Intenta conectarse hasta 30 veces
- Usa `sqlcmd` para ejecutar una consulta simple
- El parámetro `-C` habilita la confianza en el certificado del servidor
- `&>/dev/null` redirige tanto la salida estándar como los errores a /dev/null
- Retorna 0 si la conexión es exitosa, 1 si falla después de 30 intentos

## Menú Principal

```bash
function show_menu() {
    clear
    echo -e "${purple}
    ⠄⠄⠄⠄⢠⣿⣿⣿⣿⣿⢻⣿⣿⣿⣿⣿⣿⣿⣿⣯⢻⣿⣿⣿⣿⣆⠄⠄⠄
    # ... ASCII art ...
    ${reset}"
    echo -e "${blue}========================================="
    # ... opciones del menú ...
    echo -e "${red}0) Salir${reset}"
}
```

Esta función muestra el menú interactivo:
- `clear` limpia la pantalla antes de mostrar el menú
- Incluye arte ASCII para mejorar la presentación
- Las opciones están coloreadas para mejor visibilidad
- Cada opción corresponde a una función específica

## Inicio de Contenedores

```bash
function start_containers() {
    echo -e "${green}Levantando contenedores Docker...${reset}"
    docker compose -f "$POSTGRES_DIR/docker-compose.yml" up -d
    docker compose -f "$SQLSERVER_DIR/docker-compose.yml" up -d

    if check_sqlserver_ready; then
        log_operation "Contenedores levantados exitosamente."
        docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd \
            -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
            -Q "IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = '${SQLSERVER_DB}') 
                CREATE DATABASE ${SQLSERVER_DB};"
    else
        error_log "Tiempo de espera agotado para SQL Server"
    fi
}
```

Esta función inicia los contenedores Docker:
- Usa Docker Compose para levantar ambas bases de datos
- `-d` ejecuta los contenedores en segundo plano
- Verifica que SQL Server esté listo usando la función `check_sqlserver_ready`
- Crea la base de datos si no existe
- Registra el resultado de la operación

## Respaldo 

### Función: backup_postgres()

```bash
function backup_postgres() {
    local backup_file="$BACKUP_DIR/backup_postgres_$(date +%Y%m%d).sql"
    echo -e "${green}Realizando backup de PostgreSQL...${reset}"
    if docker exec "$POSTGRES_CONTAINER" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$backup_file"; then
        log_operation "Backup de PostgreSQL completado: $backup_file"
    else
        error_log "Error al realizar backup de PostgreSQL"
    fi
}
```

Esta función realiza un respaldo completo de una base de datos PostgreSQL. El proceso es relativamente directo pero muy importante para la seguridad de los datos. Comienza generando un nombre de archivo único que incluye la fecha actual en formato YYYYMMDD, lo que permite mantener un histórico organizado de respaldos. 

La función utiliza `pg_dump`, una herramienta nativa de PostgreSQL que crea una representación consistente de la base de datos en formato SQL. Este archivo resultante contiene todas las instrucciones necesarias para recrear la base de datos en el mismo estado en que se encontraba al momento del respaldo, incluyendo datos, esquemas, funciones y otros objetos de la base de datos.

### Función: backup_sqlserver()

```bash
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
```

Esta función maneja el respaldo de SQL Server, que es un proceso más complejo que requiere varios pasos de verificación. El proceso incluye:

1. Primero, crea un nombre de archivo único con la fecha actual
2. Asegura la existencia del directorio de respaldos dentro del contenedor
3. Utiliza el comando BACKUP DATABASE de SQL Server con opciones específicas:
   - WITH INIT: Sobrescribe cualquier backup existente
   - FORMAT: Crea un nuevo conjunto de respaldo
   - COMPRESSION: Reduce el tamaño del archivo resultante
4. Finalmente, copia el archivo de respaldo desde el contenedor al sistema host

La función incluye verificaciones en cada paso para garantizar que el proceso se complete correctamente.

## Restauración

### Función: restore_postgres()

```bash
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
```

Esta función restaura una base de datos PostgreSQL desde un archivo de respaldo. El proceso es inteligente en varios aspectos:

1. Automáticamente selecciona el archivo de respaldo más reciente (usando `ls -t` para ordenar por fecha y `head -n 1` para tomar el más reciente)
2. Verifica la existencia del archivo antes de intentar la restauración
3. Utiliza el comando psql para ejecutar los comandos SQL contenidos en el archivo de respaldo
4. Mantiene un registro de la operación, ya sea exitosa o fallida

La restauración es un proceso directo gracias al formato SQL del respaldo, que permite ejecutar los comandos directamente en la base de datos.

### Función: restore_sqlserver()

```bash
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
```

Esta función maneja la restauración de SQL Server, que es más compleja que la de PostgreSQL debido a la necesidad de especificar las ubicaciones de los archivos de datos. El proceso incluye:

1. Selecciona automáticamente el archivo de respaldo más reciente con extensión .bak
2. Utiliza el comando RESTORE DATABASE con opciones específicas:
   - WITH MOVE: Especifica las nuevas ubicaciones para los archivos de datos (.mdf) y log (.ldf)
   - REPLACE: Permite sobrescribir una base de datos existente
3. Maneja los archivos de datos y logs de manera separada, asegurando que se ubiquen en los directorios correctos
4. Registra el resultado de la operación en el log del sistema

La función es particularmente cuidadosa con la especificación de las rutas de los archivos, ya que SQL Server requiere que se definan explícitamente las ubicaciones de los archivos de datos y logs durante la restauración.


## Gestión de Usuarios

### PostgreSQL

```bash
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
        error_log "Error al crear usuario de solo lectura"
    fi
}
```

Esta función crea un usuario de solo lectura en PostgreSQL:
- Crea un nuevo usuario con contraseña
- Otorga permisos de conexión a la base de datos
- Permite SELECT en todas las tablas existentes
- Configura permisos para tablas futuras
- Usa here-document (`<< EOF`) para múltiples comandos SQL

### SQL Server

```bash
function create_readonly_user_sqlserver() {
    echo -e "${green}Creando usuario solo lectura en SQL Server...${reset}"
    if docker exec -it "$SQLSERVER_CONTAINER" /opt/mssql-tools/bin/sqlcmd \
        -C -S localhost -U SA -P "$SQLSERVER_PASSWORD" \
        -Q "CREATE LOGIN ReadOnlyUser WITH PASSWORD='ReadonlyPass1'; 
            USE $SQLSERVER_DB; 
            CREATE USER ReadOnlyUser FOR LOGIN ReadOnlyUser; 
            EXEC sp_addrolemember N'db_datareader', N'ReadOnlyUser';"; then
        log_operation "Usuario solo lectura creado en SQL Server."
    else
        error_log "Error al crear usuario de solo lectura"
    fi
}
```

Esta función crea un usuario de solo lectura en SQL Server:
- Crea un nuevo login a nivel de servidor
- Crea un usuario asociado en la base de datos
- Asigna el rol db_datareader para permisos de lectura
- Todo en una sola transacción T-SQL

## Operaciones CSV

### Función: import_csv_postgres()

```bash
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
```

Esta función se encarga de importar datos desde un archivo CSV a una base de datos PostgreSQL. El proceso se desarrolla en varias etapas importantes:

1. Primero, solicita al usuario la ruta del archivo CSV y el nombre de la tabla donde se importarán los datos.

2. Realiza una serie de verificaciones y preparaciones:
   - Comprueba que el archivo existe
   - Preprocesa el archivo CSV para manejar caracteres especiales
   - Escapa comillas dobles, comas y maneja saltos de línea
   - Copia el archivo al contenedor de Docker de PostgreSQL

3. Analiza la estructura del CSV:
   - Lee los encabezados del archivo
   - Verifica si la tabla existe en PostgreSQL
   - Si la tabla no existe, la crea automáticamente con columnas basadas en los encabezados

4. Finalmente, utiliza el comando COPY de PostgreSQL para importar los datos, garantizando una importación eficiente y manteniendo un registro de la operación.

### Función: export_csv_postgres()

```bash
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
```

Esta función realiza la exportación de datos desde PostgreSQL a un archivo CSV. Su funcionamiento es más directo:

1. Solicita al usuario el nombre de la tabla que desea exportar
2. Genera un nombre de archivo único usando la fecha actual
3. Utiliza el comando COPY de PostgreSQL para exportar los datos a un archivo temporal
4. Copia el archivo desde el contenedor al sistema host
5. Registra la operación en el log del sistema

### Función: import_csv_sqlserver()

```bash
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
```

Esta función maneja la importación de datos CSV a SQL Server. El proceso es diferente al de PostgreSQL:

1. Solicita la información básica al usuario (ruta del archivo y tabla destino)
2. Verifica la existencia del archivo
3. Copia el archivo al contenedor de SQL Server
4. Utiliza la utilidad BCP (Bulk Copy Program) para realizar la importación
5. Registra el resultado de la operación

### Función: export_csv_sqlserver()

```bash
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
```

Esta función exporta datos desde SQL Server a un archivo CSV:

1. Solicita el nombre de la tabla a exportar
2. Genera un nombre de archivo único con la fecha
3. Utiliza BCP para exportar los datos, ejecutando una consulta SELECT
4. Copia el archivo resultante desde el contenedor al sistema host
5. Registra la operación en el log

### Función: migrate_postgres_to_sqlserver()

```bash
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
```

Esta función realiza la migración de datos desde PostgreSQL a SQL Server. Es una operación compleja que involucra varios pasos:

1. Exporta los datos de PostgreSQL a un archivo CSV temporal
2. Preprocesa el archivo CSV para compatibilidad
3. Analiza la estructura de la tabla en PostgreSQL
4. Mapea los tipos de datos de PostgreSQL a SQL Server
5. Crea la tabla en SQL Server con la estructura adecuada
6. Importa los datos usando BCP
7. Maneja errores y registra la operación

### Función: migrate_sqlserver_to_postgres()

```bash
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
```

 
Esta función realiza la migración en sentido contrario, desde SQL Server a PostgreSQL:

1. Exporta los datos de SQL Server usando BCP
2. Verifica la existencia de la tabla en PostgreSQL
3. Crea la tabla si no existe
4. Copia el archivo CSV al contenedor de PostgreSQL
5. Importa los datos usando el comando COPY
6. Registra la operación y maneja posibles errores

## Función de Exportación JSON

### export_json_sqlserver()

Exporta datos de una tabla de SQL Server a formato JSON.

```bash
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

```

**Proceso en detalle:**
1. Exportación a CSV:
   - Usa `bcp` dentro del contenedor Docker para exportar a CSV
   - Especifica delimitador y credenciales
   - Copia el archivo temporal fuera del contenedor

2. Conversión a JSON:
   - Utiliza Python para convertir CSV a JSON
   - Lee el CSV con `csv.DictReader`
   - Formatea el JSON con indentación
   - Guarda el resultado en el archivo final
 
 
## Respaldo en Google Cloud

### upload_postgres_backup_to_gcloud()

Esta función sube el backup más reciente de PostgreSQL a Google Cloud Storage.

```bash
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
```

**Explicación detallada:**
1. `local backup_file=...`: 
   - Busca el archivo más reciente en `$BACKUP_DIR`
   - Usa `ls -t` para listar por fecha (más reciente primero)
   - `grep -E` filtra por el patrón 'backup_postgres_*.sql'
   - `head -n 1` toma solo el primer resultado

2. Verificación y subida:
   - Comprueba si el archivo existe con `[ -f "$backup_file" ]`
   - Usa `gsutil cp` para subir el archivo al bucket
   - Registra el resultado con `log_operation` o `error_log`

### restore_postgres_from_gcloud()

Permite restaurar un backup específico desde Google Cloud Storage.

```bash
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
```

**Explicación detallada:**
1. Interacción con usuario:
   - Solicita el nombre del archivo a restaurar
   - Construye la ruta local donde se guardará

2. Proceso de restauración:
   - Descarga el archivo usando `gsutil cp`
   - Si es exitoso, llama a `restore_postgres` con el archivo
   - Maneja errores con `error_log`

### upload_sqlserver_backup_to_gcloud()

Similar a la función de PostgreSQL, pero para backups de SQL Server.

```bash
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
```

**Diferencias clave con PostgreSQL:**
- Busca archivos `.bak` en lugar de `.sql`
- Usa un bucket específico para SQL Server
- El patrón de nombre es diferente ('my_database_*')

### restore_sqlserver_from_gcloud()

Restaura backups de SQL Server desde Google Cloud Storage.

```bash
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
```

**Diferencias clave con PostgreSQL:**
- Usa un bucket diferente
- Llama a `restore_sqlserver` en lugar de `restore_postgres`






Cada una de estas funciones forma parte de un sistema integral de gestión de datos que permite la interoperabilidad entre PostgreSQL y SQL Server, facilitando la migración y manipulación de datos entre ambos sistemas de gestión de bases de datos.
