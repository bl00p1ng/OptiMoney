"""
Módulo que define las rutas API para operaciones de autenticación.

Este módulo expone los endpoints para el registro e inicio de sesión
de usuarios, así como la gestión de perfiles.
"""
from flask import Blueprint, request, jsonify
from controllers.auth_controller import AuthController
from utils.logger import get_logger
from utils.auth_middleware import authenticate_user

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de autenticación
auth_controller = AuthController()

# Crear el blueprint para las rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
async def register():
    """
    Registra un nuevo usuario en el sistema.
    
    Request body:
        - email (str): Correo electrónico del usuario.
        - password (str): Contraseña del usuario.
        - name (str): Nombre completo del usuario.
        
    Returns:
        JSON: Resultado del registro con token de autenticación si es exitoso.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        user_data = request.get_json()
        
        # Llamar al controlador
        result = await auth_controller.register_user(user_data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al registrar usuario: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@auth_bp.route('/login', methods=['POST'])
async def login():
    """
    Autentica a un usuario mediante sus credenciales.
    
    Request body:
        - email (str): Correo electrónico del usuario.
        - password (str): Contraseña del usuario.
        
    Returns:
        JSON: Resultado del inicio de sesión con token de autenticación si es exitoso.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        credentials = request.get_json()
        
        # Llamar al controlador
        result = await auth_controller.login_user(credentials)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 401
    except Exception as e:
        logger.error(f"Error en inicio de sesión: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@authenticate_user
async def get_profile():
    """
    Obtiene el perfil del usuario autenticado.
    
    Returns:
        JSON: Perfil completo del usuario.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await auth_controller.get_user_profile(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error al obtener perfil: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@auth_bp.route('/profile', methods=['PUT'])
@authenticate_user
async def update_profile():
    """
    Actualiza el perfil del usuario autenticado.
    
    Request body:
        - name (str, optional): Nuevo nombre del usuario.
        - settings (dict, optional): Nuevas configuraciones del usuario.
        
    Returns:
        JSON: Resultado de la actualización con el perfil actualizado.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener datos del cuerpo de la solicitud
        profile_data = request.get_json()
        
        # Llamar al controlador
        result = await auth_controller.update_user_profile(user_id, profile_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al actualizar perfil: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@authenticate_user
async def change_password():
    """
    Cambia la contraseña del usuario autenticado.
    
    Request body:
        - current_password (str): Contraseña actual.
        - new_password (str): Nueva contraseña.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener datos del cuerpo de la solicitud
        password_data = request.get_json()
        
        # Llamar al controlador
        result = await auth_controller.change_password(user_id, password_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al cambiar contraseña: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@auth_bp.route('/verify', methods=['GET'])
@authenticate_user
async def verify_token():
    """
    Verifica que el token de autenticación sea válido.
    
    Returns:
        JSON: Información del usuario si el token es válido.
    """
    try:
        # El middleware @authenticate_user ya verificó el token
        # y añadió la información del usuario a request.auth_user
        
        return jsonify({
            'success': True,
            'message': 'Token válido',
            'user': {
                'id': request.auth_user['uid'],
                'email': request.auth_user.get('email'),
                'name': request.auth_user.get('name')
            }
        }), 200
    except Exception as e:
        logger.error(f"Error al verificar token: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_auth_routes(app):
    """
    Registra las rutas de autenticación en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(auth_bp)
    logger.info("Rutas de autenticación registradas")