# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# models_puntos_evento.py - Eventos de puntos (QR propio, fuera de caminatas)
from datetime import datetime
from db import db


class PuntosEvento(db.Model):
    __tablename__ = 'puntos_evento'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text)
    puntos = db.Column(db.Integer, default=0)
    activo = db.Column(db.Boolean, default=True)
    publico = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
