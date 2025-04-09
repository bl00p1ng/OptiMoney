"""
Controlador para gestionar las operaciones relacionadas con recomendaciones financieras.
"""
from typing import Dict, Any, Optional
from models.repositories.recommendation_repository import RecommendationRepository
from services.recommendation_service import RecommendationService
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class RecommendationController:
    """
    Controlador para operaciones relacionadas con recomendaciones financieras.
    
    Este controlador maneja la lógica de negocio para generar, consultar
    y gestionar recomendaciones personalizadas para los usuarios.
    """
    
    def __init__(self):
        """
        Inicializa el controlador de recomendaciones.
        
        Instancia los servicios y repositorios necesarios para 
        la gestión de recomendaciones.
        """
        self.recommendation_service = RecommendationService()
        self.recommendation_repo = RecommendationRepository()
        logger.debug("Controlador de recomendaciones inicializado")
    
    async def generate_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Genera recomendaciones para un usuario específico.
        
        Args:
            user_id: ID del usuario para generar recomendaciones.
            
        Returns:
            Dict[str, Any]: Resultado del proceso de generación de recomendaciones.
        """
        try:
            # Llamar al servicio para generar recomendaciones
            result = await self.recommendation_service.generate_recommendations(user_id)
            
            logger.info(f"Generadas {result.get('recommendations_generated', 0)} recomendaciones para usuario {user_id}")
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al generar recomendaciones: {str(e)}"
            }
    
    async def get_user_recommendations(
        self, 
        user_id: str, 
        limit: Optional[int] = 5
    ) -> Dict[str, Any]:
        """
        Obtiene las recomendaciones activas para un usuario.
        
        Args:
            user_id: ID del usuario.
            limit: Número máximo de recomendaciones a obtener.
            
        Returns:
            Dict[str, Any]: Lista de recomendaciones.
        """
        try:
            # Obtener recomendaciones del servicio
            recommendations = await self.recommendation_service.get_recommendations_for_user(
                user_id, 
                limit
            )
            
            # Convertir recomendaciones a formato para respuesta
            recommendations_list = []
            for recommendation in recommendations:
                rec_dict = recommendation.to_dict()
                
                # Convertir fechas a formato ISO para JSON
                for date_field in ['created_at', 'expires_at', 'last_shown_at']:
                    if rec_dict.get(date_field):
                        rec_dict[date_field] = rec_dict[date_field].isoformat()
                
                recommendations_list.append(rec_dict)
            
            logger.debug(f"Obtenidas {len(recommendations_list)} recomendaciones para usuario {user_id}")
            return {
                "success": True,
                "recommendations": recommendations_list
            }
        except Exception as e:
            logger.error(f"Error al obtener recomendaciones: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener recomendaciones: {str(e)}"
            }
    
    async def mark_recommendation_shown(
        self, 
        recommendation_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Marca una recomendación como mostrada al usuario.
        
        Args:
            recommendation_id: ID de la recomendación.
            user_id: ID del usuario para verificación de propiedad.
            
        Returns:
            Dict[str, Any]: Resultado de la operación.
        """
        try:
            # Verificar que la recomendación pertenece al usuario
            recommendations = await self.recommendation_repo.query({
                "id": recommendation_id,
                "user_id": user_id
            }, limit=1)
            
            if not recommendations:
                return {
                    "success": False,
                    "error": "Recomendación no encontrada o no pertenece al usuario"
                }
            
            # Marcar como mostrada
            result = await self.recommendation_service.mark_recommendation_shown(
                recommendation_id
            )
            
            if result:
                logger.info(f"Recomendación {recommendation_id} marcada como mostrada")
                return {
                    "success": True,
                    "message": "Recomendación marcada como mostrada"
                }
            else:
                logger.warning(f"No se pudo marcar como mostrada la recomendación {recommendation_id}")
                return {
                    "success": False,
                    "error": "No se pudo marcar la recomendación como mostrada"
                }
        except Exception as e:
            logger.error(f"Error al marcar recomendación como mostrada: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al marcar recomendación como mostrada: {str(e)}"
            }
    
    async def update_recommendation_interaction(
        self, 
        recommendation_id: str, 
        user_id: str, 
        interaction_type: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Actualiza la interacción del usuario con una recomendación.
        
        Args:
            recommendation_id: ID de la recomendación.
            user_id: ID del usuario para verificación de propiedad.
            interaction_type: Tipo de interacción (dismiss, action_taken, etc.).
            details: Detalles adicionales de la interacción.
            
        Returns:
            Dict[str, Any]: Resultado de la operación.
        """
        try:
            # Verificar que la recomendación pertenece al usuario
            recommendations = await self.recommendation_repo.query({
                "id": recommendation_id,
                "user_id": user_id
            }, limit=1)
            
            if not recommendations:
                return {
                    "success": False,
                    "error": "Recomendación no encontrada o no pertenece al usuario"
                }
            
            # Actualizar interacción
            result = await self.recommendation_service.update_recommendation_interaction(
                recommendation_id, 
                interaction_type, 
                details
            )
            
            if result:
                logger.info(
                    f"Interacción {interaction_type} registrada para recomendación {recommendation_id}"
                )
                return {
                    "success": True,
                    "message": "Interacción registrada exitosamente"
                }
            else:
                logger.warning(
                    f"No se pudo registrar interacción {interaction_type} para recomendación {recommendation_id}"
                )
                return {
                    "success": False,
                    "error": "No se pudo registrar la interacción"
                }
        except Exception as e:
            logger.error(f"Error al registrar interacción de recomendación: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al registrar interacción: {str(e)}"
            }