# modules/points_bonuses.py - Regalías automáticas de puntos
from datetime import datetime
from sqlalchemy import extract
from db import db
from models import Hiker, HikerPoints


class PointsBonuses:
    """Aplica regalías automáticas: bienvenida y cumpleaños."""

    def _record(self, cedula, hiker_id, points, tipo, detalle):
        db.session.add(HikerPoints(
            cedula=cedula,
            hiker_id=hiker_id,
            event_id=None,
            points=points,
            tipo=tipo,
            detalle=detalle,
            created_by='sistema',
            created_at=datetime.utcnow()
        ))
        db.session.commit()

    def welcome(self, cedula):
        existing = HikerPoints.query.filter_by(cedula=cedula).first()
        if existing:
            return 0
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        self._record(cedula, hiker.id if hiker else None, 500, 'bienvenida', '500 puntos de regalía por primera entrada al sistema de puntos')
        return 500

    def birthday(self, cedula):
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        if not hiker or not hiker.fecha_nacimiento:
            return 0
        now = datetime.utcnow()
        if hiker.fecha_nacimiento.month != now.month or hiker.fecha_nacimiento.day != now.day:
            return 0
        start = datetime(now.year, 1, 1)
        end = datetime(now.year + 1, 1, 1)
        existing = HikerPoints.query.filter_by(cedula=cedula, tipo='cumpleanos').filter(
            HikerPoints.created_at >= start, HikerPoints.created_at < end
        ).first()
        if existing:
            return 0
        self._record(cedula, hiker.id, 500, 'cumpleanos', f'500 puntos de regalo por cumpleaños ({hiker.fecha_nacimiento.strftime("%d/%m")}, año {now.year})')
        return 500

    def apply(self, cedula):
        added = 0
        added += self.welcome(cedula)
        added += self.birthday(cedula)
        return added


_bonuses = None


def get_points_bonuses():
    global _bonuses
    if _bonuses is None:
        _bonuses = PointsBonuses()
    return _bonuses
