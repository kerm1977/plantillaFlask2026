# ══ BLINDADO — RASTREO EN VIVO ══
# Código probado y estable. NO modificar sin revisar el flujo completo:
# panel admin -> sesión por evento -> GPS -> viewers con código de 4 dígitos.
# Modelos para rastreo en vivo del coordinador (independiente de otros módulos)
from datetime import datetime
from db import db


class LiveSession(db.Model):
    """Sesión de transmisión de ubicación ligada a un evento.

    - view_token: enlace público para familiares (pide código de 4 dígitos).
    - tx_token:   enlace dedicado del coordinador para transmitir su GPS.
    - code:       código de ingreso de 4 dígitos definido por el superusuario.
    - show_track: si True, los espectadores ven además el recorrido del día.
    """
    __tablename__ = 'live_session'
    id          = db.Column(db.Integer, primary_key=True)
    event_id    = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
    view_token  = db.Column(db.String(32), unique=True, nullable=False)
    tx_token    = db.Column(db.String(32), unique=True, nullable=False)
    code        = db.Column(db.String(8), nullable=False, default='0000')
    show_track  = db.Column(db.Boolean, default=False)
    active      = db.Column(db.Boolean, default=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    stopped_at  = db.Column(db.DateTime)


class LivePoint(db.Model):
    """Un punto GPS reportado por el coordinador."""
    __tablename__ = 'live_point'
    id         = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('live_session.id'),
                           nullable=False, index=True)
    lat        = db.Column(db.Float, nullable=False)
    lng        = db.Column(db.Float, nullable=False)
    acc        = db.Column(db.Float)  # precisión en metros
    ts         = db.Column(db.DateTime, default=datetime.utcnow, index=True)
