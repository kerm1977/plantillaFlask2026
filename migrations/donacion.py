# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/donacion.py - Tabla de finalidades de donación + columna en hiker_points
from sqlalchemy import text, inspect
from db import db


def _migrate_donacion_finalidad():
    from models_donacion import DonacionFinalidad
    if not inspect(db.engine).has_table('donacion_finalidad'):
        DonacionFinalidad.__table__.create(db.engine)


def _migrate_hiker_points_donacion():
    try:
        db.session.execute(text(
            'ALTER TABLE hiker_points ADD COLUMN donacion_finalidad_id INTEGER'))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if 'duplicate column name' in msg or 'already exists' in msg:
            return
        raise
