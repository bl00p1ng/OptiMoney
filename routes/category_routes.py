"""
Módulo que define las rutas API para operaciones con categorías - Versión temporal para pruebas.
"""
from flask import Blueprint, request, jsonify
from controllers.category_controller import CategoryController
from utils.logger import get_logger
# from utils.auth_middleware import authenticate_user

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de categorías
category_controller = CategoryController()

# Crear el blueprint para las rutas de categorías
category_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@category_bp.route('', methods=['GET'])
# @authenticate_user
async def get_categories():
    """
    Obtiene todas las categorías disponibles para el usuario.
    
    Query params:
        - type (str, optional): Filtro por tipo ("expense" o "income").
        
    Returns:
        JSON: Lista de categorías.
    """
    try:
        # Extraer parámetros de consulta
        category_type = request.args.get('type')
        
        # MODIFICACIÓN TEMPORAL: Usar un user_id fijo para pruebas
        # En lugar de obtener el ID del usuario autenticado
        # user_id = request.auth_user['uid']
        user_id = "test_user_id"  # ID de usuario para pruebas
        
        # Llamar al controlador según el tipo
        if category_type:
            result = await category_controller.get_categories_by_type(category_type, user_id)
        else:
            result = await category_controller.get_all_categories(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al obtener categorías: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Resto del código sin cambios...

@category_bp.route('', methods=['POST'])
# @authenticate_user
async def create_category():
    """
    Crea una nueva categoría personalizada.
    
    Request body:
        - name (str): Nombre de la categoría.
        - type (str): Tipo de categoría ("expense" o "income").
        - icon (str, optional): Icono a usar.
        - color (str, optional): Color en formato hex.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # MODIFICACIÓN TEMPORAL: Usar un user_id fijo para pruebas
        # data['user_id'] = request.auth_user['uid']
        data['user_id'] = "test_user_id"  # ID de usuario para pruebas
        
        # Llamar al controlador
        result = await category_controller.create_category(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al crear categoría: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@category_bp.route('/<category_id>', methods=['PUT'])
# @authenticate_user
async def update_category(category_id):
    """
    Actualiza una categoría existente.
    
    Args:
        category_id: ID de la categoría a actualizar.
        
    Request body:
        - name (str, optional): Nuevo nombre.
        - icon (str, optional): Nuevo icono.
        - color (str, optional): Nuevo color.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # MODIFICACIÓN TEMPORAL: Usar un user_id fijo para pruebas
        # user_id = request.auth_user['uid']
        user_id = "test_user_id"  # ID de usuario para pruebas
        
        # Llamar al controlador
        result = await category_controller.update_category(category_id, user_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al actualizar categoría: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@category_bp.route('/<category_id>', methods=['DELETE'])
# @authenticate_user
async def delete_category(category_id):
    """
    Elimina una categoría personalizada.
    
    Args:
        category_id: ID de la categoría a eliminar.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # MODIFICACIÓN TEMPORAL: Usar un user_id fijo para pruebas
        # user_id = request.auth_user['uid']
        user_id = "test_user_id"  # ID de usuario para pruebas
        
        # Llamar al controlador
        result = await category_controller.delete_category(category_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al eliminar categoría: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@category_bp.route('/initialize-defaults', methods=['POST'])
async def initialize_defaults():
    """
    Inicializa las categorías predefinidas del sistema.
    
    Esta ruta no requiere autenticación ya que se usa para la instalación inicial.
    
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Llamar al controlador
        result = await category_controller.initialize_default_categories()
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al inicializar categorías predefinidas: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_category_routes(app):
    """
    Registra las rutas de categorías en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(category_bp)
    logger.info("Rutas de categorías registradas")