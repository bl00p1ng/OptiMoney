"""
Módulo que contiene el repositorio para operaciones con patrones de gasto.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from models.pattern_model import Pattern
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class PatternRepository(BaseRepository[Pattern]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con patrones de gasto.
    
    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Patrón.
    """
    
    def __init__(self):
        """Inicializa un nuevo repositorio de patrones."""
        super().__init__("patterns", Pattern)
        logger.debug("Repositorio de patrones inicializado")
    
    async def get_by_user_id(self, user_id: str) -> List[Pattern]:
        """
        Obtiene todos los patrones de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Pattern]: Lista de patrones del usuario.
        """
        try:
            return await self.query({"user_id": user_id})
        except Exception as e:
            logger.error(f"Error al obtener patrones para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_active_patterns(self, user_id: str) -> List[Pattern]:
        """
        Obtiene los patrones activos de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Pattern]: Lista de patrones activos.
        """
        try:
            return await self.query({"user_id": user_id, "status": "active"})
        except Exception as e:
            logger.error(f"Error al obtener patrones activos para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_by_type(self, user_id: str, pattern_type: str) -> List[Pattern]:
        """
        Obtiene patrones de un tipo específico para un usuario.
        
        Args:
            user_id: ID del usuario.
            pattern_type: Tipo de patrón a buscar.
            
        Returns:
            List[Pattern]: Lista de patrones del tipo especificado.
        """
        try:
            return await self.query({"user_id": user_id, "type": pattern_type})
        except Exception as e:
            logger.error(
                f"Error al obtener patrones de tipo {pattern_type} para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def get_by_category(self, user_id: str, category: str) -> List[Pattern]:
        """
        Obtiene patrones relacionados con una categoría específica.
        
        Args:
            user_id: ID del usuario.
            category: Categoría a buscar.
            
        Returns:
            List[Pattern]: Lista de patrones de la categoría especificada.
        """
        try:
            return await self.query({"user_id": user_id, "category": category})
        except Exception as e:
            logger.error(
                f"Error al obtener patrones de categoría {category} para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def add_transaction_to_pattern(
        self, 
        pattern_id: str, 
        transaction_id: str, 
        amount: float, 
        date: datetime
    ) -> bool:
        """
        Añade una transacción a un patrón existente.
        
        Args:
            pattern_id: ID del patrón.
            transaction_id: ID de la transacción.
            amount: Monto de la transacción.
            date: Fecha de la transacción.
            
        Returns:
            bool: True si la operación fue exitosa, False en caso contrario.
        """
        try:
            # Obtener el patrón actual
            pattern = await self.get_by_id(pattern_id)
            if not pattern:
                logger.warning(f"Intento de añadir transacción a patrón inexistente: {pattern_id}")
                return False
            
            # Añadir la transacción a la lista de transacciones relacionadas
            transaction_data = {
                "transaction_id": transaction_id,
                "amount": amount,
                "date": date
            }
            
            # Crear una nueva lista para asegurar que se detecta el cambio
            related_transactions = pattern.related_transactions.copy()
            related_transactions.append(transaction_data)
            
            # Actualizar el patrón
            update_data = {
                "related_transactions": related_transactions,
                "last_updated_at": datetime.now()
            }
            
            result = await self.update(pattern_id, update_data)
            
            if result:
                logger.debug(f"Transacción {transaction_id} añadida al patrón {pattern_id}")
            else:
                logger.warning(f"No se pudo añadir transacción {transaction_id} al patrón {pattern_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al añadir transacción a patrón: {str(e)}", exc_info=True)
            return False
    
    async def update_status(self, pattern_id: str, new_status: str) -> bool:
        """
        Actualiza el estado de un patrón.
        
        Args:
            pattern_id: ID del patrón.
            new_status: Nuevo estado ("active", "resolved", "ignored").
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            update_data = {
                "status": new_status,
                "last_updated_at": datetime.now()
            }
            
            result = await self.update(pattern_id, update_data)
            
            if result:
                logger.info(f"Estado del patrón {pattern_id} actualizado a: {new_status}")
            else:
                logger.warning(f"No se pudo actualizar estado del patrón {pattern_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar estado del patrón: {str(e)}", exc_info=True)
            return False
    
    async def get_patterns_by_savings_potential(self, user_id: str, min_amount: float = 0) -> List[Pattern]:
        """
        Obtiene patrones ordenados por potencial de ahorro.
        
        Args:
            user_id: ID del usuario.
            min_amount: Monto mínimo de ahorro mensual estimado.
            
        Returns:
            List[Pattern]: Lista de patrones ordenados por potencial de ahorro.
        """
        try:
            # Obtener todos los patrones activos del usuario
            patterns = await self.get_active_patterns(user_id)
            
            # Filtrar por monto mínimo de ahorro
            filtered_patterns = [
                p for p in patterns 
                if p.savings_potential.get("estimatedMonthly", 0) >= min_amount
            ]
            
            # Ordenar por potencial de ahorro (de mayor a menor)
            sorted_patterns = sorted(
                filtered_patterns, 
                key=lambda p: p.savings_potential.get("estimatedMonthly", 0),
                reverse=True
            )
            
            logger.debug(
                f"Obtenidos {len(sorted_patterns)} patrones por potencial de ahorro para usuario {user_id}"
            )
            return sorted_patterns
        except Exception as e:
            logger.error(f"Error al obtener patrones por potencial de ahorro: {str(e)}", exc_info=True)
            return []