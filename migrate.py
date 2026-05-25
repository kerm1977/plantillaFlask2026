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

    # Guardamos los cambios y cerramos
    conn.commit()
    conn.close()
    print("Actualizacion completada. Ya puedes arrancar Flask normalmente.")

if __name__ == '__main__':
    migrate_database()