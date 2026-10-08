# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# modules/retos.py - Retos de "Ganar puntos desde casa".
# La persona confirma -> solicitud pendiente -> superusuario
# aprueba (acredita puntos) o rechaza (aviso por WhatsApp).
# Cada reto se puede ganar una vez por mes.
import re
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from db import db
from models import Hiker, RetoSolicitud
from modules.points_engine import get_points_engine
from modules.points_purchase import fecha_cr

RETOS = {
    'datos': {
        'label': 'Actualizar mis datos',
        'puntos': 200,
        'wa': ('Hola, ya actualicé todos mis datos en el sistema de puntos de La Tribu de los '
               'Libres. Por favor confirmen el reto. Cédula: {cedula} - {nombre}.'),
    },
    'foto_perfil': {
        'label': 'Foto de perfil de Facebook con la camisa',
        'puntos': 200,
        'wa': ('Hola, ya puse mi foto de perfil en Facebook con la camisa de La Tribu de los '
               'Libres durante una semana. Envío el pantallazo para que lo confirmen. '
               'Cédula: {cedula} - {nombre}.'),
    },
    'foto_portada': {
        'label': 'Foto de portada de Facebook con la camisa y un paisaje',
        'puntos': 200,
        'wa': ('Hola, ya puse mi foto de portada de Facebook con la camisa de La Tribu de los '
               'Libres y un paisaje de fondo. Envío el pantallazo para que lo confirmen. '
               'Cédula: {cedula} - {nombre}.'),
    },
}
WHATSAPP_COORD = '50686529837'
_CR = timezone(timedelta(hours=-6))


def _mes(dt):
    if not dt:
        return ''
    d = dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return d.astimezone(_CR).strftime('%Y-%m')


def estado_reto(cedula, reto):
    """'pendiente' si hay solicitud sin resolver, 'ganado' si se aprobó este mes, 'ok' si puede hacerlo."""
    if reto not in RETOS:
        return 'ok'
    base = RetoSolicitud.query.filter_by(cedula=str(cedula), reto=reto)
    if base.filter_by(estado='pendiente').first():
        return 'pendiente'
    mes = _mes(datetime.now(timezone.utc))
    for s in base.filter_by(estado='aprobada').all():
        if _mes(s.resuelto_at) == mes:
            return 'ganado'
    return 'ok'


def estados_todos(cedula):
    return {reto: estado_reto(cedula, reto) for reto in RETOS}


def wa_coordinador(hiker, reto):
    msg = RETOS[reto]['wa'].format(cedula=hiker.cedula, nombre=hiker.nombre_completo or '')
    return 'https://wa.me/' + WHATSAPP_COORD + '?text=' + quote(msg)


def wa_aviso_rechazo(hiker, reto):
    tel = re.sub(r'\D', '', hiker.telefono or '')
    if tel and len(tel) <= 8:
        tel = '506' + tel
    msg = (f"Hola {hiker.nombre_completo or ''}, no pudimos comprobar tu reto "
           f"«{RETOS[reto]['label']}». Por favor confirmalo o repetilo desde Mis puntos "
           f"en latribu.top. ¡Pura vida!")
    if tel:
        return 'https://wa.me/' + tel + '?text=' + quote(msg)
    return 'https://wa.me/?text=' + quote(msg)


def crear_solicitud(cedula, reto):
    """Registra la confirmación del reto; queda pendiente de aprobación."""
    if reto not in RETOS:
        return {'ok': False, 'error': 'Reto desconocido.'}
    hiker = Hiker.query.filter_by(cedula=str(cedula)).first()
    if not hiker:
        return {'ok': False, 'error': 'Registro no encontrado.'}
    est = estado_reto(cedula, reto)
    if est == 'pendiente':
        return {'ok': True, 'ya_pendiente': True, 'error': ''}
    if est == 'ganado':
        return {'ok': False, 'error': 'Ya ganaste este reto este mes. Volvé a intentarlo el próximo mes.'}
    db.session.add(RetoSolicitud(cedula=hiker.cedula, hiker_id=hiker.id, reto=reto, estado='pendiente'))
    db.session.commit()
    return {'ok': True, 'ya_pendiente': False, 'error': ''}


def pendientes():
    out = []
    for s in RetoSolicitud.query.filter_by(estado='pendiente').order_by(RetoSolicitud.created_at).all():
        h = Hiker.query.filter_by(cedula=s.cedula).first()
        out.append({
            'id': s.id, 'reto': s.reto, 'label': RETOS.get(s.reto, {}).get('label', s.reto),
            'puntos': RETOS.get(s.reto, {}).get('puntos', 0),
            'nombre': h.nombre_completo if h else s.cedula, 'cedula': s.cedula,
            'fecha': fecha_cr(s.created_at), 'estado': s.estado,
        })
    return out


def resueltas(limit=15):
    filas = (RetoSolicitud.query.filter(RetoSolicitud.estado != 'pendiente')
             .order_by(RetoSolicitud.resuelto_at.desc()).limit(limit).all())
    out = []
    for s in filas:
        h = Hiker.query.filter_by(cedula=s.cedula).first()
        nombre = h.nombre_completo if h else s.cedula
        out.append({
            'id': s.id, 'label': RETOS.get(s.reto, {}).get('label', s.reto),
            'nombre': nombre, 'cedula': s.cedula, 'estado': s.estado,
            'fecha': fecha_cr(s.resuelto_at), 'por': s.resuelto_por or '',
            'wa_rechazo': wa_aviso_rechazo(h, s.reto) if (s.estado == 'rechazada' and h) else '',
        })
    return out


def resolver(sid, accion, operador):
    """Aprueba (acredita puntos) o rechaza la solicitud pendiente."""
    s = RetoSolicitud.query.get(sid)
    if not s:
        return {'ok': False, 'error': 'Solicitud no encontrada.'}
    if s.estado != 'pendiente':
        return {'ok': False, 'error': 'Esta solicitud ya fue resuelta.'}
    hiker = Hiker.query.filter_by(cedula=s.cedula).first()
    h_name = hiker.nombre_completo if hiker else s.cedula
    info = RETOS.get(s.reto, {'label': s.reto, 'puntos': 0})
    s.resuelto_at = datetime.utcnow()
    s.resuelto_por = operador or 'admin'
    wa = ''
    if accion == 'aprobar':
        s.estado = 'aprobada'
        db.session.commit()
        get_points_engine()._add_record(s.cedula, s.hiker_id, None, info['puntos'],
                                        'reto_' + s.reto, 'Reto aprobado: ' + info['label'], operador)
        return {'ok': True, 'mensaje': f"Reto aprobado: +{info['puntos']} pts a {h_name}.", 'wa': ''}
    if accion == 'rechazar':
        s.estado = 'rechazada'
        db.session.commit()
        if hiker:
            wa = wa_aviso_rechazo(hiker, s.reto)
        return {'ok': True, 'mensaje': f"Reto rechazado a {h_name}. Avisale por WhatsApp.", 'wa': wa}
    return {'ok': False, 'error': 'Acción desconocida.'}
