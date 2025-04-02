"""
Módulo que contiene el modelo de presupuesto para la aplicación.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from models.base_model import BaseModel

class Budget(BaseModel):
    """
    Modelo que representa un presupuesto para una categoría específica.
    
    Attributes:
        id (str): Identificador único del presupuesto.
        user_id (str): Usuario propietario.
        category_id (str): Categoría asociada al presupuesto.
        amount (float): Monto límite establecido.
        period (str): Período: "monthly", "weekly", "yearly".
        start_date (datetime): Fecha de inicio del presupuesto.
        current_amount (float): Monto actual acumulado en el período.
        last_updated (datetime): Última actualización del monto actual.
        alert_threshold (float): Umbral para alertas (porcentaje, 0-100).
        alert_sent (bool): Indica si ya se envió una alerta para este período.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "",
        category_id: str = "",
        amount: float = 0.0,
        period: str = "monthly",
        start_date: Optional[datetime] = None,
        current_amount: float = 0.0,
        last_updated: Optional[datetime] = None,
        alert_threshold: float = 80.0,
        alert_sent: bool = False
    ):
        """
        Inicializa un nuevo presupuesto.
        
        Args:
            id: Identificador único opcional.
            user_id: Usuario propietario.
            category_id: Categoría asociada al presupuesto.
            amount: Monto límite establecido.
            period: Período del presupuesto.
            start_date: Fecha de inicio del presupuesto.
            current_amount: Monto actual acumulado en el período.
            last_updated: Última actualización del monto actual.
            alert_threshold: Umbral para alertas (porcentaje).
            alert_sent: Indica si ya se envió una alerta.
        """
        super().__init__(id)
        self.user_id = user_id
        self.category_id = category_id
        self.amount = amount
        self.period = period
        self.start_date = start_date or datetime.now()
        self.current_amount = current_amount
        self.last_updated = last_updated or datetime.now()
        self.alert_threshold = alert_threshold
        self.alert_sent = alert_sent
    
    def update_amount(self, transaction_amount: float) -> None:
        """
        Actualiza el monto actual acumulado.
        
        Args:
            transaction_amount: Monto de la transacción a añadir.
        """
        self.current_amount += transaction_amount
        self.last_updated = datetime.now()
        self.updated_at = datetime.now()
    
    def reset_period(self) -> None:
        """
        Reinicia el presupuesto para un nuevo período.
        """
        self.current_amount = 0.0
        self.alert_sent = False
        self.last_updated = datetime.now()
        self.updated_at = datetime.now()
    
    def should_alert(self) -> bool:
        """
        Determina si se debe enviar una alerta basada en el umbral.
        
        Returns:
            bool: True si se debe enviar alerta, False en caso contrario.
        """
        # Si ya se envió una alerta, no enviar otra
        if self.alert_sent:
            return False
        
        # Calcular porcentaje de uso
        if self.amount <= 0:
            return False
            
        usage_percentage = (self.current_amount / self.amount) * 100
        
        # Si se superó el umbral, se debe alertar
        return usage_percentage >= self.alert_threshold
    
    def mark_alert_sent(self) -> None:
        """
        Marca que se ha enviado una alerta para este período.
        """
        self.alert_sent = True
        self.updated_at = datetime.now()
    
    def get_usage_percentage(self) -> float:
        """
        Calcula el porcentaje de uso del presupuesto.
        
        Returns:
            float: Porcentaje de uso (0-100).
        """
        if self.amount <= 0:
            return 0.0
            
        return (self.current_amount / self.amount) * 100
    
    def is_period_ended(self, current_date: Optional[datetime] = None) -> bool:
        """
        Verifica si el período actual ha terminado.
        
        Args:
            current_date: Fecha actual para comparar (opcional).
            
        Returns:
            bool: True si el período ha terminado, False en caso contrario.
        """
        if current_date is None:
            current_date = datetime.now()
            
        if self.period == "monthly":
            # Período mensual: cambia de mes
            return (current_date.year > self.start_date.year or 
                    (current_date.year == self.start_date.year and 
                     current_date.month > self.start_date.month))
        elif self.period == "weekly":
            # Período semanal: han pasado 7 o más días
            days_diff = (current_date - self.start_date).days
            return days_diff >= 7
        elif self.period == "yearly":
            # Período anual: cambia de año
            return current_date.year > self.start_date.year
        else:
            # Período desconocido, asumir que no ha terminado
            return False
    
    def update_for_new_period(self, new_start_date: Optional[datetime] = None) -> None:
        """
        Actualiza el presupuesto para un nuevo período.
        
        Args:
            new_start_date: Nueva fecha de inicio (opcional).
        """
        self.start_date = new_start_date or datetime.now()
        self.reset_period()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Budget':
        """
        Crea una instancia de Presupuesto a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos del presupuesto.
            
        Returns:
            Budget: Una nueva instancia de Presupuesto.
        """
        budget = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            # Convertir fechas si es necesario
            if key in ['start_date', 'last_updated'] and not isinstance(value, datetime):
                if isinstance(value, (int, float)):
                    setattr(budget, key, datetime.fromtimestamp(value))
                else:
                    try:
                        setattr(budget, key, datetime.fromisoformat(str(value)))
                    except (ValueError, TypeError):
                        setattr(budget, key, datetime.now())
            else:
                setattr(budget, key, value)
        
        return budget