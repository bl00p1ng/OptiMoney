"""
Módulo que contiene el modelo de categoría para la aplicación.
"""
from typing import Dict, Any, Optional
from models.base_model import BaseModel

class Category(BaseModel):
    """
    Modelo que representa una categoría para clasificar transacciones en la aplicación.
    
    Attributes:
        id (str): Identificador único de la categoría.
        user_id (str): Usuario propietario (null para categorías predefinidas).
        name (str): Nombre descriptivo de la categoría.
        type (str): Tipo: "expense" (gasto) o "income" (ingreso).
        icon (str): Icono asociado a la categoría.
        color (str): Color para visualización en la interfaz.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        name: str = "",
        type: str = "expense",
        icon: str = "default",
        color: str = "#808080"
    ):
        """
        Inicializa una nueva categoría.
        
        Args:
            id: Identificador único opcional.
            user_id: Usuario propietario (None para categorías predefinidas).
            name: Nombre descriptivo de la categoría.
            type: Tipo de categoría ("expense" o "income").
            icon: Icono asociado a la categoría.
            color: Color para visualización en la interfaz.
        """
        super().__init__(id)
        self.user_id = user_id
        self.name = name
        self.type = type
        self.icon = icon
        self.color = color
    
    def is_predefined(self) -> bool:
        """
        Verifica si la categoría es predefinida (del sistema).
        
        Returns:
            bool: True si es una categoría predefinida, False si es personalizada.
        """
        return self.user_id is None
    
    def update_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Actualiza los atributos de la categoría.
        
        Args:
            attributes: Diccionario con los atributos a actualizar.
        """
        # Solo se permite modificar ciertos atributos
        allowed_fields = ["name", "icon", "color"]
        
        for field in allowed_fields:
            if field in attributes:
                setattr(self, field, attributes[field])
        
        self.updated_at = self._get_current_timestamp()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Category':
        """
        Crea una instancia de Categoría a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la categoría.
            
        Returns:
            Category: Una nueva instancia de Categoría.
        """
        category = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            setattr(category, key, value)
        
        return category
    
    @staticmethod
    def get_default_categories() -> Dict[str, Dict[str, Any]]:
        """
        Retorna un diccionario con las categorías predefinidas del sistema.
        
        Returns:
            Dict[str, Dict[str, Any]]: Diccionario con categorías predefinidas.
        """
        return {
            "alimentacion": {
                "name": "Alimentación",
                "type": "expense",
                "icon": "restaurant",
                "color": "#FF5722"
            },
            "transporte": {
                "name": "Transporte",
                "type": "expense",
                "icon": "directions_car",
                "color": "#3F51B5"
            },
            "vivienda": {
                "name": "Vivienda",
                "type": "expense",
                "icon": "home",
                "color": "#673AB7"
            },
            "servicios": {
                "name": "Servicios",
                "type": "expense",
                "icon": "lightbulb",
                "color": "#FFC107"
            },
            "entretenimiento": {
                "name": "Entretenimiento",
                "type": "expense",
                "icon": "movie",
                "color": "#E91E63"
            },
            "salud": {
                "name": "Salud",
                "type": "expense",
                "icon": "local_hospital",
                "color": "#4CAF50"
            },
            "educacion": {
                "name": "Educación",
                "type": "expense",
                "icon": "school",
                "color": "#009688"
            },
            "ropa": {
                "name": "Ropa",
                "type": "expense",
                "icon": "checkroom",
                "color": "#9C27B0"
            },
            "otros_gastos": {
                "name": "Otros Gastos",
                "type": "expense",
                "icon": "more_horiz",
                "color": "#607D8B"
            },
            "salario": {
                "name": "Salario",
                "type": "income",
                "icon": "payments",
                "color": "#4CAF50"
            },
            "inversiones": {
                "name": "Inversiones",
                "type": "income",
                "icon": "trending_up",
                "color": "#2196F3"
            },
            "otros_ingresos": {
                "name": "Otros Ingresos",
                "type": "income",
                "icon": "account_balance",
                "color": "#00BCD4"
            }
        }