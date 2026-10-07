# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# migrations/fidelidad.py - Tablas del programa de fidelidad
from sqlalchemy import inspect
from db import db


def _migrate_fidelidad():
    from models_fidelidad import FidelidadAjuste, FidelidadLog
    if not inspect(db.engine).has_table('fidelidad_ajuste'):
        FidelidadAjuste.__table__.create(db.engine)
    if not inspect(db.engine).has_table('fidelidad_log'):
        FidelidadLog.__table__.create(db.engine)
