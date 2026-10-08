# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# models_reto.py - Solicitudes de retos de puntos ("Ganar puntos
# desde casa"). La persona confirma el reto -> queda pendiente ->
# el superusuario lo aprueba (acredita puntos) o lo rechaza.
from datetime import datetime
from db import db


class RetoSolicitud(db.Model):
    __tablename__ = 'reto_solicitud'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), nullable=False, index=True)
    hiker_id = db.Column(db.Integer, db.ForeignKey('hiker.id'), nullable=True)
    reto = db.Column(db.String(30), nullable=False)  # clave builtin o 'custom_<id>'
    estado = db.Column(db.String(20), default='pendiente', index=True)  # pendiente/aprobada/rechazada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resuelto_at = db.Column(db.DateTime)
    resuelto_por = db.Column(db.String(100))


class Reto(db.Model):
    """Retos personalizados creados por el superusuario (constructor de retos)."""
    __tablename__ = 'reto'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    texto = db.Column(db.String(500), nullable=False)
    puntos = db.Column(db.Integer, nullable=False, default=0)
    frecuencia_dias = db.Column(db.Integer, default=30)  # días hasta poder repetir el reto
    enlace = db.Column(db.String(300), default='')
    activo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.String(100))
