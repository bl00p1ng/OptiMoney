"""
Módulo que contiene la clase base para todos los modelos de la aplicación.
"""
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

class BaseModel:
    """
    Clase base para todos los modelos de datos de la aplicación.
    
    Esta clase proporciona funcionalidad común para todos los modelos como:
    - Generación de IDs
    - Conversión a/desde diccionarios
    - Manejo de fechas de creación/actualización
    """
    
    def __init__(self, id: Optional[str] = None):
        """
        Inicializa un nuevo modelo base.
        
        Args:
            id: Identificador único opcional. Si no se proporciona, se genera uno.
        """
        self.id = id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el modelo a un diccionario para almacenamiento en Firestore.
        
        Returns:
            Dict[str, Any]: Representación del modelo como diccionario.
        """
        # Se excluyen atributos especiales o que empiezan con _
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, datetime):
                    # Firestore maneja automáticamente los objetos datetime
                    result[key] = value
                else:
                    result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Crea una instancia del modelo a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos del modelo.
            
        Returns:
            BaseModel: Una nueva instancia del modelo.
        """
        instance = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            setattr(instance, key, value)
            
        return instance
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Actualiza los atributos del modelo con los datos proporcionados.
        
        Args:
            data: Diccionario con los datos a actualizar.
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Se actualiza la fecha de modificación
        self.updated_at = datetime.now()