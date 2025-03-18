"""
Módulo que contiene el repositorio para operaciones con usuarios.
"""
from typing import Optional, List, Dict, Any
from models.user_model import User
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class UserRepository(BaseRepository[User]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con usuarios.

    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Usuario.
    """

    def __init__(self):
        """Inicializa un nuevo repositorio de usuarios."""
        super().__init__("users", User)
        logger.debug("Repositorio de usuarios inicializado")

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Busca un usuario por su dirección de correo electrónico.

        Args:
            email: Dirección de correo electrónico a buscar.

        Returns:
            Optional[User]: Usuario encontrado o None si no existe.
        """
        try:
            # Realizar consulta por email
            users = await self.query({"email": email}, limit=1)

            if users and len(users) > 0:
                logger.debug(f"Usuario encontrado con email: {email}")
                return users[0]
            else:
                logger.debug(f"Usuario no encontrado con email: {email}")
                return None
        except Exception as e:
            logger.error(f"Error al buscar usuario por email {email}: {str(e)}", exc_info=True)
            return None

    async def update_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        """
        Actualiza la configuración de un usuario.

        Args:
            user_id: ID del usuario a actualizar.
            settings: Nueva configuración a aplicar.

        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Primero verificamos si el usuario existe
            user = await self.get_by_id(user_id)
            if not user:
                logger.warning(f"Intento de actualizar configuración para usuario inexistente: {user_id}")
                return False

            # Luego actualizamos solo el campo settings
            result = await self.update(user_id, {"settings": settings})

            if result:
                logger.info(f"Configuración actualizada para usuario: {user_id}")
            else:
                logger.warning(f"No se pudo actualizar la configuración para usuario: {user_id}")

            return result
        except Exception as e:
            logger.error(f"Error al actualizar configuración para usuario {user_id}: {str(e)}", exc_info=True)
            return False

    async def get_user_count(self) -> int:
        """
        Obtiene el número total de usuarios en el sistema.

        Returns:
            int: Número total de usuarios.
        """
        try:
            # En Firestore no hay una función directa para contar documentos,
            # así que tenemos que obtener todos y contar
            users = await self.get_all()
            count = len(users)
            logger.debug(f"Número total de usuarios: {count}")
            return count
        except Exception as e:
            logger.error(f"Error al obtener número de usuarios: {str(e)}", exc_info=True)
            return 0