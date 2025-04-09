"""
Módulo para la inicialización y registro de todas las rutas de la API.
"""
from flask import Flask
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

def register_routes(app: Flask) -> None:
    """
    Registra todas las rutas de la API en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    try:
        # Importar funciones de registro de cada módulo de rutas
        from routes.transaction_routes import register_transaction_routes
        from routes.health_routes import register_health_routes
        from routes.category_routes import register_category_routes
        from routes.analysis_routes import register_analysis_routes
        
        # Registrar cada conjunto de rutas
        register_health_routes(app)
        register_transaction_routes(app)
        register_category_routes(app)
        register_analysis_routes(app)
        register_category_routes(app)
        
        logger.info("Todas las rutas API han sido registradas correctamente")
    except Exception as e:
        logger.error(f"Error al registrar rutas: {str(e)}", exc_info=True)
        raise