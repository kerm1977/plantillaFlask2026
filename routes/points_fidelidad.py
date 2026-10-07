# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# routes/points_fidelidad.py - Programa de fidelidad (solo superusuario)
import re
from flask import session, jsonify, request
from models import Hiker
from modules import fidelidad
from modules.points_admin import get_points_admin
from . import bp
from routes.points import _current_user


def _super():
    return session.get('role') == 'Superusuario'


@bp.route('/api/fidelidad/lista')
def fidelidad_lista():
    """Personas con nivel VIP (automático o manual), para el gestor."""
    if not _super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    items = []
    for h in Hiker.query.order_by(Hiker.nombre_completo).all():
        i = fidelidad.info(h.cedula)
        if not i['es_vip'] and not i['manual']:
            continue
        items.append({
            'cedula': h.cedula, 'nombre': h.nombre_completo,
            'participaciones': i['participaciones'],
            'nivel': i['nivel'], 'nivel_label': i['nivel_label'],
            'nivel_auto': i['nivel_auto'], 'manual': i['manual'],
            'multiplicador': i['multiplicador'], 'nota': i['nota'],
        })
    return jsonify({'ok': True, 'items': items})


@bp.route('/api/fidelidad/info/<cedula>')
def fidelidad_info(cedula):
    """Estado de fidelidad de una persona (para el gestor y el propio usuario)."""
    cedula = re.sub(r'\D', '', cedula or '')
    if not _super() and session.get('mis_puntos_ok') != cedula:
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'error': 'Cédula no registrada.'}), 404
    i = fidelidad.info(cedula)
    i['nombre'] = hiker.nombre_completo
    return jsonify({'ok': True, **i})


@bp.route('/api/fidelidad/nivel', methods=['POST'])
def fidelidad_nivel():
    """Cambia el nivel de una persona: 'activo', 'exclusivo' o 'auto'.
    Degradar exige nota con el motivo (queda en la bitácora)."""
    if not _super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    nivel = (data.get('nivel') or '').strip()
    nota = (data.get('nota') or '').strip()
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'error': 'Cédula no registrada.'}), 404
    res = fidelidad.cambiar_nivel(cedula, nivel, nota, _current_user())
    if res.get('ok'):
        res['nombre'] = hiker.nombre_completo
        res['info'] = fidelidad.info(cedula)
    return jsonify(res), (200 if res.get('ok') else 400)


@bp.route('/api/fidelidad/historial/<cedula>')
def fidelidad_historial(cedula):
    """Bitácora de cambios de nivel de una persona (solo superusuario)."""
    if not _super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    rows = historial_fmt(None if cedula == 'todos' else cedula)
    return jsonify({'ok': True, 'items': rows})


@bp.route('/api/fidelidad/obsequio', methods=['POST'])
def fidelidad_obsequio():
    """Obsequia puntos por fidelidad al grupo (solo superusuario)."""
    if not _super():
        return jsonify({'ok': False, 'error': 'No autorizado'}), 403
    data = request.get_json(silent=True) or {}
    cedula = re.sub(r'\D', '', str(data.get('cedula') or ''))
    try:
        monto = int(data.get('monto') or 0)
    except (TypeError, ValueError):
        monto = 0
    motivo = (data.get('motivo') or '').strip() or 'fidelidad al grupo'
    hiker = Hiker.query.filter_by(cedula=cedula).first()
    if not hiker:
        return jsonify({'ok': False, 'error': 'Cédula no registrada.'}), 404
    res = get_points_admin().gift(cedula, monto, _current_user(), f'fidelidad al grupo - {motivo}')
    if res.get('ok'):
        res['nombre'] = hiker.nombre_completo
    return jsonify(res), (200 if res.get('ok') else 400)


def historial_fmt(cedula=None):
    return [{
        'cedula': r.cedula,
        'de': fidelidad.ETIQUETAS.get(r.nivel_anterior) or 'Sin nivel VIP',
        'a': fidelidad.ETIQUETAS.get(r.nivel_nuevo) or 'Sin nivel VIP',
        'origen': r.origen, 'nota': r.nota or '', 'por': r.created_by or '',
        'fecha': r.created_at.strftime('%d/%m/%Y %H:%M') if r.created_at else '',
    } for r in fidelidad.historial(cedula)]
