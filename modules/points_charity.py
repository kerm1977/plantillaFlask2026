# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/points_charity.py - Donación de puntos con fin benéfico
# Reglas: con menos de 5.000 puntos solo se dona la TOTALIDAD; con 5.000 o más
# se dona de 1 hasta el 80% del total (nunca queda en cero).
from datetime import datetime
from sqlalchemy import func
from db import db
from models import Hiker, HikerPoints, DonacionFinalidad

MIN_TOTAL = 5000
TOPE = 0.8
TIPO = 'donacion_benefica'


def reglas(total):
    total = int(total or 0)
    if total <= 0:
        return {'modo': 'sin_puntos', 'min': 0, 'max': 0}
    if total < MIN_TOTAL:
        return {'modo': 'total', 'min': total, 'max': total}
    return {'modo': 'parcial', 'min': 1, 'max': int(total * TOPE)}


def finalidades_activas():
    return DonacionFinalidad.query.filter_by(activo=True).order_by(DonacionFinalidad.nombre).all()


def finalidades_admin():
    filas = (db.session.query(HikerPoints.donacion_finalidad_id, func.coalesce(-func.sum(HikerPoints.points), 0),
                              func.count(func.distinct(HikerPoints.cedula)))
             .filter(HikerPoints.donacion_finalidad_id.isnot(None))
             .group_by(HikerPoints.donacion_finalidad_id).all())
    donado = {fid: (int(pts), int(n)) for fid, pts, n in filas}
    return [{'id': f.id, 'nombre': f.nombre, 'descripcion': f.descripcion or '', 'activo': f.activo,
             'donado': donado.get(f.id, (0, 0))[0], 'donantes': donado.get(f.id, (0, 0))[1]}
            for f in DonacionFinalidad.query.order_by(DonacionFinalidad.created_at.desc()).all()]


def donantes(finalidad_id):
    """Personas que donaron a una finalidad: nombre, cédula y total de puntos (de mayor a menor)."""
    filas = (db.session.query(HikerPoints.cedula, func.coalesce(-func.sum(HikerPoints.points), 0),
                              func.max(HikerPoints.created_at))
             .filter(HikerPoints.donacion_finalidad_id == finalidad_id)
             .group_by(HikerPoints.cedula).all())
    nombres = {h.cedula: h.nombre_completo for h in Hiker.query.filter(Hiker.cedula.in_([f[0] for f in filas])).all()}
    lista = [{'nombre': nombres.get(ced) or 'Sin nombre', 'cedula': ced, 'puntos': int(pts),
              'fecha': ult.strftime('%d/%m/%Y') if ult else ''} for ced, pts, ult in filas]
    return sorted(lista, key=lambda d: d['puntos'], reverse=True)


def donar(cedula, finalidad_id, monto, operator):
    from modules.points_engine import get_points_engine
    total = get_points_engine().total_by_cedula(cedula)
    r = reglas(total)
    if r['modo'] == 'sin_puntos':
        return {'ok': False, 'error': 'No tenés puntos para donar.'}
    fin = DonacionFinalidad.query.get(finalidad_id) if finalidad_id else None
    if not fin or not fin.activo:
        return {'ok': False, 'error': 'Seleccioná una finalidad de donación válida.'}
    if r['modo'] == 'total' and monto != total:
        return {'ok': False, 'error': f'Con menos de 5.000 puntos la donación es por la totalidad de tus {total} puntos.'}
    if r['modo'] == 'parcial' and not 1 <= monto <= r['max']:
        return {'ok': False, 'error': f'Tenés {total} puntos. Podés donar de 1 hasta {r["max"]} puntos (80% de tus puntos).'}
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    db.session.add(HikerPoints(
        cedula=cedula, hiker_id=hiker.id if hiker else None, points=-monto, tipo=TIPO,
        detalle=f'Donación benéfica de {monto} puntos a: {fin.nombre}', created_by=operator,
        created_at=datetime.utcnow(), donacion_finalidad_id=fin.id))
    db.session.commit()
    return {'ok': True, 'restante': total - monto, 'finalidad': fin.nombre}
