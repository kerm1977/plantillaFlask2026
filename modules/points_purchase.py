# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/points_purchase.py - Compra de puntos: monto + comisión fija (configurable por el superusuario).
# Flujo: pendiente -> (aprobar: acredita puntos) aprobada -> (confirmar) confirmada.
# Rechazar deja la solicitud pendiente, esperando que se confirme el pago de nuevo.
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from db import db
from models import Hiker, CompraPuntos, SiteContent

FEE_DEFECTO = 200
FEE_MAXIMO = 100000
KEY_FEE = 'compra_comision'
MINIMO = 1000
MAXIMO = 1000000
MAX_PENDIENTES = 3
WHATSAPP = '50686529837'
CR = timezone(timedelta(hours=-6))  # Costa Rica no usa horario de verano


def miles(n):
    return '{:,}'.format(int(n)).replace(',', '.')


def fecha_cr(dt):
    """Fecha y hora de Costa Rica (los datos se guardan en UTC)."""
    if not dt:
        return ''
    return dt.replace(tzinfo=timezone.utc).astimezone(CR).strftime('%d/%m/%Y %I:%M %p')


def fee():
    """Comisión vigente por compra (colones). Se cambia en Gestión de superusuario."""
    fila = SiteContent.query.filter_by(key=KEY_FEE).first()
    try:
        return max(0, int(fila.value)) if fila else FEE_DEFECTO
    except (TypeError, ValueError):
        return FEE_DEFECTO


def guardar_fee(valor):
    if not 0 <= valor <= FEE_MAXIMO:
        return {'ok': False, 'error': f'La comisión debe estar entre 0 y {miles(FEE_MAXIMO)} colones.'}
    fila = SiteContent.query.filter_by(key=KEY_FEE).first()
    if fila:
        fila.value = str(valor)
    else:
        db.session.add(SiteContent(key=KEY_FEE, value=str(valor)))
    db.session.commit()
    return {'ok': True, 'fee': valor}


def costo(puntos):
    return int(puntos) + fee()


def url_whatsapp(c, nombre='', pagar=None):
    pagar = pagar or c.monto_pagar
    texto = (f'Hola, he comprado {miles(c.puntos)} puntos. Voy a transferir el dinero por ₡{miles(pagar)} '
             f'({miles(c.puntos)} para mi uso + ₡{miles(pagar - c.puntos)} para donaciones, administración y hosting del sitio). '
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
    return {'ok': True, 'pagar': c.monto_pagar, 'wa': url_whatsapp(c, hiker.nombre_completo if hiker else '')}


def pendientes_usuario(cedula):
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    nombre = hiker.nombre_completo if hiker else ''
    filas = CompraPuntos.query.filter_by(cedula=cedula, estado='pendiente').order_by(CompraPuntos.created_at.desc()).all()
    comision = fee()
    return [{'puntos': c.puntos, 'pagar': c.puntos + comision, 'fecha': fecha_cr(c.created_at),
             'wa': url_whatsapp(c, nombre, c.puntos + comision)} for c in filas]


def pendientes_admin():
    """Solicitudes que siguen en la lista: pendientes de pago y aprobadas sin 'Confirmado'."""
    filas = CompraPuntos.query.filter(CompraPuntos.estado.in_(['pendiente', 'aprobada'])).order_by(CompraPuntos.created_at).all()
    nombres = {h.cedula: h.nombre_completo for h in Hiker.query.filter(Hiker.cedula.in_([c.cedula for c in filas])).all()}
    comision = fee()
    return [{'id': c.id, 'cedula': c.cedula, 'nombre': nombres.get(c.cedula) or 'Sin nombre', 'puntos': c.puntos,
             'pagar': c.puntos + comision if c.estado == 'pendiente' else c.monto_pagar, 'fecha': fecha_cr(c.created_at), 'estado': c.estado,
             'aprobado': fecha_cr(c.resuelto_at) if c.estado == 'aprobada' else '',
             'rechazado': fecha_cr(c.rechazado_at)} for c in filas]


def resolver(compra_id, accion, operator):
    from modules.points_engine import get_points_engine
    c = CompraPuntos.query.get(compra_id)
    if not c:
        return {'ok': False, 'error': 'La solicitud no existe.'}
    ahora = datetime.utcnow()
    if accion == 'aprobar':
        if c.estado != 'pendiente':
            return {'ok': False, 'error': 'La solicitud ya fue aprobada o cerrada.'}
        c.estado, c.resuelto_at, c.resuelto_por = 'aprobada', ahora, operator
        c.monto_pagar = c.puntos + fee()  # se fija la comisión vigente al aprobar
        detalle = (f'Compra de {c.puntos} puntos. Pago de {c.monto_pagar} colones confirmado '
                   f'({c.monto_pagar - c.puntos} colones para donaciones, administración y hosting).')
        get_points_engine()._add_record(c.cedula, c.hiker_id, None, c.puntos, 'compra', detalle, operator)
    elif accion == 'rechazar':
        if c.estado != 'pendiente':
            return {'ok': False, 'error': 'Solo se puede rechazar una solicitud pendiente.'}
        c.rechazado_at, c.resuelto_por = ahora, operator
        db.session.commit()
    elif accion == 'confirmar':
        if c.estado != 'aprobada':
            return {'ok': False, 'error': 'Primero hay que aprobar el pago.'}
        c.estado, c.resuelto_at, c.resuelto_por = 'confirmada', ahora, operator
        db.session.commit()
    else:
        return {'ok': False, 'error': 'Acción no válida.'}
    return {'ok': True, 'cedula': c.cedula, 'puntos': c.puntos}
