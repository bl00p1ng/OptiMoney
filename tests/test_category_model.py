"""
Tests unitarios para el modelo de Categoría.
"""
import unittest
from models.category_model import Category

class TestCategoryModel(unittest.TestCase):
    """Pruebas unitarias para el modelo de Categoría."""
    
    def test_create_category(self):
        """Prueba la creación básica de una categoría."""
        # Crear una categoría
        category = Category(
            name="Test Category",
            type="expense",
            icon="test_icon",
            color="#FF0000"
        )
        
        # Verificar atributos
        self.assertEqual(category.name, "Test Category")
        self.assertEqual(category.type, "expense")
        self.assertEqual(category.icon, "test_icon")
        self.assertEqual(category.color, "#FF0000")
        self.assertIsNone(category.user_id)  # Debería ser None por defecto
        
    def test_is_predefined(self):
        """Prueba la detección de categorías predefinidas vs personalizadas."""
        # Categoría predefinida (user_id es None)
        predefined = Category(
            user_id=None,
            name="Predefined Category"
        )
        
        # Categoría personalizada (user_id tiene valor)
        custom = Category(
            user_id="user123",
            name="Custom Category"
        )
        
        # Verificar
        self.assertTrue(predefined.is_predefined())
        self.assertFalse(custom.is_predefined())
        
    def test_from_dict(self):
        """Prueba la creación de una categoría a partir de un diccionario."""
        # Datos de prueba
        data = {
            "id": "cat123",
            "name": "Dict Category",
            "type": "income",
            "user_id": "user456",
            "icon": "dict_icon",
            "color": "#00FF00"
        }
        
        # Crear categoría desde diccionario
        category = Category.from_dict(data)
        
        # Verificar
        self.assertEqual(category.id, "cat123")
        self.assertEqual(category.name, "Dict Category")
        self.assertEqual(category.type, "income")
        self.assertEqual(category.user_id, "user456")
        self.assertEqual(category.icon, "dict_icon")
        self.assertEqual(category.color, "#00FF00")
        
    def test_default_categories(self):
        """Prueba la obtención de categorías predefinidas."""
        # Obtener categorías predefinidas
        categories = Category.get_default_categories()
        
        # Verificar que no está vacío
        self.assertTrue(len(categories) > 0)
        
        # Verificar que existe al menos una categoría de gasto y una de ingreso
        has_expense = False
        has_income = False
        
        for _, data in categories.items():
            if data["type"] == "expense":
                has_expense = True
            elif data["type"] == "income":
                has_income = True
                
        self.assertTrue(has_expense)
        self.assertTrue(has_income)

if __name__ == '__main__':
    unittest.main()