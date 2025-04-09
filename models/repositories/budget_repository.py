"""
Módulo que contiene el repositorio para operaciones con presupuestos.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.budget_model import Budget
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class BudgetRepository(BaseRepository[Budget]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con presupuestos.
    
    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Presupuesto.
    """
    
    def _init_(self):
        """Inicializa un nuevo repositorio de presupuestos."""
        super()._init_("budgets", Budget)
        logger.debug("Repositorio de presupuestos inicializado")
    
    async def get_by_user_id(self, user_id: str) -> List[Budget]:
        """
        Obtiene todos los presupuestos de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Budget]: Lista de presupuestos del usuario.
        """
        try:
            return await self.query({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error al obtener presupuestos para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_by_category(self, user_id: str, category_id: str) -> Optional[Budget]:
        """
        Obtiene el presupuesto de un usuario para una categoría específica.
        
        Args:
            user_id: ID del usuario.
            category_id: ID de la categoría.
            
        Returns:
            Optional[Budget]: Presupuesto encontrado o None si no existe.
        """
        try:
            budgets = await self.query({"user_id": user_id, "category_id": category_id})
            
            if budgets and len(budgets) > 0:
                return budgets[0]
            else:
                return None
        except Exception as e:
            logger.error(
                f"Error al obtener presupuesto para categoría {category_id} de usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return None
    
    async def get_active_budgets(self, user_id: str) -> List[Budget]:
        """
        Obtiene los presupuestos activos (no vencidos) de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Budget]: Lista de presupuestos activos.
        """
        try:
            # Obtener todos los presupuestos del usuario
            budgets = await self.get_by_user_id(user_id)
            
            # Verificar cuáles están en período activo
            now = datetime.now()
            active_budgets = []
            
            for budget in budgets:
                if not budget.is_period_ended(now):
                    active_budgets.append(budget)
                else:
                    # Si el período terminó, actualizarlo para el nuevo período
                    await self.update_for_new_period(budget.id)
                    # Obtener la versión actualizada
                    updated_budget = await self.get_by_id(budget.id)
                    if updated_budget:
                        active_budgets.append(updated_budget)
            
            logger.debug(f"Obtenidos {len(active_budgets)} presupuestos activos para usuario {user_id}")
            return active_budgets
        except Exception as e:
            logger.error(f"Error al obtener presupuestos activos: {str(e)}", exc_info=True)
            return []
    
    async def update_current_amount(self, budget_id: str, amount: float, increment: bool = True) -> bool:
        """
        Actualiza el monto actual de un presupuesto.
        
        Args:
            budget_id: ID del presupuesto.
            amount: Monto a actualizar.
            increment: Si True, suma el monto; si False, lo resta.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Obtener el presupuesto actual
            budget = await self.get_by_id(budget_id)
            if not budget:
                logger.warning(f"Presupuesto {budget_id} no encontrado")
                return False
            
            # Calcular el nuevo monto
            if increment:
                new_amount = budget.current_amount + amount
            else:
                new_amount = budget.current_amount - amount
                # Evitar montos negativos
                if new_amount < 0:
                    new_amount = 0
            
            # Actualizar el presupuesto
            update_data = {
                "current_amount": new_amount,
                "last_updated": datetime.now()
            }
            
            # Si se superó el umbral y no se había enviado alerta, marcar para enviar
            if budget.should_alert() and not budget.alert_sent:
                update_data["alert_sent"] = True
            
            result = await self.update(budget_id, update_data)
            
            if result:
                logger.debug(f"Monto actual actualizado para presupuesto {budget_id}: {new_amount}")
            else:
                logger.warning(f"No se pudo actualizar monto actual para presupuesto {budget_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar monto actual: {str(e)}", exc_info=True)
            return False
    
    async def update_for_new_period(self, budget_id: str) -> bool:
        """
        Actualiza un presupuesto para un nuevo período.
        
        Args:
            budget_id: ID del presupuesto.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Obtener el presupuesto actual
            budget = await self.get_by_id(budget_id)
            if not budget:
                logger.warning(f"Presupuesto {budget_id} no encontrado")
                return False
            
            # Verificar si realmente ha terminado el período
            if not budget.is_period_ended():
                logger.debug(f"El período del presupuesto {budget_id} no ha terminado aún")
                return True  # No es un error, simplemente no es necesario actualizar
            
            # Datos para el nuevo período
            now = datetime.now()
            update_data = {
                "current_amount": 0.0,
                "alert_sent": False,
                "last_updated": now,
                "start_date": now
            }
            
            result = await self.update(budget_id, update_data)
            
            if result:
                logger.info(f"Presupuesto {budget_id} actualizado para nuevo período")
            else:
                logger.warning(f"No se pudo actualizar presupuesto {budget_id} para nuevo período")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar presupuesto para nuevo período: {str(e)}", exc_info=True)
            return False
    
    async def get_budgets_requiring_alerts(self, user_id: str) -> List[Budget]:
        """
        Obtiene los presupuestos que requieren alertas.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Budget]: Lista de presupuestos que requieren alertas.
        """
        try:
            # Obtener presupuestos activos
            active_budgets = await self.get_active_budgets(user_id)
            
            # Filtrar los que requieren alerta
            budgets_to_alert = []
            for budget in active_budgets:
                if budget.should_alert():
                    budgets_to_alert.append(budget)
                    
                    # Marcar la alerta como enviada
                    await self.update(budget.id, {"alert_sent": True})
            
            logger.debug(f"Encontrados {len(budgets_to_alert)} presupuestos que requieren alertas")
            return budgets_to_alert
        except Exception as e:
            logger.error(f"Error al obtener presupuestos para alertas: {str(e)}", exc_info=True)
            return []
    
    async def check_and_update_expired_periods(self, user_id: str) -> int:
        """
        Verifica y actualiza los presupuestos con períodos vencidos.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            int: Número de presupuestos actualizados.
        """
        try:
            # Obtener todos los presupuestos del usuario
            budgets = await self.get_by_user_id(user_id)
            
            # Verificar y actualizar los períodos vencidos
            now = datetime.now()
            updated_count = 0
            
            for budget in budgets:
                if budget.is_period_ended(now):
                    result = await self.update_for_new_period(budget.id)
                    if result:
                        updated_count += 1
            
            logger.info(f"Actualizados {updated_count} presupuestos con períodos vencidos")
            return updated_count
        except Exception as e:
            logger.error(f"Error al actualizar períodos vencidos: {str(e)}", exc_info=True)
            return 0
    
    async def get_budget_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen del uso de todos los presupuestos de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Resumen de uso de presupuestos.
        """
        try:
            # Obtener presupuestos activos
            active_budgets = await self.get_active_budgets(user_id)
            
            # Preparar resumen
            summary = {
                "total_budgeted": 0.0,
                "total_spent": 0.0,
                "categories": []
            }
            
            # Calcular totales y detalles por categoría
            for budget in active_budgets:
                summary["total_budgeted"] += budget.amount
                summary["total_spent"] += budget.current_amount
                
                category_summary = {
                    "category_id": budget.category_id,
                    "amount": budget.amount,
                    "current_amount": budget.current_amount,
                    "percentage": budget.get_usage_percentage(),
                    "alert_threshold": budget.alert_threshold,
                    "needs_alert": budget.should_alert(),
                    "period": budget.period
                }
                
                summary["categories"].append(category_summary)
            
            # Calcular porcentaje global
            if summary["total_budgeted"] > 0:
                summary["global_percentage"] = (summary["total_spent"] / summary["total_budgeted"]) * 100
            else:
                summary["global_percentage"] = 0.0
            
            return summary
        except Exception as e:
            logger.error(f"Error al obtener resumen de uso de presupuestos: {str(e)}", exc_info=True)
            return {
                "total_budgeted": 0.0,
                "total_spent": 0.0,
                "global_percentage": 0.0,
                "categories": []
            }