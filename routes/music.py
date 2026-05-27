import os
import json
from flask import request, jsonify, session
from werkzeug.utils import secure_filename
from routes import bp, _PROJECT_ROOT

# ==========================================
# RUTAS REPRODUCTOR DE MÚSICA
# ==========================================
MUSICA_FOLDER = os.path.join(_PROJECT_ROOT, 'static', 'musica')
MUSICA_METADATA_FILE = os.path.join(MUSICA_FOLDER, 'metadata.json')
ALLOWED_AUDIO = {'mp3', 'ogg', 'wav', 'flac', 'm4a', 'aac'}

def _load_musica_meta():
    if os.path.exists(MUSICA_METADATA_FILE):
        with open(MUSICA_METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_musica_meta(data):
    os.makedirs(MUSICA_FOLDER, exist_ok=True)
    with open(MUSICA_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _safe_musica_name(name):
    return '/' not in name and '\\' not in name and '..' not in name


@bp.route('/api/musica')
def list_musica():
    if not os.path.exists(MUSICA_FOLDER):
        return jsonify([])
    meta = _load_musica_meta()
    songs = []
    for fname in sorted(os.listdir(MUSICA_FOLDER)):
        ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
        if ext in ALLOWED_AUDIO:
            songs.append({
                'filename': fname,
                'display_name': meta.get(fname, os.path.splitext(fname)[0]),
                'url': '/static/musica/' + fname
            })
    return jsonify(songs)


@bp.route('/api/musica/rename', methods=['POST'])
def rename_musica():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json() or {}
    filename = payload.get('filename', '')
    new_name = payload.get('new_name', '').strip()
    if not new_name or not _safe_musica_name(filename):
        return jsonify({'error': 'Datos inválidos'}), 400
    meta = _load_musica_meta()
    meta[filename] = new_name
    _save_musica_meta(meta)
    return jsonify({'ok': True})


@bp.route('/api/musica/delete', methods=['POST'])
def delete_musica():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json() or {}
    filename = payload.get('filename', '')
    if not _safe_musica_name(filename):
        return jsonify({'error': 'Nombre inválido'}), 400
    path = os.path.join(MUSICA_FOLDER, filename)
    if os.path.exists(path) and os.path.isfile(path):
        os.remove(path)
    meta = _load_musica_meta()
    meta.pop(filename, None)
    _save_musica_meta(meta)
    return jsonify({'ok': True})


@bp.route('/api/musica/upload', methods=['POST'])
def upload_musica():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    files = request.files.getlist('files')
    if not files:
        return jsonify({'error': 'No se enviaron archivos'}), 400
    os.makedirs(MUSICA_FOLDER, exist_ok=True)
    uploaded = []
    for f in files:
        if f and f.filename:
            ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
            if ext in ALLOWED_AUDIO:
                safe_name = secure_filename(f.filename)
                dest = os.path.join(MUSICA_FOLDER, safe_name)
                f.save(dest)
                uploaded.append(safe_name)
    if not uploaded:
        return jsonify({'error': 'Ningún archivo de audio válido'}), 400
    return jsonify({'ok': True, 'uploaded': uploaded, 'count': len(uploaded)})
