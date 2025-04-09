"""
Controlador para gestionar las operaciones relacionadas con análisis financiero.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from models.repositories.transaction_repository import TransactionRepository
from models.repositories.budget_repository import BudgetRepository
from models.repositories.category_repository import CategoryRepository
from models.repositories.pattern_repository import PatternRepository
from services.analysis_service import AnalysisService
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class AnalysisController:
    """
    Controlador para operaciones relacionadas con análisis financiero.
    
    Este controlador maneja la lógica de negocio para generar reportes,
    analizar datos financieros y proporcionar insights sobre las finanzas
    del usuario.
    """
    
    def __init__(self):
        """Inicializa el controlador de análisis financiero."""
        # Inicializar repositorios
        self.transaction_repo = TransactionRepository()
        self.budget_repo = BudgetRepository()
        self.category_repo = CategoryRepository()
        self.pattern_repo = PatternRepository()
        
        # Inicializar servicio de análisis
        self.analysis_service = AnalysisService(
            self.transaction_repo,
            self.budget_repo,
            self.category_repo,
            self.pattern_repo
        )
        
        logger.debug("Controlador de análisis financiero inicializado")
    
    async def get_financial_overview(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene una visión general de la situación financiera del usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Resumen financiero general.
        """
        try:
            logger.info(f"Obteniendo resumen financiero para usuario {user_id}")
            
            # Obtener resumen del servicio de análisis
            overview = await self.analysis_service.get_financial_overview(user_id)
            
            return {
                "success": True,
                "overview": overview
            }
        except Exception as e:
            logger.error(f"Error al obtener resumen financiero: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al obtener resumen financiero: {str(e)}"
            }
    
    async def get_expense_report(
        self,
        user_id: str,
        start_date_str: Optional[str] = None,
        end_date_str: Optional[str] = None,
        group_by: str = "category"
    ) -> Dict[str, Any]:
        """
        Genera un reporte detallado de gastos.
        
        Args:
            user_id: ID del usuario.
            start_date_str: Fecha de inicio en formato ISO (opcional).
            end_date_str: Fecha de fin en formato ISO (opcional).
            group_by: Criterio de agrupación ("category", "day", "week", "month").
            
        Returns:
            Dict[str, Any]: Reporte detallado de gastos.
        """
        try:
            logger.info(f"Generando reporte de gastos para usuario {user_id}")
            
            # Convertir fechas si se proporcionan
            start_date = None
            end_date = None
            
            if start_date_str:
                try:
                    start_date = datetime.fromisoformat(start_date_str)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Formato de fecha de inicio inválido. Use formato ISO."
                    }
            
            if end_date_str:
                try:
                    end_date = datetime.fromisoformat(end_date_str)
                except ValueError:
                    return {
                        "success": False,
                        "error": "Formato de fecha de fin inválido. Use formato ISO."
                    }
            
            # Validar criterio de agrupación
            valid_group_by = ["category", "day", "week", "month"]
            if group_by not in valid_group_by:
                return {
                    "success": False,
                    "error": f"Criterio de agrupación inválido. Opciones válidas: {', '.join(valid_group_by)}"
                }
            
            # Generar reporte
            report = await self.analysis_service.get_expense_report(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                group_by=group_by
            )
            
            return {
                "success": True,
                "report": report
            }
        except Exception as e:
            logger.error(f"Error al generar reporte de gastos: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al generar reporte de gastos: {str(e)}"
            }
    
    async def get_income_expense_ratio(
        self,
        user_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Analiza la relación entre ingresos y gastos a lo largo del tiempo.
        
        Args:
            user_id: ID del usuario.
            months: Número de meses a analizar.
            
        Returns:
            Dict[str, Any]: Análisis de la relación ingresos/gastos.
        """
        try:
            logger.info(f"Analizando relación ingresos/gastos para usuario {user_id}")
            
            # Validar número de meses
            if months <= 0:
                return {
                    "success": False,
                    "error": "El número de meses debe ser mayor que cero."
                }
            
            # Limitar a un máximo razonable (por ejemplo, 24 meses)
            months = min(months, 24)
            
            # Obtener análisis
            ratio_analysis = await self.analysis_service.get_income_expense_ratio(
                user_id=user_id,
                months=months
            )
            
            return {
                "success": True,
                "analysis": ratio_analysis
            }
        except Exception as e:
            logger.error(f"Error al analizar relación ingresos/gastos: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al analizar relación ingresos/gastos: {str(e)}"
            }
    
    async def get_savings_potential(self, user_id: str) -> Dict[str, Any]:
        """
        Analiza el potencial de ahorro basado en patrones detectados.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Análisis del potencial de ahorro.
        """
        try:
            logger.info(f"Analizando potencial de ahorro para usuario {user_id}")
            
            # Obtener análisis
            savings_analysis = await self.analysis_service.get_savings_potential(
                user_id=user_id
            )
            
            return {
                "success": True,
                "analysis": savings_analysis
            }
        except Exception as e:
            logger.error(f"Error al analizar potencial de ahorro: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al analizar potencial de ahorro: {str(e)}"
            }
    
    async def get_category_spending_trends(
        self,
        user_id: str,
        category_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Analiza tendencias de gasto en una categoría específica.
        
        Args:
            user_id: ID del usuario.
            category_id: ID de la categoría a analizar.
            months: Número de meses a analizar.
            
        Returns:
            Dict[str, Any]: Análisis de tendencias para la categoría.
        """
        try:
            logger.info(f"Analizando tendencias para categoría {category_id} de usuario {user_id}")
            
            # Validar número de meses
            if months <= 0:
                return {
                    "success": False,
                    "error": "El número de meses debe ser mayor que cero."
                }
            
            # Limitamos a un máximo razonable
            months = min(months, 24)
            
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # Obtener transacciones de la categoría
            transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
            
            # Filtrar por categoría y solo gastos
            category_transactions = [
                t for t in transactions 
                if t.category == category_id and t.is_expense
            ]
            
            # Si no hay transacciones
            if not category_transactions:
                return {
                    "success": True,
                    "analysis": {
                        "status": "no_data",
                        "message": "No hay datos para esta categoría en el período seleccionado."
                    }
                }
            
            # Obtener información de la categoría
            category = None
            categories = await self.category_repo.get_by_user_id(user_id)
            for cat in categories:
                if cat.id == category_id:
                    category = cat
                    break
            
            category_name = category.name if category else "Categoría desconocida"
            
            # Agrupar por mes
            monthly_data = {}
            
            for transaction in category_transactions:
                month_key = transaction.date.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "total": 0,
                        "count": 0,
                        "min": float('inf'),
                        "max": 0
                    }
                
                monthly_data[month_key]["total"] += transaction.amount
                monthly_data[month_key]["count"] += 1
                monthly_data[month_key]["min"] = min(monthly_data[month_key]["min"], transaction.amount)
                monthly_data[month_key]["max"] = max(monthly_data[month_key]["max"], transaction.amount)
            
            # Ordenar meses
            sorted_months = sorted(monthly_data.keys())
            
            # Preparar datos para el análisis
            trend_data = []
            
            for month_key in sorted_months:
                data = monthly_data[month_key]
                average = data["total"] / data["count"] if data["count"] > 0 else 0
                
                # Fecha en formato legible
                date_obj = datetime.strptime(month_key, '%Y-%m')
                month_name = date_obj.strftime('%b %Y')
                
                trend_data.append({
                    "month": month_key,
                    "month_name": month_name,
                    "total": data["total"],
                    "count": data["count"],
                    "average": average,
                    "min": data["min"] if data["min"] != float('inf') else 0,
                    "max": data["max"]
                })
            
            # Calcular tendencia
            if len(trend_data) >= 2:
                first_month = trend_data[0]["total"]
                last_month = trend_data[-1]["total"]
                trend_percentage = ((last_month - first_month) / first_month * 100) if first_month > 0 else 0
                
                trend_direction = "stable"
                if trend_percentage > 10:
                    trend_direction = "increasing"
                elif trend_percentage < -10:
                    trend_direction = "decreasing"
            else:
                trend_percentage = 0
                trend_direction = "insufficient_data"
            
            # Preparar análisis
            analysis = {
                "status": "success",
                "category_id": category_id,
                "category_name": category_name,
                "months_analyzed": len(trend_data),
                "total_spent": sum(m["total"] for m in trend_data),
                "average_monthly": sum(m["total"] for m in trend_data) / len(trend_data) if trend_data else 0,
                "trend_direction": trend_direction,
                "trend_percentage": trend_percentage,
                "monthly_data": trend_data
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error al analizar tendencias de categoría: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"Error al analizar tendencias de categoría: {str(e)}"
            }