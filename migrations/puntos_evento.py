# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/puntos_evento.py - Tabla de eventos de puntos + columna dedup
from sqlalchemy import text, inspect
from db import db


def _migrate_puntos_evento():
    from models_puntos_evento import PuntosEvento
    if not inspect(db.engine).has_table('puntos_evento'):
        PuntosEvento.__table__.create(db.engine)


def _migrate_hiker_points_puntos_evento():
    try:
        db.session.execute(text(
            'ALTER TABLE hiker_points ADD COLUMN puntos_evento_id INTEGER'))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if 'duplicate column name' in msg or 'already exists' in msg:
            return
        raise
