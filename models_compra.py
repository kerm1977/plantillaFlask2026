# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# models_compra.py - Solicitudes de compra de puntos (se acreditan al aprobar el pago)
from datetime import datetime
from db import db


class CompraPuntos(db.Model):
    __tablename__ = 'compra_puntos'
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(50), nullable=False, index=True)
    hiker_id = db.Column(db.Integer, db.ForeignKey('hiker.id'), nullable=True)
    puntos = db.Column(db.Integer, nullable=False)
    monto_pagar = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(20), default='pendiente', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resuelto_at = db.Column(db.DateTime)
    resuelto_por = db.Column(db.String(100))
