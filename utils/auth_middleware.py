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
            # Verificar el token
            # Primero intentar con Firebase Auth
            try:
                # Verificar el token con Firebase Auth
                decoded_token = auth.verify_id_token(token)
                
                # Añadir información del usuario al request
                request.auth_user = decoded_token
                
                logger.debug(f"Usuario autenticado con Firebase: {decoded_token.get('uid')}")
            except Exception as firebase_error:
                logger.debug(f"No se pudo verificar con Firebase: {str(firebase_error)}")
                
                # Si falla la verificación con Firebase, intentar con JWT propio
                jwt_secret = os.environ.get('JWT_SECRET', 'optimoney_secret_key')
                
                try:
                    # Decodificar con nuestro secreto JWT
                    payload = jwt.decode(token, jwt_secret, algorithms=['HS256'])
                    
                    # Añadir información del usuario al request
                    request.auth_user = {
                        'uid': payload.get('uid'),
                        'email': payload.get('email'),
                        'name': payload.get('name')
                    }
                    
                    logger.debug(f"Usuario autenticado con JWT: {payload.get('uid')}")
                except jwt.ExpiredSignatureError:
                    logger.warning("Token JWT expirado")
                    return jsonify({
                        'success': False,
                        'error': 'Token expirado'
                    }), 401
                except jwt.InvalidTokenError:
                    logger.warning("Token JWT inválido")
                    return jsonify({
                        'success': False,
                        'error': 'Token inválido'
                    }), 401
                except Exception as jwt_error:
                    # Si también falla JWT, verificar token de desarrollo
                    if token.startswith("dev_") and os.environ.get('ENVIRONMENT') != 'production':
                        # Tokens de desarrollo para pruebas
                        parts = token.split("_")
                        if len(parts) >= 2:
                            uid = parts[1]
                            
                            # Añadir información básica del usuario al request
                            request.auth_user = {
                                'uid': uid,
                                'email': f'dev_{uid}@example.com',
                                'name': f'Dev User {uid}'
                            }
                            
                            logger.debug(f"Usuario autenticado con token de desarrollo: {uid}")
                        else:
                            logger.warning("Token de desarrollo inválido")
                            return jsonify({
                                'success': False,
                                'error': 'Token de desarrollo inválido'
                            }), 401
                    else:
                        # Si ningún método funciona, el token es inválido
                        logger.warning("Token inválido - No se pudo verificar con ningún método")
                        return jsonify({
                            'success': False,
                            'error': 'Token inválido'
                        }), 401
            
            # A este punto, el usuario está autenticado y el token es válido
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
    
    # Clave secreta para pruebas
    secret = os.environ.get('JWT_SECRET', 'optimoney_secret_key')
    
    # Generar token
    token = jwt.encode(payload, secret, algorithm='HS256')
    
    return token