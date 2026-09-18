# ══ BLINDADO — RASTREO EN VIVO ══
# Código probado y estable. NO modificar sin revisar el flujo completo:
# panel admin -> sesión por evento -> GPS -> viewers con código de 4 dígitos.
# Rutas de administración del rastreo en vivo (solo superusuario)
import secrets
from datetime import datetime
from flask import request, jsonify, session, render_template, redirect
from models import Event
from models_tracking import LiveSession, LivePoint
from db import db
from routes import bp


def _require_super():
    return 'user_id' in session and session.get('role') == 'Superusuario'


def _session_dict(s):
    return {
        'id': s.id,
        'event_id': s.event_id,
        'view_token': s.view_token,
        'tx_token': s.tx_token,
        'code': s.code,
        'show_track': bool(s.show_track),
        'active': bool(s.active),
        'created_at': s.created_at.strftime('%d/%m/%Y %H:%M') if s.created_at else '',
        'puntos': LivePoint.query.filter_by(session_id=s.id).count(),
    }


@bp.route('/rastreo/admin')
def rastreo_admin():
    if not _require_super():
        return redirect('/')
    eventos = Event.query.order_by(Event.id.desc()).all()
    return render_template('rastreo_admin.html', eventos=eventos)


@bp.route('/api/rastreo/sessions')
def api_rastreo_sessions():
    if not _require_super():
        return jsonify({'error': 'No autorizado'}), 403
    sesiones = LiveSession.query.order_by(LiveSession.id.desc()).all()
    nombres = {e.id: e.nombre_lugar for e in Event.query.all()}
    out = []
    for s in sesiones:
        d = _session_dict(s)
        d['evento'] = nombres.get(s.event_id, 'Sin evento')
        out.append(d)
    return jsonify(out)


@bp.route('/api/rastreo/session', methods=['POST'])
def api_rastreo_start():
    """Activa la transmisión para un evento.

    Cada caminata tiene UNA sesión permanente con enlaces fijos: si ya
    existe, se reutilizan los mismos tokens y solo se limpia el recorrido
    del día anterior. Detiene cualquier otra sesión activa."""
    if not _require_super():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    code = ''.join(ch for ch in str(data.get('code', '')) if ch.isdigit())[:8]
    event_id = data.get('event_id') or None

    # Detener sesiones previas activas — una sola transmisión en vivo
    for s in LiveSession.query.filter_by(active=True).all():
        s.active = False
        s.stopped_at = datetime.utcnow()

    # Reutilizar la sesión permanente del evento (enlaces fijos)
    s = LiveSession.query.filter_by(event_id=event_id).first() if event_id else None
    if s:
        if code and len(code) < 4:
            return jsonify({'error': 'El código debe tener al menos 4 dígitos'}), 400
        LivePoint.query.filter_by(session_id=s.id).delete()
        if code:
            s.code = code
        s.show_track = bool(data.get('show_track'))
        s.active = True
        s.stopped_at = None
    elif len(code) < 4:
        return jsonify({'error': 'El código debe tener al menos 4 dígitos'}), 400
    else:
        s = LiveSession(
            event_id=event_id,
            view_token=secrets.token_hex(16),
            tx_token=secrets.token_hex(16),
            code=code,
            show_track=bool(data.get('show_track')),
            active=True,
        )
        db.session.add(s)
    db.session.commit()
    return jsonify({'ok': True, 'session': _session_dict(s)})


@bp.route('/api/rastreo/session/<int:sid>/stop', methods=['POST'])
def api_rastreo_stop(sid):
    if not _require_super():
        return jsonify({'error': 'No autorizado'}), 403
    s = LiveSession.query.get_or_404(sid)
    s.active = False
    s.stopped_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/rastreo/session/<int:sid>/config', methods=['POST'])
def api_rastreo_config(sid):
    """Actualiza el código de ingreso y el toggle de recorrido."""
    if not _require_super():
        return jsonify({'error': 'No autorizado'}), 403
    s = LiveSession.query.get_or_404(sid)
    data = request.get_json(silent=True) or {}
    if 'code' in data:
        code = ''.join(ch for ch in str(data['code']) if ch.isdigit())[:8]
        if len(code) < 4:
            return jsonify({'error': 'El código debe tener al menos 4 dígitos'}), 400
        s.code = code
    if 'show_track' in data:
        s.show_track = bool(data['show_track'])
    db.session.commit()
    return jsonify({'ok': True, 'session': _session_dict(s)})


@bp.route('/api/rastreo/session/<int:sid>', methods=['DELETE'])
def api_rastreo_delete(sid):
    if not _require_super():
        return jsonify({'error': 'No autorizado'}), 403
    s = LiveSession.query.get_or_404(sid)
    if s.active:
        return jsonify({'error': 'Detené la sesión antes de eliminarla'}), 400
    LivePoint.query.filter_by(session_id=s.id).delete()
    db.session.delete(s)
    db.session.commit()
    return jsonify({'ok': True})
