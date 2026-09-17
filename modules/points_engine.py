# modules/points_engine.py - Motor de puntuación por cédula
from db import db
from models import Hiker, HikerPoints, Event, EventRegistration, User
from sqlalchemy import func
from datetime import datetime
from modules.points_helpers import is_past_event


class PointsEngine:
    """Asigna, retira y consulta puntos acumulados por cédula."""

    def total_by_cedula(self, cedula):
        return db.session.query(func.coalesce(func.sum(HikerPoints.points), 0)) \
            .filter(HikerPoints.cedula == cedula).scalar() or 0

    def history(self, cedula):
        return HikerPoints.query \
            .filter_by(cedula=cedula) \
            .order_by(HikerPoints.created_at.desc()).all()

    def history_with_names(self, cedula):
        rows = self.history(cedula)
        result = []
        for row in rows:
            hiker = Hiker.query.get(row.hiker_id) if row.hiker_id else None
            event = Event.query.get(row.event_id) if row.event_id else None
            result.append({
                'id': row.id,
                'cedula': row.cedula,
                'nombre_completo': hiker.nombre_completo if hiker else '',
                'evento_nombre': event.nombre_lugar if event else '',
                'puntos': row.points,
                'tipo': row.tipo,
                'detalle': row.detalle,
                'creado_por': row.created_by,
                'creado_at': row.created_at.isoformat() if row.created_at else '',
            })
        return result

    def event_assignments(self, event_id):
        rows = HikerPoints.query.filter_by(event_id=event_id, tipo='participacion').all()
        result = {}
        for row in rows:
            result[row.cedula] = {
                'cedula': row.cedula,
                'hiker_id': row.hiker_id,
                'puntos': row.points,
                'retirado': False,
            }
        retiros = HikerPoints.query.filter_by(event_id=event_id, tipo='retiro').all()
        for row in retiros:
            if row.cedula in result:
                result[row.cedula]['puntos'] += row.points
                if result[row.cedula]['puntos'] <= 0:
                    result[row.cedula]['retirado'] = True
            else:
                result[row.cedula] = {'cedula': row.cedula, 'hiker_id': row.hiker_id, 'puntos': row.points, 'retirado': True}
        return list(result.values())

    def assign_to_event(self, event_id, operator_name):
        event = Event.query.get_or_404(event_id)
        if not event.puntos:
            return {'ok': False, 'error': 'Esta caminata no tiene puntos configurados.'}
        if is_past_event(event):
            return {'ok': False, 'error': 'La caminata ya pasó, no se pueden generar puntos.'}

        regs = EventRegistration.query.filter_by(event_id=event_id).all()
        if not regs:
            return {'ok': False, 'error': 'No hay registrados en esta caminata.'}

        added = 0
        skipped = 0
        for reg in regs:
            hiker = Hiker.query.get(reg.hiker_id)
            if not hiker:
                continue
            existing = HikerPoints.query.filter_by(
                event_id=event_id, cedula=hiker.cedula, tipo='participacion'
            ).first()
            if existing:
                skipped += 1
                continue
            record = HikerPoints(
                cedula=hiker.cedula,
                hiker_id=hiker.id,
                event_id=event_id,
                points=event.puntos,
                tipo='participacion',
                detalle=f'Participación en {event.nombre_lugar}',
                created_by=operator_name,
                created_at=datetime.utcnow()
            )
            db.session.add(record)
            added += 1

        db.session.commit()
        return {'ok': True, 'added': added, 'skipped': skipped, 'points_per_person': event.puntos}

    def withdraw(self, event_id, cedula, operator_name, justificado=False, mensaje=''):
        event = Event.query.get_or_404(event_id)
        hiker = Hiker.query.filter_by(cedula=cedula).first()

        existing = HikerPoints.query.filter_by(
            event_id=event_id, cedula=cedula, tipo='retiro'
        ).first()
        if existing:
            return {'ok': False, 'error': 'Esa persona ya fue retirada de esta caminata.'}

        base = event.puntos or 0
        extra = 0 if justificado else 250
        total_deducted = base + extra
        detalle = f'Retiro en {event.nombre_lugar}'
        if justificado:
            detalle += f' (justificado por lesión: {mensaje})'
        else:
            detalle += ' (sin justificación, -250 puntos adicionales)'

        record = HikerPoints(
            cedula=cedula,
            hiker_id=hiker.id if hiker else None,
            event_id=event_id,
            points=-total_deducted,
            tipo='retiro',
            detalle=detalle,
            created_by=operator_name,
            created_at=datetime.utcnow()
        )
        db.session.add(record)

        reembolso = 0
        descuento = 0
        redencion = HikerPoints.query.filter_by(
            event_id=event_id, cedula=cedula, tipo='redencion_caminata'
        ).order_by(HikerPoints.id.desc()).first()
        if redencion:
            monto_redencion = abs(redencion.points)
            valor_redencion = monto_redencion  # caminata = 100%
            descuento = int(round(valor_redencion * 0.12))
            reembolso = monto_redencion - descuento
            existe_reversion = HikerPoints.query.filter_by(
                event_id=event_id, cedula=cedula, tipo='reversion'
            ).first()
            if not existe_reversion:
                db.session.add(HikerPoints(
                    cedula=cedula,
                    hiker_id=hiker.id if hiker else None,
                    event_id=event_id,
                    points=reembolso,
                    tipo='reversion',
                    detalle=(f'Reversión por retiro en {event.nombre_lugar}. '
                             f'Redención original: {monto_redencion} puntos, '
                             f'devolución: {reembolso} puntos (descuento 12% del valor).'),
                    created_by=operator_name,
                    created_at=datetime.utcnow()
                ))

        db.session.commit()
        return {
            'ok': True,
            'points_deducted': total_deducted,
            'reembolso': reembolso,
            'descuento': descuento,
            'justificado': justificado,
            'mensaje': mensaje
        }


    def has_earned(self, event_id, cedula):
        return HikerPoints.query.filter_by(event_id=event_id, cedula=cedula, tipo='participacion').first() is not None

    def _get_hiker(self, cedula):
        return Hiker.query.filter_by(cedula=cedula).first()

    def _add_record(self, cedula, hiker_id, event_id, points, tipo, detalle, created_by):
        db.session.add(HikerPoints(
            cedula=cedula, hiker_id=hiker_id, event_id=event_id, points=points,
            tipo=tipo, detalle=detalle, created_by=created_by, created_at=datetime.utcnow()
        ))
        db.session.commit()

    def earn_from_link(self, event_id, cedula, operator='link'):
        event = Event.query.get_or_404(event_id)
        if not event.puntos:
            return {'ok': False, 'error': 'Esta caminata no tiene puntos configurados.'}
        if is_past_event(event):
            return {'ok': False, 'error': 'La caminata ya pasó, no se pueden generar puntos.'}
        if self.has_earned(event_id, cedula):
            return {'ok': False, 'error': 'Esta cédula ya ganó puntos en esta caminata.'}
        hiker = self._get_hiker(cedula)
        self._add_record(cedula, hiker.id if hiker else None, event_id, event.puntos,
                         'participacion', f'Puntos ganados en {event.nombre_lugar} (enlace)', operator)
        return {'ok': True, 'puntos_ganados': event.puntos, 'total': self.total_by_cedula(cedula)}

    def purchase_cost(self, puntos):
        if puntos < 500:
            return None
        fee = 150 if puntos <= 1000 else 250
        return {'puntos': puntos, 'fee': fee, 'total': puntos + fee, 'tribu': 50, 'admin': fee - 50}

    def buy_points(self, cedula, event_id, puntos, operator='link'):
        cost = self.purchase_cost(puntos)
        if not cost:
            return {'ok': False, 'error': 'La compra mínima es de 500 puntos.'}
        hiker = self._get_hiker(cedula)
        detalle = (f'Compra de {puntos} puntos. Total a pagar {cost["total"]} colones (Jenny Ceciliano Córdova). '
                   f'Excedente {cost["fee"]}: 50 para actividades La Tribu, {cost["admin"]} administrativos.')
        self._add_record(cedula, hiker.id if hiker else None, event_id, puntos, 'compra', detalle, operator)
        return {'ok': True, 'costo': cost}

    def redeem(self, cedula, monto, tipo, operator='link', detalle='', event_id=None):
        total = self.total_by_cedula(cedula)
        if total < 5000:
            return {'ok': False, 'error': 'No tenés 5.000 puntos acumulados para redimir.'}
        if monto <= 0 or monto > total:
            return {'ok': False, 'error': 'El monto a redimir no es válido.'}
        valor = monto if tipo == 'caminata' else int(monto * 0.8)
        hiker = self._get_hiker(cedula)
        base = f'Redención de {monto} puntos. Tipo: {"Caminata" if tipo == "caminata" else "Devolución de dinero"}. Valor aplicado: {valor}.'
        if detalle:
            base += f' Detalle: {detalle}.'
        self._add_record(cedula, hiker.id if hiker else None, event_id, -monto, f'redencion_{tipo}', base, operator)
        return {'ok': True, 'monto': monto, 'valor': valor}


_points_engine = None


def get_points_engine():
    global _points_engine
    if _points_engine is None:
        _points_engine = PointsEngine()
    return _points_engine
