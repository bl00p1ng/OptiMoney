# OptiMoney

**OptiMoney** es una aplicación web para la gestión y seguimiento de las finanzad personales. Permite registrar todos los gastos realizados por el usuario, definir presupuestos y conocer sugerencias de ahorro y optimización de gatos.

## Ejecución de la app

### Primeros pasos

1. Clonar el repositorio
2. Agregar una cuenta de servicio en la ruta `credentials/firebase-key.json`
3. Crear un entorno virtual en Python (se recomienda usar Python 3.11 para mejor compatibilidad)
4. Activar el entorno virtual.
5. Instalar las dependencias listadas en el archivo `requirements.txt`: `pip install -r requirements.txt`

### Ejecutar entorno de pruebas

Para ejecutar la aplicación en desarrollo, tienes dos opciones principales:

1. **Método directo con Python**:
   ```bash
   python3 main.py
   ```
   Este comando es correcto y funcionará para entornos de desarrollo, esto iniciará el servidor en `http://0.0.0.0:8080`.

2. **Usando Gunicorn** (recomendado para probar la configuración de producción):
   ```bash
   gunicorn -b :8080 main:app
   ```
   Este método es más similar a cómo funcionará en Google App Engine.

Algunas consideraciones adicionales para el entorno de desarrollo:

- **Variables de entorno**: Asegúrate de configurar las variables de entorno necesarias, especialmente las credenciales de Firebase:
  ```bash
  export ENVIRONMENT=development
  export FIREBASE_CREDENTIALS_PATH=./credentials/firebase-key.json
  ```
  También se pueden definir las variables de entorno en un archivo `.env`

- **Hot reload**: Si se quiere que la aplicación se recargue automáticamente cuando se hacen cambios en el código, usar Flask con el flag de debug:
  ```bash
  FLASK_APP=main.py FLASK_DEBUG=1 flask run --port=8080
  ```

Para probar que todo funciona correctamente, acceder a `http://localhost:8080/health` en el navegador, que debería mostrar un mensaje de estado indicando que la aplicación está funcionando.