from db import db


def _migrate_holidays_autoplay():
    """Agrega la columna autoplay a la tabla holidays si no existe."""
    try:
        conn = db.engine.raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(holidays)")
        existing_cols = {row[1] for row in cursor.fetchall()}

        if 'autoplay' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN autoplay BOOLEAN DEFAULT 0")
            conn.commit()

        if 'show_confetti' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN show_confetti BOOLEAN DEFAULT 1")
            conn.commit()

        if 'custom_message' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN custom_message TEXT")
            conn.commit()

        if 'show_player' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN show_player BOOLEAN DEFAULT 1")
            conn.commit()

        if 'end_month' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN end_month INTEGER")
            conn.commit()

        if 'end_day' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN end_day INTEGER")
            conn.commit()

        if 'superuser_only' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN superuser_only BOOLEAN DEFAULT 0")
            conn.commit()

        if 'link_url' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN link_url TEXT")
            conn.commit()

        if 'link_enabled' not in existing_cols:
            cursor.execute("ALTER TABLE holidays ADD COLUMN link_enabled BOOLEAN DEFAULT 0")
            conn.commit()

        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_holidays_autoplay: {e}")
