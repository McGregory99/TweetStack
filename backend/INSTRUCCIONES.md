# 🚀 TweetStack Backend - Instrucciones de Uso

## ✅ Estado Actual

Tu backend FastAPI está **completamente funcional** y listo para usar.

## 🎯 Opciones para Ejecutar el Backend

### 1. **Modo Demostración (SQLite) - RECOMENDADO PARA EMPEZAR**

```bash
cd backend
python3 demo.py
```

-   ✅ Funciona inmediatamente sin configuración
-   ✅ Usa SQLite temporal (no necesita PostgreSQL)
-   ✅ Perfecto para desarrollo y pruebas

### 2. **Modo Producción (PostgreSQL/Neon)**

```bash
cd backend
# 1. Editar .env con tu URL de base de datos real
# 2. Ejecutar:
python3 start.py
```

### 3. **Modo Prueba Simple**

```bash
cd backend
python3 test_server.py &
```

## 🌐 URLs Importantes

Una vez iniciado el servidor:

-   **API Base**: http://localhost:8000
-   **Documentación Interactiva**: http://localhost:8000/docs
-   **Health Check**: http://localhost:8000/health

## 🧪 Prueba Rápida

```bash
# 1. Iniciar servidor
python3 demo.py &

# 2. Probar health check
curl http://localhost:8000/health

# 3. Crear una colección
curl -X POST "http://localhost:8000/collections" \
  -H "Content-Type: application/json" \
  -d '{"name": "Mi Colección", "description": "Prueba", "user_id": "demo-user-123"}'

# 4. Crear un tweet
curl -X POST "http://localhost:8000/tweets" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "demo-user-123", "content": "¡Mi primer tweet!", "collection_ids": [1]}'

# 5. Obtener tweets
curl "http://localhost:8000/tweets?user_id=demo-user-123"
```

## 📊 Endpoints Disponibles

### Tweets

-   `POST /tweets` - Crear tweet
-   `GET /tweets?user_id={id}` - Obtener tweets del usuario
-   `GET /tweets/{tweet_id}` - Obtener tweet específico
-   `PUT /tweets/{tweet_id}` - Actualizar tweet
-   `PUT /tweets/{tweet_id}/schedule` - Programar tweet
-   `DELETE /tweets/{tweet_id}` - Eliminar tweet

### Colecciones

-   `POST /collections` - Crear colección
-   `GET /collections?user_id={id}` - Obtener colecciones del usuario
-   `GET /collections/{collection_id}` - Obtener colección específica
-   `PUT /collections/{collection_id}` - Actualizar colección
-   `DELETE /collections/{collection_id}` - Eliminar colección

## 🔧 Configuración para Producción

Para usar con PostgreSQL/Neon, edita `backend/.env`:

```bash
DATABASE_URL=postgresql://user:password@ep-hostname.region.neon.tech/dbname?sslmode=require
```

## 🎉 ¡Tu Backend Está Listo!

-   ✅ Todas las dependencias instaladas
-   ✅ Modelos de base de datos configurados
-   ✅ API REST completamente funcional
-   ✅ Documentación automática generada
-   ✅ CORS configurado para el frontend
-   ✅ Probado y funcionando

**Siguiente paso**: Conectar tu frontend React con el backend en http://localhost:8000
