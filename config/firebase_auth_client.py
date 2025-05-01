"""
Cliente para interactuar con la API REST de Firebase Authentication.

Este módulo implementa las llamadas a la API REST de Firebase Authentication
para realizar operaciones como verificación de credenciales y gestión de tokens.
"""
import os
import json
import requests
from typing import Dict, Any, Optional, Tuple
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class FirebaseAuthClient:
    """
    Cliente para interactuar con la API REST de Firebase Authentication.
    
    Esta clase proporciona métodos para verificar credenciales, generar tokens
    y otras operaciones de autenticación usando la API REST de Firebase.
    """
    
    def __init__(self):
        """Inicializa el cliente de Firebase Authentication."""
        self.api_key = os.environ.get('FIREBASE_API_KEY')
        if not self.api_key:
            logger.warning("FIREBASE_API_KEY no está configurada. La autenticación con Firebase REST API no funcionará.")
            
        self.base_url = "https://identitytoolkit.googleapis.com/v1"
        self.signin_url = f"{self.base_url}/accounts:signInWithPassword"
        self.user_data_url = f"{self.base_url}/accounts:lookup"
        
    def verify_credentials(self, email: str, password: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica las credenciales de un usuario usando la API REST de Firebase.
        
        Args:
            email: Email del usuario.
            password: Contraseña del usuario.
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Tupla con el resultado de la
                verificación (success, user_data).
        """
        if not self.api_key:
            logger.error("No se puede verificar credenciales: FIREBASE_API_KEY no está configurada")
            return False, None
            
        try:
            # Datos para la solicitud
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            
            # Realizar la solicitud a Firebase Auth REST API
            response = requests.post(
                f"{self.signin_url}?key={self.api_key}",
                json=payload
            )
            
            # Verificar respuesta
            if response.status_code == 200:
                data = response.json()
                
                # Extraer información relevante
                user_data = {
                    "uid": data.get("localId"),
                    "email": data.get("email"),
                    "emailVerified": data.get("emailVerified", False),
                    "displayName": data.get("displayName", ""),
                    "idToken": data.get("idToken"),
                    "refreshToken": data.get("refreshToken"),
                    "expiresIn": data.get("expiresIn")
                }
                
                logger.info(f"Credenciales verificadas exitosamente para {email}")
                return True, user_data
            else:
                # Obtener mensaje de error
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Error desconocido")
                
                if error_message == "EMAIL_NOT_FOUND":
                    logger.warning(f"Email no encontrado: {email}")
                elif error_message == "INVALID_PASSWORD":
                    logger.warning(f"Contraseña inválida para: {email}")
                else:
                    logger.warning(f"Error de autenticación: {error_message}")
                    
                return False, None
                
        except Exception as e:
            logger.error(f"Error al verificar credenciales: {str(e)}", exc_info=True)
            return False, None
            
    def get_user_data(self, id_token: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene datos de usuario a partir de un token de ID.
        
        Args:
            id_token: Token de ID de Firebase.
            
        Returns:
            Optional[Dict[str, Any]]: Datos del usuario o None si hay error.
        """
        if not self.api_key:
            logger.error("No se puede obtener datos de usuario: FIREBASE_API_KEY no está configurada")
            return None
            
        try:
            # Datos para la solicitud
            payload = {
                "idToken": id_token
            }
            
            # Realizar la solicitud a Firebase Auth REST API
            response = requests.post(
                f"{self.user_data_url}?key={self.api_key}",
                json=payload
            )
            
            # Verificar respuesta
            if response.status_code == 200:
                data = response.json()
                users = data.get("users", [])
                
                if users:
                    user = users[0]
                    
                    # Extraer información relevante
                    user_data = {
                        "uid": user.get("localId"),
                        "email": user.get("email"),
                        "emailVerified": user.get("emailVerified", False),
                        "displayName": user.get("displayName", ""),
                        "photoUrl": user.get("photoUrl", ""),
                        "createdAt": user.get("createdAt")
                    }
                    
                    return user_data
                else:
                    logger.warning("No se encontraron datos de usuario para el token proporcionado")
                    return None
            else:
                # Obtener mensaje de error
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Error desconocido")
                logger.warning(f"Error al obtener datos de usuario: {error_message}")
                return None
                
        except Exception as e:
            logger.error(f"Error al obtener datos de usuario: {str(e)}", exc_info=True)
            return None
            
    def refresh_token(self, refresh_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Refresca un token de autenticación usando el refresh token.
        
        Args:
            refresh_token: Token de refresco proporcionado durante la autenticación.
            
        Returns:
            Tuple[bool, Optional[Dict[str, Any]]]: Tupla con el resultado de la
                operación (success, token_data).
        """
        if not self.api_key:
            logger.error("No se puede refrescar token: FIREBASE_API_KEY no está configurada")
            return False, None
            
        try:
            # Datos para la solicitud
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            }
            
            # Realizar la solicitud a Firebase Auth REST API
            response = requests.post(
                f"https://securetoken.googleapis.com/v1/token?key={self.api_key}",
                json=payload
            )
            
            # Verificar respuesta
            if response.status_code == 200:
                data = response.json()
                
                # Extraer información relevante
                token_data = {
                    "id_token": data.get("id_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in")
                }
                
                logger.info("Token refrescado exitosamente")
                return True, token_data
            else:
                # Obtener mensaje de error
                error_data = response.json()
                error_message = error_data.get("error", {}).get("message", "Error desconocido")
                logger.warning(f"Error al refrescar token: {error_message}")
                return False, None
                
        except Exception as e:
            logger.error(f"Error al refrescar token: {str(e)}", exc_info=True)
            return False, None

# Instancia global del cliente
firebase_auth_client = FirebaseAuthClient()