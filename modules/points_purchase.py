# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/points_purchase.py - Compra de puntos: monto + 200 colones fijos, acreditación al aprobar el pago
from datetime import datetime
from urllib.parse import quote
from db import db
from models import Hiker, CompraPuntos

FEE = 200
MINIMO = 1000
MAXIMO = 1000000
MAX_PENDIENTES = 3
WHATSAPP = '50686529837'


def miles(n):
    return '{:,}'.format(int(n)).replace(',', '.')


def costo(puntos):
    return int(puntos) + FEE


def url_whatsapp(c, nombre=''):
    texto = (f'Hola, he comprado {miles(c.puntos)} puntos. Voy a transferir el dinero por ₡{miles(c.monto_pagar)} '
             f'({miles(c.puntos)} para mi uso + ₡{FEE} para donaciones, administración y hosting del sitio). '
             f'Cédula: {c.cedula}{" - " + nombre if nombre else ""}. Quedo atento a la aprobación del pago.')
    return f'https://wa.me/{WHATSAPP}?text=' + quote(texto)


def solicitar(cedula, puntos):
    if puntos < MINIMO or puntos > MAXIMO:
        return {'ok': False, 'error': f'La compra mínima es de {miles(MINIMO)} puntos (máximo {miles(MAXIMO)}).'}
    if CompraPuntos.query.filter_by(cedula=cedula, estado='pendiente').count() >= MAX_PENDIENTES:
        return {'ok': False, 'error': f'Ya tenés {MAX_PENDIENTES} solicitudes pendientes. Esperá a que se aprueben tus pagos.'}
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    c = CompraPuntos(cedula=cedula, hiker_id=hiker.id if hiker else None, puntos=puntos, monto_pagar=costo(puntos))
    db.session.add(c)
    db.session.commit()
    return {'ok': True, 'pagar': c.monto_pagar}


def pendientes_usuario(cedula):
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    nombre = hiker.nombre_completo if hiker else ''
    filas = CompraPuntos.query.filter_by(cedula=cedula, estado='pendiente').order_by(CompraPuntos.created_at.desc()).all()
    return [{'puntos': c.puntos, 'pagar': c.monto_pagar, 'fecha': c.created_at.strftime('%d/%m/%Y %H:%M'),
             'wa': url_whatsapp(c, nombre)} for c in filas]


def pendientes_admin():
    filas = CompraPuntos.query.filter_by(estado='pendiente').order_by(CompraPuntos.created_at).all()
    nombres = {h.cedula: h.nombre_completo for h in Hiker.query.filter(Hiker.cedula.in_([c.cedula for c in filas])).all()}
    return [{'id': c.id, 'cedula': c.cedula, 'nombre': nombres.get(c.cedula) or 'Sin nombre', 'puntos': c.puntos,
             'pagar': c.monto_pagar, 'fecha': c.created_at.strftime('%d/%m/%Y %H:%M')} for c in filas]


def resolver(compra_id, aprobar, operator):
    from modules.points_engine import get_points_engine
    c = CompraPuntos.query.get(compra_id)
    if not c or c.estado != 'pendiente':
        return {'ok': False, 'error': 'La solicitud ya fue resuelta o no existe.'}
    c.estado = 'aprobada' if aprobar else 'rechazada'
    c.resuelto_at = datetime.utcnow()
    c.resuelto_por = operator
    if aprobar:
        detalle = (f'Compra de {c.puntos} puntos. Pago de {c.monto_pagar} colones confirmado '
                   f'({FEE} colones para donaciones, administración y hosting).')
        get_points_engine()._add_record(c.cedula, c.hiker_id, None, c.puntos, 'compra', detalle, operator)
    else:
        db.session.commit()
    return {'ok': True, 'cedula': c.cedula, 'puntos': c.puntos}
