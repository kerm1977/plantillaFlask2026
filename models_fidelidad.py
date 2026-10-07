# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# models_fidelidad.py - Programa de fidelidad: ajuste manual de nivel y bitácora
from datetime import datetime
from db import db


class FidelidadAjuste(db.Model):
    """Ajuste manual del nivel VIP de una persona (hecho por superusuario)."""
    __tablename__ = 'fidelidad_ajuste'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), nullable=False, unique=True, index=True)
    nivel = db.Column(db.String(20), nullable=False)  # 'activo' o 'exclusivo'
    nota = db.Column(db.String(255))
    created_by = db.Column(db.String(100))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FidelidadLog(db.Model):
    """Bitácora de cambios de nivel (automáticos o manuales)."""
    __tablename__ = 'fidelidad_log'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), nullable=False, index=True)
    nivel_anterior = db.Column(db.String(20))
    nivel_nuevo = db.Column(db.String(20))
    origen = db.Column(db.String(20), default='manual')  # 'manual' o 'auto'
    nota = db.Column(db.String(255))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
