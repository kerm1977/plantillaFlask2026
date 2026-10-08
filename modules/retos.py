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
from models import Hiker, RetoSolicitud, Reto
from modules.points_engine import get_points_engine
from modules.points_purchase import fecha_cr

RETOS = {
    'datos': {
        'label': 'Actualizar mis datos',
        'puntos': 200,
        'dias': 30,
        'wa': ('Hola, ya actualicé todos mis datos en el sistema de puntos de La Tribu de los '
               'Libres. Por favor confirmen el reto. Cédula: {cedula} - {nombre}.'),
    },
    'foto_perfil': {
        'label': 'Foto de perfil de Facebook con la camisa',
        'puntos': 200,
        'dias': 30,
        'wa': ('Hola, ya puse mi foto de perfil en Facebook con la camisa de La Tribu de los '
               'Libres durante una semana. Envío el pantallazo para que lo confirmen. '
               'Cédula: {cedula} - {nombre}.'),
    },
    'foto_portada': {
        'label': 'Foto de portada de Facebook con la camisa y un paisaje',
        'puntos': 200,
        'dias': 30,
        'wa': ('Hola, ya puse mi foto de portada de Facebook con la camisa de La Tribu de los '
               'Libres y un paisaje de fondo. Envío el pantallazo para que lo confirmen. '
               'Cédula: {cedula} - {nombre}.'),
    },
}
WHATSAPP_COORD = '50686529837'
_CR = timezone(timedelta(hours=-6))


def dias_reto(key):
    """Días de frecuencia de un reto fijo; el superusuario puede cambiarlos
    (SiteContent 'reto_dias_<key>'). Por defecto 30."""
    from models import SiteContent
    fila = SiteContent.query.filter_by(key='reto_dias_' + key).first()
    try:
        valor = int(fila.value) if fila else 0
    except (TypeError, ValueError):
        valor = 0
    return valor if valor > 0 else RETOS.get(key, {}).get('dias', 30)


def _info_reto(key):
    """{'label','puntos','dias','wa'} de un reto builtin ('datos', 'foto_*') o personalizado ('custom_<id>')."""
    if key in RETOS:
        info = dict(RETOS[key])
        info['dias'] = dias_reto(key)
        return info
    if key.startswith('custom_'):
        try:
            rid = int(key.split('_', 1)[1])
        except ValueError:
            return None
        r = Reto.query.get(rid)
        if not r:
            return None
        return {'label': r.titulo, 'puntos': r.puntos or 0, 'dias': r.frecuencia_dias or 30,
                'wa': ('Hola, ya cumplí el reto «' + (r.titulo or '') + '». Envío el comprobante '
                       'para que lo confirmen. Cédula: {cedula} - {nombre}.'),
                'reto_obj': r}
    return None


def _ultima_aprobada(cedula, reto):
    return (RetoSolicitud.query.filter_by(cedula=str(cedula), reto=reto, estado='aprobada')
            .order_by(RetoSolicitud.resuelto_at.desc()).first())


def estado_reto(cedula, reto):
    """'pendiente' si hay solicitud sin resolver, 'ganado' si se aprobó dentro de la
    frecuencia del reto (por defecto 30 días), 'ok' si puede volver a hacerlo."""
    info = _info_reto(reto)
    if info is None:
        return 'ok'
    if RetoSolicitud.query.filter_by(cedula=str(cedula), reto=reto, estado='pendiente').first():
        return 'pendiente'
    ultima = _ultima_aprobada(cedula, reto)
    if ultima and ultima.resuelto_at and \
            ultima.resuelto_at >= datetime.utcnow() - timedelta(days=info.get('dias', 30)):
        return 'ganado'
    return 'ok'


def proximo_disponible(cedula, reto):
    """Fecha (dd/mm/aaaa) en que el reto se vuelve a habilitar; '' si ya está disponible."""
    info = _info_reto(reto) or {}
    ultima = _ultima_aprobada(cedula, reto)
    if not ultima or not ultima.resuelto_at:
        return ''
    fecha = ultima.resuelto_at + timedelta(days=info.get('dias', 30))
    if fecha <= datetime.utcnow():
        return ''
    return fecha_cr(fecha).split(' ')[0]


def estados_todos(cedula):
    return {reto: {'estado': estado_reto(cedula, reto),
                   'proximo': proximo_disponible(cedula, reto)} for reto in RETOS}


def wa_coordinador(hiker, reto):
    info = _info_reto(reto)
    if not info:
        return ''
    msg = info['wa'].format(cedula=hiker.cedula, nombre=hiker.nombre_completo or '')
    return 'https://wa.me/' + WHATSAPP_COORD + '?text=' + quote(msg)


def wa_aviso_rechazo(hiker, reto):
    info = _info_reto(reto)
    if not info:
        return ''
    tel = re.sub(r'\D', '', hiker.telefono or '')
    if tel and len(tel) <= 8:
        tel = '506' + tel
    msg = (f"Hola {hiker.nombre_completo or ''}, no pudimos comprobar tu reto "
           f"«{info['label']}». Por favor confirmalo o repetilo desde Mis puntos "
           f"en latribu.top. ¡Pura vida!")
    if tel:
        return 'https://wa.me/' + tel + '?text=' + quote(msg)
    return 'https://wa.me/?text=' + quote(msg)


def crear_solicitud(cedula, reto):
    """Registra la confirmación del reto; queda pendiente de aprobación."""
    info = _info_reto(reto)
    if not info or (info.get('reto_obj') and not info['reto_obj'].activo):
        return {'ok': False, 'error': 'Reto desconocido o inactivo.'}
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
        info = _info_reto(s.reto) or {'label': s.reto, 'puntos': 0}
        out.append({
            'id': s.id, 'reto': s.reto, 'label': info['label'], 'puntos': info['puntos'],
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
        info = _info_reto(s.reto) or {'label': s.reto}
        out.append({
            'id': s.id, 'label': info['label'],
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
    info = _info_reto(s.reto) or {'label': s.reto, 'puntos': 0}
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


def cumplidos(cedula):
    """Retos aprobados de una persona (estado de cuenta de retos):
    [{'label','puntos','fecha'}] más totales, del más reciente al más viejo."""
    filas = (RetoSolicitud.query.filter_by(cedula=str(cedula), estado='aprobada')
             .order_by(RetoSolicitud.resuelto_at.desc()).all())
    lista, total_pts = [], 0
    for s in filas:
        info = _info_reto(s.reto) or {'label': s.reto, 'puntos': 0}
        lista.append({'label': info['label'], 'puntos': info['puntos'],
                      'fecha': fecha_cr(s.resuelto_at)})
        total_pts += info['puntos']
    return {'lista': lista, 'cantidad': len(lista), 'puntos': total_pts}
