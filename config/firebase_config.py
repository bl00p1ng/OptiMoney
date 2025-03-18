"""
Módulo para la configuración y conexión con Firebase.
"""
import os
import json
from firebase_admin import credentials, initialize_app, firestore

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
        # En producción, Google App Engine proporciona las credenciales como variable de entorno
        if os.environ.get('ENVIRONMENT') == 'production':
            # Obtener credenciales desde variable de entorno
            cred_json = os.environ.get('FIREBASE_CREDENTIALS')
            if cred_json:
                cred_dict = json.loads(cred_json)
                cred = credentials.Certificate(cred_dict)
            else:
                # En Google Cloud Platform, se puede usar la autenticación implícita
                cred = None
        else:
            # En desarrollo, se usa un archivo de credenciales
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH', './credentials/firebase-key.json')
            cred = credentials.Certificate(cred_path)
        
        # Inicializar la aplicación de Firebase
        firebase_app = initialize_app(cred)
        
        # Opcional: Verificar la conexión con la base de datos
        db = firestore.client()
        
        print("Firebase inicializado correctamente")
        return firebase_app
    
    except Exception as e:
        print(f"Error al inicializar Firebase: {e}")
        # En un entorno real, quizás queramos reintentarlo o lanzar la excepción
        # dependiendo del contexto
        raise

def get_firestore_client():
    """
    Obtiene una instancia del cliente de Firestore.
    
    Returns:
        google.cloud.firestore.Client: Cliente de Firestore.
    """
    return firestore.client()