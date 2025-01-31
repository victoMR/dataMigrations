import subprocess
from typing import Optional, Tuple
import os
import logging
from pathlib import Path

class DockerManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Verificar que docker compose está instalado
        self._verify_docker_compose()

    def _verify_docker_compose(self):
        """Verificar que docker compose está instalado y disponible"""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise Exception("Docker Compose no está instalado o no es accesible")
            self.logger.info(f"Docker Compose versión detectada: {result.stdout.strip()}")
        except Exception as e:
            self.logger.error(f"Error verificando Docker Compose: {e}")
            raise

    def _verify_compose_file(self, compose_file: str) -> bool:
        """Verificar que el archivo docker-compose existe y es válido"""
        compose_path = Path(compose_file)
        if not compose_path.exists():
            self.logger.error(f"No se encontró el archivo docker-compose en: {compose_path}")
            return False
        
        if not compose_path.is_file():
            self.logger.error(f"La ruta no es un archivo válido: {compose_path}")
            return False
            
        return True

    def run_docker_command(self, command: list, cwd: Optional[str] = None) -> Tuple[int, str, str]:
        """Ejecutar un comando docker y retornar status, output y error."""
        try:
            self.logger.debug(f"Ejecutando comando: {' '.join(command)}")
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=cwd,
                text=True
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            self.logger.error(f"Error ejecutando comando docker: {e}")
            return 1, "", str(e)

    def docker_compose_up(self, compose_file: str) -> Tuple[bool, str]:
        """Iniciar contenedores usando docker compose up."""
        if not self._verify_compose_file(compose_file):
            return False, f"No se encontró el archivo docker-compose en: {compose_file}"

        cwd = os.path.dirname(compose_file)
        self.logger.info(f"Iniciando contenedores en: {cwd}")
        
        code, out, err = self.run_docker_command(
            ["docker", "compose", "-f", compose_file, "up", "-d"],
            cwd=cwd
        )
        if code == 0:
            self.logger.info("Contenedores iniciados exitosamente")
        else:
            self.logger.error(f"Error iniciando contenedores: {err}")
        return code == 0, err if code != 0 else "Contenedores iniciados exitosamente"

    def docker_compose_down(self, compose_file: str) -> Tuple[bool, str]:
        """Detener contenedores usando docker compose down."""
        if not self._verify_compose_file(compose_file):
            return False, f"No se encontró el archivo docker-compose en: {compose_file}"

        cwd = os.path.dirname(compose_file)
        self.logger.info(f"Deteniendo contenedores en: {cwd}")
        
        code, out, err = self.run_docker_command(
            ["docker", "compose", "-f", compose_file, "down"],
            cwd=cwd
        )
        if code == 0:
            self.logger.info("Contenedores detenidos exitosamente")
        else:
            self.logger.error(f"Error deteniendo contenedores: {err}")
        return code == 0, err if code != 0 else "Contenedores detenidos exitosamente"

    def check_docker_status(self, compose_file: str) -> Tuple[bool, str]:
        """Verificar si los contenedores están en ejecución."""
        if not self._verify_compose_file(compose_file):
            return False, f"No se encontró el archivo docker-compose en: {compose_file}"

        cwd = os.path.dirname(compose_file)
        code, out, err = self.run_docker_command(
            ["docker", "compose", "-f", compose_file, "ps"],
            cwd=cwd
        )
        return code == 0, out if code == 0 else err