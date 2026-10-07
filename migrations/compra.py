# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/compra.py - Tabla de solicitudes de compra de puntos
from sqlalchemy import inspect
from db import db


def _migrate_compra_puntos():
    from models_compra import CompraPuntos
    if not inspect(db.engine).has_table('compra_puntos'):
        CompraPuntos.__table__.create(db.engine)
