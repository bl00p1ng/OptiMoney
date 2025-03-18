"""
Módulo que contiene el modelo de usuario para la aplicación.
"""
from typing import Dict, Any, Optional
from models.base_model import BaseModel

class User(BaseModel):
    """
    Modelo que representa a un usuario en la aplicación.
    
    Attributes:
        id (str): Identificador único del usuario.
        email (str): Correo electrónico del usuario.
        name (str): Nombre completo del usuario.
        settings (Dict): Configuraciones de usuario como moneda preferida.
    """
    
    def __init__(
        self, 
        id: Optional[str] = None,
        email: str = "",
        name: str = "",
        settings: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa un nuevo usuario.
        
        Args:
            id: Identificador único opcional.
            email: Correo electrónico del usuario.
            name: Nombre completo del usuario.
            settings: Configuraciones de usuario.
        """
        super().__init__(id)
        self.email = email
        self.name = name
        self.settings = settings or {
            "currency": "COP",  # Moneda por defecto
            "notificationsEnabled": True  # Notificaciones habilitadas por defecto
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Crea una instancia de Usuario a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos del usuario.
            
        Returns:
            User: Una nueva instancia de Usuario.
        """
        user = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            setattr(user, key, value)
            
        # Se asegura que settings tenga los valores por defecto si no existen
        if user.settings is None:
            user.settings = {
                "currency": "CLP",
                "notificationsEnabled": True
            }
        elif isinstance(user.settings, dict):
            if "currency" not in user.settings:
                user.settings["currency"] = "CLP"
            if "notificationsEnabled" not in user.settings:
                user.settings["notificationsEnabled"] = True
        
        return user
    
    def update_settings(self, new_settings: Dict[str, Any]) -> None:
        """
        Actualiza las configuraciones del usuario.
        
        Args:
            new_settings: Nuevas configuraciones a aplicar.
        """
        if self.settings is None:
            self.settings = {}
            
        self.settings.update(new_settings)
        self.updated_at = self._get_current_timestamp()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el usuario a un diccionario para almacenamiento en Firestore.
        
        Returns:
            Dict[str, Any]: Representación del usuario como diccionario.
        """
        user_dict = super().to_dict()
        
        # Asegurarse de que no se incluyan datos sensibles si existieran
        if 'password_hash' in user_dict:
            del user_dict['password_hash']
            
        return user_dict
    
    def to_public_dict(self) -> Dict[str, Any]:
        """
        Genera un diccionario con la información pública del usuario.
        
        Returns:
            Dict[str, Any]: Diccionario con la información pública del usuario.
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "settings": {
                "currency": self.settings.get("currency", "CLP")
            }
        }