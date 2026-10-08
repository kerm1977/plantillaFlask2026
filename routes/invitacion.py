# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/invitacion.py - Invitación personalizada 9:16 (solo superusuario).
import os

from flask import request, session, jsonify, send_file, current_app

from models import Event, Hiker
from modules.invitacion import build_invitacion_image, invitacion_bytes
from modules.points_helpers import is_past_event
from routes import bp


def _is_super():
    return session.get('role') == 'Superusuario'


def _flyer_url(ev):
    """URL pública del flyer (para la vista previa DOM del modal)."""
    for nombre in (ev.flyer_bg, ev.poster):
        if not nombre:
            continue
        if os.path.exists(os.path.join(current_app.static_folder, 'uploads', nombre)):
            return '/static/uploads/' + nombre
        if os.path.exists(os.path.join(current_app.static_folder, nombre)):
            return '/static/' + nombre
    return '/static/default.png'


@bp.route('/api/invitacion/eventos')
def invitacion_eventos():
    """Eventos futuros con flyer para el selector de la invitación."""
    if not _is_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    salida = []
    for ev in Event.query.order_by(Event.id.desc()).all():
        if is_past_event(ev):
            continue
        if not (ev.poster or ev.flyer_bg):
            continue
        salida.append({
            'id': ev.id,
            'nombre': ev.nombre_lugar or '',
            'fecha': ev.fecha_unica or ev.fecha_inicio or '',
            'lugar': ev.lugar_salida or ev.provincia or '',
            'puntos': ev.puntos or 0,
            'flyer': _flyer_url(ev),
        })
    return jsonify({'ok': True, 'eventos': salida})


@bp.route('/api/invitacion.png')
def invitacion_png():
    """Genera la invitación 9:16 personalizada (flyer + persona + puntos)."""
    if not _is_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    try:
        evento_id = int(request.args.get('evento') or 0)
    except ValueError:
        evento_id = 0
    cedula = (request.args.get('cedula') or '').strip()
    event = Event.query.get(evento_id)
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not event:
        return jsonify({'ok': False, 'error': 'Evento no encontrado'}), 404
    if not hiker:
        return jsonify({'ok': False, 'error': 'Persona no encontrada'}), 404
    params = {k: request.args.get(k) for k in ('pos', 'band', 'soft', 'blur', 'fnombre', 'finfo', 'fboton')}
    img = build_invitacion_image(event, hiker, params)
    return send_file(invitacion_bytes(img), mimetype='image/png')
