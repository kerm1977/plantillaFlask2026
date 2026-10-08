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
    reto = db.Column(db.String(30), nullable=False)
    estado = db.Column(db.String(20), default='pendiente', index=True)  # pendiente/aprobada/rechazada
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resuelto_at = db.Column(db.DateTime)
    resuelto_por = db.Column(db.String(100))
