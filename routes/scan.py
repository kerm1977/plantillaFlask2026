# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/scan.py - Escáner QR de caminatas: asignación de puntos en entrada
import io
import re
from datetime import datetime
from urllib.parse import quote

import qrcode
from flask import render_template, session, jsonify, request, send_file, url_for
from sqlalchemy import or_

from db import db
from models import Event, Hiker, User, PuntosEvento, HikerPoints
from modules.points_engine import get_points_engine
from modules.points_bonuses import get_points_bonuses
from modules import fidelidad
from modules.points_helpers import is_past_event, build_estado_cuenta_whatsapp
from modules.qr_card import build_card_png
from . import bp


def _require_super():
    return session.get('role') == 'Superusuario'


def _scan_url(event_id):
    return url_for('main.puntos_scan', event_id=event_id, _external=True)


@bp.route('/puntos-scan/<int:event_id>')
def puntos_scan(event_id):
    """Página pública que muestra el QR de la caminata (la comparte el superusuario)."""
    event = Event.query.get_or_404(event_id)
    qr_img = url_for('main.puntos_scan_qr', event_id=event_id)
    return render_template('scan_qr.html', titulo=event.nombre_lugar,
                           subtitulo=event.actividad, puntos=event.puntos, qr_img=qr_img)


@bp.route('/scan/evento/<int:event_id>/qr.png')
def puntos_scan_qr(event_id):
    """Genera el PNG del QR que codifica el enlace /puntos-scan/<id>."""
    Event.query.get_or_404(event_id)
    img = qrcode.make(_scan_url(event_id), box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@bp.route('/scan/evento/<int:event_id>/card.png')
def puntos_scan_card(event_id):
    """PNG del recuadro completo (idéntico a la página /puntos-scan/<id>)."""
    event = Event.query.get_or_404(event_id)
    buf = build_card_png(event.nombre_lugar, event.actividad, event.puntos,
                         _scan_url(event_id))
    return send_file(buf, mimetype='image/png',
                     download_name=f'qr-puntos-{event_id}.png')


@bp.route('/api/scan/info/<kind>/<int:item_id>')
def scan_info(kind, item_id):
    """Nombre y puntos del código escaneado (caminata o evento de puntos)."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    if kind == 'evento':
        pe = PuntosEvento.query.get(item_id)
        if not pe:
            return jsonify({'ok': False, 'error': 'Evento de puntos no encontrado.'}), 404
        if not pe.activo:
            return jsonify({'ok': False, 'error': 'Este evento está inactivo.'})
        return jsonify({'ok': True, 'nombre': pe.nombre, 'puntos': pe.puntos or 0})
    event = Event.query.get(item_id)
    if not event:
        return jsonify({'ok': False, 'error': 'Caminata no encontrada.'}), 404
    return jsonify({'ok': True, 'nombre': event.nombre_lugar, 'puntos': event.puntos or 0})


@bp.route('/api/scan/hikers')
def scan_hikers():
    """Buscador en vivo de caminantes por cualquier criterio (solo superusuario)."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    q = (request.args.get('q') or '').strip()
    if len(q) < 2:
        return jsonify({'ok': True, 'results': []})
    like = f'%{q}%'
    rows = Hiker.query.filter(or_(
        Hiker.nombre_completo.ilike(like),
        Hiker.cedula.ilike(like),
        Hiker.telefono.ilike(like),
        Hiker.pasaporte.ilike(like),
        Hiker.tipo_sangre.ilike(like),
    )).order_by(Hiker.nombre_completo).limit(20).all()
    return jsonify({'ok': True, 'results': [{
        'cedula': h.cedula,
        'nombre': h.nombre_completo,
        'telefono': h.telefono or '',
        'tipo_sangre': h.tipo_sangre or '',
    } for h in rows]})


def _operador():
    user = User.query.get(session.get('user_id')) if session.get('user_id') else None
    return f'{user.name} {user.last_name_1}'.strip() if user else 'superusuario'


def _estado_wa_url(cedula, hiker):
    estado_txt = build_estado_cuenta_whatsapp(cedula, hiker)
    telefono = re.sub(r'\D', '', hiker.telefono or '')
    if telefono and len(telefono) <= 8:
        telefono = '506' + telefono
    wa_base = f'https://wa.me/{telefono}' if telefono else 'https://wa.me/'
    return wa_base + '?text=' + quote(estado_txt)


@bp.route('/api/scan/estado', methods=['POST'])
def scan_estado():
    """Devuelve el link de WhatsApp con el estado de cuenta de una cédula
    (solo superusuario). Se usa desde el escáner sin asignar puntos."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    if not cedula:
        return jsonify({'ok': False, 'error': 'Ingresá una cédula válida.'})
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'code': 'not_found',
                        'error': f'La cédula {cedula} no está registrada.'})
    return jsonify({'ok': True, 'nombre': hiker.nombre_completo, 'cedula': cedula,
                    'total': get_points_engine().total_by_cedula(cedula),
                    'estado_texto': build_estado_cuenta_whatsapp(cedula, hiker),
                    'estado_whatsapp_url': _estado_wa_url(cedula, hiker)})


def _registros_escaneo(kind, item_id, cedula):
    """Todos los movimientos de esa persona en esa caminata/evento
    (la cédula se compara normalizada a dígitos por formatos viejos)."""
    if kind == 'evento':
        q = HikerPoints.query.filter_by(puntos_evento_id=item_id)
    else:
        q = HikerPoints.query.filter_by(event_id=item_id)
    return [r for r in q.order_by(HikerPoints.created_at.desc()).all()
            if re.sub(r'\D', '', r.cedula or '') == cedula]


def _tiene_anulacion(kind, item_id, cedula):
    """True si la persona tuvo un escaneo anulado en esa caminata/evento:
    el re-escaneo requiere triple confirmación del superusuario."""
    if kind == 'evento':
        q = HikerPoints.query.filter_by(puntos_evento_id=item_id, tipo='anulacion')
    else:
        q = HikerPoints.query.filter_by(event_id=item_id, tipo='anulacion')
    return any(re.sub(r'\D', '', r.cedula or '') == cedula for r in q.all())


@bp.route('/api/scan/verificar', methods=['POST'])
def scan_verificar():
    """Diagnóstico de un escaneo problemático: muestra todos los registros
    que la persona tiene en esa caminata/evento (solo superusuario)."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    kind = data.get('kind') or 'caminata'
    item_id = data.get('id') or data.get('event_id')
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    if not cedula:
        return jsonify({'ok': False, 'error': 'Ingresá una cédula válida.'})
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'code': 'not_found',
                        'error': f'La cédula {cedula} no está registrada.'})
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Evento no válido.'})
    if kind == 'evento':
        pe = PuntosEvento.query.get(item_id)
        if not pe:
            return jsonify({'ok': False, 'error': 'Evento de puntos no encontrado.'}), 404
        nombre_ev, puntos_ev, tipo_bloqueo = pe.nombre, pe.puntos or 0, 'evento'
    else:
        event = Event.query.get(item_id)
        if not event:
            return jsonify({'ok': False, 'error': 'Caminata no encontrada.'}), 404
        nombre_ev, puntos_ev, tipo_bloqueo = event.nombre_lugar, event.puntos or 0, 'participacion'
    regs = _registros_escaneo(kind, item_id, cedula)
    return jsonify({
        'ok': True,
        'nombre': hiker.nombre_completo, 'cedula': cedula,
        'evento_nombre': nombre_ev, 'puntos_evento': puntos_ev,
        'bloqueado': any(r.tipo == tipo_bloqueo for r in regs),
        'total': get_points_engine().total_by_cedula(cedula),
        'registros': [{
            'tipo': r.tipo or '', 'puntos': r.points or 0,
            'fecha': r.created_at.strftime('%d-%m-%Y %H:%M') if r.created_at else '',
            'operador': r.created_by or '', 'detalle': r.detalle or '',
        } for r in regs],
    })


@bp.route('/api/scan/reset', methods=['POST'])
def scan_reset():
    """Anula el escaneo (participación/evento) de una persona para que pueda
    volver a escanear. Borra el registro y deja una 'anulacion' de 0 puntos
    con el motivo y el detalle de lo eliminado (solo superusuario)."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    kind = data.get('kind') or 'caminata'
    item_id = data.get('id') or data.get('event_id')
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    motivo = (data.get('motivo') or '').strip() or 'Sin motivo indicado'
    if not cedula:
        return jsonify({'ok': False, 'error': 'Ingresá una cédula válida.'})
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'code': 'not_found',
                        'error': f'La cédula {cedula} no está registrada.'})
    try:
        item_id = int(item_id)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'Evento no válido.'})
    if kind == 'evento':
        pe = PuntosEvento.query.get(item_id)
        if not pe:
            return jsonify({'ok': False, 'error': 'Evento de puntos no encontrado.'}), 404
        nombre_ev, tipo_bloqueo = pe.nombre, 'evento'
    else:
        event = Event.query.get(item_id)
        if not event:
            return jsonify({'ok': False, 'error': 'Caminata no encontrada.'}), 404
        nombre_ev, tipo_bloqueo = event.nombre_lugar, 'participacion'
    regs = [r for r in _registros_escaneo(kind, item_id, cedula) if r.tipo == tipo_bloqueo]
    if not regs:
        return jsonify({'ok': False, 'error': 'No hay escaneo que resetear: la persona no tiene registro en esta caminata.'})
    quitados = sum(r.points or 0 for r in regs)
    resumen = '; '.join(
        f"{r.tipo} {r.points:+d} del {r.created_at.strftime('%d-%m-%Y %H:%M') if r.created_at else '?'}"
        for r in regs)
    for r in regs:
        db.session.delete(r)
    db.session.add(HikerPoints(
        cedula=cedula, hiker_id=hiker.id,
        event_id=(None if kind == 'evento' else item_id),
        puntos_evento_id=(item_id if kind == 'evento' else None),
        points=0, tipo='anulacion',
        detalle=f'Escaneo anulado en {nombre_ev}. Motivo: {motivo}. Registros eliminados: {resumen}.',
        created_by=_operador(), created_at=datetime.utcnow()))
    db.session.commit()
    return jsonify({'ok': True, 'nombre': hiker.nombre_completo,
                    'puntos_quitados': quitados,
                    'total': get_points_engine().total_by_cedula(cedula)})


@bp.route('/api/scan/award', methods=['POST'])
def scan_award():
    """Asigna puntos a una cédula desde un código escaneado (solo superusuario).
    kind='caminata' -> Event / kind='evento' -> PuntosEvento."""
    if not _require_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    kind = data.get('kind') or 'caminata'
    item_id = data.get('id') or data.get('event_id')
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    if not cedula:
        return jsonify({'ok': False, 'error': 'Ingresá una cédula válida.'})
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'code': 'not_found',
                        'error': f'La cédula {cedula} no está registrada.'})
    engine = get_points_engine()
    operador = _operador()

    if kind == 'evento':
        pe = PuntosEvento.query.get(item_id)
        if not pe:
            return jsonify({'ok': False, 'error': 'Evento de puntos no encontrado.'}), 404
        if not pe.activo:
            return jsonify({'ok': False, 'error': 'Este evento está inactivo.'})
        if not pe.puntos:
            return jsonify({'ok': False, 'error': 'Este evento no tiene puntos configurados.'})
        ya = HikerPoints.query.filter_by(
            puntos_evento_id=pe.id, cedula=cedula, tipo='evento').first()
        if ya:
            return jsonify({'ok': False, 'code': 'duplicate',
                            'error': f'{hiker.nombre_completo} ya recibió los puntos de este evento.'})
        if not data.get('confirmado_3') and _tiene_anulacion('evento', pe.id, cedula):
            return jsonify({'ok': False, 'code': 'requires_confirm',
                            'nombre': hiker.nombre_completo, 'evento': pe.nombre,
                            'puntos': pe.puntos,
                            'error': f'{hiker.nombre_completo} tiene un escaneo anulado en este evento. Confirmá la re-asignación.'})
        # Primer ingreso al sistema de puntos: regalía de bienvenida antes de asignar
        get_points_bonuses().apply(cedula)
        puntos = fidelidad.puntos_con_bono(cedula, pe.puntos)
        db.session.add(HikerPoints(
            cedula=cedula, hiker_id=hiker.id, puntos_evento_id=pe.id,
            points=puntos, tipo='evento',
            detalle=f'Puntos ganados en {pe.nombre} (escaneo QR){fidelidad.etiqueta_bono(cedula, pe.puntos)}',
            created_by=operador, created_at=datetime.utcnow()))
        db.session.commit()
        return jsonify({'ok': True, 'nombre': hiker.nombre_completo, 'cedula': cedula,
                        'puntos_ganados': puntos, 'total': engine.total_by_cedula(cedula),
                        'evento': pe.nombre, 'nivel_label': fidelidad.info(cedula)['nivel_label'],
                        'estado_whatsapp_url': _estado_wa_url(cedula, hiker)})

    event = Event.query.get(item_id) if item_id else None
    if not event:
        return jsonify({'ok': False, 'error': 'Caminata no encontrada.'}), 404
    if not event.puntos:
        return jsonify({'ok': False, 'error': 'Esta caminata no tiene puntos configurados.'})
    if engine.has_earned(event.id, cedula):
        return jsonify({'ok': False, 'code': 'duplicate',
                        'error': f'{hiker.nombre_completo} ya recibió los puntos de esta caminata.'})
    anulada = _tiene_anulacion('caminata', event.id, cedula)
    pasada = is_past_event(event)
    if not data.get('confirmado_3'):
        if anulada:
            return jsonify({'ok': False, 'code': 'requires_confirm',
                            'nombre': hiker.nombre_completo, 'evento': event.nombre_lugar,
                            'puntos': event.puntos,
                            'error': f'{hiker.nombre_completo} tiene un escaneo anulado en esta caminata. Confirmá la re-asignación.'})
        if pasada:
            return jsonify({'ok': False, 'code': 'requires_confirm',
                            'nombre': hiker.nombre_completo, 'evento': event.nombre_lugar,
                            'puntos': event.puntos,
                            'error': f'La caminata ya pasó. Confirmá si igual querés asignarle los puntos a {hiker.nombre_completo}.'})
    # Primer ingreso al sistema de puntos: regalía de bienvenida antes de asignar
    get_points_bonuses().apply(cedula)
    puntos = fidelidad.puntos_con_bono(cedula, event.puntos)
    engine._add_record(cedula, hiker.id, event.id, puntos, 'participacion',
                       f'Puntos ganados en {event.nombre_lugar} (escaneo QR){fidelidad.etiqueta_bono(cedula, event.puntos)}', operador)
    return jsonify({'ok': True, 'nombre': hiker.nombre_completo, 'cedula': cedula,
                    'puntos_ganados': puntos, 'total': engine.total_by_cedula(cedula),
                    'evento': event.nombre_lugar, 'nivel_label': fidelidad.info(cedula)['nivel_label'],
                    'estado_whatsapp_url': _estado_wa_url(cedula, hiker)})
