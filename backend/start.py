#!/usr/bin/env python3
"""
Script de inicio para el backend FastAPI de TweetStack
"""

import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env
from dotenv import load_dotenv

# Cargar el archivo .env
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# Verificar que la DATABASE_URL esté configurada
if not os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL") == "postgresql://username:password@hostname:port/database":
    print("❌ ERROR: DATABASE_URL no está configurada correctamente")
    print("📝 Por favor edita el archivo .env con tu URL de base de datos real")
    print("💡 Ejemplos:")
    print("   - Neon: DATABASE_URL=postgresql://user:pass@ep-xxx.region.neon.tech/dbname?sslmode=require")
    print("   - Local: DATABASE_URL=postgresql://localhost:5432/tweetstack")
    sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando TweetStack Backend...")
    print(f"📊 Base de datos: {os.getenv('DATABASE_URL')[:50]}...")
    print("🌐 Servidor: http://localhost:8000")
    print("📖 Documentación: http://localhost:8000/docs")
    print("❤️  Health check: http://localhost:8000/health")
    
    # Importar y crear las tablas
    try:
        from main import Base, engine
        print("📋 Creando tablas de base de datos...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
    except Exception as e:
        print(f"⚠️  Error al crear tablas: {e}")
        print("🔧 El servidor continuará, pero podrías necesitar crear las tablas manualmente")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 