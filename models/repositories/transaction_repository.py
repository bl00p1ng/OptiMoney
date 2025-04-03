"""
Módulo que contiene el repositorio para operaciones con transacciones.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from models.transaction_model import Transaction
from models.repositories.base_repository import BaseRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(_name_)

class TransactionRepository(BaseRepository[Transaction]):
    """
    Repositorio para operaciones CRUD y consultas relacionadas con transacciones.
    
    Este repositorio extiende el repositorio base para proporcionar
    funcionalidad específica para el modelo de Transacción.
    """
    
    def _init_(self):
        """Inicializa un nuevo repositorio de transacciones."""
        super()._init_("transactions", Transaction)
        logger.debug("Repositorio de transacciones inicializado")
    
    async def get_by_user_id(self, user_id: str, limit: Optional[int] = None) -> List[Transaction]:
        """
        Obtiene las transacciones de un usuario.
        
        Args:
            user_id: ID del usuario.
            limit: Número máximo de transacciones a retornar.
            
        Returns:
            List[Transaction]: Lista de transacciones del usuario.
        """
        try:
            return await self.query({"user_id": user_id}, limit=limit)
        except Exception as e:
            logger.error(f"Error al obtener transacciones para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_by_user_id_and_date_range(
        self, 
        user_id: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Transaction]:
        """
        Obtiene las transacciones de un usuario en un rango de fechas.
        
        Args:
            user_id: ID del usuario.
            start_date: Fecha de inicio del rango.
            end_date: Fecha de fin del rango.
            
        Returns:
            List[Transaction]: Lista de transacciones en el rango de fechas.
        """
        try:
            # En Firestore, las consultas con múltiples condiciones de desigualdad
            # en campos diferentes no están soportadas directamente.
            # Por eso, obtenemos las transacciones del usuario y filtramos por fecha en memoria.
            transactions = await self.get_by_user_id(user_id)
            
            # Filtrar por rango de fechas
            filtered_transactions = [
                t for t in transactions 
                if start_date <= t.date <= end_date
            ]
            
            logger.debug(
                f"Obtenidas {len(filtered_transactions)} transacciones entre {start_date} y {end_date} "
                f"para usuario {user_id}"
            )
            return filtered_transactions
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones por rango de fechas para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def get_by_user_id_and_category(
        self, 
        user_id: str, 
        category: str
    ) -> List[Transaction]:
        """
        Obtiene las transacciones de un usuario por categoría.
        
        Args:
            user_id: ID del usuario.
            category: Categoría de las transacciones.
            
        Returns:
            List[Transaction]: Lista de transacciones de la categoría especificada.
        """
        try:
            return await self.query({"user_id": user_id, "category": category})
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones de categoría {category} para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def get_expenses_by_user_id(self, user_id: str) -> List[Transaction]:
        """
        Obtiene los gastos (transacciones con is_expense=True) de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Transaction]: Lista de gastos del usuario.
        """
        try:
            return await self.query({"user_id": user_id, "is_expense": True})
        except Exception as e:
            logger.error(f"Error al obtener gastos para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_income_by_user_id(self, user_id: str) -> List[Transaction]:
        """
        Obtiene los ingresos (transacciones con is_expense=False) de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Transaction]: Lista de ingresos del usuario.
        """
        try:
            return await self.query({"user_id": user_id, "is_expense": False})
        except Exception as e:
            logger.error(f"Error al obtener ingresos para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_transactions_by_metadata(
        self, 
        user_id: str, 
        metadata_filters: Dict[str, Any]
    ) -> List[Transaction]:
        """
        Obtiene transacciones filtrando por campos de metadatos.
        
        Args:
            user_id: ID del usuario.
            metadata_filters: Diccionario con filtros de metadatos (campo: valor).
            
        Returns:
            List[Transaction]: Lista de transacciones que cumplen los filtros.
        """
        try:
            # Primero obtenemos todas las transacciones del usuario
            transactions = await self.get_by_user_id(user_id)
            
            # Filtramos por los metadatos especificados
            filtered_transactions = []
            for transaction in transactions:
                match = True
                for key, value in metadata_filters.items():
                    # Verificamos si el campo existe en los metadatos y tiene el valor esperado
                    if (transaction.metadata is None or 
                        key not in transaction.metadata or 
                        transaction.metadata[key] != value):
                        match = False
                        break
                
                if match:
                    filtered_transactions.append(transaction)
            
            logger.debug(
                f"Obtenidas {len(filtered_transactions)} transacciones con filtros de metadatos "
                f"{metadata_filters} para usuario {user_id}"
            )
            return filtered_transactions
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones por metadatos para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def get_recurring_transactions(self, user_id: str) -> List[Transaction]:
        """
        Obtiene las transacciones marcadas como recurrentes de un usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            List[Transaction]: Lista de transacciones recurrentes.
        """
        try:
            # Usando el método anterior con un filtro específico
            return await self.get_transactions_by_metadata(
                user_id, 
                {"isRecurring": True}
            )
        except Exception as e:
            logger.error(f"Error al obtener transacciones recurrentes para usuario {user_id}: {str(e)}", exc_info=True)
            return []
    
    async def get_transactions_by_analysis_flag(
        self, 
        user_id: str, 
        flag_name: str, 
        flag_value: bool = True
    ) -> List[Transaction]:
        """
        Obtiene transacciones filtrando por un flag de análisis específico.
        
        Args:
            user_id: ID del usuario.
            flag_name: Nombre del flag de análisis.
            flag_value: Valor esperado del flag (True o False).
            
        Returns:
            List[Transaction]: Lista de transacciones que cumplen el criterio.
        """
        try:
            # Primero obtenemos todas las transacciones del usuario
            transactions = await self.get_by_user_id(user_id)
            
            # Filtramos por el flag de análisis
            filtered_transactions = []
            for transaction in transactions:
                if (transaction.analysis_flags is not None and 
                    flag_name in transaction.analysis_flags and 
                    transaction.analysis_flags[flag_name] == flag_value):
                    filtered_transactions.append(transaction)
            
            logger.debug(
                f"Obtenidas {len(filtered_transactions)} transacciones con flag {flag_name}={flag_value} "
                f"para usuario {user_id}"
            )
            return filtered_transactions
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones por flag de análisis para usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def get_transactions_to_analyze(
        self, 
        user_id: str, 
        max_age: Optional[timedelta] = None
    ) -> List[Transaction]:
        """
        Obtiene transacciones que deberían ser analizadas (no analizadas recientemente).
        
        Args:
            user_id: ID del usuario.
            max_age: Edad máxima del último análisis.
            
        Returns:
            List[Transaction]: Lista de transacciones para analizar.
        """
        try:
            # Si no se especifica max_age, usar 7 días
            if max_age is None:
                max_age = timedelta(days=7)
                
            # Obtener todas las transacciones del usuario
            transactions = await self.get_by_user_id(user_id)
            
            # Filtrar las que no se han analizado o se analizaron hace mucho tiempo
            now = datetime.now()
            to_analyze = []
            
            for transaction in transactions:
                last_analyzed = transaction.analysis_flags.get("lastAnalyzedAt")
                
                # Incluir si nunca se ha analizado o si se analizó hace más de max_age
                if last_analyzed is None or (now - last_analyzed) > max_age:
                    to_analyze.append(transaction)
            
            logger.debug(
                f"Encontradas {len(to_analyze)} transacciones pendientes de análisis "
                f"para usuario {user_id}"
            )
            return to_analyze
        except Exception as e:
            logger.error(
                f"Error al obtener transacciones para analizar de usuario {user_id}: {str(e)}", 
                exc_info=True
            )
            return []
    
    async def update_analysis_flags(
        self, 
        transaction_id: str, 
        flags: Dict[str, Any]
    ) -> bool:
        """
        Actualiza las banderas de análisis de una transacción.
        
        Args:
            transaction_id: ID de la transacción.
            flags: Diccionario con los flags a actualizar.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Crear diccionario para la actualización
            update_data = {}
            for key, value in flags.items():
                update_data[f"analysis_flags.{key}"] = value
            
            update_data["updated_at"] = datetime.now()
            
            result = await self.update(transaction_id, update_data)
            
            if result:
                logger.debug(f"Banderas de análisis actualizadas para transacción {transaction_id}")
            else:
                logger.warning(f"No se pudieron actualizar banderas de análisis para transacción {transaction_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar banderas de análisis: {str(e)}", exc_info=True)
            return False
    
    async def update_metadata(
        self, 
        transaction_id: str, 
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Actualiza los metadatos de una transacción.
        
        Args:
            transaction_id: ID de la transacción.
            metadata: Diccionario con los metadatos a actualizar.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Crear diccionario para la actualización
            update_data = {}
            for key, value in metadata.items():
                update_data[f"metadata.{key}"] = value
            
            update_data["updated_at"] = datetime.now()
            
            result = await self.update(transaction_id, update_data)
            
            if result:
                logger.debug(f"Metadatos actualizados para transacción {transaction_id}")
            else:
                logger.warning(f"No se pudieron actualizar metadatos para transacción {transaction_id}")
                
            return result
        except Exception as e:
            logger.error(f"Error al actualizar metadatos: {str(e)}", exc_info=True)
            return False
    
    async def get_user_monthly_totals(
        self, 
        user_id: str, 
        months: int = 12
    ) -> Dict[str, Dict[str, float]]:
        """
        Calcula los totales mensuales de gastos e ingresos para un usuario.
        
        Args:
            user_id: ID del usuario.
            months: Número de meses a considerar hacia atrás.
            
        Returns:
            Dict[str, Dict[str, float]]: Diccionario con los totales mensuales.
            Formato: {'YYYY-MM': {'expenses': float, 'income': float}}
        """
        try:
            # Calcular fecha de inicio
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # Obtener transacciones en el rango
            transactions = await self.get_by_user_id_and_date_range(user_id, start_date, end_date)
            
            # Inicializar resultados
            monthly_totals = {}
            
            # Agrupar y sumar por mes
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')
                
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = {'expenses': 0.0, 'income': 0.0}
                
                # Sumar al total correspondiente
                if transaction.is_expense:
                    monthly_totals[month_key]['expenses'] += transaction.amount
                else:
                    monthly_totals[month_key]['income'] += transaction.amount
            
            logger.debug(f"Calculados totales mensuales para usuario {user_id} en {len(monthly_totals)} meses")
            return monthly_totals
        except Exception as e:
            logger.error(f"Error al calcular totales mensuales para usuario {user_id}: {str(e)}", exc_info=True)
            return {}
