# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
# Cambios rápidos de evento (superusuario): fecha y hora de salida.
import os
from datetime import datetime, timedelta
from flask import request, jsonify, session, url_for
from werkzeug.utils import secure_filename
from models import Event
from models_core import EventDateChange
from db import db
from routes import bp, allowed_file, ALLOWED_IMAGE_EXTENSIONS


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


@bp.route('/api/eventos/<int:event_id>/fondo-flyer', methods=['POST'])
def cambiar_fondo_flyer(event_id):
    """Fondo propio del flyer (superusuario): archivo nuevo, uno de uploads, o '' = usar póster."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    evento = Event.query.get_or_404(event_id)
    file = request.files.get('fondo')
    existente = (request.form.get('existente') or '').strip()
    try:
        if file and file.filename:
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            evento.flyer_bg = filename
        elif existente:
            evento.flyer_bg = existente
        else:
            evento.flyer_bg = None
        db.session.commit()
        url = url_for('static', filename='uploads/' + evento.flyer_bg) if evento.flyer_bg else ''
        return jsonify({"ok": True, "url": url})
    except Exception:
        db.session.rollback()
        return jsonify({"error": "Error al guardar el fondo"}), 500


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
