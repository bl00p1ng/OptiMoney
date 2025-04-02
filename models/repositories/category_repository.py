"""
Módulo que contiene el repositorio para operaciones con categorías.
"""
from typing import Optional, List, Dict, Any
from models.category_model import Category
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class CategoryRepository(BaseRepository[Category]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con categorías.
    
    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Categoría.
    """
    
    def __init__(self):
        """Inicializa un nuevo repositorio de categorías."""
        super().__init__("categories", Category)
        logger.debug("Repositorio de categorías inicializado")
    
    async def get_by_user_id(self, user_id: Optional[str] = None) -> List[Category]:
        """
        Obtiene las categorías de un usuario o las categorías predefinidas.
        
        Args:
            user_id: ID del usuario o None para obtener categorías predefinidas.
            
        Returns:
            List[Category]: Lista de categorías.
        """
        try:
            # Para categorías predefinidas, user_id será None
            # Para categorías del usuario, se filtra por user_id
            if user_id is None:
                return await self.query({"user_id": None})
            else:
                # Obtener tanto las categorías del usuario como las predefinidas
                user_categories = await self.query({"user_id": user_id})
                predefined_categories = await self.query({"user_id": None})
                
                # Combinar ambas listas
                return user_categories + predefined_categories
        except Exception as e:
            logger.error(f"Error al obtener categorías para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_by_type(self, type: str, user_id: Optional[str] = None) -> List[Category]:
        """
        Obtiene categorías por tipo (expense o income).
        
        Args:
            type: Tipo de categoría ("expense" o "income").
            user_id: ID del usuario para incluir categorías personalizadas (opcional).
            
        Returns:
            List[Category]: Lista de categorías del tipo especificado.
        """
        try:
            # Obtener categorías predefinidas del tipo especificado
            predefined = await self.query({"user_id": None, "type": type})
            
            # Si no se especifica user_id, solo devolver predefinidas
            if user_id is None:
                return predefined
            
            # De lo contrario, combinar con las categorías personalizadas del usuario
            user_categories = await self.query({"user_id": user_id, "type": type})
            
            return user_categories + predefined
        except Exception as e:
            logger.error(f"Error al obtener categorías por tipo {type}: {str(e)}", exc_info=True)
            return []
    
    async def create_default_categories(self) -> bool:
        """
        Crea las categorías predefinidas por defecto en la base de datos.
        
        Returns:
            bool: True si se crearon correctamente, False en caso contrario.
        """
        try:
            # Obtener categorías predefinidas actuales
            existing_categories = await self.query({"user_id": None})
            
            # Si ya existen categorías predefinidas, no hacer nada
            if existing_categories:
                logger.debug("Las categorías predefinidas ya existen en la base de datos")
                return True
            
            # Obtener las categorías predefinidas del modelo
            default_categories = Category.get_default_categories()
            
            # Crear cada categoría predefinida
            for code, data in default_categories.items():
                category = Category(
                    user_id=None,  # None indica que es predefinida
                    name=data["name"],
                    type=data["type"],
                    icon=data["icon"],
                    color=data["color"]
                )
                
                # El ID será el código para facilitar referencias
                category.id = code
                
                # Añadir a la base de datos
                await self.add(category)
            
            logger.info(f"Creadas {len(default_categories)} categorías predefinidas")
            return True
        except Exception as e:
            logger.error(f"Error al crear categorías predefinidas: {str(e)}", exc_info=True)
            return False
    
    async def delete_user_category(self, category_id: str, user_id: str) -> bool:
        """
        Elimina una categoría personalizada de un usuario.
        
        Args:
            category_id: ID de la categoría a eliminar.
            user_id: ID del usuario propietario.
            
        Returns:
            bool: True si se eliminó correctamente, False en caso contrario.
        """
        try:
            # Obtener la categoría
            category = await self.get_by_id(category_id)
            
            # Verificar que exista y pertenezca al usuario
            if not category:
                logger.warning(f"Categoría {category_id} no encontrada")
                return False
                
            if category.user_id != user_id:
                logger.warning(f"Categoría {category_id} no pertenece al usuario {user_id}")
                return False
                
            # Si es una categoría predefinida, no se puede eliminar
            if category.is_predefined():
                logger.warning(f"No se puede eliminar la categoría predefinida {category_id}")
                return False
            
            # Eliminar la categoría
            result = await self.delete(category_id)
            
            if result:
                logger.info(f"Categoría {category_id} eliminada correctamente")
            else:
                logger.warning(f"No se pudo eliminar la categoría {category_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al eliminar categoría {category_id}: {str(e)}", exc_info=True)
            return False
    
    async def update_user_category(self, category_id: str, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza una categoría personalizada de un usuario.
        
        Args:
            category_id: ID de la categoría a actualizar.
            user_id: ID del usuario propietario.
            data: Datos a actualizar.
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario.
        """
        try:
            # Obtener la categoría
            category = await self.get_by_id(category_id)
            
            # Verificar que exista y pertenezca al usuario
            if not category:
                logger.warning(f"Categoría {category_id} no encontrada")
                return False
                
            # Verificar propiedad:
            # - Si es predefinida (user_id=None), cualquiera puede personalizarla
            # - Si es personalizada, solo el propietario puede modificarla
            if category.user_id is not None and category.user_id != user_id:
                logger.warning(f"Categoría {category_id} no pertenece al usuario {user_id}")
                return False
            
            # Si es predefinida, crear una copia personalizada en lugar de modificar la original
            if category.is_predefined():
                # Crear una nueva categoría personalizada basada en la predefinida
                new_category = Category(
                    user_id=user_id,
                    name=data.get("name", category.name),
                    type=category.type,  # El tipo no se puede cambiar
                    icon=data.get("icon", category.icon),
                    color=data.get("color", category.color)
                )
                
                # Generar un nuevo ID que haga referencia a la original
                new_category.id = f"{user_id}_{category_id}"
                
                # Añadir la nueva categoría personalizada
                await self.add(new_category)
                logger.info(f"Creada personalización de categoría {category_id} para usuario {user_id}")
                return True
            else:
                # Si es personalizada, actualizar directamente
                result = await self.update(category_id, data)
                
                if result:
                    logger.info(f"Categoría {category_id} actualizada correctamente")
                else:
                    logger.warning(f"No se pudo actualizar la categoría {category_id}")
                    
                return result
        except Exception as e:
            logger.error(f"Error al actualizar categoría {category_id}: {str(e)}", exc_info=True)
            return False