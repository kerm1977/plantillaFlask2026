# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/puntos_eventos.py - Eventos de puntos: CRUD admin + página QR pública
import io

import qrcode
from flask import render_template, session, jsonify, request, send_file, url_for, redirect

from db import db
from models import PuntosEvento, HikerPoints
from modules.qr_card import build_card_png
from . import bp


def _is_super():
    return session.get('role') == 'Superusuario'


def _evento_scan_url(pid):
    return url_for('main.puntos_evento_qr_page', pid=pid, _external=True)


@bp.route('/puntos-eventos')
def puntos_eventos_admin():
    """Panel de gestión de eventos de puntos (solo superusuario)."""
    if not _is_super():
        return redirect(url_for('main.home'))
    eventos = PuntosEvento.query.order_by(PuntosEvento.id.desc()).all()
    return render_template('puntos_eventos.html', eventos=eventos)


@bp.route('/api/puntos-eventos', methods=['POST'])
def puntos_evento_crear():
    if not _is_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    if not nombre:
        return jsonify({'ok': False, 'error': 'Falta el nombre del evento.'})
    try:
        puntos = max(0, int(data.get('puntos') or 0))
    except (TypeError, ValueError):
        puntos = 0
    if puntos <= 0:
        return jsonify({'ok': False, 'error': 'Indicá cuántos puntos vale el evento.'})
    ev = PuntosEvento(nombre=nombre, puntos=puntos,
                      descripcion=(data.get('descripcion') or '').strip(),
                      publico=bool(data.get('publico', True)), activo=True)
    db.session.add(ev)
    db.session.commit()
    return jsonify({'ok': True, 'id': ev.id, 'scan_url': _evento_scan_url(ev.id)})


@bp.route('/api/puntos-eventos/<int:pid>/toggle', methods=['POST'])
def puntos_evento_toggle(pid):
    """Activa/desactiva el evento o lo hace público/privado (campo: activo|publico)."""
    if not _is_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    ev = PuntosEvento.query.get_or_404(pid)
    campo = (request.get_json(silent=True) or {}).get('campo')
    if campo not in ('activo', 'publico'):
        return jsonify({'ok': False, 'error': 'Campo inválido'}), 400
    setattr(ev, campo, not getattr(ev, campo))
    db.session.commit()
    return jsonify({'ok': True, campo: getattr(ev, campo)})


@bp.route('/api/puntos-eventos/<int:pid>/borrar', methods=['POST'])
def puntos_evento_borrar(pid):
    """Elimina el evento solo si nadie ha recibido puntos por él todavía."""
    if not _is_super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    ev = PuntosEvento.query.get_or_404(pid)
    usado = HikerPoints.query.filter_by(puntos_evento_id=pid).first()
    if usado:
        return jsonify({'ok': False,
                        'error': 'No se puede borrar: ya tiene puntos asignados. Desactivalo.'})
    db.session.delete(ev)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/puntos-evento/<int:pid>')
def puntos_evento_qr_page(pid):
    """Página con el QR del evento de puntos (la comparte el superusuario)."""
    ev = PuntosEvento.query.get_or_404(pid)
    if not ev.publico and not _is_super():
        return redirect(url_for('main.home'))
    qr_img = url_for('main.puntos_evento_qr_png', pid=pid)
    return render_template('scan_qr.html', titulo=ev.nombre,
                           subtitulo=ev.descripcion, puntos=ev.puntos, qr_img=qr_img)


@bp.route('/scan/puntos-evento/<int:pid>/qr.png')
def puntos_evento_qr_png(pid):
    """PNG del QR que codifica /puntos-evento/<id> (espacio separado de caminatas)."""
    ev = PuntosEvento.query.get_or_404(pid)
    if not ev.publico and not _is_super():
        return redirect(url_for('main.home'))
    img = qrcode.make(_evento_scan_url(pid), box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')


@bp.route('/scan/puntos-evento/<int:pid>/card.png')
def puntos_evento_card_png(pid):
    """PNG del recuadro completo del evento de puntos (para descargar)."""
    ev = PuntosEvento.query.get_or_404(pid)
    if not ev.publico and not _is_super():
        return redirect(url_for('main.home'))
    buf = build_card_png(ev.nombre, ev.descripcion, ev.puntos,
                         _evento_scan_url(pid))
    return send_file(buf, mimetype='image/png',
                     download_name=f'qr-puntos-evento-{pid}.png')
