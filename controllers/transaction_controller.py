"""
Controlador para gestionar las operaciones relacionadas con transacciones.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from models.transaction_model import Transaction
from models.repositories.transaction_repository import TransactionRepository
from utils.logger import get_logger
from services.transaction_analysis_service import TransactionAnalysisService
from models.repositories.pattern_repository import PatternRepository

# Logger específico para este módulo
logger = get_logger(__name__)

class TransactionController:
    """
    Controlador para operaciones relacionadas con transacciones.
    
    Este controlador maneja la lógica de negocio para crear, actualizar,
    eliminar y consultar transacciones, así como para analizar patrones de gasto.
    """
    
    def __init__(self):
        """Inicializa el controlador de transacciones."""
        self.transaction_repo = TransactionRepository()
        self.pattern_repo = PatternRepository()
        self.analysis_service = TransactionAnalysisService(
            self.transaction_repo, 
            self.pattern_repo
        )
        logger.debug("Controlador de transacciones inicializado")
    
    async def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea una nueva transacción.
        
        Args:
            transaction_data: Datos de la transacción a crear.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Validar datos mínimos requeridos
            required_fields = ["user_id", "amount", "category", "is_expense"]
            for field in required_fields:
                if field not in transaction_data:
                    return {
                        "success": False, 
                        "error": f"El campo '{field}' es requerido"
                    }
            
            # Crear la transacción
            transaction = Transaction(
                user_id=transaction_data["user_id"],
                amount=float(transaction_data["amount"]),
                category=transaction_data["category"],
                description=transaction_data.get("description", ""),
                is_expense=bool(transaction_data["is_expense"]),
                date=transaction_data.get("date") or datetime.now()
            )
            
            # Guardar en la base de datos
            transaction_id = await self.transaction_repo.add(transaction)
            
            logger.info(f"Transacción creada con ID: {transaction_id}")
            return {
                "success": True,
                "transaction_id": transaction_id,
                "message": "Transacción creada exitosamente"
            }
        except Exception as e:
            logger.error(f"Error al crear transacción: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al crear transacción: {str(e)}"
            }
    
    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Obtiene una transacción por su ID.
        
        Args:
            transaction_id: ID de la transacción a obtener.
            
        Returns:
            Dict[str, Any]: Respuesta con los datos de la transacción.
        """
        try:
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            
            if not transaction:
                return {
                    "success": False,
                    "error": f"Transacción con ID {transaction_id} no encontrada"
                }
            
            # Convertir a diccionario
            transaction_dict = transaction.to_dict()
            
            # Formatear fecha para JSON
            if "date" in transaction_dict and isinstance(transaction_dict["date"], datetime):
                transaction_dict["date"] = transaction_dict["date"].isoformat()
            
            return {
                "success": True,
                "transaction": transaction_dict
            }
        except Exception as e:
            logger.error(f"Error al obtener transacción: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener transacción: {str(e)}"
            }
    
    async def update_transaction(self, transaction_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una transacción existente.
        
        Args:
            transaction_id: ID de la transacción a actualizar.
            update_data: Datos a actualizar.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Verificar que la transacción existe
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            
            if not transaction:
                return {
                    "success": False,
                    "error": f"Transacción con ID {transaction_id} no encontrada"
                }
            
            # Actualizar los campos permitidos
            allowed_fields = ["amount", "category", "description", "is_expense", "date"]
            update_dict = {}
            
            for field in allowed_fields:
                if field in update_data:
                    update_dict[field] = update_data[field]
            
            # Si se cambia la fecha, actualizar metadatos
            if "date" in update_dict:
                # Actualizar la transacción completa para recalcular metadatos
                transaction.date = update_dict["date"]
                transaction.update_metadata()
                
                # Actualizar todo
                result = await self.transaction_repo.update(transaction_id, transaction.to_dict())
            else:
                # Actualizar solo los campos específicos
                result = await self.transaction_repo.update(transaction_id, update_dict)
            
            if result:
                logger.info(f"Transacción {transaction_id} actualizada exitosamente")
                return {
                    "success": True,
                    "message": "Transacción actualizada exitosamente"
                }
            else:
                logger.warning(f"No se pudo actualizar la transacción {transaction_id}")
                return {
                    "success": False,
                    "error": "No se pudo actualizar la transacción"
                }
        except Exception as e:
            logger.error(f"Error al actualizar transacción: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al actualizar transacción: {str(e)}"
            }
    
    async def delete_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """
        Elimina una transacción.
        
        Args:
            transaction_id: ID de la transacción a eliminar.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado de la operación.
        """
        try:
            # Verificar que la transacción existe
            transaction = await self.transaction_repo.get_by_id(transaction_id)
            
            if not transaction:
                return {
                    "success": False,
                    "error": f"Transacción con ID {transaction_id} no encontrada"
                }
            
            # Eliminar la transacción
            result = await self.transaction_repo.delete(transaction_id)
            
            if result:
                logger.info(f"Transacción {transaction_id} eliminada exitosamente")
                return {
                    "success": True,
                    "message": "Transacción eliminada exitosamente"
                }
            else:
                logger.warning(f"No se pudo eliminar la transacción {transaction_id}")
                return {
                    "success": False,
                    "error": "No se pudo eliminar la transacción"
                }
        except Exception as e:
            logger.error(f"Error al eliminar transacción: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al eliminar transacción: {str(e)}"
            }
    
    async def get_user_transactions(
        self, 
        user_id: str, 
        category: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        is_expense: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Obtiene las transacciones de un usuario con filtros opcionales.
        
        Args:
            user_id: ID del usuario.
            category: Filtro por categoría (opcional).
            start_date: Fecha de inicio para filtrar (opcional).
            end_date: Fecha de fin para filtrar (opcional).
            limit: Número máximo de transacciones a retornar (opcional).
            is_expense: Filtro por tipo de transacción (gasto o ingreso) (opcional).
            
        Returns:
            Dict[str, Any]: Respuesta con las transacciones filtradas.
        """
        try:
            transactions = []
            
            # Aplicar filtros según los parámetros proporcionados
            if category:
                # Filtrar por categoría
                transactions = await self.transaction_repo.get_by_user_id_and_category(user_id, category)
            elif start_date and end_date:
                # Filtrar por rango de fechas
                transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                    user_id, start_date, end_date
                )
            elif is_expense is not None:
                # Filtrar por tipo (gasto o ingreso)
                if is_expense:
                    transactions = await self.transaction_repo.get_expenses_by_user_id(user_id)
                else:
                    transactions = await self.transaction_repo.get_income_by_user_id(user_id)
            else:
                # Sin filtros específicos, obtener todas las transacciones del usuario
                transactions = await self.transaction_repo.get_by_user_id(user_id, limit)
            
            # Aplicar filtros adicionales en memoria si es necesario
            if is_expense is not None and (category or (start_date and end_date)):
                transactions = [t for t in transactions if t.is_expense == is_expense]
            
            # Aplicar límite si no se aplicó en la consulta inicial
            if limit and not (transactions and len(transactions) <= limit):
                transactions = transactions[:limit]
            
            # Convertir a formato JSON
            transactions_json = []
            for transaction in transactions:
                transaction_dict = transaction.to_dict()
                
                # Formatear fecha para JSON
                if "date" in transaction_dict and isinstance(transaction_dict["date"], datetime):
                    transaction_dict["date"] = transaction_dict["date"].isoformat()
                
                transactions_json.append(transaction_dict)
            
            logger.debug(f"Obtenidas {len(transactions_json)} transacciones para usuario {user_id}")
            return {
                "success": True,
                "transactions": transactions_json
            }
        except Exception as e:
            logger.error(f"Error al obtener transacciones de usuario: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener transacciones: {str(e)}"
            }
    
    async def get_user_statistics(
        self, 
        user_id: str, 
        period: str = "monthly",
        months: int = 12
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de gastos e ingresos para un usuario.
        
        Args:
            user_id: ID del usuario.
            period: Período para las estadísticas ("monthly", "weekly", "yearly").
            months: Número de meses a considerar para los datos históricos.
            
        Returns:
            Dict[str, Any]: Respuesta con las estadísticas calculadas.
        """
        try:
            # Obtener totales mensuales
            monthly_totals = await self.transaction_repo.get_user_monthly_totals(user_id, months)
            
            if not monthly_totals:
                return {
                    "success": True,
                    "statistics": {
                        "periods": [],
                        "expenses": [],
                        "income": [],
                        "balance": [],
                        "summary": {
                            "total_expenses": 0,
                            "total_income": 0,
                            "total_balance": 0,
                            "average_monthly_expenses": 0,
                            "average_monthly_income": 0
                        }
                    }
                }
            
            # Ordenar por fecha
            sorted_months = sorted(monthly_totals.keys())
            
            # Preparar datos para la respuesta
            periods = []
            expenses = []
            income = []
            balance = []
            
            for month in sorted_months:
                periods.append(month)
                expenses.append(monthly_totals[month]["expenses"])
                income.append(monthly_totals[month]["income"])
                balance.append(monthly_totals[month]["income"] - monthly_totals[month]["expenses"])
            
            # Calcular totales y promedios
            total_expenses = sum(expenses)
            total_income = sum(income)
            total_balance = sum(balance)
            
            average_monthly_expenses = total_expenses / len(sorted_months) if sorted_months else 0
            average_monthly_income = total_income / len(sorted_months) if sorted_months else 0
            
            statistics = {
                "periods": periods,
                "expenses": expenses,
                "income": income,
                "balance": balance,
                "summary": {
                    "total_expenses": total_expenses,
                    "total_income": total_income,
                    "total_balance": total_balance,
                    "average_monthly_expenses": average_monthly_expenses,
                    "average_monthly_income": average_monthly_income
                }
            }
            
            logger.info(f"Estadísticas calculadas para usuario {user_id}")
            return {
                "success": True,
                "statistics": statistics
            }
        except Exception as e:
            logger.error(f"Error al calcular estadísticas: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al calcular estadísticas: {str(e)}"
            }
    
    async def analyze_user_transactions(self, user_id: str) -> Dict[str, Any]:
        """
        Inicia un análisis de transacciones para detectar patrones.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Respuesta con el resultado del análisis.
        """
        try:
            analysis_result = await self.analysis_service.analyze_user_transactions(user_id)
            
            if analysis_result.get("status") == "success":
                logger.info(f"Análisis de transacciones completado para usuario {user_id}")
                return {
                    "success": True,
                    "result": analysis_result
                }
            else:
                logger.warning(f"Error en análisis de transacciones para usuario {user_id}")
                return {
                    "success": False,
                    "error": analysis_result.get("message", "Error en el análisis")
                }
        except Exception as e:
            logger.error(f"Error al analizar transacciones: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al analizar transacciones: {str(e)}"
            }