"""
Módulo que define las rutas API para operaciones con transacciones.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify
from controllers.transaction_controller import TransactionController
from utils.auth_middleware import authenticate_user
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de transacciones
transaction_controller = TransactionController()

# Crear el blueprint para las rutas de transacciones
transaction_bp = Blueprint('transactions', __name__, url_prefix='/api/transactions')

@transaction_bp.route('', methods=['POST'])
@authenticate_user
async def create_transaction():
    """
    Crea una nueva transacción.
    
    Request body:
        - amount (float): Monto de la transacción.
        - category (str): Categoría de la transacción.
        - description (str, optional): Descripción de la transacción.
        - is_expense (bool): Indica si es un gasto (True) o ingreso (False).
        - date (str, optional): Fecha de la transacción en formato ISO.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # Extraer user_id del contexto de autenticación
        user_id = request.auth_user['uid']
        data['user_id'] = user_id
        
        # Convertir fecha si se proporciona
        if 'date' in data and isinstance(data['date'], str):
            try:
                data['date'] = datetime.fromisoformat(data['date'])
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use formato ISO (YYYY-MM-DDTHH:MM:SS)'
                }), 400
        
        # Llamar al controlador
        result = await transaction_controller.create_transaction(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al crear transacción: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('/<transaction_id>', methods=['GET'])
@authenticate_user
async def get_transaction(transaction_id):
    """
    Obtiene una transacción por su ID.
    
    Args:
        transaction_id: ID de la transacción a obtener.
        
    Returns:
        JSON: Datos de la transacción.
    """
    try:
        # Obtener transacción
        result = await transaction_controller.get_transaction(transaction_id)
        
        if result['success']:
            # Verificar que la transacción pertenece al usuario autenticado
            if result['transaction']['user_id'] != request.auth_user['uid']:
                return jsonify({
                    'success': False,
                    'error': 'No autorizado para acceder a esta transacción'
                }), 403
                
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error al obtener transacción: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('/<transaction_id>', methods=['PUT'])
@authenticate_user
async def update_transaction(transaction_id):
    """
    Actualiza una transacción existente.
    
    Args:
        transaction_id: ID de la transacción a actualizar.
        
    Request body:
        - amount (float, optional): Nuevo monto.
        - category (str, optional): Nueva categoría.
        - description (str, optional): Nueva descripción.
        - is_expense (bool, optional): Nuevo tipo (gasto o ingreso).
        - date (str, optional): Nueva fecha en formato ISO.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Verificar que la transacción existe y pertenece al usuario
        get_result = await transaction_controller.get_transaction(transaction_id)
        if not get_result['success']:
            return jsonify(get_result), 404
            
        if get_result['transaction']['user_id'] != request.auth_user['uid']:
            return jsonify({
                'success': False,
                'error': 'No autorizado para modificar esta transacción'
            }), 403
        
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # Convertir fecha si se proporciona
        if 'date' in data and isinstance(data['date'], str):
            try:
                data['date'] = datetime.fromisoformat(data['date'])
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Formato de fecha inválido. Use formato ISO (YYYY-MM-DDTHH:MM:SS)'
                }), 400
        
        # Llamar al controlador
        result = await transaction_controller.update_transaction(transaction_id, data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al actualizar transacción: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('/<transaction_id>', methods=['DELETE'])
@authenticate_user
async def delete_transaction(transaction_id):
    """
    Elimina una transacción.
    
    Args:
        transaction_id: ID de la transacción a eliminar.
        
    Returns:
        JSON: Resultado de la operación.
    """
    try:
        # Verificar que la transacción existe y pertenece al usuario
        get_result = await transaction_controller.get_transaction(transaction_id)
        if not get_result['success']:
            return jsonify(get_result), 404
            
        if get_result['transaction']['user_id'] != request.auth_user['uid']:
            return jsonify({
                'success': False,
                'error': 'No autorizado para eliminar esta transacción'
            }), 403
        
        # Llamar al controlador
        result = await transaction_controller.delete_transaction(transaction_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al eliminar transacción: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('', methods=['GET'])
@authenticate_user
async def get_user_transactions():
    """
    Obtiene las transacciones del usuario autenticado con filtros opcionales.
    
    Query params:
        - category (str, optional): Filtro por categoría.
        - start_date (str, optional): Fecha de inicio en formato ISO.
        - end_date (str, optional): Fecha de fin en formato ISO.
        - limit (int, optional): Número máximo de transacciones a retornar.
        - is_expense (bool, optional): Filtro por tipo (gasto o ingreso).
        
    Returns:
        JSON: Lista de transacciones.
    """
    try:
        # Extraer parámetros de consulta
        category = request.args.get('category')
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        limit_str = request.args.get('limit')
        is_expense_str = request.args.get('is_expense')
        
        # Convertir parámetros
        start_date = datetime.fromisoformat(start_date_str) if start_date_str else None
        end_date = datetime.fromisoformat(end_date_str) if end_date_str else None
        limit = int(limit_str) if limit_str else None
        
        # Convertir is_expense a booleano si se proporciona
        is_expense = None
        if is_expense_str:
            is_expense = is_expense_str.lower() == 'true'
        
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await transaction_controller.get_user_transactions(
            user_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            is_expense=is_expense
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f"Error de formato en los parámetros: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error al obtener transacciones: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('/statistics', methods=['GET'])
@authenticate_user
async def get_user_statistics():
    """
    Obtiene estadísticas de gastos e ingresos para el usuario autenticado.
    
    Query params:
        - period (str, optional): Período para las estadísticas ("monthly", "weekly", "yearly").
        - months (int, optional): Número de meses a considerar (default: 12).
        
    Returns:
        JSON: Estadísticas calculadas.
    """
    try:
        # Extraer parámetros de consulta
        period = request.args.get('period', 'monthly')
        months_str = request.args.get('months', '12')
        
        # Convertir parámetros
        months = int(months_str)
        
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await transaction_controller.get_user_statistics(
            user_id,
            period=period,
            months=months
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': f"Error de formato en los parámetros: {str(e)}"
        }), 400
    except Exception as e:
        logger.error(f"Error al obtener estadísticas: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@transaction_bp.route('/analyze', methods=['POST'])
@authenticate_user
async def analyze_transactions():
    """
    Inicia un análisis de transacciones para detectar patrones.
    
    Returns:
        JSON: Resultado del análisis.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await transaction_controller.analyze_user_transactions(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al analizar transacciones: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_transaction_routes(app):
    """
    Registra las rutas de transacciones en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(transaction_bp)
    logger.info("Rutas de transacciones registradas")