# Migración Bitácora: visibilidad (3 opciones) + contenido legado -> página 1
from db import db


def _migrate_bitacora():
    """Agrega visibilidad y migra el contenido viejo a bitacora_page."""
    try:
        conn = db.engine.raw_connection()
        cur = conn.cursor()
        cols = {r[1] for r in cur.execute("PRAGMA table_info(bitacora_entry)")}
        if 'visibilidad' not in cols:
            cur.execute("ALTER TABLE bitacora_entry "
                        "ADD COLUMN visibilidad VARCHAR(20)")
            cur.execute("UPDATE bitacora_entry SET visibilidad="
                        "CASE WHEN privada=0 THEN 'seleccion' "
                        "ELSE 'privada' END WHERE visibilidad IS NULL")
        # Tabla de páginas (por si create_all no la creó aún)
        cur.execute("""CREATE TABLE IF NOT EXISTS bitacora_page (
                        id INTEGER PRIMARY KEY,
                        entry_id INTEGER NOT NULL,
                        orden INTEGER DEFAULT 0,
                        contenido TEXT DEFAULT '')""")
        # El contenido legado de cada entrada pasa a ser su Página 1
        for eid, contenido in cur.execute(
                "SELECT id, contenido FROM bitacora_entry").fetchall():
            tiene = cur.execute(
                "SELECT 1 FROM bitacora_page WHERE entry_id=?",
                (eid,)).fetchone()
            if not tiene and contenido:
                cur.execute("INSERT INTO bitacora_page (entry_id,orden,contenido)"
                            " VALUES (?,0,?)", (eid, contenido))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Migration] Error en _migrate_bitacora: {e}")
