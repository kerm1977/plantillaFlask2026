# modules/points_donations.py - Donar puntos a cumpleañeros
from datetime import datetime, date
from db import db
from sqlalchemy import extract
from models import Hiker, HikerPoints


def _today():
    return date.today()


def birthday_hikers():
    today = _today()
    return Hiker.query.filter(
        extract('month', Hiker.fecha_nacimiento) == today.month,
        extract('day', Hiker.fecha_nacimiento) == today.day
    ).all()


def _record(cedula, hiker_id, points, tipo, detalle, created_by):
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


def _total(cedula):
    return db.session.query(db.func.coalesce(db.func.sum(HikerPoints.points), 0)) \
        .filter(HikerPoints.cedula == cedula).scalar() or 0


def donate(donor_cedula, recipient_cedula, monto, created_by='donante', detalle=''):
    if not monto or monto <= 0:
        return {'ok': False, 'error': 'El monto debe ser mayor a 0.'}
    total = _total(donor_cedula)
    if total < 1000:
        return {'ok': False, 'error': 'Necesitás al menos 1.000 puntos para donar.'}
    if monto >= total:
        return {'ok': False, 'error': 'No podés donar todos tus puntos. Tenés que quedarte con al menos 1.'}
    recipient = Hiker.query.filter_by(cedula=recipient_cedula).first()
    if not recipient:
        return {'ok': False, 'error': 'La cédula del receptor no está registrada.'}
    donor = Hiker.query.filter_by(cedula=donor_cedula).first()
    donor_name = donor.nombre_completo if donor else donor_cedula
    extra = f' - {detalle}' if detalle else ''
    _record(donor_cedula, donor.id if donor else None, -monto, 'donacion_envio',
            f'Donación de {monto} puntos a {recipient.nombre_completo}{extra}', created_by)
    _record(recipient_cedula, recipient.id, monto, 'donacion_recibida',
            f'Donación recibida de {monto} puntos de {donor_name}{extra}', created_by)
    return {'ok': True, 'donor_total': _total(donor_cedula), 'recipient_total': _total(recipient_cedula)}
