"""
Módulo que contiene el repositorio base para todas las operaciones de acceso a datos.
"""
from typing import Dict, List, Any, Optional, TypeVar, Generic, Type
from datetime import datetime
from google.cloud.firestore import DocumentReference, DocumentSnapshot
from config.firebase_config import get_firestore_client
from models.base_model import BaseModel
from utils.logger import get_logger

# Logger específico para este módulo
logger = get_logger(__name__)

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T]):
    """
    Repositorio base para operaciones CRUD en Firestore.
    
    Este repositorio proporciona funcionalidad común para acceder
    y manipular datos en colecciones de Firestore.
    
    Attributes:
        collection_name (str): Nombre de la colección en Firestore.
        model_class (Type[T]): Clase del modelo con el que trabaja el repositorio.
    """
    
    def __init__(self, collection_name: str, model_class: Type[T]):
        """
        Inicializa un nuevo repositorio base.
        
        Args:
            collection_name: Nombre de la colección en Firestore.
            model_class: Clase del modelo con el que trabaja el repositorio.
        """
        self.db = get_firestore_client()
        self.collection_name = collection_name
        self.collection = self.db.collection(collection_name)
        self.model_class = model_class
        logger.debug(f"Repositorio inicializado para colección: {collection_name}")
    
    async def add(self, model: T) -> str:
        """
        Añade un nuevo documento a la colección.
        
        Args:
            model: Instancia del modelo a añadir.
            
        Returns:
            str: ID del documento creado.
        """
        try:
            model_dict = model.to_dict()
            # Asegurar que se registra la fecha de creación
            if 'created_at' not in model_dict:
                model_dict['created_at'] = datetime.now()
            
            if model.id:
                # Si el modelo ya tiene ID, usamos ese documento
                doc_ref = self.collection.document(model.id)
                doc_ref.set(model_dict)
                logger.info(f"Documento creado en {self.collection_name} con ID: {model.id}")
                return model.id
            else:
                # Si no tiene ID, Firestore generará uno
                doc_ref = self.collection.document()
                doc_ref.set(model_dict)
                # Actualizar el ID del modelo
                model.id = doc_ref.id
                logger.info(f"Documento creado en {self.collection_name} con ID: {doc_ref.id}")
                return doc_ref.id
        except Exception as e:
            logger.error(f"Error al añadir documento en {self.collection_name}: {str(e)}", exc_info=True)
            raise
    
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """
        Actualiza un documento existente.
        
        Args:
            id: ID del documento a actualizar.
            data: Datos a actualizar.
            
        Returns:
            bool: True si la actualización fue exitosa, False en caso contrario.
        """
        try:
            # Asegurar que se registra la fecha de actualización
            data['updated_at'] = datetime.now()
            
            doc_ref = self.collection.document(id)
            doc_ref.update(data)
            logger.info(f"Documento actualizado en {self.collection_name} con ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error al actualizar documento {id} en {self.collection_name}: {str(e)}", exc_info=True)
            return False
    
    async def delete(self, id: str) -> bool:
        """
        Elimina un documento existente.
        
        Args:
            id: ID del documento a eliminar.
            
        Returns:
            bool: True si la eliminación fue exitosa, False en caso contrario.
        """
        try:
            doc_ref = self.collection.document(id)
            doc_ref.delete()
            logger.info(f"Documento eliminado en {self.collection_name} con ID: {id}")
            return True
        except Exception as e:
            logger.error(f"Error al eliminar documento {id} en {self.collection_name}: {str(e)}", exc_info=True)
            return False
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Obtiene un documento por su ID.
        
        Args:
            id: ID del documento a obtener.
            
        Returns:
            Optional[T]: Instancia del modelo si se encontró, None en caso contrario.
        """
        try:
            doc_ref = self.collection.document(id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Asegurar que el ID esté incluido
                data['id'] = doc.id
                logger.debug(f"Documento obtenido de {self.collection_name} con ID: {id}")
                return self.model_class.from_dict(data)
            else:
                logger.debug(f"Documento no encontrado en {self.collection_name} con ID: {id}")
                return None
        except Exception as e:
            logger.error(f"Error al obtener documento {id} de {self.collection_name}: {str(e)}", exc_info=True)
            return None
    
    async def get_all(self) -> List[T]:
        """
        Obtiene todos los documentos de la colección.
        
        Returns:
            List[T]: Lista de instancias del modelo.
        """
        try:
            docs = self.collection.stream()
            result = []
            
            for doc in docs:
                data = doc.to_dict()
                # Asegurar que el ID esté incluido
                data['id'] = doc.id
                model = self.model_class.from_dict(data)
                result.append(model)
            
            logger.debug(f"Obtenidos {len(result)} documentos de {self.collection_name}")
            return result
        except Exception as e:
            logger.error(f"Error al obtener todos los documentos de {self.collection_name}: {str(e)}", exc_info=True)
            return []
    
    async def query(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[T]:
        """
        Realiza una consulta con filtros específicos.
        
        Args:
            filters: Diccionario de filtros (campo: valor).
            limit: Límite de resultados (opcional).
            
        Returns:
            List[T]: Lista de instancias del modelo que cumplen los filtros.
        """
        try:
            query = self.collection
            
            # Aplicar cada filtro
            for field, value in filters.items():
                query = query.where(field, '==', value)
            
            # Aplicar límite si existe
            if limit:
                query = query.limit(limit)
            
            # Ejecutar la consulta
            docs = query.stream()
            result = []
            
            for doc in docs:
                data = doc.to_dict()
                # Asegurar que el ID esté incluido
                data['id'] = doc.id
                model = self.model_class.from_dict(data)
                result.append(model)
            
            logger.debug(f"Consulta en {self.collection_name} con filtros {filters} retornó {len(result)} resultados")
            return result
        except Exception as e:
            logger.error(f"Error al realizar consulta en {self.collection_name}: {str(e)}", exc_info=True)
            return []
    
    async def exists(self, id: str) -> bool:
        """
        Verifica si existe un documento con el ID especificado.
        
        Args:
            id: ID del documento a verificar.
            
        Returns:
            bool: True si existe, False en caso contrario.
        """
        try:
            doc_ref = self.collection.document(id)
            doc = doc_ref.get()
            return doc.exists
        except Exception as e:
            logger.error(f"Error al verificar existencia de documento {id} en {self.collection_name}: {str(e)}", exc_info=True)
            return False