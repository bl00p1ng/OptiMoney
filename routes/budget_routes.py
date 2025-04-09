"""
Módulo que define las rutas API para operaciones con presupuestos.
"""
from flask import Blueprint, request, jsonify
from controllers.budget_controller import BudgetController
from utils.logger import get_logger
from utils.auth_middleware import authenticate_user

# Logger específico para este módulo
logger = get_logger(__name__)

# Crear el controlador de presupuestos
budget_controller = BudgetController()

# Crear el blueprint para las rutas de presupuestos
budget_bp = Blueprint('budgets', __name__, url_prefix='/api/budgets')

@budget_bp.route('', methods=['POST'])
@authenticate_user
async def create_budget():
    """
    Crea un nuevo presupuesto para una categoría.
    
    Request body:
        - category_id (str): ID de la categoría.
        - amount (float): Monto del presupuesto.
        - period (str): Período del presupuesto ("monthly", "weekly", "yearly").
        - alert_threshold (float, optional): Umbral de alerta (predeterminado: 80).
        
    Returns:
        JSON: Resultado de la creación del presupuesto.
    """
    try:
        # Obtener datos del cuerpo de la solicitud
        data = request.get_json()
        
        # Añadir ID del usuario autenticado
        data['user_id'] = request.auth_user['uid']
        
        # Llamar al controlador
        result = await budget_controller.create_budget(data)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al crear presupuesto: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@budget_bp.route('', methods=['GET'])
@authenticate_user
async def get_user_budgets():
    """
    Obtiene los presupuestos del usuario autenticado.
    
    Returns:
        JSON: Lista de presupuestos del usuario.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await budget_controller.get_user_budgets(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al obtener presupuestos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@budget_bp.route('/summary', methods=['GET'])
@authenticate_user
async def get_budget_summary():
    """
    Obtiene un resumen de los presupuestos del usuario.
    
    Returns:
        JSON: Resumen de presupuestos.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await budget_controller.get_budget_summary(user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al obtener resumen de presupuestos: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@budget_bp.route('/<budget_id>', methods=['GET'])
@authenticate_user
async def get_budget(budget_id):
    """
    Obtiene los detalles de un presupuesto específico.
    
    Args:
        budget_id: ID del presupuesto a obtener.
        
    Returns:
        JSON: Detalles del presupuesto.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await budget_controller.get_budget(budget_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
    except Exception as e:
        logger.error(f"Error al obtener presupuesto: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@budget_bp.route('/<budget_id>', methods=['PUT'])
@authenticate_user
async def update_budget(budget_id):
    """
    Actualiza un presupuesto existente.
    
    Args:
        budget_id: ID del presupuesto a actualizar.
        
    Request body:
        - amount (float, optional): Nuevo monto del presupuesto.
        - alert_threshold (float, optional): Nuevo umbral de alerta.
        - period (str, optional): Nuevo período del presupuesto.
        
    Returns:
        JSON: Resultado de la actualización.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Obtener datos del cuerpo de la solicitud
        update_data = request.get_json()
        
        # Llamar al controlador
        result = await budget_controller.update_budget(budget_id, user_id, update_data)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al actualizar presupuesto: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

@budget_bp.route('/<budget_id>', methods=['DELETE'])
@authenticate_user
async def delete_budget(budget_id):
    """
    Elimina un presupuesto existente.
    
    Args:
        budget_id: ID del presupuesto a eliminar.
        
    Returns:
        JSON: Resultado de la eliminación.
    """
    try:
        # Obtener ID del usuario autenticado
        user_id = request.auth_user['uid']
        
        # Llamar al controlador
        result = await budget_controller.delete_budget(budget_id, user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        logger.error(f"Error al eliminar presupuesto: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f"Error al procesar la solicitud: {str(e)}"
        }), 500

# Función para registrar el blueprint en la aplicación
def register_budget_routes(app):
    """
    Registra las rutas de presupuestos en la aplicación Flask.
    
    Args:
        app: Instancia de la aplicación Flask.
    """
    app.register_blueprint(budget_bp)
    logger.info("Rutas de presupuestos registradas")