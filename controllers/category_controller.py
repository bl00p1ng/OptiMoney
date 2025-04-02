"""
Controlador para gestionar las operaciones relacionadas con categorías.
"""
from typing import Dict, Any, List, Optional
from models.category_model import Category
from models.repositories.category_repository import CategoryRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class CategoryController:
    """
    Controlador para operaciones relacionadas con categorías.
    
    Este controlador maneja la lógica de negocio para crear, actualizar,
    eliminar y consultar categorías.
    """
    
    def __init__(self):
        """Inicializa el controlador de categorías."""
        self.category_repo = CategoryRepository()
        logger.debug("Controlador de categorías inicializado")
    
    async def get_all_categories(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene todas las categorías disponibles para un usuario.
        
        Args:
            user_id: ID del usuario o None para obtener solo predefinidas.
            
        Returns:
            Dict[str, Any]: Respuesta con las categorías.
        """
        try:
            categories = await self.category_repo.get_by_user_id(user_id)
            
            # Convertir a formato para respuesta
            categories_list = []
            for category in categories:
                cat_dict = category.to_dict()
                categories_list.append(cat_dict)
            
            logger.info(f"Obtenidas {len(categories_list)} categorías para usuario {user_id}")
            return {
                "success": True,
                "categories": categories_list
            }
        except Exception as e:
            logger.error(f"Error al obtener categorías: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener categorías: {str(e)}"
            }
    
    async def get_categories_by_type(
        self, 
        type: str, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene categorías por tipo (expense o income).
        
        Args:
            type: Tipo de categoría ("expense" o "income").
            user_id: ID del usuario o None para obtener solo predefinidas.
            
        Returns:
            Dict[str, Any]: Respuesta con las categorías del tipo especificado.
        """
        try:
            if type not in ["expense", "income"]:
                return {
                    "success": False,
                    "error": f"Tipo de categoría no válido: {type}. Debe ser 'expense' o 'income'."
                }
                
            categories = await self.category_repo.get_by_type(type, user_id)
            
            # Convertir a formato para respuesta
            categories_list = []
            for category in categories:
                cat_dict = category.to_dict()
                categories_list.append(cat_dict)
            
            logger.info(f"Obtenidas {len(categories_list)} categorías de tipo {type}")
            return {
                "success": True,
                "categories": categories_list
            }
        except Exception as e:
            logger.error(f"Error al obtener categorías por tipo: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener categorías por tipo: {str(e)}"
            }
    
    async def create_category(self, category_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva categoría personalizada.
        
        Args:
            category_data: Datos de la categoría a crear.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Validar datos mínimos requeridos
            required_fields = ["user_id", "name", "type"]
            for field in required_fields:
                if field not in category_data:
                    return {
                        "success": False, 
                        "error": f"El campo '{field}' es requerido"
                    }
            
            # Validar tipo
            if category_data["type"] not in ["expense", "income"]:
                return {
                    "success": False,
                    "error": "El tipo debe ser 'expense' o 'income'"
                }
            
            # Crear la categoría
            category = Category(
                user_id=category_data["user_id"],
                name=category_data["name"],
                type=category_data["type"],
                icon=category_data.get("icon", "default"),
                color=category_data.get("color", "#808080")
            )
            
            # Guardar en la base de datos
            category_id = await self.category_repo.add(category)
            
            logger.info(f"Categoría creada con ID: {category_id}")
            return {
                "success": True,
                "category_id": category_id,
                "message": "Categoría creada exitosamente"
            }
        except Exception as e:
            logger.error(f"Error al crear categoría: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al crear categoría: {str(e)}"
            }
    
    async def update_category(
        self, 
        category_id: str, 
        user_id: str, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza una categoría existente.
        
        Args:
            category_id: ID de la categoría a actualizar.
            user_id: ID del usuario propietario.
            update_data: Datos a actualizar.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Validar que no se intente cambiar el tipo
            if "type" in update_data:
                return {
                    "success": False,
                    "error": "No se permite cambiar el tipo de una categoría existente"
                }
            
            # Intentar actualizar
            result = await self.category_repo.update_user_category(
                category_id, 
                user_id, 
                update_data
            )
            
            if result:
                logger.info(f"Categoría {category_id} actualizada exitosamente")
                return {
                    "success": True,
                    "message": "Categoría actualizada exitosamente"
                }
            else:
                logger.warning(f"No se pudo actualizar la categoría {category_id}")
                return {
                    "success": False,
                    "error": "No se pudo actualizar la categoría"
                }
        except Exception as e:
            logger.error(f"Error al actualizar categoría: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al actualizar categoría: {str(e)}"
            }
    
    async def delete_category(self, category_id: str, user_id: str) -> Dict[str, Any]:
        """
        Elimina una categoría personalizada.
        
        Args:
            category_id: ID de la categoría a eliminar.
            user_id: ID del usuario propietario.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            result = await self.category_repo.delete_user_category(category_id, user_id)
            
            if result:
                logger.info(f"Categoría {category_id} eliminada exitosamente")
                return {
                    "success": True,
                    "message": "Categoría eliminada exitosamente"
                }
            else:
                logger.warning(f"No se pudo eliminar la categoría {category_id}")
                return {
                    "success": False,
                    "error": "No se pudo eliminar la categoría. Verifica que exista y te pertenezca."
                }
        except Exception as e:
            logger.error(f"Error al eliminar categoría: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al eliminar categoría: {str(e)}"
            }
    
    async def initialize_default_categories(self) -> Dict[str, Any]:
        """
        Inicializa las categorías predefinidas del sistema.
        
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            result = await self.category_repo.create_default_categories()
            
            if result:
                logger.info("Categorías predefinidas inicializadas exitosamente")
                return {
                    "success": True,
                    "message": "Categorías predefinidas inicializadas exitosamente"
                }
            else:
                logger.warning("No se pudieron inicializar las categorías predefinidas")
                return {
                    "success": False,
                    "error": "No se pudieron inicializar las categorías predefinidas"
                }
        except Exception as e:
            logger.error(f"Error al inicializar categorías predefinidas: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al inicializar categorías predefinidas: {str(e)}"
            }