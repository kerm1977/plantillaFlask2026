import os
import secrets
import string
from flask import request, jsonify, session, send_from_directory
from models import Event
from db import db
from werkzeug.utils import secure_filename
from routes import bp, _PROJECT_ROOT

# ==========================================
# RUTAS GPX POR EVENTO
# ==========================================
GPX_FOLDER = os.path.join(_PROJECT_ROOT, 'static', 'gpx')


@bp.route('/api/evento/<int:event_id>/gpx', methods=['POST'])
def upload_gpx(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    if 'gpx_file' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    gpx_file = request.files['gpx_file']
    if not gpx_file.filename.lower().endswith('.gpx'):
        return jsonify({'error': 'Solo se permiten archivos .gpx'}), 400
    os.makedirs(GPX_FOLDER, exist_ok=True)
    filename = secure_filename(f"evento_{event_id}_{gpx_file.filename}")
    gpx_file.save(os.path.join(GPX_FOLDER, filename))
    evento.gpx_filename = filename
    db.session.commit()
    return jsonify({'ok': True, 'filename': filename})


@bp.route('/api/evento/<int:event_id>/gpx', methods=['DELETE'])
def delete_gpx(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    if evento.gpx_filename:
        path = os.path.join(GPX_FOLDER, evento.gpx_filename)
        if os.path.exists(path):
            os.remove(path)
        evento.gpx_filename = None
        evento.gpx_password = None
        db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/evento/<int:event_id>/gpx/password', methods=['POST'])
def set_gpx_password(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    payload = request.get_json() or {}
    pwd = payload.get('password', '').strip()
    if not pwd:
        chars = string.ascii_uppercase + string.digits
        pwd = ''.join(secrets.choice(chars) for _ in range(6))
    evento.gpx_password = pwd
    db.session.commit()
    return jsonify({'ok': True, 'password': pwd})


@bp.route('/api/evento/<int:event_id>/gpx/download')
def download_gpx(event_id):
    evento = Event.query.get_or_404(event_id)
    if not evento.gpx_filename:
        return jsonify({'error': 'No hay GPX para este evento'}), 404
    if evento.gpx_password:
        clave = request.args.get('clave', '')
        if clave.strip().upper() != evento.gpx_password.strip().upper():
            return jsonify({'error': 'Contraseña incorrecta'}), 403
    return send_from_directory(GPX_FOLDER, evento.gpx_filename, as_attachment=True)


@bp.route('/api/evento/<int:event_id>/organicmaps', methods=['POST'])
def set_organicmaps(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    payload = request.get_json() or {}
    evento.organicmaps_url = payload.get('url', '').strip()
    db.session.commit()
    return jsonify({'ok': True})
