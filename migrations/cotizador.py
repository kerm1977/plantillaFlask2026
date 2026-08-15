# Auto-generated migration module
from db import db

def _migrate_cotizador():
    """Crea tablas cotizador y cotizador_lugar si no existen."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        
        # Crear tabla cotizador si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cotizador (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                nombre VARCHAR(200) NOT NULL,
                slug VARCHAR(250) UNIQUE,
                clave_acceso VARCHAR(100) NOT NULL,
                titulo VARCHAR(500),
                descripcion TEXT,
                fecha_creacion DATETIME
            )
        ''')
        
        # Agregar columnas titulo y descripcion si no existen
        cursor.execute("PRAGMA table_info(cotizador)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'titulo' not in columns:
            cursor.execute("ALTER TABLE cotizador ADD COLUMN titulo VARCHAR(500)")
        if 'descripcion' not in columns:
            cursor.execute("ALTER TABLE cotizador ADD COLUMN descripcion TEXT")
        if 'mostrar_nombre' not in columns:
            cursor.execute("ALTER TABLE cotizador ADD COLUMN mostrar_nombre BOOLEAN DEFAULT 1")
        if 'mostrar_descripcion' not in columns:
            cursor.execute("ALTER TABLE cotizador ADD COLUMN mostrar_descripcion BOOLEAN DEFAULT 1")
        if 'mostrar_titulo' not in columns:
            cursor.execute("ALTER TABLE cotizador ADD COLUMN mostrar_titulo BOOLEAN DEFAULT 1")
        
        # Crear tabla cotizador_lugar si no existe
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cotizador_lugar (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                cotizador_id INTEGER NOT NULL,
                nombre VARCHAR(500) NOT NULL,
                provincia VARCHAR(100),
                duracion VARCHAR(20) DEFAULT '1_dia',
                fecha_ida VARCHAR(20),
                fecha_regreso VARCHAR(20),
                hora VARCHAR(10),
                maps_ida VARCHAR(1000),
                maps_regreso VARCHAR(1000),
                moneda VARCHAR(20) DEFAULT 'colones',
                precio FLOAT,
                "order" INTEGER DEFAULT 0,
                FOREIGN KEY (cotizador_id) REFERENCES cotizador (id)
            )
        ''')
        
        # Agregar columnas faltantes a cotizador_lugar
        cursor.execute("PRAGMA table_info(cotizador_lugar)")
        lugar_columns = [column[1] for column in cursor.fetchall()]
        if 'precios_historial' not in lugar_columns:
            cursor.execute("ALTER TABLE cotizador_lugar ADD COLUMN precios_historial TEXT DEFAULT '[]'")
        
        conn.commit()
        conn.close()
        print("[Migration] Tablas cotizador creadas/verificadas correctamente")
    except Exception as e:
        print(f"[Migration] Error en _migrate_cotizador: {e}")

