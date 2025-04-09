"""
Módulo que define las rutas API para operaciones con recomendaciones.
"""
from flask import Blueprint, request, jsonify
from controllers.recommendation_controller import RecommendationController
from utils.logger import get_logger
from utils.auth_middleware import authenticate_user

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de recomendaciones
recommendation_controller = RecommendationController()

# Crear el blueprint para las rutas de recomendaciones
recommendation_bp = Blueprint('recommendations', __name__, url_prefix='/api/recommendations')

@recommendation_bp.route('/generate', methods=['POST'])
@authenticate_user
async def generate_recommendations():
    """
    Genera recomendaciones para el usuario autenticado.
    
    Returns:
        JSON: Resultado del proceso de generación de recomendaciones.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await recommendation_controller.generate_recommendations(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al generar recomendaciones: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@recommendation_bp.route('', methods=['GET'])
@authenticate_user
async def get_user_recommendations():
    """
    Obtiene las recomendaciones activas para el usuario autenticado.
    
    Query params:
        - limit (int, optional): Número máximo de recomendaciones a obtener.
        
    Returns:
        JSON: Lista de recomendaciones.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener parámetro de límite
        limit_str = request.args.get('limit', '5')
        
        try:
            limit = int(limit_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': "El parámetro 'limit' debe ser un número entero."
            }), 400
        
        # Llamar al controlador
        result = await recommendation_controller.get_user_recommendations(
            user_id, 
            limit
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al obtener recomendaciones: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@recommendation_bp.route('/<recommendation_id>/shown', methods=['POST'])
@authenticate_user
async def mark_recommendation_shown(recommendation_id):
    """
    Marca una recomendación específica como mostrada.
    
    Args:
        recommendation_id: ID de la recomendación a marcar.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await recommendation_controller.mark_recommendation_shown(
            recommendation_id, 
            user_id
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al marcar recomendación como mostrada: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@recommendation_bp.route('/<recommendation_id>/interaction', methods=['POST'])
@authenticate_user
async def update_recommendation_interaction(recommendation_id):
    """
    Registra la interacción del usuario con una recomendación.
    
    Args:
        recommendation_id: ID de la recomendación.
        
    Request body:
        - interaction_type (str): Tipo de interacción.
        - details (dict, optional): Detalles adicionales de la interacción.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # Validar datos de entrada
        if 'interaction_type' not in data:
            return jsonify({
                'success': False,
                'error': "El campo 'interaction_type' es requerido"
            }), 400
        
        # Obtener parámetros
        interaction_type = data['interaction_type']
        details = data.get('details')
        
        # Llamar al controlador
        result = await recommendation_controller.update_recommendation_interaction(
            recommendation_id, 
            user_id, 
            interaction_type, 
            details
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al registrar interacción de recomendación: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_recommendation_routes(app):
    """
    Registra las rutas de recomendaciones en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(recommendation_bp)
    logger.info("Rutas de recomendaciones registradas")