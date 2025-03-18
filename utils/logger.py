"""
Módulo para la configuración y gestión centralizada de logs de la aplicación.

Este módulo proporciona funciones para configurar y obtener loggers personalizados
para cada componente de la aplicación, asegurando un formato consistente
y niveles de log apropiados según el entorno.
"""
import os
import logging
import sys
from datetime import datetime
from typing import Optional

# Formato estándar para todos los logs
LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Niveles de log según entorno
LOG_LEVELS = {
    'development': logging.DEBUG,
    'production': logging.INFO
}

def setup_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Configura y devuelve un logger personalizado para un módulo específico.
    
    Args:
        name: Nombre del módulo o componente (se usará como identificador en los logs).
        level: Nivel de logging opcional. Si no se proporciona, se usa el nivel según el entorno.
        
    Returns:
        logging.Logger: Logger configurado listo para usar.
    """
    # Determinar el nivel de log según el entorno si no se especifica
    environment = os.environ.get('ENVIRONMENT', 'development')
    if level is None:
        level = LOG_LEVELS.get(environment, logging.INFO)
    
    # Crear y configurar el logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Evitar duplicación de handlers si el logger ya está configurado
    if not logger.handlers:
        # Handler para salida a consola
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # Formatter con el formato estándar
        formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(formatter)
        
        # Agregar el handler al logger
        logger.addHandler(console_handler)
    
    return logger

def get_logger(module_name: str) -> logging.Logger:
    """
    Obtiene un logger configurado para un módulo específico.
    
    Esta función debe ser usada por todos los componentes de la aplicación
    para obtener un logger consistente.
    
    Args:
        module_name: Nombre del módulo o componente.
        
    Returns:
        logging.Logger: Logger configurado.
    """
    return setup_logger(module_name)

# Logger principal de la aplicación
app_logger = get_logger('app')
