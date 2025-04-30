# OptiMoney

**OptiMoney** es una aplicación web para la gestión y seguimiento de las finanzas personales. Permite registrar todos los gastos realizados por el usuario, definir presupuestos y conocer sugerencias de ahorro y optimización de gastos.

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

## Pruebas de la aplicación

### Endpoints de prueba

Puedes verificar la correcta configuración mediante estos endpoints:

1. **Verificar estado general**:
   - GET `/api/ping` - Respuesta simple para verificar que la API responde.
   - GET `/api/health` - Verificar el estado general y conectividad con Firebase.

2. **Inicializar categorías predefinidas**:
   - POST `/api/categories/initialize-defaults` - Crea las categorías predefinidas del sistema.

3. **Categorías**:
   - GET `/api/categories` - Obtener categorías (requiere autenticación).
   - POST `/api/categories` - Crear categoría personalizada (requiere autenticación).

4. **Transacciones**:
   - POST `/api/transactions` - Crear transacción (requiere autenticación).
   - GET `/api/transactions` - Listar transacciones (requiere autenticación).

La mayoría de las rutas requieren autenticación de Firebase. Para pruebas de desarrollo, puedes crear un token utilizando la función `get_test_token` del módulo `utils.auth_middleware`.

### Pruebas unitarias

Para ejecutar las pruebas unitarias:

```bash
python -m tests.run_tests
```

También puedes ejecutar tests individuales:

```bash
python -m unittest tests.test_category_model
```

## Verificación inicial

Para probar que todo funciona correctamente, acceder a `http://localhost:8080/api/ping` en el navegador, que debería mostrar un mensaje de estado indicando que la aplicación está funcionando.

# Documentación del Sistema de Autenticación de OptiMoney

## Descripción General

El sistema de autenticación de OptiMoney utiliza Firebase Authentication para gestionar la autenticación de usuarios, complementado con un sistema JWT propio para mayor flexibilidad. Este documento describe la implementación, endpoints disponibles y cómo utilizarlos.

## Endpoints de Autenticación

### Registro de Usuario
- **URL**: `/api/auth/register`
- **Método**: `POST`
- **Cuerpo de la solicitud**:
  ```json
  {
    "email": "usuario@ejemplo.com",
    "password": "contraseña123",
    "name": "Nombre Completo"
  }
  ```
- **Respuesta exitosa** (201 Created):
  ```json
  {
    "success": true,
    "message": "Usuario registrado exitosamente",
    "user": {
      "id": "user123",
      "email": "usuario@ejemplo.com",
      "name": "Nombre Completo"
    },
    "auth": {
      "token": "jwt_token_here",
      "expiry": 1715126400
    }
  }
  ```

### Inicio de Sesión
- **URL**: `/api/auth/login`
- **Método**: `POST`
- **Cuerpo de la solicitud**:
  ```json
  {
    "email": "usuario@ejemplo.com",
    "password": "contraseña123"
  }
  ```
- **Respuesta exitosa** (200 OK):
  ```json
  {
    "success": true,
    "message": "Inicio de sesión exitoso",
    "user": {
      "id": "user123",
      "email": "usuario@ejemplo.com",
      "name": "Nombre Completo",
      "settings": {
        "currency": "CLP",
        "notificationsEnabled": true
      }
    },
    "auth": {
      "token": "jwt_token_here",
      "expiry": 1715126400
    }
  }
  ```

### Obtener Perfil de Usuario
- **URL**: `/api/auth/profile`
- **Método**: `GET`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Respuesta exitosa** (200 OK):
  ```json
  {
    "success": true,
    "profile": {
      "id": "user123",
      "email": "usuario@ejemplo.com",
      "name": "Nombre Completo",
      "settings": {
        "currency": "CLP",
        "notificationsEnabled": true
      },
      "email_verified": true,
      "created_at": "2025-04-01T12:00:00Z",
      "firebase_created_at": 1714576800000
    }
  }
  ```

### Actualizar Perfil de Usuario
- **URL**: `/api/auth/profile`
- **Método**: `PUT`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Cuerpo de la solicitud**:
  ```json
  {
    "name": "Nuevo Nombre",
    "settings": {
      "currency": "USD",
      "notificationsEnabled": false
    }
  }
  ```
- **Respuesta exitosa** (200 OK):
  ```json
  {
    "success": true,
    "message": "Perfil actualizado correctamente",
    "profile": {
      "id": "user123",
      "email": "usuario@ejemplo.com",
      "name": "Nuevo Nombre",
      "settings": {
        "currency": "USD",
        "notificationsEnabled": false
      },
      "email_verified": true,
      "created_at": "2025-04-01T12:00:00Z"
    }
  }
  ```

### Cambiar Contraseña
- **URL**: `/api/auth/change-password`
- **Método**: `POST`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Cuerpo de la solicitud**:
  ```json
  {
    "current_password": "contraseña123",
    "new_password": "nuevaContraseña456"
  }
  ```
- **Respuesta exitosa** (200 OK):
  ```json
  {
    "success": true,
    "message": "Contraseña actualizada correctamente"
  }
  ```

### Verificar Token
- **URL**: `/api/auth/verify`
- **Método**: `GET`
- **Headers**: 
  - `Authorization: Bearer {token}`
- **Respuesta exitosa** (200 OK):
  ```json
  {
    "success": true,
    "message": "Token válido",
    "user": {
      "id": "user123",
      "email": "usuario@ejemplo.com",
      "name": "Nombre Completo"
    }
  }
  ```

## Uso del Token de Autenticación

Una vez obtenido el token de autenticación (mediante registro o inicio de sesión), este debe incluirse en todas las peticiones a endpoints protegidos mediante el encabezado HTTP `Authorization`:

```
Authorization: Bearer {token}
```

El token tiene una validez de 24 horas por defecto, aunque este valor es configurable mediante la variable de entorno `TOKEN_EXPIRY`.

## Autenticación en Desarrollo

Para facilitar el desarrollo, se ha implementado un sistema de tokens de desarrollo que pueden utilizarse en entornos que no sean de producción:

```
Authorization: Bearer dev_{user_id}
```

Este tipo de token solo funcionará si la variable de entorno `ENVIRONMENT` no está configurada como "production".

## Implementación Técnica

El sistema de autenticación utiliza:

1. **Firebase Authentication**: Para la autenticación principal de usuarios.
2. **JWT (JSON Web Tokens)**: Como mecanismo alternativo y para mayor flexibilidad.
3. **Middleware Flask**: Para proteger rutas que requieren autenticación.

La implementación se encuentra en:
- `controllers/auth_controller.py`: Lógica de negocio para autenticación
- `routes/auth_routes.py`: Endpoints de la API de autenticación
- `utils/auth_middleware.py`: Middleware para proteger rutas

## Variables de Entorno

La configuración del sistema de autenticación puede personalizarse mediante las siguientes variables de entorno:

- `JWT_SECRET`: Clave secreta para firmar los tokens JWT
- `TOKEN_EXPIRY`: Tiempo de validez del token en segundos (por defecto: 86400, es decir, 24 horas)
- `ENVIRONMENT`: Entorno de la aplicación ("development" o "production")