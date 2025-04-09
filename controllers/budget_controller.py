"""
Controlador para gestionar las operaciones relacionadas con presupuestos.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from models.budget_model import Budget
from models.repositories.budget_repository import BudgetRepository
from models.repositories.category_repository import CategoryRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class BudgetController:
    """
    Controlador para operaciones relacionadas con presupuestos.
    
    Este controlador maneja la lógica de negocio para crear, actualizar,
    eliminar y consultar presupuestos, así como para realizar análisis
    y seguimiento de los mismos.
    """
    
    def __init__(self):
        """
        Inicializa el controlador de presupuestos.
        
        Instancia los repositorios necesarios para las operaciones 
        de gestión de presupuestos.
        """
        self.budget_repo = BudgetRepository()
        self.category_repo = CategoryRepository()
        logger.debug("Controlador de presupuestos inicializado")
    
    async def create_budget(self, budget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo presupuesto para una categoría específica.
        
        Args:
            budget_data: Diccionario con los datos del presupuesto.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Validar datos mínimos requeridos
            required_fields = ["user_id", "category_id", "amount", "period"]
            for field in required_fields:
                if field not in budget_data:
                    return {
                        "success": False, 
                        "error": f"El campo '{field}' es requerido"
                    }
            
            # Verificar que la categoría exista y pertenezca al usuario
            categories = await self.category_repo.get_by_user_id(budget_data["user_id"])
            category_exists = any(
                cat.id == budget_data["category_id"] 
                for cat in categories
            )
            
            if not category_exists:
                return {
                    "success": False,
                    "error": "La categoría no existe o no pertenece al usuario"
                }
            
            # Validar período
            valid_periods = ["monthly", "weekly", "yearly"]
            if budget_data["period"] not in valid_periods:
                return {
                    "success": False,
                    "error": f"Período inválido. Debe ser uno de: {', '.join(valid_periods)}"
                }
            
            # Crear el presupuesto
            budget = Budget(
                user_id=budget_data["user_id"],
                category_id=budget_data["category_id"],
                amount=float(budget_data["amount"]),
                period=budget_data["period"],
                alert_threshold=budget_data.get("alert_threshold", 80.0),
                start_date=budget_data.get("start_date") or datetime.now()
            )
            
            # Guardar en la base de datos
            budget_id = await self.budget_repo.add(budget)
            
            logger.info(f"Presupuesto creado con ID: {budget_id}")
            return {
                "success": True,
                "budget_id": budget_id,
                "message": "Presupuesto creado exitosamente"
            }
        except Exception as e:
            logger.error(f"Error al crear presupuesto: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al crear presupuesto: {str(e)}"
            }
    
    async def get_user_budgets(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene todos los presupuestos de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Respuesta con los presupuestos del usuario.
        """
        try:
            # Obtener presupuestos del usuario
            budgets = await self.budget_repo.get_by_user_id(user_id)
            
            # Convertir a formato para respuesta
            budget_list = []
            for budget in budgets:
                budget_dict = budget.to_dict()
                
                # Intentar obtener nombre de categoría
                categories = await self.category_repo.get_by_user_id(user_id)
                category = next(
                    (cat for cat in categories if cat.id == budget.category_id), 
                    None
                )
                
                budget_dict['category_name'] = category.name if category else "Categoría desconocida"
                
                budget_list.append(budget_dict)
            
            logger.debug(f"Obtenidos {len(budget_list)} presupuestos para usuario {user_id}")
            return {
                "success": True,
                "budgets": budget_list
            }
        except Exception as e:
            logger.error(f"Error al obtener presupuestos: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener presupuestos: {str(e)}"
            }
    
    async def get_budget(self, budget_id: str, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un presupuesto específico por su ID.
        
        Args:
            budget_id: ID del presupuesto.
            user_id: ID del usuario para verificación de propiedad.
            
        Returns:
            Dict[str, Any]: Respuesta con los detalles del presupuesto.
        """
        try:
            # Obtener el presupuesto
            budget = await self.budget_repo.get_by_id(budget_id)
            
            if not budget:
                return {
                    "success": False,
                    "error": f"Presupuesto con ID {budget_id} no encontrado"
                }
            
            # Verificar que el presupuesto pertenezca al usuario
            if budget.user_id != user_id:
                return {
                    "success": False,
                    "error": "No autorizado para acceder a este presupuesto"
                }
            
            # Obtener nombre de categoría
            categories = await self.category_repo.get_by_user_id(user_id)
            category = next(
                (cat for cat in categories if cat.id == budget.category_id), 
                None
            )
            
            # Convertir a diccionario con información adicional
            budget_dict = budget.to_dict()
            budget_dict['category_name'] = category.name if category else "Categoría desconocida"
            
            return {
                "success": True,
                "budget": budget_dict
            }
        except Exception as e:
            logger.error(f"Error al obtener presupuesto: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener presupuesto: {str(e)}"
            }
    
    async def update_budget(
        self, 
        budget_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza un presupuesto existente.
        
        Args:
            budget_id: ID del presupuesto a actualizar.
            user_id: ID del usuario propietario.
            update_data: Datos a actualizar.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Verificar que el presupuesto existe y pertenece al usuario
            budget = await self.budget_repo.get_by_id(budget_id)
            
            if not budget:
                return {
                    "success": False,
                    "error": f"Presupuesto con ID {budget_id} no encontrado"
                }
            
            if budget.user_id != user_id:
                return {
                    "success": False,
                    "error": "No autorizado para modificar este presupuesto"
                }
            
            # Campos permitidos para actualización
            allowed_fields = ["amount", "alert_threshold", "period"]
            update_dict = {}
            
            for field in allowed_fields:
                if field in update_data:
                    update_dict[field] = update_data[field]
            
            # Validar período si se proporciona
            if "period" in update_dict:
                valid_periods = ["monthly", "weekly", "yearly"]
                if update_dict["period"] not in valid_periods:
                    return {
                        "success": False,
                        "error": f"Período inválido. Debe ser uno de: {', '.join(valid_periods)}"
                    }
            
            # Actualizar el presupuesto
            result = await self.budget_repo.update(budget_id, update_dict)
            
            if result:
                logger.info(f"Presupuesto {budget_id} actualizado exitosamente")
                return {
                    "success": True,
                    "message": "Presupuesto actualizado exitosamente"
                }
            else:
                logger.warning(f"No se pudo actualizar el presupuesto {budget_id}")
                return {
                    "success": False,
                    "error": "No se pudo actualizar el presupuesto"
                }
        except Exception as e:
            logger.error(f"Error al actualizar presupuesto: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al actualizar presupuesto: {str(e)}"
            }
    
    async def delete_budget(self, budget_id: str, user_id: str) -> Dict[str, Any]:
        """
        Elimina un presupuesto existente.
        
        Args:
            budget_id: ID del presupuesto a eliminar.
            user_id: ID del usuario propietario.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Verificar que el presupuesto existe y pertenece al usuario
            budget = await self.budget_repo.get_by_id(budget_id)
            
            if not budget:
                return {
                    "success": False,
                    "error": f"Presupuesto con ID {budget_id} no encontrado"
                }
            
            if budget.user_id != user_id:
                return {
                    "success": False,
                    "error": "No autorizado para eliminar este presupuesto"
                }
            
            # Eliminar el presupuesto
            result = await self.budget_repo.delete(budget_id)
            
            if result:
                logger.info(f"Presupuesto {budget_id} eliminado exitosamente")
                return {
                    "success": True,
                    "message": "Presupuesto eliminado exitosamente"
                }
            else:
                logger.warning(f"No se pudo eliminar el presupuesto {budget_id}")
                return {
                    "success": False,
                    "error": "No se pudo eliminar el presupuesto"
                }
        except Exception as e:
            logger.error(f"Error al eliminar presupuesto: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al eliminar presupuesto: {str(e)}"
            }
    
    async def get_budget_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de los presupuestos del usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Resumen de los presupuestos.
        """
        try:
            # Obtener resumen de uso de presupuestos
            summary = await self.budget_repo.get_budget_usage_summary(user_id)
            
            # Intentar obtener nombres de categorías
            categories = await self.category_repo.get_by_user_id(user_id)
            category_map = {cat.id: cat.name for cat in categories}
            
            # Actualizar nombres de categorías en el resumen
            for category_summary in summary.get("categories", []):
                category_id = category_summary.get("category_id")
                category_summary["category_name"] = category_map.get(
                    category_id, 
                    "Categoría desconocida"
                )
            
            logger.debug(f"Obtenido resumen de presupuestos para usuario {user_id}")
            return {
                "success": True,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen de presupuestos: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener resumen de presupuestos: {str(e)}"
            }