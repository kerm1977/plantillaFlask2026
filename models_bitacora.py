# ══ BITÁCORA — mini blog interno ══
# Módulo independiente. Solo el superusuario escribe/edita/elimina.
# Visibilidad: privada = solo superusuarios; compartida = superusuarios
# + los usuarios registrados seleccionados en BitacoraShare.
from datetime import datetime
from db import db


class BitacoraEntry(db.Model):
    """Una entrada de la bitácora (mini blog)."""
    __tablename__ = 'bitacora_entry'
    id          = db.Column(db.Integer, primary_key=True)
    titulo      = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')   # descripción / nota corta
    contenido   = db.Column(db.Text, default='')   # HTML del WYSIWYG
    privada     = db.Column(db.Boolean, default=True)
    creado      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    shares = db.relationship('BitacoraShare', backref='entry',
                             cascade='all, delete-orphan', lazy=True)


class BitacoraShare(db.Model):
    """Usuario registrado con quien se comparte una entrada no privada."""
    __tablename__ = 'bitacora_share'
    id       = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('bitacora_entry.id'),
                         nullable=False, index=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'),
                         nullable=False, index=True)
