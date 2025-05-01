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

# Guía de Configuración del Sistema de Autenticación

Este documento explica cómo configurar correctamente el sistema de autenticación de OptiMoney utilizando Firebase Authentication.

## 1. Crear proyecto en Firebase

1. Ve a [Firebase Console](https://console.firebase.google.com/) y crea un nuevo proyecto o usa uno existente.
2. Asegúrate de que el plan de facturación permita la autenticación.

## 2. Habilitar métodos de autenticación

1. En la consola de Firebase, navega a **Authentication** > **Sign-in method**
2. Habilita el método **Email/Password**

## 3. Obtener las credenciales necesarias

### Cuenta de servicio (para Backend)

1. En la consola de Firebase, ve a **Configuración del proyecto** > **Cuentas de servicio**
2. Haz clic en **Generar nueva clave privada**
3. Guarda el archivo JSON descargado en `credentials/firebase-key.json`

### API Key (para autenticación REST)

1. En la consola de Firebase, ve a **Configuración del proyecto** > **Configuración general**
2. Copia la **API Key** que aparece en la sección "Configuración de SDK"

## 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido, reemplazando los valores con los de tu proyecto:

```
# Entorno de ejecución
ENVIRONMENT=development

# Ruta del archivo de credenciales de Firebase
FIREBASE_CREDENTIALS_PATH=./credentials/firebase-key.json

# API Key de Firebase para autenticación con API REST
FIREBASE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Configuración de autenticación
JWT_SECRET=optimoney_secure_secret_key_personalizado
TOKEN_EXPIRY=86400
```

### Generar un JWT_SECRET seguro

Puedes usar este comando para generar una clave secreta segura:

```bash
python -c "import secrets; print(f'optimoney_{secrets.token_hex(16)}')"
```

## 5. Verificar la configuración

Para verificar que la configuración funciona correctamente:

1. Reinicia la aplicación
2. Intenta registrar un usuario:

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"test123", "name":"Test User"}'
```

3. Intenta iniciar sesión:

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com", "password":"test123"}'
```

4. Verifica que recibes un token JWT en la respuesta.

## 6. Uso en desarrollo

Para facilitar las pruebas en entorno de desarrollo, puedes usar tokens simplificados:

1. Genera un token de desarrollo:

```bash
python scripts/create_test_user.py --dev
```

2. Utiliza el token en tus solicitudes:

```bash
curl -X GET http://localhost:8080/api/auth/profile \
  -H "Authorization: Bearer dev_test123"
```

## 7. Activar la autenticación en las rutas

Una vez configurado el sistema de autenticación, debes descomentar el middleware `@authenticate_user` en todas las rutas que requieran autenticación:

```python
# Antes
@transaction_bp.route('', methods=['GET'])
# @authenticate_user
async def get_user_transactions():
    # ...

# Después
@transaction_bp.route('', methods=['GET'])
@authenticate_user
async def get_user_transactions():
    # ...
```

## 8. Depuración de problemas comunes

### El token no es aceptado

- Verifica que estás enviando el header correcto: `Authorization: Bearer tu_token`
- Asegúrate de que el token no ha expirado
- Comprueba que el JWT_SECRET en el archivo .env coincide con el que se usó para generar el token

### Error en el registro de usuarios

- Verifica que la API Key de Firebase es correcta
- Comprueba que el método Email/Password está habilitado en Firebase
- Asegúrate de que el email no está ya registrado

### Error en el inicio de sesión

- Verifica que las credenciales son correctas
- Comprueba que estás usando la API Key correcta de Firebase
- Verifica la conexión a Internet (necesaria para la autenticación con Firebase)

## 9. Resumen de endpoints disponibles

- `/api/auth/register` (POST): Registrar nuevo usuario
- `/api/auth/login` (POST): Iniciar sesión
- `/api/auth/profile` (GET): Obtener perfil de usuario
- `/api/auth/profile` (PUT): Actualizar perfil de usuario
- `/api/auth/change-password` (POST): Cambiar contraseña
- `/api/auth/verify` (GET): Verificar validez del token

Con esta guía, deberías poder configurar y utilizar correctamente el sistema de autenticación de OptiMoney.