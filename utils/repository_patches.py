"""
Módulo para aplicar parches a los repositorios y corregir problemas de inicialización.

Este módulo aplica monkey patching a las clases de repositorio para asegurar
que se inicialicen correctamente pasando los parámetros requeridos a BaseRepository.
"""

import logging
from typing import Type, Dict, Any

# Obtener logger
logger = logging.getLogger(__name__)

def apply_repository_patches():
    """
    Aplica parches a las clases de repositorio para corregir problemas de inicialización.
    
    Esta función debe llamarse antes de inicializar cualquier controlador.
    """
    try:
        logger.info("Aplicando parches a las clases de repositorio...")
        
        # Importar modelos y repositorios
        from models.transaction_model import Transaction
        from models.user_model import User
        from models.budget_model import Budget
        from models.category_model import Category
        from models.pattern_model import Pattern
        from models.recommendation_model import Recommendation
        
        from models.repositories.transaction_repository import TransactionRepository
        from models.repositories.user_repository import UserRepository
        from models.repositories.budget_repository import BudgetRepository
        from models.repositories.category_repository import CategoryRepository
        from models.repositories.pattern_repository import PatternRepository
        from models.repositories.recommendation_repository import RecommendationRepository
        
        # Definir mapeo entre repositorios y sus parámetros de inicialización
        repo_configs = {
            TransactionRepository: ("transactions", Transaction),
            UserRepository: ("users", User),
            BudgetRepository: ("budgets", Budget),
            CategoryRepository: ("categories", Category),
            PatternRepository: ("patterns", Pattern),
            RecommendationRepository: ("recommendations", Recommendation)
        }
        
        # Aplicar parches a cada repositorio
        for repo_class, params in repo_configs.items():
            patch_repository_init(repo_class, *params)
            
        logger.info("Parches aplicados con éxito a todas las clases de repositorio")
    except Exception as e:
        logger.error(f"Error al aplicar parches a los repositorios: {str(e)}", exc_info=True)
        raise

def patch_repository_init(repo_class: Type, collection_name: str, model_class: Type):
    """
    Aplica un parche al método __init__ de un repositorio.
    
    Args:
        repo_class: Clase de repositorio a parchear.
        collection_name: Nombre de la colección en Firestore.
        model_class: Clase del modelo asociado al repositorio.
    """
    # Verificar si la clase tiene problemas con _init_ vs __init__
    if hasattr(repo_class, '_init_') and not hasattr(repo_class, '__init__'):
        # Si solo tiene _init_, crear un nuevo __init__ que llame a BaseRepository.__init__
        original_init = repo_class._init_
        
        def new_init(self, *args, **kwargs):
            # Llamar al constructor de la clase base con los parámetros correctos
            from models.repositories.base_repository import BaseRepository
            BaseRepository.__init__(self, collection_name, model_class)
            
            # Llamar al método de inicialización original si tiene parámetros adicionales
            if args or kwargs:
                original_init(self, *args, **kwargs)
                
        # Asignar el nuevo __init__ a la clase
        repo_class.__init__ = new_init
        logger.debug(f"Parche aplicado a {repo_class.__name__}._init_")
    else:
        # Si ya tiene __init__, reemplazarlo para asegurar que llame a BaseRepository correctamente
        original_init = getattr(repo_class, '__init__', None)
        
        def new_init(self, *args, **kwargs):
            # Llamar al constructor de la clase base con los parámetros correctos
            from models.repositories.base_repository import BaseRepository
            BaseRepository.__init__(self, collection_name, model_class)
            
            # Llamar al método de inicialización original si existe y tiene parámetros adicionales
            if original_init and (args or kwargs):
                # Omitir self al llamar al método original
                original_init(self, *args, **kwargs)
                
        # Asignar el nuevo __init__ a la clase
        repo_class.__init__ = new_init
        logger.debug(f"Parche aplicado a {repo_class.__name__}.__init__")