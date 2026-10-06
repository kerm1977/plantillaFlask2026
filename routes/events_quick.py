# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# Cambios rápidos de evento (superusuario): fecha y hora de salida.
from datetime import datetime, timedelta
from flask import request, jsonify, session
from models import Event
from models_core import EventDateChange
from db import db
from routes import bp


@bp.route('/api/eventos/<int:event_id>/hora', methods=['POST'])
def cambiar_hora_evento(event_id):
    """Cambio rápido de hora de salida desde el editor de flyer (superusuario)."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    data = request.get_json(silent=True) or {}
    hora = (data.get('hora') or '').strip()
    if hora:
        try:
            datetime.strptime(hora, '%H:%M')
        except ValueError:
            return jsonify({"error": "Hora inválida"}), 400
    evento = Event.query.get_or_404(event_id)
    try:
        evento.hora_salida = hora or None
        db.session.commit()
        return jsonify({"ok": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error al guardar la hora"}), 500


@bp.route('/api/eventos/<int:event_id>/fecha', methods=['POST'])
def cambiar_fecha_evento(event_id):
    """Cambio rápido de fecha (solo superusuario). 'dias' redefine la duración."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    data = request.get_json(silent=True) or {}
    nueva = (data.get('fecha') or '').strip()
    try:
        f0 = datetime.strptime(nueva, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return jsonify({"error": "Fecha inválida"}), 400
    try:
        dias = max(1, min(30, int(data.get('dias') or 0)))
    except (TypeError, ValueError):
        dias = 0
    evento = Event.query.get_or_404(event_id)
    if not dias:
        dias = evento.dias or 1
    estado = data.get('estado') or ''   # '', 'suspendida', 'lleno'
    try:
        anterior = evento.fecha_unica or evento.fecha_inicio or ''
        evento.dias = dias
        if dias > 1:
            evento.fecha_inicio = nueva
            evento.fecha_regreso = (f0 + timedelta(days=dias - 1)).isoformat()
            evento.fecha_unica = None
        else:
            evento.fecha_unica = nueva
            evento.fecha_inicio = None
            evento.fecha_regreso = None
        evento.suspendida = estado == 'suspendida'
        evento.is_sold_out = estado == 'lleno'
        # Al asignar fecha a una caminata pendiente, se programa automáticamente
        if (evento.visitado or '') in ('Pendiente', 'No', ''):
            evento.visitado = 'Programados'
        db.session.add(EventDateChange(
            event_id=event_id, fecha_anterior=anterior,
            fecha_nueva=nueva, usuario=session.get('email', 'Sistema')))
        db.session.commit()
        return jsonify({"ok": True})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error al guardar la fecha"}), 500
