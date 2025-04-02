"""
Controlador para verificar el estado y conectividad del sistema.
"""
from typing import Dict, Any
from config.firebase_config import get_firestore_client
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class HealthController:
    """
    Controlador para verificar el estado del sistema y sus conexiones.
    
    Este controlador proporciona métodos para comprobar la conectividad con Firebase
    y otros servicios esenciales para el funcionamiento de la aplicación.
    """
    
    async def check_system_health(self) -> Dict[str, Any]:
        """
        Verifica el estado general del sistema.
        
        Returns:
            Dict[str, Any]: Estado del sistema con detalles de conectividad.
        """
        try:
            logger.info("Realizando verificación de salud del sistema")
            
            # Resultado general
            health_result = {
                "status": "ok",
                "services": {}
            }
            
            # Verificar Firebase/Firestore
            firebase_result = await self.check_firebase_connection()
            health_result["services"]["firebase"] = firebase_result
            
            # Si algún servicio crítico está caído, cambiar el estado general
            if firebase_result["status"] != "ok":
                health_result["status"] = "degraded"
            
            logger.info(f"Verificación de salud completada: {health_result['status']}")
            return health_result
        except Exception as e:
            logger.error(f"Error al verificar salud del sistema: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error en la verificación de salud: {str(e)}",
                "services": {}
            }
    
    async def check_firebase_connection(self) -> Dict[str, Any]:
        """
        Verifica la conexión con Firebase/Firestore.
        
        Returns:
            Dict[str, Any]: Estado de la conexión con Firebase.
        """
        try:
            # Intentar obtener cliente de Firestore
            db = get_firestore_client()
            
            # Realizar una operación simple para verificar conectividad
            collection_ref = db.collection('_health_check')
            current_time = {"timestamp": db.server_timestamp()}
            
            # Añadir documento temporal
            doc_ref = collection_ref.document('connectivity_test')
            doc_ref.set(current_time)
            
            # Leer el documento
            doc = doc_ref.get()
            
            # Eliminar el documento de prueba
            doc_ref.delete()
            
            logger.info("Conexión con Firebase verificada correctamente")
            return {
                "status": "ok",
                "message": "Conexión con Firebase establecida correctamente"
            }
        except Exception as e:
            logger.error(f"Error al verificar conexión con Firebase: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error en la conexión con Firebase: {str(e)}"
            }