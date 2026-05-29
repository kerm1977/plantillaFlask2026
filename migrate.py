import sqlite3

def migrate_database():
    print("Iniciando actualización de la base de datos...")
    # Conectamos directamente al archivo de la base de datos
    conn = sqlite3.connect('local_app.db')
    cursor = conn.cursor()

    # Lista de las nuevas columnas booleanas que agregamos en la Fase 1
    # En SQLite, los booleanos (False) se representan con 0.
    nuevas_columnas = [
        ("logistica_segura", "BOOLEAN", "0"),
        ("is_sold_out", "BOOLEAN", "0"),
        ("solo_chat", "BOOLEAN", "0"),
        ("gpx_filename", "TEXT", "NULL"),
        ("gpx_password", "TEXT", "NULL"),
        ("organicmaps_url", "TEXT", "NULL"),
    ]

    for columna, tipo, default in nuevas_columnas:
        try:
            # Comando SQL puro para añadir la columna respetando los datos actuales
            cursor.execute(f"ALTER TABLE event ADD COLUMN {columna} {tipo} DEFAULT {default}")
            print(f"[OK] Columna '{columna}' anyadida con exito a la tabla event.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"[--] La columna '{columna}' ya existia. Omitiendo...")
            else:
                print(f"[ERROR] Error con '{columna}': {e}")

    # Columna para mostrar logo de sueños en eventos especiales
    try:
        cursor.execute("ALTER TABLE publicacion ADD COLUMN mostrar_logo_suenos BOOLEAN DEFAULT 0")
        print("[OK] Columna 'mostrar_logo_suenos' añadida con éxito a la tabla publicacion.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[--] La columna 'mostrar_logo_suenos' ya existía. Omitiendo...")
        else:
            print(f"[ERROR] Error con 'mostrar_logo_suenos': {e}")

    # Tabla para configuración del logo de sueños
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logo_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mostrar BOOLEAN DEFAULT 1,
                enlace VARCHAR(500),
                tamaño_pc INTEGER DEFAULT 150,
                tamaño_mobile INTEGER DEFAULT 120,
                posicion_left INTEGER DEFAULT 20,
                posicion_bottom INTEGER DEFAULT 100,
                nombre_archivo VARCHAR(255) DEFAULT 'logosueños.png',
                updated_at DATETIME,
                created_at DATETIME
            )
        """)
        print("[OK] Tabla 'logo_config' creada o ya existía.")
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Error creando tabla 'logo_config': {e}")

    # Columna para monto recaudado en publicaciones
    try:
        cursor.execute("ALTER TABLE publicacion ADD COLUMN monto_recaudado REAL DEFAULT 0.0")
        print("[OK] Columna 'monto_recaudado' añadida con éxito a la tabla publicacion.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("[--] La columna 'monto_recaudado' ya existía. Omitiendo...")
        else:
            print(f"[ERROR] Error con 'monto_recaudado': {e}")

    # Columnas adicionales para SINPE y cuentas bancarias
    new_columns = [
        ('sinpe_info_2', 'VARCHAR(300)'),
        ('sinpe_info_3', 'VARCHAR(300)'),
        ('sinpe_info_4', 'VARCHAR(300)'),
        ('cuenta_info_2', 'VARCHAR(400)'),
        ('cuenta_info_3', 'VARCHAR(400)'),
        ('cuenta_info_4', 'VARCHAR(400)'),
        ('cuentas_visibles', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE publicacion ADD COLUMN {col_name} {col_type} DEFAULT ''")
            print(f"[OK] Columna '{col_name}' añadida con éxito a la tabla publicacion.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"[--] La columna '{col_name}' ya existía. Omitiendo...")
            else:
                print(f"[ERROR] Error con '{col_name}': {e}")

    # Guardamos los cambios y cerramos
    conn.commit()
    conn.close()
    print("Actualizacion completada. Ya puedes arrancar Flask normalmente.")

if __name__ == '__main__':
    migrate_database()