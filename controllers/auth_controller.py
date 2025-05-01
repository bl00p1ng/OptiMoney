"""
Controlador para gestionar la autenticación de usuarios.

Este módulo implementa las operaciones relacionadas con la autenticación
de usuarios, como registro, inicio de sesión y gestión de tokens.
"""
import os
import json
import time
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import jwt
from firebase_admin import auth

from models.user_model import User
from models.repositories.user_repository import UserRepository
from utils.logger import get_logger
from config.firebase_auth_client import firebase_auth_client

# Logger específico para este módulo
logger = get_logger(__name__)

class AuthController:
    """
    Controlador para operaciones de autenticación de usuarios.
    
    Este controlador maneja el registro, inicio de sesión y verificación
    de usuarios en la aplicación, utilizando Firebase Authentication.
    """
    
    def __init__(self):
        """Inicializa el controlador de autenticación."""
        self.user_repo = UserRepository()
        self.jwt_secret = os.environ.get('JWT_SECRET', 'optimoney_secret_key')
        self.token_expiry = int(os.environ.get('TOKEN_EXPIRY', '86400'))  # Default: 24 horas
        logger.debug("Controlador de autenticación inicializado")
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Registra un nuevo usuario en el sistema.
        
        Args:
            user_data: Diccionario con los datos del usuario a registrar
                (email, password, name).
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Validar datos requeridos
            required_fields = ["email", "password", "name"]
            for field in required_fields:
                if field not in user_data:
                    return {
                        "success": False,
                        "error": f"El campo '{field}' es requerido"
                    }
                    
            email = user_data["email"]
            password = user_data["password"]
            name = user_data["name"]
            
            # Validar formato de email
            if "@" not in email or "." not in email:
                return {
                    "success": False,
                    "error": "Formato de email inválido"
                }
                
            # Validar longitud de contraseña
            if len(password) < 6:
                return {
                    "success": False,
                    "error": "La contraseña debe tener al menos 6 caracteres"
                }
                
            # Verificar si el usuario ya existe
            try:
                # Verificar en Firebase
                auth.get_user_by_email(email)
                return {
                    "success": False,
                    "error": "El email ya está registrado"
                }
            except auth.UserNotFoundError:
                # Si no existe, continuar con el registro
                pass
            except Exception as e:
                logger.error(f"Error al verificar existencia de email: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error al verificar disponibilidad de email: {str(e)}"
                }
                
            # Crear usuario en Firebase Authentication
            try:
                # Crear usuario
                firebase_user = auth.create_user(
                    email=email,
                    password=password,
                    display_name=name
                )
                uid = firebase_user.uid
                logger.info(f"Usuario creado en Firebase Auth con ID: {uid}")
            except Exception as e:
                logger.error(f"Error al crear usuario en Firebase Auth: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error al crear usuario: {str(e)}"
                }
                
            # Crear usuario la DB
            user = User(
                id=uid,
                email=email,
                name=name,
                settings={
                    "currency": "CLP",
                    "notificationsEnabled": True
                }
            )
            
            # Guardar usuario en la base de datos
            await self.user_repo.add(user)
            
            # Generar token de autenticación
            token, expiry = self._generate_auth_token(uid, email, name)
            
            return {
                "success": True,
                "message": "Usuario registrado exitosamente",
                "user": {
                    "id": uid,
                    "email": email,
                    "name": name
                },
                "auth": {
                    "token": token,
                    "expiry": expiry
                }
            }
            
        except Exception as e:
            logger.error(f"Error al registrar usuario: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al registrar usuario: {str(e)}"
            }
    
    async def login_user(self, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """
        Autentica a un usuario mediante sus credenciales.
        
        Args:
            credentials: Diccionario con las credenciales (email, password).
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado del inicio de sesión.
        """
        try:
            # Validar datos requeridos
            if "email" not in credentials or "password" not in credentials:
                return {
                    "success": False,
                    "error": "Se requiere email y contraseña"
                }
                
            email = credentials["email"]
            password = credentials["password"]
            
            # Autenticar mediante Firebase REST API
            success, user_data = firebase_auth_client.verify_credentials(email, password)
            
            if not success:
                return {
                    "success": False,
                    "error": "Credenciales inválidas"
                }
                
            # Extraer datos del usuario
            uid = user_data["uid"]
            firebase_token = user_data["idToken"]
            
            # Buscar usuario en la BD
            user = await self.user_repo.get_by_id(uid)
            
            # Si no existe en la BD, crearlo
            if not user:
                display_name = user_data.get("displayName", email.split("@")[0])
                user = User(
                    id=uid,
                    email=email,
                    name=display_name,
                    settings={
                        "currency": "CLP",
                        "notificationsEnabled": True
                    }
                )
                await self.user_repo.add(user)
                logger.info(f"Creado usuario en base de datos: {uid}")
            
            # Generar token JWT
            token, expiry = self._generate_auth_token(uid, email, user.name)
            
            return {
                "success": True,
                "message": "Inicio de sesión exitoso",
                "user": {
                    "id": uid,
                    "email": email,
                    "name": user.name,
                    "settings": user.settings
                },
                "auth": {
                    "token": token,
                    "firebase_token": firebase_token,
                    "expiry": expiry
                }
            }
                
        except Exception as e:
            logger.error(f"Error en proceso de login: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error de autenticación: {str(e)}"
            }
    
    async def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica la validez de un token de autenticación.
        
        Args:
            token: Token JWT a verificar.
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Tupla con el resultado de la
                verificación (valid, user_data).
        """
        try:
            # Verificar si es un token de ambiente de desarrollo
            if token.startswith("dev_") and os.environ.get('ENVIRONMENT', 'development') != 'production':
                # Tokens de desarrollo para pruebas
                parts = token.split("_")
                if len(parts) < 2:
                    return False, None
                
                uid = parts[1]
                user = await self.user_repo.get_by_id(uid)
                
                if not user:
                    return False, None
                    
                # Crear datos de usuario para desarrollo
                return True, {
                    "uid": uid,
                    "email": user.email,
                    "name": user.name
                }
            
            # En caso contrario, verificar como token JWT normal
            try:
                # Verificar el token con Firebase Auth
                decoded_token = auth.verify_id_token(token)
                return True, decoded_token
            except Exception as firebase_error:
                logger.warning(f"Error al verificar token con Firebase: {str(firebase_error)}")
                
                # Si falla la verificación con Firebase, intentar con el sistema JWT propio
                try:
                    payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
                    
                    # Verificar que el token no haya expirado
                    if payload.get('exp', 0) < time.time():
                        logger.warning("Token JWT expirado")
                        return False, None
                        
                    # Token válido
                    return True, payload
                except Exception as jwt_error:
                    logger.warning(f"Error al verificar token JWT: {str(jwt_error)}")
                    return False, None
                    
        except Exception as e:
            logger.error(f"Error al verificar token: {str(e)}", exc_info=True)
            return False, None
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene el perfil completo de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Perfil del usuario o error si no existe.
        """
        try:
            # Obtener usuario de la base de datos
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                return {
                    "success": False,
                    "error": "Usuario no encontrado"
                }
                
            # Obtener información adicional de Firebase si es necesario
            try:
                firebase_user = auth.get_user(user_id)
                email_verified = firebase_user.email_verified
                creation_date = firebase_user.user_metadata.creation_timestamp
            except Exception as e:
                logger.warning(f"No se pudo obtener datos adicionales de Firebase: {str(e)}")
                email_verified = False
                creation_date = None
            
            # Construir respuesta
            return {
                "success": True,
                "profile": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "settings": user.settings,
                    "email_verified": email_verified,
                    "created_at": user.created_at.isoformat(),
                    "firebase_created_at": creation_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error al obtener perfil de usuario: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener perfil: {str(e)}"
            }
    
    async def update_user_profile(
        self, 
        user_id: str, 
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza el perfil de un usuario.
        
        Args:
            user_id: ID del usuario.
            profile_data: Datos a actualizar en el perfil.
            
        Returns:
            Dict[str, Any]: Resultado de la operación.
        """
        try:
            # Obtener usuario actual
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                return {
                    "success": False,
                    "error": "Usuario no encontrado"
                }
                
            # Campos permitidos para actualización
            allowed_fields = ["name", "settings"]
            update_data = {}
            
            for field in allowed_fields:
                if field in profile_data:
                    update_data[field] = profile_data[field]
            
            # Si no hay datos para actualizar
            if not update_data:
                return {
                    "success": False,
                    "error": "No se proporcionaron datos válidos para actualizar"
                }
                
            # Actualizar en la base de datos
            result = await self.user_repo.update(user_id, update_data)
            
            if not result:
                return {
                    "success": False,
                    "error": "Error al actualizar perfil"
                }
                
            # Si se actualiza el nombre, actualizar también en Firebase
            if "name" in update_data:
                try:
                    auth.update_user(
                        user_id,
                        display_name=update_data["name"]
                    )
                except Exception as e:
                    logger.warning(f"No se pudo actualizar nombre en Firebase: {str(e)}")
            
            # Obtener perfil actualizado
            updated_profile = await self.get_user_profile(user_id)
            
            return {
                "success": True,
                "message": "Perfil actualizado correctamente",
                "profile": updated_profile.get("profile", {})
            }
            
        except Exception as e:
            logger.error(f"Error al actualizar perfil de usuario: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al actualizar perfil: {str(e)}"
            }
    
    async def change_password(
        self, 
        user_id: str, 
        password_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cambia la contraseña de un usuario.
        
        Args:
            user_id: ID del usuario.
            password_data: Diccionario con las contraseñas (current_password, new_password).
            
        Returns:
            Dict[str, Any]: Resultado de la operación.
        """
        try:
            # Validar datos requeridos
            if "current_password" not in password_data or "new_password" not in password_data:
                return {
                    "success": False,
                    "error": "Se requiere contraseña actual y nueva"
                }
                
            current_password = password_data["current_password"]
            new_password = password_data["new_password"]
            
            # Validar longitud de nueva contraseña
            if len(new_password) < 6:
                return {
                    "success": False,
                    "error": "La nueva contraseña debe tener al menos 6 caracteres"
                }
                
            # Obtener el usuario
            user = await self.user_repo.get_by_id(user_id)
            
            if not user:
                return {
                    "success": False,
                    "error": "Usuario no encontrado"
                }
                
            # Verificar la contraseña actual
            try:
                firebase_user = auth.get_user(user_id)
                email = firebase_user.email
                
                # Verificar credenciales actuales con Firebase REST API
                success, _ = firebase_auth_client.verify_credentials(email, current_password)
                
                if not success:
                    return {
                        "success": False,
                        "error": "La contraseña actual es incorrecta"
                    }
                
                # Si la contraseña actual es correcta, actualizar a la nueva
                auth.update_user(
                    user_id,
                    password=new_password
                )
                
                return {
                    "success": True,
                    "message": "Contraseña actualizada correctamente"
                }
                
            except Exception as e:
                logger.error(f"Error al cambiar contraseña: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"Error al cambiar contraseña: {str(e)}"
                }
            
        except Exception as e:
            logger.error(f"Error en cambio de contraseña: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al cambiar contraseña: {str(e)}"
            }
    
    def _generate_auth_token(
        self, 
        user_id: str, 
        email: str, 
        name: str
    ) -> Tuple[str, int]:
        """
        Genera un token JWT para autenticación.
        
        Args:
            user_id: ID del usuario.
            email: Email del usuario.
            name: Nombre del usuario.
            
        Returns:
            Tuple[str, int]: Token generado y timestamp de expiración.
        """
        # Calcular tiempo de expiración
        expiry = int(time.time()) + self.token_expiry
        
        # Crear payload
        payload = {
            "uid": user_id,
            "email": email,
            "name": name,
            "iat": int(time.time()),
            "exp": expiry
        }
        
        # Generar token
        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        
        # Si es una cadena de bytes, convertir a str
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        
        return token, expiry