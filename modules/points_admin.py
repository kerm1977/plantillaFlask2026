# modules/points_admin.py - Acciones de superusuario sobre puntos
from datetime import datetime
from db import db
from models import Hiker, HikerPoints


class PointsAdmin:
    """Obsequiar, restar y gestionar puntos manualmente."""

    def _record(self, cedula, hiker_id, points, tipo, detalle, created_by):
        db.session.add(HikerPoints(
            cedula=cedula,
            hiker_id=hiker_id,
            event_id=None,
            points=points,
            tipo=tipo,
            detalle=detalle,
            created_by=created_by,
            created_at=datetime.utcnow()
        ))
        db.session.commit()

    def total(self, cedula):
        return db.session.query(db.func.coalesce(db.func.sum(HikerPoints.points), 0)).filter_by(cedula=cedula).scalar()

    def gift(self, cedula, monto, created_by, mensaje=''):
        if not monto or monto <= 0:
            return {'ok': False, 'error': 'El monto debe ser mayor a 0.'}
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        detalle = f'Obsequio de {monto} puntos'
        if mensaje:
            detalle += f' por {mensaje}'
        self._record(cedula, hiker.id if hiker else None, monto, 'obsequio', detalle, created_by)
        return {'ok': True, 'total': self.total(cedula)}

    def subtract(self, cedula, monto, created_by, mensaje=''):
        if not monto or monto <= 0:
            return {'ok': False, 'error': 'El monto debe ser mayor a 0.'}
        total = self.total(cedula)
        if monto > total:
            return {'ok': False, 'error': 'No se pueden restar más puntos de los que tiene la persona.'}
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        detalle = f'Resta de {monto} puntos'
        if mensaje:
            detalle += f' - {mensaje}'
        self._record(cedula, hiker.id if hiker else None, -monto, 'resta', detalle, created_by)
        return {'ok': True, 'total': self.total(cedula)}


_admin = None


def get_points_admin():
    global _admin
    if _admin is None:
        _admin = PointsAdmin()
    return _admin
