"""
Módulo que proporciona servicios para la generación y gestión de recomendaciones financieras.

Este servicio convierte los patrones detectados en recomendaciones accionables
para los usuarios, personalizando los mensajes según el contexto.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
from models.pattern_model import Pattern
from models.recommendation_model import Recommendation
from models.repositories.pattern_repository import PatternRepository
from models.repositories.recommendation_repository import RecommendationRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class RecommendationService:
    """
    Servicio para generar y gestionar recomendaciones personalizadas.
    
    Este servicio transforma los patrones detectados por el servicio de análisis
    en recomendaciones accionables con mensajes personalizados para el usuario.
    """
    
    def __init__(self):
        """Inicializa el servicio de recomendaciones."""
        self.pattern_repository = PatternRepository()
        self.recommendation_repository = RecommendationRepository()
        logger.info("Servicio de recomendaciones inicializado")
    
    async def generate_recommendations(self, user_id: str) -> Dict[str, Any]:
        """
        Genera recomendaciones basadas en los patrones activos de un usuario.
        
        Args:
            user_id: ID del usuario para el que se generan recomendaciones.
            
        Returns:
            Dict[str, Any]: Resultado del proceso de generación.
        """
        try:
            logger.info(f"Generando recomendaciones para usuario {user_id}")
            
            # Primero, expirar recomendaciones antiguas
            expired_count = await self.recommendation_repository.expire_old_recommendations(user_id)
            if expired_count > 0:
                logger.debug(f"Expiradas {expired_count} recomendaciones antiguas")
            
            # Obtener patrones activos ordenados por potencial de ahorro
            patterns = await self.pattern_repository.get_patterns_by_savings_potential(user_id)
            
            if not patterns:
                logger.warning(f"No hay patrones activos para generar recomendaciones (usuario: {user_id})")
                return {"status": "no_patterns", "recommendations_generated": 0}
            
            # Generar recomendaciones para cada patrón
            recommendations_generated = 0
            for pattern in patterns:
                # Verificar si ya existe una recomendación activa para este patrón
                existing_recommendations = await self.recommendation_repository.query({
                    "user_id": user_id, 
                    "pattern_id": pattern.id,
                    "status": "pending"
                })
                
                if existing_recommendations:
                    logger.debug(f"Ya existe una recomendación activa para el patrón {pattern.id}")
                    continue
                    
                # Generar nueva recomendación
                recommendation = await self._create_recommendation_from_pattern(pattern)
                
                if recommendation:
                    recommendations_generated += 1
                    logger.debug(
                        f"Nueva recomendación generada: {recommendation.id} "
                        f"para patrón {pattern.id}"
                    )
            
            result = {
                "status": "success",
                "patterns_analyzed": len(patterns),
                "recommendations_generated": recommendations_generated
            }
            
            logger.info(
                f"Generación de recomendaciones completada para usuario {user_id}. "
                f"Generadas: {recommendations_generated}"
            )

            logger.debug(f"Resultado de generación: {result}")
            logger.info(f"Recomendaciones generadas: {recommendations_generated}")
            
            return result
        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {str(e)}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def _create_recommendation_from_pattern(self, pattern: Pattern) -> Optional[Recommendation]:
        """
        Crea una recomendación personalizada a partir de un patrón.
        
        Args:
            pattern: Patrón a partir del cual se genera la recomendación.
            
        Returns:
            Optional[Recommendation]: Recomendación generada o None si falla.
        """
        try:
            # Determinar el tipo de recomendación según el tipo de patrón
            if pattern.type == "micro_expense":
                return await self._create_micro_expense_recommendation(pattern)
            elif pattern.type == "temporal":
                return await self._create_temporal_recommendation(pattern)
            elif pattern.type == "recurring":
                return await self._create_recurring_expense_recommendation(pattern)
            elif pattern.type == "category_deviation":
                return await self._create_deviation_recommendation(pattern)
            else:
                logger.warning(f"Tipo de patrón no soportado para recomendación: {pattern.type}")
                return None
        except Exception as e:
            logger.error(f"Error al crear recomendación desde patrón: {str(e)}", exc_info=True)
            return None
    
    async def _create_micro_expense_recommendation(self, pattern: Pattern) -> Optional[Recommendation]:
        """
        Crea una recomendación para un patrón de micro-gastos.
        
        Args:
            pattern: Patrón de micro-gastos.
            
        Returns:
            Optional[Recommendation]: Recomendación generada o None si falla.
        """
        try:
            # Obtener datos relevantes del patrón
            category = pattern.category
            total_amount = pattern.metrics.get("totalAmount", 0)
            avg_amount = pattern.metrics.get("averageAmount", 0)
            transactions_count = len(pattern.related_transactions)
            monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
            yearly_savings = pattern.savings_potential.get("estimatedYearly", 0)
            
            # Crear contenido personalizado
            title = f"Pequeños gastos en {category} suman {total_amount:,.0f}"
            
            message = (
                f"Has realizado {transactions_count} pequeños gastos en {category} "
                f"por un total de {total_amount:,.0f}. Aunque cada uno promedia solo "
                f"{avg_amount:,.0f}, en conjunto representan una suma importante.\n\n"
                f"Si reduces estos micro-gastos a la mitad, podrías ahorrar "
                f"aproximadamente {monthly_savings:,.0f} al mes, o {yearly_savings:,.0f} al año."
            )
            
            action_type = "reduce"
            action_description = (
                f"Intenta consolidar tus compras de {category} para reducir la frecuencia "
                f"y aprovechar mejores precios por volumen."
            )
            
            # Crear la recomendación
            recommendation = Recommendation(
                user_id=pattern.user_id,
                pattern_id=pattern.id,
                created_at=datetime.now(),
                priority=self._calculate_priority(pattern),
                content={
                    "title": title,
                    "message": message,
                    "savingsEstimate": monthly_savings,
                    "timeframe": "monthly",
                    "actionType": action_type,
                    "actionDescription": action_description
                },
                context={
                    "relevantCategories": [category],
                    "relevantAmounts": {
                        "total": total_amount,
                        "average": avg_amount,
                        "max": max([t.get("amount", 0) for t in pattern.related_transactions], default=0)
                    },
                    "temporalInfo": {
                        "transactionsCount": transactions_count,
                        "periodDays": 90  # Asumimos análisis de 90 días
                    }
                }
            )
            
            # Persistir la recomendación
            await self.recommendation_repository.add(recommendation)
            
            logger.debug(f"Recomendación de micro-gastos creada: {recommendation.id}")
            return recommendation
        except Exception as e:
            logger.error(f"Error al crear recomendación de micro-gastos: {str(e)}", exc_info=True)
            return None
    
    async def _create_temporal_recommendation(self, pattern: Pattern) -> Optional[Recommendation]:
        """
        Crea una recomendación para un patrón temporal.
        
        Args:
            pattern: Patrón temporal.
            
        Returns:
            Optional[Recommendation]: Recomendación generada o None si falla.
        """
        try:
            # Obtener datos relevantes del patrón
            time_unit = pattern.temporal_data.get("timeUnit", "")
            time_value = pattern.temporal_data.get("timeValue", "")
            day_name = pattern.temporal_data.get("dayName", "")
            avg_expense = pattern.temporal_data.get("averageExpense", 0)
            overall_avg = pattern.temporal_data.get("overallAverage", 0)
            
            monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
            yearly_savings = pattern.savings_potential.get("estimatedYearly", 0)
            
            # Crear contenido personalizado según el tipo de patrón temporal
            if time_unit == "day_of_week":
                title = f"Gastas más los días {day_name}"
                
                message = (
                    f"Hemos detectado que tus gastos son significativamente mayores los días {day_name}. "
                    f"En promedio, gastas {avg_expense:,.0f} estos días, comparado con "
                    f"{overall_avg:,.0f} en otros días de la semana.\n\n"
                    f"Si equilibras tus gastos durante la semana, podrías ahorrar "
                    f"aproximadamente {monthly_savings:,.0f} al mes."
                )
                
                action_type = "redistribute"
                action_description = (
                    f"Planifica tus actividades para distribuir mejor tus gastos durante la semana "
                    f"y evitar concentrarlos los {day_name}."
                )
            elif time_unit == "time_of_day":
                period_names = {
                    "morning": "las mañanas",
                    "afternoon": "las tardes",
                    "evening": "las noches",
                    "night": "las madrugadas"
                }
                period = period_names.get(time_value, time_value)
                
                title = f"Tus gastos aumentan durante {period}"
                
                message = (
                    f"Hemos detectado que tus gastos son significativamente mayores durante {period}. "
                    f"En promedio, gastas {avg_expense:,.0f} en estos horarios, comparado con "
                    f"{overall_avg:,.0f} en otros momentos del día.\n\n"
                    f"Si equilibras tus gastos durante el día, podrías ahorrar "
                    f"aproximadamente {monthly_savings:,.0f} al mes."
                )
                
                action_type = "redistribute"
                action_description = (
                    f"Planifica tus actividades para distribuir mejor tus gastos durante el día "
                    f"y evitar concentrarlos durante {period}."
                )
            else:
                title = "Patrón temporal detectado"
                message = (
                    f"Hemos detectado un patrón temporal en tus gastos que podría optimizarse. "
                    f"Si equilibras mejor tus gastos, podrías ahorrar aproximadamente "
                    f"{monthly_savings:,.0f} al mes."
                )
                action_type = "redistribute"
                action_description = "Planifica tus actividades para distribuir mejor tus gastos."
            
            # Crear la recomendación
            recommendation = Recommendation(
                user_id=pattern.user_id,
                pattern_id=pattern.id,
                created_at=datetime.now(),
                priority=self._calculate_priority(pattern),
                content={
                    "title": title,
                    "message": message,
                    "savingsEstimate": monthly_savings,
                    "timeframe": "monthly",
                    "actionType": action_type,
                    "actionDescription": action_description
                },
                context={
                    "relevantCategories": ["multiple"],
                    "relevantAmounts": {
                        "total": pattern.metrics.get("totalAmount", 0),
                        "average": avg_expense,
                        "overall_average": overall_avg
                    },
                    "temporalInfo": pattern.temporal_data
                }
            )
            
            # Persistir la recomendación
            await self.recommendation_repository.add(recommendation)
            
            logger.debug(f"Recomendación temporal creada: {recommendation.id}")
            return recommendation
        except Exception as e:
            logger.error(f"Error al crear recomendación temporal: {str(e)}", exc_info=True)
            return None
    
    async def _create_recurring_expense_recommendation(self, pattern: Pattern) -> Optional[Recommendation]:
        """
        Crea una recomendación para un patrón de gasto recurrente.
        
        Args:
            pattern: Patrón de gasto recurrente.
            
        Returns:
            Optional[Recommendation]: Recomendación generada o None si falla.
        """
        try:
            # Obtener datos relevantes del patrón
            category = pattern.category
            avg_amount = pattern.metrics.get("averageAmount", 0)
            frequency = pattern.temporal_data.get("frequency", "")
            monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
            yearly_savings = pattern.savings_potential.get("estimatedYearly", 0)
            
            # Crear contenido personalizado
            title = f"Optimiza tu gasto recurrente en {category}"
            
            message = (
                f"Has estado pagando regularmente {avg_amount:,.0f} en {category} "
                f"con frecuencia {frequency}.\n\n"
                f"Revisando opciones alternativas o negociando mejores términos, "
                f"podrías ahorrar aproximadamente {monthly_savings:,.0f} al mes, "
                f"o {yearly_savings:,.0f} al año."
            )
            
            action_type = "optimize"
            action_description = (
                f"Investiga proveedores alternativos para {category} o considera "
                f"negociar mejores condiciones con tu proveedor actual."
            )
            
            # Crear la recomendación
            recommendation = Recommendation(
                user_id=pattern.user_id,
                pattern_id=pattern.id,
                created_at=datetime.now(),
                priority=self._calculate_priority(pattern),
                content={
                    "title": title,
                    "message": message,
                    "savingsEstimate": monthly_savings,
                    "timeframe": "monthly",
                    "actionType": action_type,
                    "actionDescription": action_description
                },
                context={
                    "relevantCategories": [category],
                    "relevantAmounts": {
                        "total": pattern.metrics.get("totalAmount", 0),
                        "average": avg_amount,
                        "max": max([t.get("amount", 0) for t in pattern.related_transactions], default=0)
                    },
                    "temporalInfo": pattern.temporal_data
                }
            )
            
            # Persistir la recomendación
            await self.recommendation_repository.add(recommendation)
            
            logger.debug(f"Recomendación de gasto recurrente creada: {recommendation.id}")
            return recommendation
        except Exception as e:
            logger.error(f"Error al crear recomendación de gasto recurrente: {str(e)}", exc_info=True)
            return None
    
    async def _create_deviation_recommendation(self, pattern: Pattern) -> Optional[Recommendation]:
        """
        Crea una recomendación para un patrón de desviación por categoría.
        
        Args:
            pattern: Patrón de desviación.
            
        Returns:
            Optional[Recommendation]: Recomendación generada o None si falla.
        """
        try:
            # Obtener datos relevantes del patrón
            category = pattern.category
            month = pattern.temporal_data.get("month", "")
            current_total = pattern.temporal_data.get("currentTotal", 0)
            std_avg = pattern.temporal_data.get("standardAverage", 0)
            deviation = pattern.metrics.get("deviation", 0)
            monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
            
            # Crear contenido personalizado
            title = f"Aumento significativo en gastos de {category}"
            
            message = (
                f"Tus gastos en {category} durante {month} aumentaron un {deviation:.1f}% "
                f"respecto a tu promedio habitual. Gastaste {current_total:,.0f} cuando "
                f"normalmente gastas alrededor de {std_avg:,.0f}.\n\n"
                f"Si vuelves a tu patrón normal de gastos, podrías ahorrar "
                f"aproximadamente {monthly_savings:,.0f} el próximo mes."
            )
            
            action_type = "reduce"
            action_description = (
                f"Revisa tus gastos recientes en {category} para identificar "
                f"qué causó este aumento y cómo puedes volver a tu nivel habitual."
            )
            
            # Crear la recomendación
            recommendation = Recommendation(
                user_id=pattern.user_id,
                pattern_id=pattern.id,
                created_at=datetime.now(),
                priority=self._calculate_priority(pattern),
                content={
                    "title": title,
                    "message": message,
                    "savingsEstimate": monthly_savings,
                    "timeframe": "monthly",
                    "actionType": action_type,
                    "actionDescription": action_description
                },
                context={
                    "relevantCategories": [category],
                    "relevantAmounts": {
                        "total": current_total,
                        "average": std_avg,
                        "deviation_percentage": deviation
                    },
                    "temporalInfo": {
                        "month": month
                    }
                }
            )
            
            # Persistir la recomendación
            await self.recommendation_repository.add(recommendation)
            
            logger.debug(f"Recomendación de desviación creada: {recommendation.id}")
            return recommendation
        except Exception as e:
            logger.error(f"Error al crear recomendación de desviación: {str(e)}", exc_info=True)
            return None
    
    def _calculate_priority(self, pattern: Pattern) -> int:
        """
        Calcula la prioridad de una recomendación basada en el patrón.
        
        Args:
            pattern: Patrón a evaluar.
            
        Returns:
            int: Nivel de prioridad (1-10, donde 10 es máxima prioridad).
        """
        # Base inicial
        priority = 5
        
        # Ajustar según el potencial de ahorro
        monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
        if monthly_savings > 50000:  # Ahorro significativo
            priority += 3
        elif monthly_savings > 20000:
            priority += 2
        elif monthly_savings > 5000:
            priority += 1
        
        # Ajustar según la confianza del patrón
        confidence = pattern.metrics.get("confidence", 0)
        if confidence > 0.9:
            priority += 1
        elif confidence < 0.6:
            priority -= 1
        
        # Ajustar según el tipo de patrón
        if pattern.type == "category_deviation":
            # Las desviaciones suelen ser más urgentes
            priority += 1
        elif pattern.type == "recurring":
            # Los gastos recurrentes son buenas oportunidades
            priority += 1
        
        # Asegurar que esté en el rango 1-10
        return max(1, min(10, priority))
    
    async def get_recommendations_for_user(self, user_id: str, limit: int = 5) -> List[Recommendation]:
        """
        Obtiene las recomendaciones activas para un usuario.
        
        Args:
            user_id: ID del usuario.
            limit: Número máximo de recomendaciones a retornar.
            
        Returns:
            List[Recommendation]: Lista de recomendaciones ordenadas por prioridad.
        """
        try:
            logger.debug(f"Obteniendo recomendaciones para usuario {user_id}")
            
            # Primero, expirar recomendaciones antiguas
            await self.recommendation_repository.expire_old_recommendations(user_id)
            
            # Luego, obtener las recomendaciones pendientes
            recommendations = await self.recommendation_repository.get_pending_recommendations(user_id, limit)
            
            logger.debug(f"Obtenidas {len(recommendations)} recomendaciones para usuario {user_id}")
            return recommendations
        except Exception as e:
            logger.error(f"Error al obtener recomendaciones: {str(e)}", exc_info=True)
            return []
    
    async def mark_recommendation_shown(self, recommendation_id: str) -> bool:
        """
        Marca una recomendación como mostrada al usuario.
        
        Args:
            recommendation_id: ID de la recomendación mostrada.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            result = await self.recommendation_repository.mark_as_shown(recommendation_id)
            
            if result:
                logger.debug(f"Recomendación {recommendation_id} marcada como mostrada")
            else:
                logger.warning(f"No se pudo marcar como mostrada la recomendación {recommendation_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al marcar recomendación como mostrada: {str(e)}", exc_info=True)
            return False
    
    async def update_recommendation_interaction(
        self, 
        recommendation_id: str, 
        interaction_type: str, 
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Actualiza la interacción del usuario con una recomendación.
        
        Args:
            recommendation_id: ID de la recomendación.
            interaction_type: Tipo de interacción (dismiss, action_taken, save_for_later, etc.).
            details: Detalles adicionales de la interacción (opcional).
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Obtener la recomendación
            recommendations = await self.recommendation_repository.query({"id": recommendation_id}, limit=1)
            if not recommendations:
                logger.warning(f"Recomendación no encontrada: {recommendation_id}")
                return False
                
            recommendation = recommendations[0]
            
            # Preparar datos de interacción
            interaction_data = {}
            
            if interaction_type == "dismiss":
                interaction_data["dismissed"] = True
                if details and "reason" in details:
                    interaction_data["dismissReason"] = details["reason"]
                    
            elif interaction_type == "action_taken":
                interaction_data["actionTaken"] = True
                
            elif interaction_type == "save_for_later":
                interaction_data["savedForLater"] = True
                
            elif interaction_type == "feedback":
                if not details:
                    logger.warning("Feedback sin detalles")
                    return False
                    
                # Crear un diccionario anidado para feedback
                interaction_data["feedback"] = {}
                
                if "is_helpful" in details:
                    interaction_data["feedback"]["isHelpful"] = details["is_helpful"]
                if "rating" in details:
                    interaction_data["feedback"]["rating"] = details["rating"]
                if "comment" in details:
                    interaction_data["feedback"]["comment"] = details["comment"]
            
            # Actualizar la interacción
            result = await self.recommendation_repository.update_user_interaction(
                recommendation_id, interaction_data
            )
            
            if result:
                logger.info(
                    f"Interacción {interaction_type} registrada para recomendación {recommendation_id}"
                )
                
                # Si se toma acción, actualizar también el patrón relacionado
                if interaction_type == "action_taken":
                    await self.pattern_repository.update_status(recommendation.pattern_id, "resolved")
                    logger.debug(f"Patrón {recommendation.pattern_id} marcado como resuelto")
                
                # Si se descarta, podríamos marcar el patrón como ignorado
                if interaction_type == "dismiss":
                    # Solo si la razón implica que el usuario no está interesado
                    dismiss_reason = details.get("reason", "") if details else ""
                    if dismiss_reason in ["not_relevant", "not_interested"]:
                        await self.pattern_repository.update_status(recommendation.pattern_id, "ignored")
                        logger.debug(f"Patrón {recommendation.pattern_id} marcado como ignorado")
            else:
                logger.warning(
                    f"No se pudo actualizar interacción {interaction_type} para recomendación {recommendation_id}"
                )
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar interacción de recomendación: {str(e)}", exc_info=True)
            return False

# Instancia global del servicio
recommendation_service = RecommendationService()