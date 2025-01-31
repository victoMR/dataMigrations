import os
import logging
from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class DatabaseConfig:
    """Configuración para conexiones de base de datos"""
    host: str
    port: str
    database: str
    username: str
    password: str
    table_name: str

    def get_postgres_url(self) -> str:
        """Retorna la URL de conexión para PostgreSQL"""
        return f'postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'

    def get_sqlserver_url(self) -> str:
        """Retorna la URL de conexión para SQL Server"""
        return f'mssql+pymssql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}'

@dataclass
class DockerConfig:
    """Configuración para servicios Docker"""
    compose_file: str
    env_file: Optional[str] = None
    container_name: Optional[str] = None
    service_name: Optional[str] = None

class AppConfig:
    """Configuración principal de la aplicación"""
    def __init__(self):
        # Configuración de rutas base
        self.BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
        self.LOGS_DIR = self.BASE_DIR / "logs"
        self.POSTGRES_DOCKER_DIR = self.BASE_DIR / "postgres"
        self.SQLSERVER_DOCKER_DIR = self.BASE_DIR / "sqlServer"
        
        # Crear directorio de logs si no existe
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # Configurar logging
        self._setup_logging()
        
        # Verificar y configurar rutas de Docker
        self._setup_docker_paths()
        
        # Configurar bases de datos por defecto
        self._setup_database_configs()

    def _setup_logging(self):
        """Configurar el sistema de logging"""
        log_file = self.LOGS_DIR / "app.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Logging configurado exitosamente")

    def _setup_docker_paths(self):
        """Configurar y verificar rutas de Docker Compose"""
        # Verificar existencia de directorios
        for dir_path in [self.POSTGRES_DOCKER_DIR, self.SQLSERVER_DOCKER_DIR]:
            if not dir_path.exists():
                self.logger.error(f"No se encontró el directorio: {dir_path}")
                raise FileNotFoundError(f"Directorio no encontrado: {dir_path}")
        
        # Definir configuraciones de Docker
        self.DOCKER_CONFIGS = {
            "postgres": DockerConfig(
                compose_file=str(self.POSTGRES_DOCKER_DIR / "docker-compose.yml"),
                container_name="postgres_container",
                service_name="postgres"
            ),
            "sqlserver": DockerConfig(
                compose_file=str(self.SQLSERVER_DOCKER_DIR / "docker-compose.yml"),
                container_name="sqlserver_container",
                service_name="sqlserver"
            )
        }
        
        # Verificar existencia de archivos docker-compose
        for service, config in self.DOCKER_CONFIGS.items():
            compose_path = Path(config.compose_file)
            if not compose_path.exists():
                self.logger.error(f"No se encontró el archivo docker-compose para {service}: {compose_path}")
                raise FileNotFoundError(f"Archivo docker-compose no encontrado para {service}: {compose_path}")
            self.logger.info(f"Archivo docker-compose encontrado para {service}: {compose_path}")

    def _setup_database_configs(self):
        """Configurar conexiones de base de datos por defecto"""
        # Configuración por defecto para PostgreSQL
        self.DEFAULT_PG_CONFIG = DatabaseConfig(
            host="127.0.0.1",
            port="5433",
            database="my_database",
            username="my_user",
            password="Batmanlol1",
            table_name="anime_list"
        )
        
        # Configuración por defecto para SQL Server
        self.DEFAULT_SQL_CONFIG = DatabaseConfig(
            host="127.0.0.1",
            port="1433",
            database="TestBD",
            username="sa",
            password="Batmanlol1",
            table_name="anime_list"
        )

    def get_postgres_config(self) -> DatabaseConfig:
        """Retorna la configuración de PostgreSQL"""
        return self.DEFAULT_PG_CONFIG

    def get_sqlserver_config(self) -> DatabaseConfig:
        """Retorna la configuración de SQL Server"""
        return self.DEFAULT_SQL_CONFIG

    def get_docker_config(self, service: str) -> DockerConfig:
        """Retorna la configuración de Docker para un servicio específico"""
        if service not in self.DOCKER_CONFIGS:
            raise ValueError(f"Servicio no encontrado: {service}")
        return self.DOCKER_CONFIGS[service]

    def update_postgres_config(self, **kwargs):
        """Actualizar configuración de PostgreSQL"""
        config_dict = self.DEFAULT_PG_CONFIG.__dict__.copy()
        config_dict.update(kwargs)
        self.DEFAULT_PG_CONFIG = DatabaseConfig(**config_dict)

    def update_sqlserver_config(self, **kwargs):
        """Actualizar configuración de SQL Server"""
        config_dict = self.DEFAULT_SQL_CONFIG.__dict__.copy()
        config_dict.update(kwargs)
        self.DEFAULT_SQL_CONFIG = DatabaseConfig(**config_dict)

# Constantes de la aplicación
APP_NAME = "ETL Tool"
APP_VERSION = "1.0.0"
DEFAULT_ENCODING = "utf-8"
MAX_PREVIEW_ROWS = 100
SUPPORTED_FILE_TYPES = [("CSV files", "*.csv")]

# Configuración de la interfaz gráfica
GUI_CONFIG = {
    "window_title": APP_NAME,
    "window_size": "1200x800",
    "theme": "dark",  # or "light"
    "font_family": "Arial",
    "font_size": {
        "small": 10,
        "normal": 12,
        "large": 14,
        "title": 18
    },
    "padding": {
        "small": 5,
        "normal": 10,
        "large": 20
    }
}