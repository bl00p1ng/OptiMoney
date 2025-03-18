"""
Punto de entrada principal de la aplicación de finanzas personales.
Este módulo inicializa la aplicación Flask y configura todas las rutas y servicios.
"""
import os
from flask import Flask
from flask_cors import CORS
from config.firebase_config import initialize_firebase


def create_app():
    """
    Crea y configura una instancia de la aplicación Flask.
    
    Returns:
        Flask: La aplicación configurada lista para ejecutarse.
    """
    # Se inicializa la aplicación Flask
    app = Flask(__name__)
    
    # Se configura CORS para permitir peticiones desde el frontend
    CORS(app)
    
    # Se inicializa la conexión con Firebase
    initialize_firebase()
    
    # Configuración desde variables de entorno
    app.config['ENV'] = os.environ.get('ENVIRONMENT', 'development')
    app.config['DEBUG'] = os.environ.get('ENVIRONMENT', 'development') != 'production'
    
    # Ruta para verificar que la aplicación está funcionando
    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint básico para verificar que la aplicación está funcionando."""
        return {'status': 'ok', 'environment': app.config['ENV']}
    
    return app

# Se crea la aplicación utilizando la función factory
app = create_app()

if __name__ == '__main__':
    # Esto se ejecutará cuando se corra directamente este archivo
    # pero no cuando se importe como módulo
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)