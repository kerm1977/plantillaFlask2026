# ══ BLINDADO — BITÁCORA ══
# Módulo independiente y estable. NO modificar sin revisar el flujo:
# lista -> entrada (páginas) -> visibilidad (privada/publica/seleccion).
# Solo el superusuario escribe/edita/elimina.
from datetime import datetime
from db import db


class BitacoraEntry(db.Model):
    """Una entrada de la bitácora (mini blog), con páginas ordenadas."""
    __tablename__ = 'bitacora_entry'
    id          = db.Column(db.Integer, primary_key=True)
    titulo      = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, default='')   # descripción / nota corta
    contenido   = db.Column(db.Text, default='')   # legado: migrado a página 1
    privada     = db.Column(db.Boolean, default=True)  # legado -> visibilidad
    visibilidad = db.Column(db.String(20), default='privada')
    editado_por = db.Column(db.String(160), default='')
    creado      = db.Column(db.DateTime, default=datetime.utcnow)
    actualizado = db.Column(db.DateTime, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    shares = db.relationship('BitacoraShare', backref='entry',
                             cascade='all, delete-orphan', lazy=True)
    pages = db.relationship('BitacoraPage', backref='entry',
                            cascade='all, delete-orphan', lazy=True,
                            order_by='BitacoraPage.orden')


class BitacoraPage(db.Model):
    """Una página de contenido WYSIWYG dentro de una entrada."""
    __tablename__ = 'bitacora_page'
    id        = db.Column(db.Integer, primary_key=True)
    entry_id  = db.Column(db.Integer, db.ForeignKey('bitacora_entry.id'),
                          nullable=False, index=True)
    orden     = db.Column(db.Integer, default=0)
    contenido = db.Column(db.Text, default='')


class BitacoraShare(db.Model):
    """Usuario registrado con quien se comparte una entrada 'seleccion'."""
    __tablename__ = 'bitacora_share'
    id       = db.Column(db.Integer, primary_key=True)
    entry_id = db.Column(db.Integer, db.ForeignKey('bitacora_entry.id'),
                         nullable=False, index=True)
    user_id  = db.Column(db.Integer, db.ForeignKey('user.id'),
                         nullable=False, index=True)
