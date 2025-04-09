"""
Módulo que define las rutas API para operaciones de análisis financiero.
"""
from flask import Blueprint, request, jsonify
from controllers.analysis_controller import AnalysisController
from utils.logger import get_logger
from utils.auth_middleware import authenticate_user

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de análisis
analysis_controller = AnalysisController()

# Crear el blueprint para las rutas de análisis
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api/analysis')

@analysis_bp.route('/overview', methods=['GET'])
@authenticate_user
async def get_financial_overview():
    """
    Obtiene una visión general de la situación financiera del usuario.
    
    Esta ruta proporciona un resumen completo que incluye:
    - Balance general
    - Datos del mes actual y comparación con el mes anterior
    - Distribución de gastos por categoría
    - Tendencias mensuales
    - Estado de presupuestos
    - Índice de salud financiera
    
    Returns:
        JSON: Resumen financiero general.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener resumen financiero
        result = await analysis_controller.get_financial_overview(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al obtener resumen financiero: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@analysis_bp.route('/expenses', methods=['GET'])
@authenticate_user
async def get_expense_report():
    """
    Genera un reporte detallado de gastos.
    
    Query params:
        - start_date (str, optional): Fecha de inicio en formato ISO.
        - end_date (str, optional): Fecha de fin en formato ISO.
        - group_by (str, optional): Criterio de agrupación ("category", "day", "week", "month").
        
    Returns:
        JSON: Reporte detallado de gastos.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener parámetros de consulta
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        group_by = request.args.get('group_by', 'category')
        
        # Generar reporte
        result = await analysis_controller.get_expense_report(
            user_id=user_id,
            start_date_str=start_date,
            end_date_str=end_date,
            group_by=group_by
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al generar reporte de gastos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@analysis_bp.route('/income-expense-ratio', methods=['GET'])
@authenticate_user
async def get_income_expense_ratio():
    """
    Analiza la relación entre ingresos y gastos a lo largo del tiempo.
    
    Query params:
        - months (int, optional): Número de meses a analizar (predeterminado: 6).
        
    Returns:
        JSON: Análisis de la relación ingresos/gastos.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener parámetros de consulta
        months_str = request.args.get('months', '6')
        
        try:
            months = int(months_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': "El parámetro 'months' debe ser un número entero."
            }), 400
        
        # Obtener análisis
        result = await analysis_controller.get_income_expense_ratio(
            user_id=user_id,
            months=months
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al analizar relación ingresos/gastos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@analysis_bp.route('/savings-potential', methods=['GET'])
@authenticate_user
async def get_savings_potential():
    """
    Analiza el potencial de ahorro basado en patrones detectados.
    
    Returns:
        JSON: Análisis del potencial de ahorro.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener análisis
        result = await analysis_controller.get_savings_potential(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al analizar potencial de ahorro: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@analysis_bp.route('/category-trends/<category_id>', methods=['GET'])
@authenticate_user
async def get_category_spending_trends(category_id):
    """
    Analiza tendencias de gasto en una categoría específica.
    
    Args:
        category_id: ID de la categoría a analizar.
        
    Query params:
        - months (int, optional): Número de meses a analizar (predeterminado: 6).
        
    Returns:
        JSON: Análisis de tendencias para la categoría.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener parámetros de consulta
        months_str = request.args.get('months', '6')
        
        try:
            months = int(months_str)
        except ValueError:
            return jsonify({
                'success': False,
                'error': "El parámetro 'months' debe ser un número entero."
            }), 400
        
        # Obtener análisis
        result = await analysis_controller.get_category_spending_trends(
            user_id=user_id,
            category_id=category_id,
            months=months
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al analizar tendencias de categoría: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_analysis_routes(app):
    """
    Registra las rutas de análisis financiero en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(analysis_bp)
    logger.info("Rutas de análisis financiero registradas")