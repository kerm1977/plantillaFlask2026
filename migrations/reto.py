# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/reto.py - Tablas de retos + columna frecuencia_dias
from sqlalchemy import inspect, text
from db import db


def _migrate_reto():
    from models_reto import Reto, RetoSolicitud
    if not inspect(db.engine).has_table('reto'):
        Reto.__table__.create(db.engine)
    if not inspect(db.engine).has_table('reto_solicitud'):
        RetoSolicitud.__table__.create(db.engine)


def _migrate_reto_frecuencia():
    try:
        db.session.execute(text('ALTER TABLE reto ADD COLUMN frecuencia_dias INTEGER DEFAULT 30'))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if 'duplicate column name' in msg or 'already exists' in msg:
            return
        raise
