"""
Módulo que contiene el modelo de patrón de gasto para la aplicación.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.base_model import BaseModel

class Pattern(BaseModel):
    """
    Modelo que representa un patrón de gasto detectado en la aplicación.
    
    Attributes:
        id (str): Identificador único del patrón.
        user_id (str): Usuario al que pertenece este patrón.
        type (str): Tipo de patrón: "micro_expense", "temporal", "recurring", "category_deviation".
        category (str): Categoría principal involucrada en el patrón.
        subcategory (str): Subcategoría específica si aplica.
        detected_at (datetime): Fecha y hora de la primera detección.
        last_updated_at (datetime): Última actualización del patrón.
        status (str): Estado del patrón: "active", "resolved", "ignored".
        metrics (Dict): Métricas asociadas al patrón.
        temporal_data (Dict): Datos temporales para patrones de tipo temporal.
        savings_potential (Dict): Potencial de ahorro estimado.
        related_transactions (List): Lista de transacciones relacionadas con el patrón.
        analysis_metadata (Dict): Metadatos del análisis que generó el patrón.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "",
        type: str = "",
        category: str = "",
        subcategory: str = "",
        detected_at: Optional[datetime] = None,
        last_updated_at: Optional[datetime] = None,
        status: str = "active",
        metrics: Optional[Dict[str, Any]] = None,
        temporal_data: Optional[Dict[str, Any]] = None,
        savings_potential: Optional[Dict[str, Any]] = None,
        related_transactions: Optional[List[Dict[str, Any]]] = None,
        analysis_metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa un nuevo patrón de gasto.
        
        Args:
            id: Identificador único opcional.
            user_id: Usuario al que pertenece este patrón.
            type: Tipo de patrón.
            category: Categoría principal involucrada.
            subcategory: Subcategoría específica si aplica.
            detected_at: Fecha y hora de la primera detección.
            last_updated_at: Última actualización del patrón.
            status: Estado del patrón.
            metrics: Métricas asociadas al patrón.
            temporal_data: Datos temporales para patrones de tipo temporal.
            savings_potential: Potencial de ahorro estimado.
            related_transactions: Lista de transacciones relacionadas.
            analysis_metadata: Metadatos del análisis que generó el patrón.
        """
        super().__init__(id)
        self.user_id = user_id
        self.type = type
        self.category = category
        self.subcategory = subcategory
        self.detected_at = detected_at or datetime.now()
        self.last_updated_at = last_updated_at or datetime.now()
        self.status = status
        
        # Métricas asociadas al patrón
        self.metrics = metrics or {
            "frequency": 0,
            "totalAmount": 0,
            "averageAmount": 0,
            "percentageOfCategory": 0,
            "percentageOfTotal": 0,
            "deviation": 0,
            "confidence": 0
        }
        
        # Datos temporales (solo para patrones temporales)
        self.temporal_data = temporal_data or {}
        
        # Potencial de ahorro
        self.savings_potential = savings_potential or {
            "estimatedMonthly": 0,
            "estimatedYearly": 0,
            "optimizationPercentage": 0,
            "calculationMethod": "historical"
        }
        
        # Transacciones relacionadas
        self.related_transactions = related_transactions or []
        
        # Metadatos del análisis
        self.analysis_metadata = analysis_metadata or {
            "algorithmVersion": "1.0",
            "iterationNumber": 1
        }
    
    def update_status(self, new_status: str) -> None:
        """
        Actualiza el estado del patrón.
        
        Args:
            new_status: Nuevo estado del patrón ("active", "resolved", "ignored").
        """
        self.status = new_status
        self.last_updated_at = datetime.now()
    
    def add_related_transaction(self, transaction_id: str, amount: float, date: datetime) -> None:
        """
        Añade una transacción relacionada al patrón.
        
        Args:
            transaction_id: ID de la transacción relacionada.
            amount: Monto de la transacción.
            date: Fecha de la transacción.
        """
        transaction_data = {
            "transaction_id": transaction_id,
            "amount": amount,
            "date": date
        }
        
        self.related_transactions.append(transaction_data)
        self.update_metrics()
        self.last_updated_at = datetime.now()
    
    def update_metrics(self) -> None:
        """
        Actualiza las métricas del patrón basadas en las transacciones relacionadas.
        """
        if not self.related_transactions:
            return
            
        # Calcular frecuencia (transacciones por mes)
        if len(self.related_transactions) > 1:
            dates = [t['date'] for t in self.related_transactions if isinstance(t.get('date'), datetime)]
            if len(dates) >= 2:
                date_range = max(dates) - min(dates)
                days = date_range.days or 1  # Evitar división por cero
                months = days / 30.0
                self.metrics["frequency"] = len(dates) / max(months, 1)
        
        # Calcular montos
        amounts = [t['amount'] for t in self.related_transactions]
        self.metrics["totalAmount"] = sum(amounts)
        self.metrics["averageAmount"] = self.metrics["totalAmount"] / len(amounts) if amounts else 0
    
    def calculate_savings_potential(self, optimization_percentage: float = 0.5) -> None:
        """
        Calcula el potencial de ahorro basado en las transacciones relacionadas.
        
        Args:
            optimization_percentage: Porcentaje estimado de optimización (0-1).
        """
        if not self.related_transactions:
            return
            
        # Calcular ahorro mensual estimado
        monthly_amount = self.metrics.get("totalAmount", 0)
        if self.metrics.get("frequency", 0) > 0:
            # Si tenemos frecuencia, ajustamos el monto total a base mensual
            monthly_amount = monthly_amount * (self.metrics["frequency"] / len(self.related_transactions))
        
        # Calcular potencial de ahorro
        self.savings_potential["optimizationPercentage"] = optimization_percentage * 100
        self.savings_potential["estimatedMonthly"] = monthly_amount * optimization_percentage
        self.savings_potential["estimatedYearly"] = self.savings_potential["estimatedMonthly"] * 12
        self.last_updated_at = datetime.now()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pattern':
        """
        Crea una instancia de Patrón a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos del patrón.
            
        Returns:
            Pattern: Una nueva instancia de Patrón.
        """
        pattern = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            # Convertir fechas si es necesario
            if key in ['detected_at', 'last_updated_at'] and not isinstance(value, datetime):
                if isinstance(value, (int, float)):
                    setattr(pattern, key, datetime.fromtimestamp(value))
                else:
                    try:
                        setattr(pattern, key, datetime.fromisoformat(str(value)))
                    except (ValueError, TypeError):
                        setattr(pattern, key, datetime.now())
            else:
                setattr(pattern, key, value)
        
        return pattern