# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/compra.py - Tabla de solicitudes de compra de puntos
from sqlalchemy import inspect, text
from db import db


def _migrate_compra_puntos():
    from models_compra import CompraPuntos
    if not inspect(db.engine).has_table('compra_puntos'):
        CompraPuntos.__table__.create(db.engine)


def _migrate_compra_rechazo():
    try:
        db.session.execute(text('ALTER TABLE compra_puntos ADD COLUMN rechazado_at DATETIME'))
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        msg = str(e).lower()
        if 'duplicate column name' in msg or 'already exists' in msg:
            return
        raise
