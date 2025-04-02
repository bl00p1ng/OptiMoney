"""
Módulo que contiene el modelo de recomendación para la aplicación.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.base_model import BaseModel

class Recommendation(BaseModel):
    """
    Modelo que representa una recomendación generada para un usuario.
    
    Attributes:
        id (str): Identificador único de la recomendación.
        user_id (str): Usuario destinatario.
        pattern_id (str): Patrón que generó esta recomendación.
        created_at (datetime): Fecha de creación.
        expires_at (datetime): Fecha tras la cual ya no se considera relevante.
        last_shown_at (datetime): Última vez que se mostró al usuario.
        show_count (int): Número de veces que se ha mostrado.
        status (str): Estado: "pending", "shown", "acted_upon", "dismissed", "expired".
        priority (int): Prioridad de visualización (1-10, donde 10 es máxima).
        content (Dict): Contenido de la recomendación.
        context (Dict): Contexto adicional de la recomendación.
        user_interaction (Dict): Interacción del usuario con la recomendación.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        user_id: str = "",
        pattern_id: str = "",
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
        last_shown_at: Optional[datetime] = None,
        show_count: int = 0,
        status: str = "pending",
        priority: int = 5,
        content: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
        user_interaction: Optional[Dict[str, Any]] = None
    ):
        """
        Inicializa una nueva recomendación.
        
        Args:
            id: Identificador único opcional.
            user_id: Usuario destinatario.
            pattern_id: Patrón que generó esta recomendación.
            created_at: Fecha de creación.
            expires_at: Fecha tras la cual ya no se considera relevante.
            last_shown_at: Última vez que se mostró al usuario.
            show_count: Número de veces que se ha mostrado.
            status: Estado de la recomendación.
            priority: Prioridad de visualización.
            content: Contenido de la recomendación.
            context: Contexto adicional de la recomendación.
            user_interaction: Interacción del usuario con la recomendación.
        """
        super().__init__(id)
        self.user_id = user_id
        self.pattern_id = pattern_id
        self.created_at = created_at or datetime.now()
        # Por defecto, las recomendaciones expiran después de 30 días
        self.expires_at = expires_at or (self.created_at + timedelta(days=30))
        self.last_shown_at = last_shown_at
        self.show_count = show_count
        self.status = status
        self.priority = priority
        
        # Contenido de la recomendación
        self.content = content or {
            "title": "",
            "message": "",
            "savingsEstimate": 0,
            "timeframe": "monthly",
            "actionType": "",
            "actionDescription": ""
        }
        
        # Contexto adicional
        self.context = context or {
            "relevantCategories": [],
            "relevantAmounts": {
                "total": 0,
                "average": 0,
                "max": 0
            },
            "temporalInfo": {}
        }
        
        # Interacción del usuario
        self.user_interaction = user_interaction or {
            "seen": False,
            "dismissed": False,
            "dismissReason": None,
            "savedForLater": False,
            "actionTaken": False,
            "feedback": {
                "isHelpful": None,
                "comment": None,
                "rating": None
            }
        }
    
    def mark_as_shown(self) -> None:
        """
        Marca la recomendación como mostrada al usuario.
        """
        self.last_shown_at = datetime.now()
        self.show_count += 1
        self.user_interaction["seen"] = True
        
        if self.status == "pending":
            self.status = "shown"
            
        self.updated_at = datetime.now()
    
    def mark_as_acted_upon(self) -> None:
        """
        Marca la recomendación como actuada por el usuario.
        """
        self.user_interaction["actionTaken"] = True
        self.status = "acted_upon"
        self.updated_at = datetime.now()
    
    def dismiss(self, reason: Optional[str] = None) -> None:
        """
        Marca la recomendación como descartada por el usuario.
        
        Args:
            reason: Razón opcional por la que se descartó.
        """
        self.user_interaction["dismissed"] = True
        self.user_interaction["dismissReason"] = reason
        self.status = "dismissed"
        self.updated_at = datetime.now()
    
    def save_for_later(self) -> None:
        """
        Marca la recomendación como guardada para más tarde.
        """
        self.user_interaction["savedForLater"] = True
        self.updated_at = datetime.now()
    
    def add_feedback(self, is_helpful: bool, rating: Optional[int] = None, comment: Optional[str] = None) -> None:
        """
        Añade feedback del usuario sobre la recomendación.
        
        Args:
            is_helpful: Si el usuario encontró útil la recomendación.
            rating: Valoración opcional (1-5 estrellas).
            comment: Comentario opcional del usuario.
        """
        self.user_interaction["feedback"] = {
            "isHelpful": is_helpful,
            "comment": comment,
            "rating": rating
        }
        self.updated_at = datetime.now()
    
    def is_expired(self) -> bool:
        """
        Verifica si la recomendación ha expirado.
        
        Returns:
            bool: True si ha expirado, False en caso contrario.
        """
        return datetime.now() > self.expires_at
    
    def should_show(self) -> bool:
        """
        Determina si la recomendación debería mostrarse al usuario.
        
        Returns:
            bool: True si debería mostrarse, False en caso contrario.
        """
        if self.is_expired():
            return False
            
        if self.status in ["dismissed", "acted_upon", "expired"]:
            return False
            
        if self.user_interaction["dismissed"] or self.user_interaction["actionTaken"]:
            return False
            
        # Si ya se ha mostrado muchas veces, quizás no mostrarla tan seguido
        if self.show_count > 3:
            # Si se ha mostrado hace menos de una semana, no mostrarla de nuevo
            if self.last_shown_at and (datetime.now() - self.last_shown_at) < timedelta(days=7):
                return False
                
        return True
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Recommendation':
        """
        Crea una instancia de Recomendación a partir de un diccionario.
        
        Args:
            data: Diccionario con los datos de la recomendación.
            
        Returns:
            Recommendation: Una nueva instancia de Recomendación.
        """
        recommendation = cls()
        
        # Se copian todos los atributos del diccionario al modelo
        for key, value in data.items():
            # Convertir fechas si es necesario
            if key in ['created_at', 'expires_at', 'last_shown_at'] and not isinstance(value, datetime):
                if isinstance(value, (int, float)):
                    setattr(recommendation, key, datetime.fromtimestamp(value))
                else:
                    try:
                        setattr(recommendation, key, datetime.fromisoformat(str(value)))
                    except (ValueError, TypeError):
                        # Si es una fecha de expiración, usar un valor futuro
                        if key == 'expires_at':
                            setattr(recommendation, key, datetime.now() + timedelta(days=30))
                        # Para otras fechas, usar la fecha actual
                        else:
                            setattr(recommendation, key, datetime.now())
            else:
                setattr(recommendation, key, value)
        
        return recommendation