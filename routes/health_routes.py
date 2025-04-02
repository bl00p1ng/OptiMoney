"""
Módulo que define las rutas para verificación de salud del sistema.
"""
from flask import Blueprint, jsonify
from controllers.health_controller import HealthController
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de salud
health_controller = HealthController()

# Crear el blueprint para las rutas de salud
health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
async def check_health():
    """
    Verifica el estado de salud del sistema.
    
    Returns:
        JSON: Estado de salud del sistema y sus servicios.
    """
    try:
        result = await health_controller.check_system_health()
        
        # Determinar el código de estado HTTP basado en el resultado
        status_code = 200
        if result["status"] == "degraded":
            status_code = 200  # Aún así retornamos 200 pero con info de degradación
        elif result["status"] == "error":
            status_code = 500
            
        return jsonify(result), status_code
    except Exception as e:
        logger.error(f"Error al verificar salud del sistema: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Error inesperado: {str(e)}"
        }), 500

@health_bp.route('/ping', methods=['GET'])
async def ping():
    """
    Endpoint simple para verificar que la aplicación está respondiendo.
    
    Returns:
        JSON: Respuesta simple de ping.
    """
    return jsonify({
        "status": "ok",
        "message": "pong"
    }), 200

# Función para registrar el blueprint en la aplicación
def register_health_routes(app):
    """
    Registra las rutas de salud en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(health_bp)
    logger.info("Rutas de salud registradas")