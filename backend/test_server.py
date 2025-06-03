#!/usr/bin/env python3
"""
Script simple para probar el servidor FastAPI
"""

import os
import tempfile

# Configurar SQLite temporal
temp_db = os.path.join(tempfile.gettempdir(), "tweetstack_test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{temp_db}"

print("🧪 SERVIDOR DE PRUEBA")
print(f"📂 Base de datos: {temp_db}")
print("🌐 Servidor: http://localhost:8000")
print("📖 Documentación: http://localhost:8000/docs")
print("❤️  Health check: http://localhost:8000/health")
print()

if __name__ == "__main__":
    # Crear las tablas
    from main_demo import Base, engine, app
    print("📋 Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")
    
    # Iniciar servidor
    import uvicorn
    print("🚀 Iniciando servidor...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info") 