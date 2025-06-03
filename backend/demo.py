#!/usr/bin/env python3
"""
Script de demostración del backend con SQLite (para pruebas locales)
"""

import os
import sys
import tempfile

# Configurar una base de datos SQLite temporal para demostración
temp_dir = tempfile.gettempdir()
sqlite_path = os.path.join(temp_dir, "tweetstack_demo.db")
os.environ["DATABASE_URL"] = f"sqlite:///{sqlite_path}"

print("🎯 MODO DEMOSTRACIÓN")
print(f"📂 Base de datos SQLite: {sqlite_path}")
print("⚠️  Esta es solo una demostración. Para producción usa PostgreSQL/Neon.")
print()

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Iniciando TweetStack Backend (DEMO)...")
    print("🌐 Servidor: http://localhost:8000")
    print("📖 Documentación: http://localhost:8000/docs")
    print("❤️  Health check: http://localhost:8000/health")
    print()
    
    # Importar y crear las tablas
    try:
        from main_demo import Base, engine
        print("📋 Creando tablas de base de datos...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tablas creadas exitosamente")
        print()
    except Exception as e:
        print(f"❌ Error al crear tablas: {e}")
        sys.exit(1)
    
    print("🎉 ¡Backend listo! Puedes probarlo en http://localhost:8000/docs")
    print("🔥 Presiona Ctrl+C para detener el servidor")
    print("-" * 60)
    
    uvicorn.run(
        "main_demo:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 