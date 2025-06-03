# TweetStack Backend - FastAPI

Backend REST API para la aplicación TweetStack construido con FastAPI y SQLAlchemy.

## 🚀 Configuración Rápida

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

Edita el archivo `.env` con tu URL de base de datos:

```bash
# Para Neon (recomendado)
DATABASE_URL=postgresql://user:password@ep-hostname.region.neon.tech/dbname?sslmode=require

# Para PostgreSQL local
DATABASE_URL=postgresql://localhost:5432/tweetstack
```

### 3. Iniciar Servidor

```bash
python start.py
```

O alternativamente:

```bash
python main.py
```

## 📊 Base de Datos

### Modelos Incluidos:

-   **Tweet**: Tweets individuales con soporte para hilos
-   **Collection**: Colecciones para organizar tweets
-   **tweet_collections**: Tabla de relación many-to-many

### Auto-creación de Tablas:

El script `start.py` crea automáticamente las tablas necesarias al iniciar.

## 🔗 Endpoints API

### Tweets

-   `POST /tweets` - Crear tweet
-   `GET /tweets?user_id={id}` - Obtener tweets del usuario
-   `GET /tweets/{tweet_id}` - Obtener tweet específico
-   `PUT /tweets/{tweet_id}` - Actualizar tweet
-   `PUT /tweets/{tweet_id}/schedule` - Actualizar programación
-   `DELETE /tweets/{tweet_id}` - Eliminar tweet

### Collections

-   `POST /collections` - Crear colección
-   `GET /collections?user_id={id}` - Obtener colecciones del usuario
-   `GET /collections/{collection_id}` - Obtener colección específica
-   `PUT /collections/{collection_id}` - Actualizar colección
-   `DELETE /collections/{collection_id}` - Eliminar colección

### Sistema

-   `GET /health` - Health check
-   `GET /docs` - Documentación interactiva (Swagger UI)

## 🌐 URLs Importantes

-   **Servidor**: http://localhost:8000
-   **Documentación**: http://localhost:8000/docs
-   **Health Check**: http://localhost:8000/health

## 🔧 Desarrollo

### Hot Reload

El servidor se reinicia automáticamente al detectar cambios en el código.

### Logs

Los logs aparecen en la consola con información de requests y errores.

### CORS

Configurado para permitir requests desde:

-   http://localhost:3000 (Frontend de desarrollo)
-   Dominios de producción (configurables)

## 📝 Estructura de Datos

### Tweet

```json
{
    "id": 1,
    "user_id": "demo-user-123",
    "content": "Mi tweet",
    "media_path": "",
    "media_type": "",
    "is_thread": false,
    "thread_tweets": [],
    "scheduled_date": null,
    "created_at": "2024-01-01T00:00:00",
    "collections": []
}
```

### Collection

```json
{
    "id": 1,
    "name": "Mi Colección",
    "description": "Descripción",
    "user_id": "demo-user-123",
    "tweet_count": 5,
    "created_at": "2024-01-01T00:00:00"
}
```
