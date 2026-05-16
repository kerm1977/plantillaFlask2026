import os
from app import create_app
from db import db

def instalar():
    """
    Este script inicializa la base de datos y crea las tablas 
    que hagan falta basándose en el archivo models.py actualizado.
    """
    app = create_app()
    with app.app_context():
        print("=== Iniciando actualización de Base de Datos (La Tribu) ===")
        
        # create_all detecta si hay tablas nuevas (como Hiker) y las crea.
        # Nota: Si ya existe la tabla pero agregaste una columna (como fecha_nacimiento),
        # create_all NO la agregará automáticamente en SQLite. 
        db.create_all()
        
        print("✅ ¡Éxito! El sistema ha intentado sincronizar las tablas del CRM.")
        print("Si el error de 'no such column' persiste, borra el archivo .db local y vuelve a correr este script.")

if __name__ == '__main__':
    instalar()