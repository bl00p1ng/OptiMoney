"""
Módulo que contiene middleware para la autenticación de usuarios.
"""
import os
import functools
from typing import Callable, Any
import jwt
from flask import request, jsonify, g
from firebase_admin import auth
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

def authenticate_user(f: Callable) -> Callable:
    """
    Decorador para verificar la autenticación del usuario.
    
    Este decorador verifica que el token de Firebase sea válido
    y añade la información del usuario a request.auth_user.
    
    Args:
        f: Función a decorar.
        
    Returns:
        Callable: Función decorada.
    """
    @functools.wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Obtener el token de autorización del encabezado
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            logger.warning("Token de autenticación no proporcionado")
            return jsonify({
                'success': False,
                'error': 'Se requiere autenticación'
            }), 401
        
        # El encabezado debe ser de la forma "Bearer {token}"
        parts = auth_header.split()
        
        if parts[0].lower() != 'bearer':
            logger.warning("Formato de token inválido")
            return jsonify({
                'success': False,
                'error': 'Formato de autenticación inválido'
            }), 401
            
        if len(parts) == 1:
            logger.warning("Token no proporcionado")
            return jsonify({
                'success': False,
                'error': 'Token no proporcionado'
            }), 401
            
        token = parts[1]
        
        try:
            # Verificar el token con Firebase Auth
            decoded_token = auth.verify_id_token(token)
            
            # Añadir información del usuario al request
            request.auth_user = decoded_token
            
            logger.debug(f"Usuario autenticado: {decoded_token.get('uid')}")
            
            # Continuar con la función original
            return await f(*args, **kwargs)
        except auth.ExpiredIdTokenError:
            logger.warning("Token expirado")
            return jsonify({
                'success': False,
                'error': 'Token expirado'
            }), 401
        except auth.InvalidIdTokenError:
            logger.warning("Token inválido")
            return jsonify({
                'success': False,
                'error': 'Token inválido'
            }), 401
        except auth.RevokedIdTokenError:
            logger.warning("Token revocado")
            return jsonify({
                'success': False,
                'error': 'Token revocado'
            }), 401
        except Exception as e:
            logger.error(f"Error al autenticar: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': 'Error de autenticación'
            }), 500
            
    return decorated_function

def get_test_token(user_id: str) -> str:
    """
    Genera un token JWT para pruebas.
    
    Este método solo debe usarse en entornos de desarrollo y pruebas.
    
    Args:
        user_id: ID del usuario para el token.
        
    Returns:
        str: Token JWT para pruebas.
    """
    if os.environ.get('ENVIRONMENT') == 'production':
        raise Exception("No se pueden generar tokens de prueba en producción")
        
    payload = {
        'uid': user_id,
        'email': f'test_{user_id}@example.com',
        'name': f'Test User {user_id}',
    }
    
    # Clave secreta para pruebas (no usar en producción)
    secret = os.environ.get('JWT_TEST_SECRET', 'test_secret_key')
    
    # Generar token
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    return token