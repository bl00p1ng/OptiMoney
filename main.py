"""
Punto de entrada principal de la aplicación de finanzas personales.
Este módulo inicializa la aplicación Flask y configura todas las rutas y servicios.
"""
import os
import time
from flask import Flask, request, g
from flask_cors import CORS
from config.firebase_config import initialize_firebase
from utils.logger import get_logger, app_logger
from utils.repository_patches import apply_repository_patches  # Importar la función de parches
from routes import register_routes

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
    
    app_logger.info("Iniciando la aplicación de finanzas personales")
    
    # Se inicializa la conexión con Firebase
    initialize_firebase()
    
    # Aplicar parches a los repositorios ANTES de cargar cualquier controlador
    apply_repository_patches()
    
    # Configuración desde variables de entorno
    environment = os.environ.get('ENVIRONMENT', 'development')
    app.config['ENV'] = environment
    app.config['DEBUG'] = environment != 'production'
    
    app_logger.info(f"Aplicación configurada en entorno: {environment}")
    
    # Middleware para registro de solicitudes y tiempo de respuesta
    @app.before_request
    def before_request():
        """Registra información antes de cada solicitud."""
        g.start_time = time.time()
        app_logger.info(f"Nueva solicitud: {request.method} {request.path}")
        if request.args:
            app_logger.debug(f"Parámetros de consulta: {dict(request.args)}")
    
    @app.after_request
    def after_request(response):
        """Registra información después de cada solicitud."""
        if hasattr(g, 'start_time'):
            elapsed_time = time.time() - g.start_time
            app_logger.info(f"Solicitud completada: {request.method} {request.path} - Código: {response.status_code} - Tiempo: {elapsed_time:.4f}s")
        return response
    
    # Manejador de errores para excepciones no capturadas
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Registra errores no capturados."""
        app_logger.error(f"Error no capturado: {str(e)}", exc_info=True)
        return {"error": "Error interno del servidor"}, 500
    
    # Registrar todas las rutas de la aplicación
    register_routes(app)
    
    app_logger.info("Aplicación configurada correctamente")
    
    return app

# Se crea la aplicación utilizando la función factory
app = create_app()

if __name__ == '__main__':
    # Esto se ejecutará cuando se corra directamente este archivo
    # pero no cuando se importe como módulo
    port = int(os.environ.get('PORT', 8080))
    app_logger.info(f"Iniciando servidor en http://0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)