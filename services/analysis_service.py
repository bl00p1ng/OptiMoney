"""
Módulo que proporciona servicios de análisis financiero general.

Este servicio proporciona análisis de alto nivel sobre las finanzas del usuario,
generando reportes, tendencias, y visualizaciones para la toma de decisiones.
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import calendar
import math

from models.repositories.transaction_repository import TransactionRepository
from models.repositories.budget_repository import BudgetRepository
from models.repositories.category_repository import CategoryRepository
from models.repositories.pattern_repository import PatternRepository
from models.transaction_model import Transaction
from models.category_model import Category
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class AnalysisService:
    """
    Servicio para análisis financiero general y generación de reportes.
    
    Este servicio proporciona funcionalidades para analizar el estado financiero
    del usuario, generar reportes y preparar datos para visualizaciones.
    """
    
    def __init__(
        self,
        transaction_repository: TransactionRepository,
        budget_repository: BudgetRepository,
        category_repository: CategoryRepository,
        pattern_repository: PatternRepository
    ):
        """
        Inicializa el servicio de análisis.
        
        Args:
            transaction_repository: Repositorio de transacciones.
            budget_repository: Repositorio de presupuestos.
            category_repository: Repositorio de categorías.
            pattern_repository: Repositorio de patrones.
        """
        self.transaction_repo = transaction_repository
        self.budget_repo = budget_repository
        self.category_repo = category_repository
        self.pattern_repo = pattern_repository
        
        logger.info("Servicio de análisis financiero inicializado")
    
    async def get_financial_overview(self, user_id: str) -> Dict[str, Any]:
        """
        Genera un resumen general de la situación financiera del usuario.
        
        Este método proporciona una visión general de los ingresos, gastos,
        balance, tendencias y presupuestos del usuario.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Resumen financiero del usuario.
        """
        try:
            # Obtener datos para análisis de los últimos 3 meses
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            # Obtener transacciones del período
            transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
            
            # Si no hay transacciones, devolver un resumen vacío
            if not transactions:
                logger.info(f"No hay transacciones para el usuario {user_id} en el período analizado")
                return self._create_empty_overview()
            
            # Obtener presupuestos activos
            budgets = await self.budget_repo.get_active_budgets(user_id)
            
            # Obtener categorías
            categories = await self.category_repo.get_by_user_id(user_id)
            
            # Calcular resumen financiero
            current_month = end_date.replace(day=1)
            previous_month = (current_month - timedelta(days=1)).replace(day=1)
            
            current_month_data = self._calculate_monthly_summary(
                transactions, current_month
            )
            previous_month_data = self._calculate_monthly_summary(
                transactions, previous_month
            )
            
            # Calcular balance general
            total_income = sum(t.amount for t in transactions if not t.is_expense)
            total_expenses = sum(t.amount for t in transactions if t.is_expense)
            balance = total_income - total_expenses
            
            # Calcular distribución de gastos por categoría
            category_distribution = self._calculate_category_distribution(
                transactions, categories
            )
            
            # Calcular tendencias mensuales
            monthly_trends = self._calculate_monthly_trends(transactions)
            
            # Obtener estado de presupuestos
            budget_status = self._get_budget_status(budgets, categories)
            
            # Crear resumen financiero
            overview = {
                "balance": {
                    "total_income": total_income,
                    "total_expenses": total_expenses,
                    "net_balance": balance
                },
                "current_month": current_month_data,
                "previous_month": previous_month_data,
                "month_comparison": self._compare_months(
                    current_month_data, previous_month_data
                ),
                "category_distribution": category_distribution,
                "monthly_trends": monthly_trends,
                "budget_status": budget_status,
                "financial_health": self._calculate_financial_health(
                    current_month_data, previous_month_data, budget_status
                )
            }
            
            logger.info(f"Resumen financiero generado para usuario {user_id}")
            return overview
        except Exception as e:
            logger.error(f"Error al generar resumen financiero: {str(e)}", exc_info=True)
            return self._create_empty_overview()
    
    def _create_empty_overview(self) -> Dict[str, Any]:
        """
        Crea un resumen financiero vacío cuando no hay datos.
        
        Returns:
            Dict[str, Any]: Estructura de resumen vacía.
        """
        return {
            "balance": {
                "total_income": 0,
                "total_expenses": 0,
                "net_balance": 0
            },
            "current_month": {
                "income": 0,
                "expenses": 0,
                "balance": 0,
                "top_expense_categories": []
            },
            "previous_month": {
                "income": 0,
                "expenses": 0,
                "balance": 0,
                "top_expense_categories": []
            },
            "month_comparison": {
                "income_change": {
                    "amount": 0,
                    "percentage": 0
                },
                "expense_change": {
                    "amount": 0,
                    "percentage": 0
                },
                "balance_change": {
                    "amount": 0,
                    "percentage": 0
                }
            },
            "category_distribution": [],
            "monthly_trends": {
                "labels": [],
                "income": [],
                "expenses": [],
                "balance": []
            },
            "budget_status": [],
            "financial_health": {
                "score": 0,
                "status": "Sin datos suficientes",
                "insights": ["No hay suficientes datos para generar insights financieros."]
            }
        }
    
    def _calculate_monthly_summary(
        self, 
        transactions: List[Transaction], 
        month_date: datetime
    ) -> Dict[str, Any]:
        """
        Calcula un resumen financiero para un mes específico.
        
        Args:
            transactions: Lista de transacciones.
            month_date: Fecha del mes a analizar.
            
        Returns:
            Dict[str, Any]: Resumen del mes.
        """
        # Filtrar transacciones del mes
        start_of_month = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Calcular el último día del mes
        _, last_day = calendar.monthrange(month_date.year, month_date.month)
        end_of_month = month_date.replace(
            day=last_day, hour=23, minute=59, second=59, microsecond=999999
        )
        
        # Filtrar transacciones del mes
        month_transactions = [
            t for t in transactions
            if start_of_month <= t.date <= end_of_month
        ]
        
        # Si no hay transacciones en el mes
        if not month_transactions:
            return {
                "income": 0,
                "expenses": 0,
                "balance": 0,
                "top_expense_categories": []
            }
        
        # Calcular ingresos y gastos
        income = sum(t.amount for t in month_transactions if not t.is_expense)
        expenses = sum(t.amount for t in month_transactions if t.is_expense)
        balance = income - expenses
        
        # Calcular top categorías de gasto
        category_expenses = defaultdict(float)
        for transaction in month_transactions:
            if transaction.is_expense:
                category_expenses[transaction.category] += transaction.amount
        
        # Ordenar categorías por monto
        top_categories = sorted(
            [{"category": cat, "amount": amount} 
             for cat, amount in category_expenses.items()],
            key=lambda x: x["amount"],
            reverse=True
        )[:5]  # Top 5 categorías
        
        return {
            "income": income,
            "expenses": expenses,
            "balance": balance,
            "top_expense_categories": top_categories
        }
    
    def _compare_months(
        self, 
        current_month: Dict[str, Any], 
        previous_month: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compara los datos financieros entre dos meses.
        
        Args:
            current_month: Datos del mes actual.
            previous_month: Datos del mes anterior.
            
        Returns:
            Dict[str, Any]: Comparación entre los dos meses.
        """
        # Calcular cambios en ingresos
        income_change = current_month["income"] - previous_month["income"]
        income_percentage = (
            (income_change / previous_month["income"]) * 100 
            if previous_month["income"] > 0 else 0
        )
        
        # Calcular cambios en gastos
        expense_change = current_month["expenses"] - previous_month["expenses"]
        expense_percentage = (
            (expense_change / previous_month["expenses"]) * 100 
            if previous_month["expenses"] > 0 else 0
        )
        
        # Calcular cambios en balance
        balance_change = current_month["balance"] - previous_month["balance"]
        balance_percentage = 0
        
        # Calcular porcentaje de cambio en balance (considerando signos)
        if previous_month["balance"] != 0:
            if (previous_month["balance"] > 0 and current_month["balance"] > 0) or \
               (previous_month["balance"] < 0 and current_month["balance"] < 0):
                # Mismo signo, cálculo normal
                balance_percentage = (balance_change / abs(previous_month["balance"])) * 100
            else:
                # Cambio de signo, marcar como cambio significativo
                balance_percentage = 100 if balance_change > 0 else -100
        
        return {
            "income_change": {
                "amount": income_change,
                "percentage": round(income_percentage, 1)
            },
            "expense_change": {
                "amount": expense_change,
                "percentage": round(expense_percentage, 1)
            },
            "balance_change": {
                "amount": balance_change,
                "percentage": round(balance_percentage, 1)
            }
        }
    
    def _calculate_category_distribution(
        self, 
        transactions: List[Transaction],
        categories: List[Category]
    ) -> List[Dict[str, Any]]:
        """
        Calcula la distribución de gastos por categoría.
        
        Args:
            transactions: Lista de transacciones.
            categories: Lista de categorías.
            
        Returns:
            List[Dict[str, Any]]: Distribución de gastos por categoría.
        """
        # Crear un mapa de IDs de categoría a nombres
        category_map = {cat.id: cat for cat in categories}
        
        # Filtrar solo gastos
        expenses = [t for t in transactions if t.is_expense]
        
        # Si no hay gastos
        if not expenses:
            return []
        
        # Calcular total por categoría
        category_totals = defaultdict(float)
        for transaction in expenses:
            category_totals[transaction.category] += transaction.amount
        
        # Calcular porcentaje del total
        total_expenses = sum(category_totals.values())
        
        distribution = []
        for category_id, amount in category_totals.items():
            percentage = (amount / total_expenses) * 100 if total_expenses > 0 else 0
            
            # Obtener información de la categoría
            category_info = category_map.get(category_id, None)
            category_name = category_info.name if category_info else category_id
            category_color = category_info.color if category_info else "#CCCCCC"
            
            distribution.append({
                "category_id": category_id,
                "name": category_name,
                "amount": amount,
                "percentage": round(percentage, 1),
                "color": category_color
            })
        
        # Ordenar por monto descendente
        distribution.sort(key=lambda x: x["amount"], reverse=True)
        
        return distribution
    
    def _calculate_monthly_trends(
        self, 
        transactions: List[Transaction]
    ) -> Dict[str, List[Any]]:
        """
        Calcula tendencias mensuales de ingresos, gastos y balance.
        
        Args:
            transactions: Lista de transacciones.
            
        Returns:
            Dict[str, List[Any]]: Tendencias mensuales para gráficos.
        """
        # Obtener rango de meses en las transacciones
        if not transactions:
            return {
                "labels": [],
                "income": [],
                "expenses": [],
                "balance": []
            }
        
        # Agrupar transacciones por mes
        month_data = defaultdict(lambda: {"income": 0, "expenses": 0})
        
        for transaction in transactions:
            month_key = transaction.date.strftime('%Y-%m')
            
            if transaction.is_expense:
                month_data[month_key]["expenses"] += transaction.amount
            else:
                month_data[month_key]["income"] += transaction.amount
        
        # Ordenar meses
        sorted_months = sorted(month_data.keys())
        
        # Formato más amigable para las etiquetas
        labels = []
        for month_key in sorted_months:
            year, month = month_key.split('-')
            month_name = datetime(int(year), int(month), 1).strftime('%b %Y')
            labels.append(month_name)
        
        # Preparar series de datos
        income_data = []
        expense_data = []
        balance_data = []
        
        for month_key in sorted_months:
            data = month_data[month_key]
            income = data["income"]
            expenses = data["expenses"]
            balance = income - expenses
            
            income_data.append(income)
            expense_data.append(expenses)
            balance_data.append(balance)
        
        return {
            "labels": labels,
            "income": income_data,
            "expenses": expense_data,
            "balance": balance_data
        }
    
    def _get_budget_status(
        self, 
        budgets: List[Any], 
        categories: List[Category]
    ) -> List[Dict[str, Any]]:
        """
        Obtiene el estado actual de los presupuestos.
        
        Args:
            budgets: Lista de presupuestos.
            categories: Lista de categorías.
            
        Returns:
            List[Dict[str, Any]]: Estado de los presupuestos.
        """
        # Crear un mapa de IDs de categoría a nombres
        category_map = {cat.id: cat.name for cat in categories}
        
        budget_status = []
        
        for budget in budgets:
            category_id = budget.category_id
            category_name = category_map.get(category_id, "Categoría desconocida")
            
            # Calcular porcentaje de uso
            percentage = budget.get_usage_percentage()
            
            # Determinar estado
            status = "normal"
            if percentage >= 100:
                status = "exceeded"
            elif percentage >= budget.alert_threshold:
                status = "warning"
            
            budget_status.append({
                "budget_id": budget.id,
                "category_id": category_id,
                "category_name": category_name,
                "amount": budget.amount,
                "current_amount": budget.current_amount,
                "percentage": percentage,
                "status": status,
                "period": budget.period
            })
        
        # Ordenar por porcentaje de uso descendente
        budget_status.sort(key=lambda x: x["percentage"], reverse=True)
        
        return budget_status
    
    def _calculate_financial_health(
        self, 
        current_month: Dict[str, Any], 
        previous_month: Dict[str, Any],
        budget_status: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calcula un indicador de salud financiera del usuario.
        
        Este método evalúa múltiples factores para determinar la
        salud financiera general del usuario y proporciona insights.
        
        Args:
            current_month: Datos del mes actual.
            previous_month: Datos del mes anterior.
            budget_status: Estado de los presupuestos.
            
        Returns:
            Dict[str, Any]: Información sobre la salud financiera.
        """
        # Inicializar score y factores
        base_score = 50  # Punto medio
        factors = []
        insights = []
        
        # Factor 1: Balance mensual positivo o negativo
        if current_month["balance"] > 0:
            base_score += 10
            factors.append(("balance_positive", 10))
            insights.append("Tu balance mensual es positivo, lo cual es excelente.")
        else:
            base_score -= 10
            factors.append(("balance_negative", -10))
            insights.append("Tu balance mensual es negativo. Intenta reducir gastos o aumentar ingresos.")
        
        # Factor 2: Tendencia del balance (mejora o empeora)
        if current_month["balance"] > previous_month["balance"]:
            base_score += 5
            factors.append(("balance_improving", 5))
            insights.append("Tu balance está mejorando comparado con el mes anterior.")
        elif current_month["balance"] < previous_month["balance"]:
            base_score -= 5
            factors.append(("balance_worsening", -5))
            insights.append("Tu balance ha empeorado comparado con el mes anterior.")
        
        # Factor 3: Ratio ingresos/gastos
        if current_month["income"] > 0:
            income_expense_ratio = current_month["income"] / max(current_month["expenses"], 1)
            
            if income_expense_ratio >= 1.5:
                base_score += 15
                factors.append(("high_income_ratio", 15))
                insights.append("Tus ingresos superan significativamente tus gastos, lo cual es muy saludable.")
            elif income_expense_ratio >= 1.2:
                base_score += 10
                factors.append(("good_income_ratio", 10))
                insights.append("La proporción entre ingresos y gastos es buena.")
            elif income_expense_ratio >= 1.0:
                base_score += 5
                factors.append(("balanced_income_ratio", 5))
                insights.append("Tus ingresos cubren justamente tus gastos. Considera aumentar tu margen de ahorro.")
            else:
                base_score -= 10
                factors.append(("negative_income_ratio", -10))
                insights.append("Tus gastos superan tus ingresos, lo cual es preocupante.")
        
        # Factor 4: Cumplimiento de presupuestos
        exceeded_budgets = [b for b in budget_status if b["status"] == "exceeded"]
        warning_budgets = [b for b in budget_status if b["status"] == "warning"]
        
        if budget_status:
            if not exceeded_budgets and not warning_budgets:
                base_score += 10
                factors.append(("budgets_under_control", 10))
                insights.append("Todos tus presupuestos están bajo control. ¡Excelente trabajo!")
            elif not exceeded_budgets and warning_budgets:
                base_score += 5
                factors.append(("budgets_warning", 5))
                insights.append("Algunos presupuestos están cerca de su límite. Monitorea estos gastos.")
            elif exceeded_budgets:
                num_exceeded = len(exceeded_budgets)
                penalty = min(num_exceeded * 5, 15)  # Máximo 15 puntos de penalización
                
                base_score -= penalty
                factors.append(("budgets_exceeded", -penalty))
                
                if num_exceeded == 1:
                    insights.append(f"Has excedido tu presupuesto en {exceeded_budgets[0]['category_name']}.")
                else:
                    insights.append(f"Has excedido {num_exceeded} presupuestos. Revisa tus gastos.")
        
        # Asegurar que el score esté entre 0 y 100
        final_score = max(0, min(100, base_score))
        
        # Determinar estado general
        if final_score >= 80:
            status = "Excelente"
        elif final_score >= 60:
            status = "Bueno"
        elif final_score >= 40:
            status = "Regular"
        elif final_score >= 20:
            status = "Necesita atención"
        else:
            status = "Crítico"
        
        return {
            "score": final_score,
            "status": status,
            "factors": factors,
            "insights": insights
        }
    
    async def get_expense_report(
        self, 
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        group_by: str = "category"
    ) -> Dict[str, Any]:
        """
        Genera un reporte detallado de gastos.
        
        Args:
            user_id: ID del usuario.
            start_date: Fecha de inicio del reporte (opcional).
            end_date: Fecha de fin del reporte (opcional).
            group_by: Criterio de agrupación ("category", "day", "week", "month").
            
        Returns:
            Dict[str, Any]: Reporte de gastos.
        """
        try:
            # Si no se especifican fechas, usar último mes
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Obtener transacciones del período
            transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
            
            # Filtrar solo gastos
            expenses = [t for t in transactions if t.is_expense]
            
            # Si no hay gastos, devolver reporte vacío
            if not expenses:
                return {
                    "total_expenses": 0,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "group_by": group_by,
                    "groups": []
                }
            
            # Calcular total de gastos
            total_expenses = sum(t.amount for t in expenses)
            
            # Agrupar gastos según criterio
            if group_by == "category":
                groups = self._group_expenses_by_category(expenses, user_id)
            elif group_by == "day":
                groups = self._group_expenses_by_time(expenses, "day")
            elif group_by == "week":
                groups = self._group_expenses_by_time(expenses, "week")
            elif group_by == "month":
                groups = self._group_expenses_by_time(expenses, "month")
            else:
                # Por defecto, agrupar por categoría
                groups = self._group_expenses_by_category(expenses, user_id)
            
            # Crear reporte
            report = {
                "total_expenses": total_expenses,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by,
                "groups": groups
            }
            
            logger.info(f"Reporte de gastos generado para usuario {user_id}")
            return report
        except Exception as e:
            logger.error(f"Error al generar reporte de gastos: {str(e)}", exc_info=True)
            return {
                "total_expenses": 0,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "group_by": group_by,
                "groups": [],
                "error": str(e)
            }
    
    async def _group_expenses_by_category(
        self, 
        expenses: List[Transaction],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Agrupa gastos por categoría.
        
        Args:
            expenses: Lista de transacciones de gasto.
            user_id: ID del usuario para obtener info de categorías.
            
        Returns:
            List[Dict[str, Any]]: Gastos agrupados por categoría.
        """
        # Obtener categorías
        categories = await self.category_repo.get_by_user_id(user_id)
        category_map = {cat.id: cat for cat in categories}
        
        # Agrupar por categoría
        category_totals = defaultdict(float)
        category_transactions = defaultdict(list)
        
        for transaction in expenses:
            category_totals[transaction.category] += transaction.amount
            category_transactions[transaction.category].append(transaction)
        
        # Crear lista de grupos
        groups = []
        for category_id, total in category_totals.items():
            # Obtener información de la categoría
            category_info = category_map.get(category_id, None)
            category_name = category_info.name if category_info else "Categoría desconocida"
            category_color = category_info.color if category_info else "#CCCCCC"
            
            # Obtener transacciones en esta categoría
            transactions_in_category = category_transactions[category_id]
            
            # Ordenar transacciones por fecha (más recientes primero)
            sorted_transactions = sorted(
                transactions_in_category,
                key=lambda t: t.date,
                reverse=True
            )
            
            # Formatear transacciones para la respuesta
            formatted_transactions = []
            for t in sorted_transactions:
                formatted_transactions.append({
                    "id": t.id,
                    "date": t.date.isoformat(),
                    "amount": t.amount,
                    "description": t.description
                })
            
            groups.append({
                "id": category_id,
                "name": category_name,
                "color": category_color,
                "total": total,
                "count": len(transactions_in_category),
                "transactions": formatted_transactions
            })
        
        # Ordenar grupos por total (mayor a menor)
        groups.sort(key=lambda g: g["total"], reverse=True)
        
        return groups
    
    def _group_expenses_by_time(
        self, 
        expenses: List[Transaction],
        period: str
    ) -> List[Dict[str, Any]]:
        """
        Agrupa gastos por período de tiempo.
        
        Args:
            expenses: Lista de transacciones de gasto.
            period: Período de agrupación ("day", "week", "month").
            
        Returns:
            List[Dict[str, Any]]: Gastos agrupados por período.
        """
        # Diccionarios para agrupar
        period_totals = defaultdict(float)
        period_transactions = defaultdict(list)
        
        for transaction in expenses:
            # Determinar clave del período
            if period == "day":
                period_key = transaction.date.strftime('%Y-%m-%d')
                display_name = transaction.date.strftime('%d %b %Y')
            elif period == "week":
                # Obtener el lunes de la semana
                week_start = transaction.date - timedelta(days=transaction.date.weekday())
                period_key = week_start.strftime('%Y-%m-%d')
                display_name = f"Semana del {week_start.strftime('%d %b %Y')}"
            elif period == "month":
                period_key = transaction.date.strftime('%Y-%m')
                display_name = transaction.date.strftime('%b %Y')
            else:
                period_key = transaction.date.strftime('%Y-%m-%d')
                display_name = transaction.date.strftime('%d %b %Y')
            
            # Agregar a los grupos
            period_totals[period_key] += transaction.amount
            period_transactions[period_key].append({
                "id": transaction.id,
                "date": transaction.date.isoformat(),
                "amount": transaction.amount,
                "description": transaction.description,
                "category": transaction.category
            })
        
        # Crear lista de grupos
        groups = []
        for period_key, total in period_totals.items():
            # Determinar nombre a mostrar
            if period == "day":
                date_obj = datetime.strptime(period_key, '%Y-%m-%d')
                display_name = date_obj.strftime('%d %b %Y')
            elif period == "week":
                date_obj = datetime.strptime(period_key, '%Y-%m-%d')
                display_name = f"Semana del {date_obj.strftime('%d %b %Y')}"
            elif period == "month":
                date_obj = datetime.strptime(period_key, '%Y-%m')
                display_name = date_obj.strftime('%b %Y')
            else:
                display_name = period_key
            
            groups.append({
                "id": period_key,
                "name": display_name,
                "total": total,
                "count": len(period_transactions[period_key]),
                "transactions": period_transactions[period_key]
            })
        
        # Ordenar grupos por fecha (más recientes primero)
        groups.sort(key=lambda g: g["id"], reverse=True)
        
        return groups
    
    async def get_income_expense_ratio(
        self, 
        user_id: str,
        months: int = 6
    ) -> Dict[str, Any]:
        """
        Calcula la relación entre ingresos y gastos a lo largo del tiempo.
        
        Args:
            user_id: ID del usuario.
            months: Número de meses a analizar.
            
        Returns:
            Dict[str, Any]: Análisis de la relación ingresos/gastos.
        """
        try:
            # Calcular fechas
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months)
            
            # Obtener transacciones
            transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
            
            # Si no hay transacciones
            if not transactions:
                return {
                    "status": "no_data",
                    "message": "No hay suficientes datos para este análisis",
                    "months_analyzed": 0,
                    "overall_ratio": 0,
                    "monthly_data": []
                }
            
            # Agrupar por mes
            monthly_data = {}
            
            for transaction in transactions:
                month_key = transaction.date.strftime('%Y-%m')
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {"income": 0, "expenses": 0}
                
                if transaction.is_expense:
                    monthly_data[month_key]["expenses"] += transaction.amount
                else:
                    monthly_data[month_key]["income"] += transaction.amount
            
            # Ordenar meses
            sorted_months = sorted(monthly_data.keys())
            
            # Calcular ratios mensuales
            monthly_ratios = []
            total_income = 0
            total_expenses = 0
            
            for month_key in sorted_months:
                income = monthly_data[month_key]["income"]
                expenses = monthly_data[month_key]["expenses"]
                
                # Sumar a totales
                total_income += income
                total_expenses += expenses
                
                # Calcular ratio (evitar división por cero)
                ratio = income / expenses if expenses > 0 else 0
                
                # Fecha en formato legible
                date_obj = datetime.strptime(month_key, '%Y-%m')
                month_name = date_obj.strftime('%b %Y')
                
                monthly_ratios.append({
                    "month": month_key,
                    "month_name": month_name,
                    "income": income,
                    "expenses": expenses,
                    "ratio": ratio,
                    "status": self._get_ratio_status(ratio)
                })
            
            # Calcular ratio general
            overall_ratio = total_income / total_expenses if total_expenses > 0 else 0
            
            # Análisis y recomendaciones
            insights = self._get_ratio_insights(monthly_ratios, overall_ratio)
            
            return {
                "status": "success",
                "months_analyzed": len(monthly_ratios),
                "overall_ratio": overall_ratio,
                "overall_status": self._get_ratio_status(overall_ratio),
                "monthly_data": monthly_ratios,
                "insights": insights
            }
        except Exception as e:
            logger.error(f"Error al calcular relación ingresos/gastos: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error al calcular relación: {str(e)}",
                "months_analyzed": 0,
                "overall_ratio": 0,
                "monthly_data": []
            }
    
    def _get_ratio_status(self, ratio: float) -> str:
        """
        Determina el estado de un ratio ingresos/gastos.
        
        Args:
            ratio: Valor del ratio.
            
        Returns:
            str: Estado del ratio.
        """
        if ratio == 0:
            return "no_income"
        elif ratio < 1:
            return "deficit"
        elif ratio < 1.2:
            return "breakeven"
        elif ratio < 1.5:
            return "good"
        else:
            return "excellent"
    
    def _get_ratio_insights(
        self, 
        monthly_ratios: List[Dict[str, Any]], 
        overall_ratio: float
    ) -> List[str]:
        """
        Genera insights sobre la relación ingresos/gastos.
        
        Args:
            monthly_ratios: Datos mensuales de ratios.
            overall_ratio: Ratio general para todo el período.
            
        Returns:
            List[str]: Lista de insights.
        """
        insights = []
        
        # Si no hay datos suficientes
        if not monthly_ratios or len(monthly_ratios) < 2:
            insights.append("No hay suficientes datos para generar insights detallados.")
            return insights
        
        # Insight general
        if overall_ratio < 1:
            insights.append(
                "En general, tus gastos superan tus ingresos. Es importante revisar y ajustar tu presupuesto."
            )
        elif overall_ratio < 1.2:
            insights.append(
                "En general, estás cerca del punto de equilibrio. Considera reducir gastos para aumentar tu margen de ahorro."
            )
        elif overall_ratio < 1.5:
            insights.append(
                "En general, tienes un buen balance entre ingresos y gastos. Puedes considerar aumentar tus ahorros."
            )
        else:
            insights.append(
                "En general, tienes una excelente relación ingresos/gastos. Considera invertir parte de tu excedente."
            )
        
        # Analizar tendencia
        recent_months = monthly_ratios[-3:] if len(monthly_ratios) >= 3 else monthly_ratios
        
        ratios = [m["ratio"] for m in recent_months]
        if all(r > r_prev for r, r_prev in zip(ratios[1:], ratios[:-1])):
            insights.append("Tu relación ingresos/gastos ha mejorado consistentemente en los últimos meses.")
        elif all(r < r_prev for r, r_prev in zip(ratios[1:], ratios[:-1])):
            insights.append("Tu relación ingresos/gastos ha disminuido consistentemente. Presta atención a esta tendencia.")
        
        # Detectar meses críticos
        deficit_months = [m for m in monthly_ratios if m["status"] == "deficit"]
        if deficit_months:
            recent_deficit = any(m["status"] == "deficit" for m in recent_months)
            if recent_deficit:
                insights.append("Has tenido déficit en meses recientes. Revisa tus gastos con atención.")
            else:
                insights.append("Tuviste meses con déficit, pero has logrado mejorarlo. ¡Sigue así!")
        
        # Recomendación personalizada
        if overall_ratio < 1:
            insights.append("Recomendación: Identifica gastos no esenciales que puedas reducir para equilibrar tu presupuesto.")
        elif overall_ratio < 1.2:
            insights.append("Recomendación: Intenta aumentar tu ratio a al menos 1.2 para tener un margen de ahorro saludable.")
        elif overall_ratio < 1.5:
            insights.append("Recomendación: Mantén este ritmo y considera destinar el excedente a un fondo de emergencia o inversiones.")
        else:
            insights.append("Recomendación: Considera estrategias de inversión para hacer crecer tu patrimonio a largo plazo.")
        
        return insights
    
    async def get_savings_potential(self, user_id: str) -> Dict[str, Any]:
        """
        Calcula el potencial de ahorro basado en patrones detectados.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Análisis del potencial de ahorro.
        """
        try:
            # Obtener patrones activos
            patterns = await self.pattern_repo.get_active_patterns(user_id)
            
            # Si no hay patrones
            if not patterns:
                return {
                    "status": "no_patterns",
                    "message": "No se han detectado patrones para calcular ahorro potencial",
                    "total_monthly_potential": 0,
                    "total_yearly_potential": 0,
                    "patterns_by_type": {},
                    "top_opportunities": []
                }
            
            # Calcular ahorro potencial total
            total_monthly = 0
            total_yearly = 0
            
            # Agrupar patrones por tipo
            patterns_by_type = defaultdict(list)
            
            for pattern in patterns:
                pattern_type = pattern.type
                monthly_savings = pattern.savings_potential.get("estimatedMonthly", 0)
                yearly_savings = pattern.savings_potential.get("estimatedYearly", 0)
                
                # Sumar al total
                total_monthly += monthly_savings
                total_yearly += yearly_savings
                
                # Agregar al grupo correspondiente
                patterns_by_type[pattern_type].append({
                    "id": pattern.id,
                    "category": pattern.category,
                    "monthly_savings": monthly_savings,
                    "yearly_savings": yearly_savings,
                    "optimization_percentage": pattern.savings_potential.get("optimizationPercentage", 0),
                    "confidence": pattern.metrics.get("confidence", 0)
                })
            
            # Calcular resumen por tipo
            summary_by_type = {}
            for pattern_type, pattern_list in patterns_by_type.items():
                type_monthly = sum(p["monthly_savings"] for p in pattern_list)
                type_yearly = sum(p["yearly_savings"] for p in pattern_list)
                
                summary_by_type[pattern_type] = {
                    "count": len(pattern_list),
                    "monthly_potential": type_monthly,
                    "yearly_potential": type_yearly,
                    "percentage_of_total": (type_monthly / total_monthly * 100) if total_monthly > 0 else 0
                }
            
            # Obtener top oportunidades de ahorro
            all_patterns = []
            for type_patterns in patterns_by_type.values():
                all_patterns.extend(type_patterns)
            
            # Ordenar por ahorro mensual potencial
            top_opportunities = sorted(
                all_patterns,
                key=lambda p: p["monthly_savings"],
                reverse=True
            )[:5]  # Top 5 oportunidades
            
            # Traducir tipos de patrones para la interfaz
            pattern_type_names = {
                "micro_expense": "Micro-gastos",
                "recurring": "Gastos recurrentes",
                "temporal": "Patrones temporales",
                "category_deviation": "Desviaciones por categoría"
            }
            
            # Formatear respuesta
            result = {
                "status": "success",
                "total_monthly_potential": total_monthly,
                "total_yearly_potential": total_yearly,
                "patterns_count": len(patterns),
                "patterns_by_type": {
                    pattern_type_names.get(t, t): data
                    for t, data in summary_by_type.items()
                },
                "top_opportunities": top_opportunities
            }
            
            # Añadir insights
            result["insights"] = self._get_savings_insights(result)
            
            return result
        except Exception as e:
            logger.error(f"Error al calcular potencial de ahorro: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"Error al calcular potencial de ahorro: {str(e)}",
                "total_monthly_potential": 0,
                "total_yearly_potential": 0,
                "patterns_by_type": {},
                "top_opportunities": []
            }
    
    def _get_savings_insights(self, savings_data: Dict[str, Any]) -> List[str]:
        """
        Genera insights sobre el potencial de ahorro.
        
        Args:
            savings_data: Datos del análisis de ahorro.
            
        Returns:
            List[str]: Lista de insights.
        """
        insights = []
        
        # Insight general
        monthly_potential = savings_data["total_monthly_potential"]
        yearly_potential = savings_data["total_yearly_potential"]
        
        insights.append(
            f"Podrías ahorrar aproximadamente {monthly_potential:,.0f} al mes "
            f"({yearly_potential:,.0f} al año) optimizando tus gastos."
        )
        
        # Insights por tipo de patrón
        patterns_by_type = savings_data["patterns_by_type"]
        
        # Si hay micro-gastos
        if "Micro-gastos" in patterns_by_type:
            micro_data = patterns_by_type["Micro-gastos"]
            insights.append(
                f"Los pequeños gastos suman {micro_data['monthly_potential']:,.0f} al mes. "
                f"Reducirlos podría representar el {micro_data['percentage_of_total']:.1f}% de tu ahorro potencial."
            )
        
        # Si hay gastos recurrentes
        if "Gastos recurrentes" in patterns_by_type:
            recurring_data = patterns_by_type["Gastos recurrentes"]
            insights.append(
                f"Tienes {recurring_data['count']} servicios o gastos recurrentes que podrías optimizar, "
                f"ahorrando hasta {recurring_data['monthly_potential']:,.0f} mensuales."
            )
        
        # Si hay patrones temporales
        if "Patrones temporales" in patterns_by_type:
            temporal_data = patterns_by_type["Patrones temporales"]
            insights.append(
                f"Tus patrones de gasto en ciertos días u horarios representan "
                f"{temporal_data['monthly_potential']:,.0f} de ahorro potencial mensual."
            )
        
        # Insight final
        if monthly_potential > 0:
            insights.append(
                "Revisa las recomendaciones específicas en la sección 'Recomendaciones' "
                "para ver acciones concretas que puedes tomar."
            )
        else:
            insights.append(
                "No hemos detectado un potencial de ahorro significativo. "
                "Continúa con tus buenos hábitos financieros."
            )
        
        return insights