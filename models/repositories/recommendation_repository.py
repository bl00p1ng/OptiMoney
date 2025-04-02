"""
Módulo que contiene el repositorio para operaciones con recomendaciones.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.recommendation_model import Recommendation
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class RecommendationRepository(BaseRepository[Recommendation]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con recomendaciones.
    
    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Recomendación.
    """
    
    def __init__(self):
        """Inicializa un nuevo repositorio de recomendaciones."""
        super().__init__("recommendations", Recommendation)
        logger.debug("Repositorio de recomendaciones inicializado")
    
    async def get_pending_recommendations(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """
        Obtiene las recomendaciones pendientes para un usuario.
        
        Args:
            user_id: ID del usuario.
            limit: Número máximo de recomendaciones a retornar.
            
        Returns:
            List[Recommendation]: Lista de recomendaciones pendientes.
        """
        try:
            # Obtener todas las recomendaciones del usuario
            all_recommendations = await self.query({"user_id": user_id})
            
            # Filtrar las que deberían mostrarse
            now = datetime.now()
            pending_recommendations = [
                r for r in all_recommendations 
                if r.should_show() and r.expires_at > now
            ]
            
            # Ordenar por prioridad (de mayor a menor)
            sorted_recommendations = sorted(
                pending_recommendations, 
                key=lambda r: r.priority,
                reverse=True
            )
            
            # Limitar la cantidad
            limited_recommendations = sorted_recommendations[:limit]
            
            logger.debug(f"Obtenidas {len(limited_recommendations)} recomendaciones pendientes para usuario {user_id}")
            return limited_recommendations
        except Exception as e:
            logger.error(f"Error al obtener recomendaciones pendientes: {str(e)}", exc_info=True)
            return []
    
    async def mark_as_shown(self, recommendation_id: str) -> bool:
        """
        Marca una recomendación como mostrada al usuario.
        
        Args:
            recommendation_id: ID de la recomendación.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Obtener la recomendación actual
            recommendation = await self.get_by_id(recommendation_id)
            if not recommendation:
                logger.warning(f"Intento de marcar como mostrada una recomendación inexistente: {recommendation_id}")
                return False
            
            # Actualizar datos
            now = datetime.now()
            update_data = {
                "last_shown_at": now,
                "show_count": recommendation.show_count + 1,
                "user_interaction.seen": True,
                "updated_at": now
            }
            
            # Si el estado es "pending", cambiarlo a "shown"
            if recommendation.status == "pending":
                update_data["status"] = "shown"
            
            result = await self.update(recommendation_id, update_data)
            
            if result:
                logger.debug(f"Recomendación {recommendation_id} marcada como mostrada")
            else:
                logger.warning(f"No se pudo marcar como mostrada la recomendación {recommendation_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al marcar recomendación como mostrada: {str(e)}", exc_info=True)
            return False
    
    async def update_user_interaction(self, recommendation_id: str, interaction_data: Dict[str, Any]) -> bool:
        """
        Actualiza la interacción del usuario con una recomendación.
        
        Args:
            recommendation_id: ID de la recomendación.
            interaction_data: Datos de interacción a actualizar.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Crear un diccionario para la actualización
            update_data = {}
            for key, value in interaction_data.items():
                update_data[f"user_interaction.{key}"] = value
            
            update_data["updated_at"] = datetime.now()
            
            # Si se está marcando como descartada o actuada, actualizar el estado
            if interaction_data.get("dismissed") is True:
                update_data["status"] = "dismissed"
            elif interaction_data.get("actionTaken") is True:
                update_data["status"] = "acted_upon"
            
            result = await self.update(recommendation_id, update_data)
            
            if result:
                logger.debug(f"Interacción actualizada para recomendación {recommendation_id}")
            else:
                logger.warning(f"No se pudo actualizar interacción para recomendación {recommendation_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar interacción de recomendación: {str(e)}", exc_info=True)
            return False
    
    async def add_feedback(
        self, 
        recommendation_id: str, 
        is_helpful: bool, 
        rating: Optional[int] = None, 
        comment: Optional[str] = None
    ) -> bool:
        """
        Añade feedback del usuario a una recomendación.
        
        Args:
            recommendation_id: ID de la recomendación.
            is_helpful: Si el usuario encontró útil la recomendación.
            rating: Valoración opcional (1-5 estrellas).
            comment: Comentario opcional del usuario.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            feedback_data = {
                "user_interaction.feedback.isHelpful": is_helpful,
                "updated_at": datetime.now()
            }
            
            if rating is not None:
                feedback_data["user_interaction.feedback.rating"] = rating
                
            if comment is not None:
                feedback_data["user_interaction.feedback.comment"] = comment
            
            result = await self.update(recommendation_id, feedback_data)
            
            if result:
                logger.info(f"Feedback añadido a recomendación {recommendation_id}: {is_helpful}")
            else:
                logger.warning(f"No se pudo añadir feedback a recomendación {recommendation_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al añadir feedback a recomendación: {str(e)}", exc_info=True)
            return False
    
    async def expire_old_recommendations(self, user_id: str) -> int:
        """
        Marca como expiradas las recomendaciones antiguas de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            int: Número de recomendaciones marcadas como expiradas.
        """
        try:
            # Obtener todas las recomendaciones del usuario
            all_recommendations = await self.query({"user_id": user_id})
            
            # Filtrar las que están expiradas pero no marcadas como tal
            now = datetime.now()
            expired_recommendations = [
                r for r in all_recommendations 
                if r.expires_at < now and r.status != "expired"
            ]
            
            # Marcar cada una como expirada
            expired_count = 0
            for recommendation in expired_recommendations:
                result = await self.update(recommendation.id, {
                    "status": "expired",
                    "updated_at": now
                })
                
                if result:
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Marcadas {expired_count} recomendaciones como expiradas para usuario {user_id}")
                
            return expired_count
        except Exception as e:
            logger.error(f"Error al expirar recomendaciones antiguas: {str(e)}", exc_info=True)
            return 0