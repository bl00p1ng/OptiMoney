"""
Script para ejecutar todas las pruebas unitarias.
"""
import unittest
import sys
import os

# Agregar directorio raíz al path para importar módulos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def run_tests():
    """Descubre y ejecuta todas las pruebas unitarias."""
    # Descubrir todos los tests en el directorio actual
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(os.path.dirname(__file__), pattern='test_*.py')
    
    # Ejecutar tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Retornar código de salida según resultados
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())