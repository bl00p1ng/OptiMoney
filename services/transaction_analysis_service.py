"""
Módulo que contiene el servicio para análisis de transacciones.

Este servicio se encarga de analizar las transacciones de los usuarios
para detectar patrones de gasto y generar información para recomendaciones.
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import json
import statistics
import math
from collections import Counter, defaultdict
from models.transaction_model import Transaction
from models.pattern_model import Pattern
from models.repositories.transaction_repository import TransactionRepository
from models.repositories.pattern_repository import PatternRepository
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

class TransactionAnalysisService:
    """
    Servicio para analizar transacciones y detectar patrones de gasto.
    
    Esta clase proporciona métodos para analizar transacciones financieras,
    detectar patrones y tendencias, y generar información para recomendaciones
    de ahorro personalizadas.
    """
    
    def __init__(
        self, 
        transaction_repository: TransactionRepository,
        pattern_repository: PatternRepository
    ):
        """
        Inicializa el servicio de análisis de transacciones.
        
        Args:
            transaction_repository: Repositorio de transacciones.
            pattern_repository: Repositorio de patrones.
        """
        self.transaction_repo = transaction_repository
        self.pattern_repo = pattern_repository
        
        # Configuración de umbrales para análisis
        self.config = {
            "micro_expense_threshold": 10000,      # Umbral para considerar micro-gasto (en unidades monetarias)
            "recurring_min_frequency": 2,          # Mínimo de ocurrencias para considerar recurrente
            "recurring_max_variance": 0.2,         # Varianza máxima (%) para gastos recurrentes
            "similarity_threshold": 0.8,           # Umbral de similitud para agrupar transacciones (0-1)
            "high_deviation_factor": 1.5,          # Factor para considerar una desviación alta
            "optimizable_recurring_min_amount": 50000,  # Mínimo monto para gasto recurrente optimizable
            "min_transactions_for_pattern": 3,     # Mínimo de transacciones para considerar un patrón
            "min_days_for_analysis": 30,           # Mínimo de días con datos para análisis completo
            "confidence_thresholds": {
                "high": 0.85,    # Confianza alta
                "medium": 0.7,   # Confianza media
                "low": 0.5       # Confianza baja
            }
        }
        
        logger.info("Servicio de análisis de transacciones inicializado")
    
    async def analyze_user_transactions(self, user_id: str) -> Dict[str, Any]:
        """
        Analiza todas las transacciones de un usuario para detectar patrones.
        
        Args:
            user_id: ID del usuario.
            
        Returns:
            Dict[str, Any]: Resultados del análisis.
        """
        try:
            logger.info(f"Iniciando análisis de transacciones para usuario {user_id}")
            
            # Obtener transacciones que necesitan análisis
            transactions = await self.transaction_repo.get_transactions_to_analyze(user_id)
            
            if not transactions:
                logger.info(f"No hay transacciones pendientes de análisis para usuario {user_id}")
                return {"status": "success", "patterns_found": 0, "transactions_analyzed": 0}
            
            # Enriquecer transacciones con metadatos
            await self._enrich_transactions_metadata(transactions)
            
            # Obtener datos históricos para comparar
            # Obtenemos 90 días de datos para tener suficiente contexto histórico
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            historical_transactions = await self.transaction_repo.get_by_user_id_and_date_range(
                user_id, start_date, end_date
            )
            
            # Si no hay suficientes datos históricos, ajustar nivel de análisis
            limited_analysis = len(historical_transactions) < self.config["min_transactions_for_pattern"]
            
            # Detectar patrones
            patterns_found = 0
            
            # 1. Detectar micro-gastos
            micro_expense_patterns = await self._detect_micro_expense_patterns(user_id, transactions)
            patterns_found += len(micro_expense_patterns)
            
            # 2. Detectar gastos recurrentes
            recurring_patterns = await self._detect_recurring_patterns(user_id, transactions)
            patterns_found += len(recurring_patterns)
            
            # Los siguientes análisis requieren más datos históricos
            if not limited_analysis:
                # 3. Detectar patrones temporales
                temporal_patterns = await self._detect_temporal_patterns(
                    user_id, 
                    transactions, 
                    historical_transactions
                )
                patterns_found += len(temporal_patterns)
                
                # 4. Detectar desviaciones por categoría
                deviation_patterns = await self._detect_category_deviations(
                    user_id, 
                    transactions, 
                    historical_transactions
                )
                patterns_found += len(deviation_patterns)
            else:
                logger.info(
                    f"Realizando análisis limitado para usuario {user_id} por falta de datos históricos"
                )
                temporal_patterns = []
                deviation_patterns = []
            
            # Marcar transacciones como analizadas
            for transaction in transactions:
                transaction.mark_as_analyzed()
                await self.transaction_repo.update_analysis_flags(
                    transaction.id, 
                    {"lastAnalyzedAt": transaction.analysis_flags["lastAnalyzedAt"]}
                )
            
            logger.info(
                f"Análisis completado para usuario {user_id}: "
                f"{patterns_found} patrones encontrados, {len(transactions)} transacciones analizadas"
            )
            
            return {
                "status": "success",
                "patterns_found": patterns_found,
                "transactions_analyzed": len(transactions),
                "pattern_types": {
                    "micro_expense": len(micro_expense_patterns),
                    "recurring": len(recurring_patterns),
                    "temporal": len(temporal_patterns),
                    "deviation": len(deviation_patterns)
                }
            }
        except Exception as e:
            logger.error(f"Error en análisis de transacciones para usuario {user_id}: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}
    
    async def _enrich_transactions_metadata(self, transactions: List[Transaction]) -> None:
        """
        Enriquece los metadatos de las transacciones para análisis.
        
        Este método actualiza los metadatos de las transacciones, calcula
        hashes de similitud y agrupa transacciones similares.
        
        Args:
            transactions: Lista de transacciones a enriquecer.
        """
        # Actualizar metadatos básicos si es necesario
        for transaction in transactions:
            transaction.update_metadata()
            
            # Calcular similitud y hashes para agrupar transacciones similares
            await self._calculate_similarity_hash(transaction)
            
        # Buscar transacciones similares para agrupar
        await self._group_similar_transactions(transactions)
    
    async def _calculate_similarity_hash(self, transaction: Transaction) -> None:
        """
        Calcula un hash de similitud para una transacción.
        
        Este hash se utiliza para encontrar transacciones similares.
        
        Args:
            transaction: Transacción a procesar.
        """
        # Normalizar la descripción para comparación
        normalized_description = transaction.description.lower().strip()
        
        # Eliminar caracteres especiales y números para tener un hash más robusto
        import re
        normalized_description = re.sub(r'[^a-zA-Z\s]', '', normalized_description)
        
        # Redondear el monto para considerar transacciones con montos similares
        rounded_amount = round(transaction.amount / 100) * 100
        
        # Crear una cadena con la información relevante para similitud
        similarity_string = f"{normalized_description}|{transaction.category}|{rounded_amount}"
        
        # Calcular el hash
        hash_object = hashlib.md5(similarity_string.encode())
        transaction.metadata["similarityHash"] = hash_object.hexdigest()
        
        # Actualizar metadata en la base de datos
        await self.transaction_repo.update_metadata(
            transaction.id, 
            {"similarityHash": transaction.metadata["similarityHash"]}
        )
    
    async def _group_similar_transactions(self, transactions: List[Transaction]) -> None:
        """
        Agrupa transacciones similares y detecta recurrencias.
        
        Este método analiza las transacciones para encontrar patrones
        de gastos similares y recurrentes basados en sus hashes de similitud.
        
        Args:
            transactions: Lista de transacciones a analizar.
        """
        # Agrupar por hash de similitud
        hash_groups = {}
        
        for transaction in transactions:
            similarity_hash = transaction.metadata.get("similarityHash")
            if similarity_hash:
                if similarity_hash not in hash_groups:
                    hash_groups[similarity_hash] = []
                hash_groups[similarity_hash].append(transaction)
        
        # Analizar cada grupo para detectar recurrencias
        for hash_value, group in hash_groups.items():
            # Si hay suficientes transacciones similares
            if len(group) >= self.config["recurring_min_frequency"]:
                # Ordenar por fecha para analizar periodicidad
                sorted_group = sorted(group, key=lambda t: t.date)
                
                # Verificar si tienen una periodicidad consistente
                is_recurring = self._check_recurring_pattern(sorted_group)
                recurrence_id = f"rec_{hash_value[:8]}"
                
                # Marcar todas las transacciones del grupo
                for transaction in group:
                    transaction.metadata["isRecurring"] = is_recurring
                    if is_recurring:
                        transaction.metadata["recurrenceGroupId"] = recurrence_id
                    
                    # Actualizar en la base de datos
                    update_data = {"isRecurring": is_recurring}
                    if is_recurring:
                        update_data["recurrenceGroupId"] = recurrence_id
                    
                    await self.transaction_repo.update_metadata(
                        transaction.id, update_data
                    )
                    
                    # Si es recurrente y tiene un monto significativo, marcar como potencialmente optimizable
                    if is_recurring and transaction.amount >= self.config["optimizable_recurring_min_amount"]:
                        transaction.set_analysis_flag("isOptimizableRecurring", True)
                        await self.transaction_repo.update_analysis_flags(
                            transaction.id, 
                            {"isOptimizableRecurring": True}
                        )
    
    def _check_recurring_pattern(self, sorted_transactions: List[Transaction]) -> bool:
        """
        Verifica si un grupo de transacciones sigue un patrón recurrente.
        
        Este método analiza la periodicidad y variación en montos para
        determinar si las transacciones forman un patrón recurrente.
        
        Args:
            sorted_transactions: Lista de transacciones ordenadas por fecha.
            
        Returns:
            bool: True si se detecta un patrón recurrente, False en caso contrario.
        """
        if len(sorted_transactions) < self.config["recurring_min_frequency"]:
            return False
            
        # Analizar periodicidad
        if len(sorted_transactions) >= 3:
            # Calcular intervalos entre fechas
            intervals = []
            for i in range(1, len(sorted_transactions)):
                interval = (sorted_transactions[i].date - sorted_transactions[i-1].date).days
                intervals.append(interval)
            
            # Si los intervalos son muy inconsistentes, no es recurrente
            if intervals:
                # Calcular la desviación estándar relativa de los intervalos
                mean_interval = sum(intervals) / len(intervals)
                if mean_interval <= 0:
                    return False
                    
                # Si solo hay 2 intervalos, comparamos directamente
                if len(intervals) == 2:
                    ratio = max(intervals) / min(intervals) if min(intervals) > 0 else float('inf')
                    return ratio < 2.0  # Si un intervalo es menos del doble del otro
                
                # Para 3 o más intervalos, usamos desviación estándar
                try:
                    std_dev = statistics.stdev(intervals)
                    relative_std_dev = std_dev / mean_interval
                    
                    # Si la desviación es alta, no es un patrón confiable
                    if relative_std_dev > 0.5:
                        return False
                except statistics.StatisticsError:
                    # No hay suficiente variación para calcular desviación
                    pass
        
        # Analizar variación en montos
        amounts = [t.amount for t in sorted_transactions]
        if not amounts:
            return False
            
        # Calcular coeficiente de variación para los montos
        mean_amount = sum(amounts) / len(amounts)
        if mean_amount <= 0:
            return False
            
        try:
            std_dev = statistics.stdev(amounts)
            coefficient_variation = std_dev / mean_amount
            
            # Si la variación en montos es alta, no es considerado recurrente
            if coefficient_variation > self.config["recurring_max_variance"]:
                return False
        except statistics.StatisticsError:
            # No hay suficiente variación para calcular desviación
            pass
        
        return True
    
    async def _detect_micro_expense_patterns(
        self, 
        user_id: str, 
        transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Detecta patrones de micro-gastos acumulados por categoría.
        
        Este método identifica pequeños gastos que en conjunto suman
        cantidades significativas, agrupándolos por categoría.
        
        Args:
            user_id: ID del usuario.
            transactions: Lista de transacciones a analizar.
            
        Returns:
            List[Pattern]: Lista de patrones de micro-gastos detectados.
        """
        # Filtrar solo gastos (no ingresos) y micro-gastos
        micro_expenses = [
            t for t in transactions 
            if t.is_expense and t.amount <= self.config["micro_expense_threshold"]
        ]
        
        # Marcar las transacciones como micro-gastos
        for transaction in micro_expenses:
            transaction.set_analysis_flag("isMicroExpense", True)
            await self.transaction_repo.update_analysis_flags(
                transaction.id, 
                {"isMicroExpense": True}
            )
        
        # Agrupar por categoría
        category_groups = defaultdict(list)
        for transaction in micro_expenses:
            category_groups[transaction.category].append(transaction)
        
        # Crear patrones para categorías con suficientes micro-gastos
        patterns = []
        for category, group in category_groups.items():
            # Necesitamos un mínimo de transacciones para considerar un patrón
            if len(group) >= self.config["min_transactions_for_pattern"]:
                total_amount = sum(t.amount for t in group)
                avg_amount = total_amount / len(group)
                
                # Calcular la frecuencia (transacciones por mes)
                # Primero obtenemos el rango de fechas
                if len(group) >= 2:
                    date_range = (max(t.date for t in group) - min(t.date for t in group)).days
                    # Evitar división por cero
                    if date_range == 0:
                        date_range = 1
                    frequency = len(group) / (date_range / 30)  # Normalizado a meses
                else:
                    frequency = 1  # Valor por defecto si solo hay una transacción
                
                # Solo crear un patrón si el total acumulado es significativo
                if total_amount >= self.config["micro_expense_threshold"] * 3:
                    # Estimar ahorro potencial (aproximadamente 50% de reducción)
                    monthly_savings = (total_amount / (date_range / 30)) * 0.5 if date_range > 0 else 0
                    
                    # Crear un patrón
                    pattern = Pattern(
                        user_id=user_id,
                        type="micro_expense",
                        category=category,
                        status="active",
                        metrics={
                            "frequency": frequency,
                            "totalAmount": total_amount,
                            "averageAmount": avg_amount,
                            "percentageOfCategory": 0,  # Se calculará después
                            "percentageOfTotal": 0,     # Se calculará después
                            "confidence": 0.85,          # Alta confianza para micro-gastos
                        },
                        savings_potential={
                            "estimatedMonthly": monthly_savings,
                            "estimatedYearly": monthly_savings * 12,
                            "optimizationPercentage": 50,
                            "calculationMethod": "historical"
                        },
                        related_transactions=[
                            {
                                "transaction_id": t.id,
                                "amount": t.amount,
                                "date": t.date
                            } for t in group
                        ]
                    )
                    
                    # Guardar el patrón
                    pattern_id = await self.pattern_repo.add(pattern)
                    if pattern_id:
                        pattern.id = pattern_id
                        patterns.append(pattern)
                        logger.debug(f"Patrón de micro-gastos creado para categoría {category}")
        
        return patterns
    
    async def _detect_recurring_patterns(
        self, 
        user_id: str, 
        transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Detecta patrones de gastos recurrentes optimizables.
        
        Este método identifica gastos que ocurren regularmente y podrían
        ser optimizados para generar ahorros.
        
        Args:
            user_id: ID del usuario.
            transactions: Lista de transacciones a analizar.
            
        Returns:
            List[Pattern]: Lista de patrones de gastos recurrentes detectados.
        """
        # Filtrar transacciones recurrentes y optimizables
        recurring_transactions = [
            t for t in transactions 
            if t.is_expense and 
            t.metadata.get("isRecurring") and 
            t.analysis_flags.get("isOptimizableRecurring")
        ]
        
        # Agrupar por ID de recurrencia
        recurrence_groups = defaultdict(list)
        for transaction in recurring_transactions:
            recurrence_id = transaction.metadata.get("recurrenceGroupId")
            if recurrence_id:
                recurrence_groups[recurrence_id].append(transaction)
        
        # Crear patrones para cada grupo recurrente
        patterns = []
        for recurrence_id, group in recurrence_groups.items():
            if len(group) >= self.config["recurring_min_frequency"]:
                # Obtener categoría y descripción representativa
                category = group[0].category
                description = group[0].description
                
                # Calcular montos
                total_amount = sum(t.amount for t in group)
                avg_amount = total_amount / len(group)
                
                # Calcular frecuencia (transacciones por mes)
                sorted_group = sorted(group, key=lambda t: t.date)
                if len(sorted_group) >= 2:
                    first_date = sorted_group[0].date
                    last_date = sorted_group[-1].date
                    date_range = (last_date - first_date).days
                    
                    # Evitar división por cero
                    if date_range == 0:
                        date_range = 1
                        
                    frequency = len(group) / (date_range / 30)  # Normalizado a meses
                    
                    # Calcular intervalo promedio entre transacciones
                    intervals = [
                        (sorted_group[i].date - sorted_group[i-1].date).days 
                        for i in range(1, len(sorted_group))
                    ]
                    avg_interval = sum(intervals) / len(intervals) if intervals else 30
                    
                    # Determinar tipo de periodicidad
                    periodicity = "desconocida"
                    if 25 <= avg_interval <= 35:
                        periodicity = "mensual"
                    elif 13 <= avg_interval <= 17:
                        periodicity = "quincenal"
                    elif 6 <= avg_interval <= 8:
                        periodicity = "semanal"
                    elif avg_interval <= 3:
                        periodicity = "diaria"
                    elif 85 <= avg_interval <= 95:
                        periodicity = "trimestral"
                    elif 350 <= avg_interval <= 380:
                        periodicity = "anual"
                else:
                    frequency = 1
                    avg_interval = 30
                    periodicity = "desconocida"
                
                # Estimar potencial de ahorro basado en el tipo de gasto
                # Para servicios recurrentes, estimamos un 30% de ahorro
                estimated_savings_percentage = 0.3
                monthly_savings = avg_amount * frequency * estimated_savings_percentage
                
                # Crear un patrón
                pattern = Pattern(
                    user_id=user_id,
                    type="recurring",
                    category=category,
                    subcategory=description[:50] if description else "",  # Limitar longitud
                    status="active",
                    metrics={
                        "frequency": frequency,
                        "totalAmount": total_amount,
                        "averageAmount": avg_amount,
                        "percentageOfCategory": 0,  # Se calculará después
                        "percentageOfTotal": 0,     # Se calculará después
                        "confidence": 0.9,          # Confianza muy alta para recurrentes
                    },
                    temporal_data={
                        "periodicity": periodicity,
                        "averageInterval": avg_interval
                    },
                    savings_potential={
                        "estimatedMonthly": monthly_savings,
                        "estimatedYearly": monthly_savings * 12,
                        "optimizationPercentage": int(estimated_savings_percentage * 100),
                        "calculationMethod": "subscription_optimization"
                    },
                    related_transactions=[
                        {
                            "transaction_id": t.id,
                            "amount": t.amount,
                            "date": t.date
                        } for t in group
                    ]
                )
                
                # Guardar el patrón
                pattern_id = await self.pattern_repo.add(pattern)
                if pattern_id:
                    pattern.id = pattern_id
                    patterns.append(pattern)
                    logger.debug(f"Patrón de gasto recurrente creado para {description}")
        
        return patterns
    
    async def _detect_temporal_patterns(
        self, 
        user_id: str, 
        transactions: List[Transaction],
        historical_transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Detecta patrones temporales (días/horas específicas de alto gasto).
        
        Este método identifica patrones donde el usuario gasta más en
        ciertos días de la semana u horas del día.
        
        Args:
            user_id: ID del usuario.
            transactions: Lista de transacciones a analizar.
            historical_transactions: Transacciones históricas para contexto.
            
        Returns:
            List[Pattern]: Lista de patrones temporales detectados.
        """
        # Combinar transacciones actuales con históricas para mejor análisis
        all_transactions = transactions + [
            t for t in historical_transactions 
            if t.id not in [trans.id for trans in transactions]
        ]
        
        # Filtrar solo gastos (no ingresos)
        expenses = [t for t in all_transactions if t.is_expense]
        
        # Si no hay suficientes transacciones, no podemos detectar patrones temporales confiables
        if len(expenses) < self.config["min_transactions_for_pattern"] * 2:
            return []
        
        patterns = []
        
        # Análisis por día de la semana
        day_patterns = self._analyze_day_of_week_patterns(user_id, expenses)
        patterns.extend(day_patterns)
        
        # Análisis por hora del día
        time_patterns = self._analyze_time_of_day_patterns(user_id, expenses)
        patterns.extend(time_patterns)
        
        # Guardar los patrones detectados
        saved_patterns = []
        for pattern in patterns:
            # Guardar el patrón en la base de datos
            pattern_id = await self.pattern_repo.add(pattern)
            if pattern_id:
                pattern.id = pattern_id
                saved_patterns.append(pattern)
                
                # Marcar las transacciones relacionadas
                for transaction_data in pattern.related_transactions:
                    transaction_id = transaction_data.get("transaction_id")
                    # Solo marcar las transacciones actuales, no las históricas
                    matching_transactions = [t for t in transactions if t.id == transaction_id]
                    if matching_transactions:
                        transaction = matching_transactions[0]
                        transaction.set_analysis_flag("isTemporalPattern", True)
                        await self.transaction_repo.update_analysis_flags(
                            transaction.id, 
                            {"isTemporalPattern": True}
                        )
        
        return saved_patterns
    
    def _analyze_day_of_week_patterns(
        self, 
        user_id: str, 
        transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Analiza patrones de gasto por día de la semana.
        
        Args:
            user_id: ID del usuario.
            transactions: Transacciones a analizar.
            
        Returns:
            List[Pattern]: Lista de patrones por día de la semana.
        """
        # Agrupar transacciones por día de la semana
        day_groups = defaultdict(list)
        for transaction in transactions:
            day_of_week = transaction.metadata.get("dayOfWeek")
            if day_of_week is not None:
                day_groups[day_of_week].append(transaction)
        
        # Calcular estadísticas por día
        day_stats = {}
        for day, group in day_groups.items():
            daily_total = sum(t.amount for t in group)
            daily_count = len(group)
            daily_avg = daily_total / daily_count if daily_count > 0 else 0
            day_stats[day] = {
                "total": daily_total,
                "count": daily_count,
                "average": daily_avg
            }
        
        # Si no hay suficientes días para comparar, no podemos generar patrones
        if len(day_stats) < 3:
            return []
        
        # Calcular promedio general
        all_daily_avgs = [stats["average"] for stats in day_stats.values()]
        overall_avg = sum(all_daily_avgs) / len(all_daily_avgs) if all_daily_avgs else 0
        
        # Identificar días con gastos significativamente más altos
        patterns = []
        
        for day, stats in day_stats.items():
            # Verificar si el gasto es significativamente mayor al promedio
            if stats["average"] > overall_avg * self.config["high_deviation_factor"]:
                # Mapear número de día a nombre
                day_names = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
                day_name = day_names[day] if 0 <= day < 7 else f"Día {day}"
                
                # Calcular cuánto se ahorraría si se gastara el promedio en lugar del monto alto
                potential_monthly_savings = (stats["average"] - overall_avg) * 4  # 4 ocurrencias del día por mes
                
                # Crear un patrón
                pattern = Pattern(
                    user_id=user_id,
                    type="temporal",
                    category="multiple",  # Puede incluir varias categorías
                    status="active",
                    temporal_data={
                        "timeUnit": "day_of_week",
                        "timeValue": day,
                        "dayName": day_name,
                        "averageExpense": stats["average"],
                        "overallAverage": overall_avg,
                        "comparisonMetric": f"{stats['average'] / overall_avg:.1f}x el promedio"
                    },
                    metrics={
                        "frequency": 4,  # Una vez por semana, 4 por mes aproximadamente
                        "totalAmount": stats["total"],
                        "averageAmount": stats["average"],
                        "percentageOfCategory": 0,
                        "percentageOfTotal": 0,
                        "deviation": stats["average"] / overall_avg,
                        "confidence": 0.75,  # Alta confianza para patrones diarios
                    },
                    savings_potential={
                        "estimatedMonthly": potential_monthly_savings,
                        "estimatedYearly": potential_monthly_savings * 12,
                        "optimizationPercentage": int(((stats["average"] - overall_avg) / stats["average"]) * 100),
                        "calculationMethod": "day_of_week_optimization"
                    },
                    related_transactions=[
                        {
                            "transaction_id": t.id,
                            "amount": t.amount,
                            "date": t.date
                        } for t in day_groups[day]
                    ]
                )
                
                patterns.append(pattern)
                logger.debug(f"Patrón temporal detectado para el día {day_name}")
        
        return patterns
    
    def _analyze_time_of_day_patterns(
        self, 
        user_id: str, 
        transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Analiza patrones de gasto por hora del día.
        
        Args:
            user_id: ID del usuario.
            transactions: Transacciones a analizar.
            
        Returns:
            List[Pattern]: Lista de patrones por hora del día.
        """
        # Agrupar transacciones por período del día
        time_groups = defaultdict(list)
        for transaction in transactions:
            time_of_day = transaction.metadata.get("timeOfDay")
            if time_of_day:
                time_groups[time_of_day].append(transaction)
        
        # Si no hay suficientes períodos del día, no hay patrón
        if len(time_groups) < 2:
            return []
        
        # Calcular estadísticas por período
        time_stats = {}
        for time_period, group in time_groups.items():
            period_total = sum(t.amount for t in group)
            period_count = len(group)
            period_avg = period_total / period_count if period_count > 0 else 0
            time_stats[time_period] = {
                "total": period_total,
                "count": period_count,
                "average": period_avg
            }
        
        # Calcular promedio general
        all_period_avgs = [stats["average"] for stats in time_stats.values()]
        overall_avg = sum(all_period_avgs) / len(all_period_avgs) if all_period_avgs else 0
        
        # Identificar períodos con gastos significativamente más altos
        patterns = []
        
        for time_period, stats in time_stats.items():
            # Verificar si el gasto es significativamente mayor al promedio
            if stats["average"] > overall_avg * self.config["high_deviation_factor"]:
                # Nombre amigable para los períodos
                period_names = {
                    "morning": "las mañanas",
                    "afternoon": "las tardes",
                    "evening": "las noches",
                    "night": "las madrugadas"
                }
                period_name = period_names.get(time_period, time_period)
                
                # Calcular ahorro potencial mensual
                # Estimar 30 días por mes, y la diferencia entre el promedio alto y el general
                potential_monthly_savings = (stats["average"] - overall_avg) * 30 / len(time_stats)
                
                # Crear un patrón
                pattern = Pattern(
                    user_id=user_id,
                    type="temporal",
                    category="multiple",  # Puede incluir varias categorías
                    status="active",
                    temporal_data={
                        "timeUnit": "time_of_day",
                        "timeValue": time_period,
                        "periodName": period_name,
                        "averageExpense": stats["average"],
                        "overallAverage": overall_avg,
                        "comparisonMetric": f"{stats['average'] / overall_avg:.1f}x el promedio"
                    },
                    metrics={
                        "frequency": 30,  # Estimación aproximada mensual
                        "totalAmount": stats["total"],
                        "averageAmount": stats["average"],
                        "percentageOfCategory": 0,
                        "percentageOfTotal": 0,
                        "deviation": stats["average"] / overall_avg,
                        "confidence": 0.7,  # Confianza media para patrones por hora
                    },
                    savings_potential={
                        "estimatedMonthly": potential_monthly_savings,
                        "estimatedYearly": potential_monthly_savings * 12,
                        "optimizationPercentage": int(((stats["average"] - overall_avg) / stats["average"]) * 100),
                        "calculationMethod": "time_of_day_optimization"
                    },
                    related_transactions=[
                        {
                            "transaction_id": t.id,
                            "amount": t.amount,
                            "date": t.date
                        } for t in time_groups[time_period]
                    ]
                )
                
                patterns.append(pattern)
                logger.debug(f"Patrón temporal detectado para el período {period_name}")
        
        return patterns
    
    async def _detect_category_deviations(
        self, 
        user_id: str, 
        transactions: List[Transaction],
        historical_transactions: List[Transaction]
    ) -> List[Pattern]:
        """
        Detecta desviaciones significativas por categoría.
        
        Este método identifica categorías donde el gasto actual es
        significativamente mayor al promedio histórico.
        
        Args:
            user_id: ID del usuario.
            transactions: Lista de transacciones a analizar.
            historical_transactions: Transacciones históricas para contexto.
            
        Returns:
            List[Pattern]: Lista de patrones de desviación detectados.
        """
        # Filtrar solo gastos (no ingresos)
        current_expenses = [t for t in transactions if t.is_expense]
        historical_expenses = [t for t in historical_transactions if t.is_expense]
        
        # Agrupar transacciones actuales por categoría
        current_category_groups = defaultdict(list)
        for transaction in current_expenses:
            current_category_groups[transaction.category].append(transaction)
        
        # Agrupar transacciones históricas por categoría
        historical_category_groups = defaultdict(list)
        for transaction in historical_expenses:
            historical_category_groups[transaction.category].append(transaction)
        
        # Calcular promedios históricos por categoría
        historical_avgs = {}
        for category, group in historical_category_groups.items():
            # Calcular el promedio mensual para comparaciones justas
            dates = [t.date for t in group]
            if not dates:
                continue
                
            min_date = min(dates)
            max_date = max(dates)
            date_range = (max_date - min_date).days
            
            if date_range < 7:  # Se necesita al menos una semana de datos
                continue
                
            months = date_range / 30.0
            months = max(months, 1.0)  # Al menos un mes para evitar inflación
            
            total_amount = sum(t.amount for t in group)
            monthly_avg = total_amount / months
            
            historical_avgs[category] = {
                "monthlyAverage": monthly_avg,
                "transactionCount": len(group),
                "dateRange": date_range
            }
        
        # Analizar desviaciones actuales
        patterns = []
        current_month = datetime.now().strftime("%B %Y")
        
        for category, group in current_category_groups.items():
            # Necesitamos datos históricos y suficientes transacciones
            if category not in historical_avgs or len(group) < 2:
                continue
                
            # Calcular total actual para esta categoría
            current_total = sum(t.amount for t in group)
            
            # Ajustar al período actual (para comparación justa)
            dates = [t.date for t in group]
            current_date_range = (max(dates) - min(dates)).days
            current_date_range = max(current_date_range, 1)  # Evitar división por cero
            
            # Proyectar a un mes completo para comparación
            projected_monthly = current_total * (30.0 / current_date_range)
            
            # Comparar con el promedio histórico
            historical_monthly = historical_avgs[category]["monthlyAverage"]
            
            # Calcular desviación
            if historical_monthly > 0:
                deviation_ratio = projected_monthly / historical_monthly
                deviation_percentage = (deviation_ratio - 1) * 100
                
                # Si hay una desviación significativa hacia arriba
                if deviation_ratio > self.config["high_deviation_factor"]:
                    # Marcar transacciones
                    for transaction in group:
                        transaction.set_analysis_flag("isHighDeviation", True)
                        await self.transaction_repo.update_analysis_flags(
                            transaction.id, 
                            {"isHighDeviation": True}
                        )
                    
                    # Calcular potencial de ahorro (volver al promedio histórico)
                    monthly_savings = projected_monthly - historical_monthly
                    
                    # Crear un patrón
                    pattern = Pattern(
                        user_id=user_id,
                        type="category_deviation",
                        category=category,
                        status="active",
                        temporal_data={
                            "month": current_month,
                            "currentTotal": current_total,
                            "currentProjected": projected_monthly,
                            "standardAverage": historical_monthly,
                            "percentageIncrease": deviation_percentage
                        },
                        metrics={
                            "frequency": 0,  # No aplica
                            "totalAmount": current_total,
                            "averageAmount": current_total / len(group),
                            "percentageOfCategory": 100,
                            "percentageOfTotal": 0,
                            "deviation": deviation_ratio,
                            "confidence": 0.8,
                        },
                        savings_potential={
                            "estimatedMonthly": monthly_savings,
                            "estimatedYearly": monthly_savings * 12,
                            "optimizationPercentage": int((monthly_savings / projected_monthly) * 100),
                            "calculationMethod": "historical_comparison"
                        },
                        related_transactions=[
                            {
                                "transaction_id": t.id,
                                "amount": t.amount,
                                "date": t.date
                            } for t in group
                        ]
                    )
                    
                    # Guardar el patrón
                    pattern_id = await self.pattern_repo.add(pattern)
                    if pattern_id:
                        pattern.id = pattern_id
                        patterns.append(pattern)
                        logger.debug(f"Patrón de desviación detectado para categoría {category}")
        
        return patterns