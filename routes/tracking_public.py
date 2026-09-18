# ══ BLINDADO — RASTREO EN VIVO ══
# Código probado y estable. NO modificar sin revisar el flujo completo:
# panel admin -> sesión por evento -> GPS -> viewers con código de 4 dígitos.
# Rutas públicas del rastreo en vivo: espectadores, transmisor y pings GPS
from datetime import datetime
from flask import request, jsonify, render_template, abort
from models_tracking import LiveSession, LivePoint
from db import db
from routes import bp


def _por_view_token(token):
    return LiveSession.query.filter_by(view_token=(token or '').strip()).first()


def _por_tx_token(token):
    return LiveSession.query.filter_by(tx_token=(token or '').strip()).first()


# ── PÁGINA DE ESPECTADORES (familiares) ──────────────────────────────────────

@bp.route('/rastreo/<view_token>')
def rastreo_ver(view_token):
    s = _por_view_token(view_token)
    if not s:
        abort(404)
    return render_template('rastreo_ver.html', session_id=s.id,
                           view_token=view_token)


# ── API DE ESTADO PARA ESPECTADORES ──────────────────────────────────────────

@bp.route('/api/rastreo/<view_token>/status')
def api_rastreo_status(view_token):
    s = _por_view_token(view_token)
    if not s:
        abort(404)
    code = (request.args.get('code') or '').strip()
    if code != s.code:
        return jsonify({'error': 'Código incorrecto'}), 403

    ultimo = (LivePoint.query.filter_by(session_id=s.id)
              .order_by(LivePoint.ts.desc()).first())
    data = {
        'active': bool(s.active),
        'show_track': bool(s.show_track),
        'last': None,
        'points': [],
    }
    if ultimo:
        data['last'] = {
            'lat': ultimo.lat, 'lng': ultimo.lng,
            'acc': ultimo.acc,
            'ts': ultimo.ts.strftime('%d/%m/%Y %H:%M:%S') if ultimo.ts else '',
            'age': int((datetime.utcnow() - ultimo.ts).total_seconds()),
        }
    if s.show_track:
        pts = (LivePoint.query.filter_by(session_id=s.id)
               .order_by(LivePoint.ts.asc()).all())
        data['points'] = [[p.lat, p.lng] for p in pts]
    return jsonify(data)


# ── PÁGINA DEL TRANSMISOR (coordinador, por token dedicado) ──────────────────

@bp.route('/rastreo/transmitir/<tx_token>')
def rastreo_transmitir(tx_token):
    s = _por_tx_token(tx_token)
    if not s:
        abort(404)
    return render_template('rastreo_transmitir.html',
                           tx_token=tx_token, session_activa=bool(s.active))


# ── API DE PING GPS DEL TRANSMISOR ───────────────────────────────────────────

@bp.route('/api/rastreo/ping/<tx_token>', methods=['POST'])
def api_rastreo_ping(tx_token):
    s = _por_tx_token(tx_token)
    if not s:
        abort(404)
    if not s.active:
        return jsonify({'ok': False, 'stopped': True}), 410

    data = request.get_json(silent=True) or {}
    try:
        lat = float(data['lat'])
        lng = float(data['lng'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Coordenadas inválidas'}), 400
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return jsonify({'error': 'Coordenadas fuera de rango'}), 400

    acc = data.get('acc')
    try:
        acc = float(acc) if acc is not None else None
    except (TypeError, ValueError):
        acc = None

    p = LivePoint(session_id=s.id, lat=lat, lng=lng, acc=acc)
    db.session.add(p)
    db.session.commit()
    total = LivePoint.query.filter_by(session_id=s.id).count()
    return jsonify({'ok': True, 'total': total})


# ── ESTADO DE LA SESIÓN PARA EL TRANSMISOR ───────────────────────────────────

@bp.route('/api/rastreo/ping/<tx_token>/info')
def api_rastreo_tx_info(tx_token):
    s = _por_tx_token(tx_token)
    if not s:
        abort(404)
    total = LivePoint.query.filter_by(session_id=s.id).count()
    return jsonify({'active': bool(s.active), 'total': total,
                    'event_id': s.event_id})
