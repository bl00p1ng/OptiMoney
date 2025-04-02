"""
Módulo que contiene el modelo de transacción para la aplicación.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from models.base_model import BaseModel

class Transaction(BaseModel):
    """
    Modelo que representa una transacción financiera en la aplicación.
    
    Attributes:
        id (str): Identificador único de la transacción.
        user_id (str): Identificador del usuario propietario.
        amount (float): Monto de la transacción.
        date (datetime): Fecha y hora de la transacción.
        category (str): Categoría asignada (Alimentación, Transporte, etc.).
        description (str): Descripción ingresada por el usuario.
        is_expense (bool): Indicador si es gasto (True) o ingreso (False).
        metadata (Dict): Metadatos adicionales para análisis.
        analysis_flags (Dict): Banderas de análisis para identificar patrones.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "",
        amount: float = 0.0,
        date: Optional[datetime] = None,
        category: str = "",
        description: str = "",
        is_expense: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
        analysis_flags: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa una nueva transacción.
        
        Args:
            id: Identificador único opcional.
            user_id: Identificador del usuario propietario.
            amount: Monto de la transacción.
            date: Fecha y hora de la transacción.
            category: Categoría asignada.
            description: Descripción ingresada por el usuario.
            is_expense: Indicador si es gasto (True) o ingreso (False).
            metadata: Metadatos adicionales para análisis.
            analysis_flags: Banderas de análisis para identificar patrones.
        """
        super().__init__(id)
        self.user_id = user_id
        self.amount = amount
        self.date = date or datetime.now()
        self.category = category
        self.description = description
        self.is_expense = is_expense
        
        # Inicializar metadatos para análisis
        self.metadata = metadata or self._initialize_metadata()
        
        # Inicializar banderas de análisis
        self.analysis_flags = analysis_flags or {
            "isMicroExpense": False,
            "isHighDeviation": False,
            "isOptimizableRecurring": False,
            "isTemporalPattern": False,
            "lastAnalyzedAt": None
        }
    
    def _initialize_metadata(self) -> Dict[str, Any]:
        """
        Inicializa los metadatos de la transacción basándose en la fecha.
        
        Returns:
            Dict[str, Any]: Diccionario con los metadatos inicializados.
        """
        # Obtener campos derivados de la fecha
        day_of_week = self.date.weekday()
        day_of_week = (day_of_week + 1) % 7
        
        # Determinar la semana del mes (aproximada)
        day = self.date.day
        week_of_month = (day - 1) // 7 + 1
        
        # Determinar la hora del día y el período
        hour = self.date.hour
        if 5 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 17:
            time_of_day = "afternoon"
        elif 17 <= hour < 21:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        # Normalizar el monto (quitar decimales pequeños)
        normalized_amount = round(self.amount * 100) / 100
        
        return {
            "dayOfWeek": day_of_week,
            "weekOfMonth": week_of_month,
            "monthOfYear": self.date.month,
            "timeOfDay": time_of_day,
            "hourOfDay": hour,
            "isRecurring": False,  # Inicialmente falso, se determina mediante análisis
            "recurrenceGroupId": None,
            "similarityHash": None,  # Se calculará en un proceso separado
            "normalizedAmount": normalized_amount
        }
    
    def update_metadata(self) -> None:
        """
        Actualiza los metadatos de la transacción basándose en sus atributos actuales.
        """
        current_metadata = self._initialize_metadata()
        
        # Preservar campos que no se derivan directamente de la fecha
        if self.metadata:
            for key in ["isRecurring", "recurrenceGroupId", "similarityHash"]:
                if key in self.metadata and self.metadata[key] is not None:
                    current_metadata[key] = self.metadata[key]
        
        self.metadata = current_metadata
        self.updated_at = datetime.now()
    
    def mark_as_analyzed(self) -> None:
        """
        Marca la transacción como analizada en el momento actual.
        """
        self.analysis_flags["lastAnalyzedAt"] = datetime.now()
        self.updated_at = datetime.now()
    
    def set_analysis_flag(self, flag_name: str, value: bool) -> None:
        """
        Establece una bandera de análisis específica.
        
        Args:
            flag_name: Nombre de la bandera a establecer.
            value: Valor a asignar (True o False).
        """
        if flag_name in self.analysis_flags:
            self.analysis_flags[flag_name] = value
            self.updated_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        """
        Crea una instancia de Transacción a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la transacción.
            
        Returns:
            Transaction: Una nueva instancia de Transacción.
        """
        transaction = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            # Convertir la fecha si es necesario
            if key == 'date' and not isinstance(value, datetime):
                if isinstance(value, (int, float)):
                    setattr(transaction, key, datetime.fromtimestamp(value))
                else:
                    try:
                        setattr(transaction, key, datetime.fromisoformat(str(value)))
                    except (ValueError, TypeError):
                        setattr(transaction, key, datetime.now())
            else:
                setattr(transaction, key, value)
        
        # Asegurarse de que los diccionarios de metadatos y banderas están inicializados
        if not hasattr(transaction, 'metadata') or transaction.metadata is None:
            transaction.metadata = transaction._initialize_metadata()
            
        if not hasattr(transaction, 'analysis_flags') or transaction.analysis_flags is None:
            transaction.analysis_flags = {
                "isMicroExpense": False,
                "isHighDeviation": False,
                "isOptimizableRecurring": False,
                "isTemporalPattern": False,
                "lastAnalyzedAt": None
            }
        
        return transaction