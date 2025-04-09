"""
Módulo para la configuración y conexión con Firebase.
"""
import os
import json
from firebase_admin import credentials, initialize_app, firestore
from utils.logger import get_logger

# Obtener logger específico para este módulo
logger = get_logger(__name__)

def initialize_firebase():
    """
    Inicializa la conexión con Firebase utilizando credenciales.
    
    Las credenciales se obtienen de variables de entorno en producción
    o de un archivo local en desarrollo.
    
    Returns:
        firebase_admin.App: La instancia de la aplicación Firebase inicializada.
    
    Raises:
        Exception: Si no se pueden cargar las credenciales.
    """
    try:
        environment = os.environ.get('ENVIRONMENT', 'development')
        logger.info(f"Inicializando Firebase en entorno: {environment}")
        
        # En producción, GAE proporciona las credenciales como variable de entorno
        if environment == 'production':
            # Obtener credenciales desde variable de entorno
            cred_json = os.environ.get('FIREBASE_CREDENTIALS')
            if cred_json:
                logger.debug("Usando credenciales de Firebase desde variable de entorno")
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                # En GCP, se puede usar la autenticación implícita
                logger.debug("Usando autenticación implícita de GCP para Firebase")
                cred = None
        else:
            # En desarrollo, se usa un archivo de credenciales
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', './credentials/firebase-key.json')
            logger.debug(f"Usando credenciales de Firebase desde archivo: {cred_path}")
            cred = credentials.Certificate(cred_path)
        
        # Inicializar la aplicación de Firebase
        firebase_app = initialize_app(cred)
        
        # Opcional: Verificar la conexión con la base de datos
        db = firestore.client()
        
        logger.info("Firebase inicializado correctamente")
        return firebase_app
    
    except Exception as e:
        logger.error(f"Error al inicializar Firebase: {e}", exc_info=True)
        
        raise

def get_firestore_client():
    """
    Obtiene una instancia del cliente de Firestore.
    
    Returns:
        google.cloud.firestore.Client: Cliente de Firestore.
    """
    logger.debug("Obteniendo cliente de Firestore")
    return firestore.client()