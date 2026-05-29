import os
import sys
import zipfile
import threading
from flask import request, jsonify, session, send_file
from datetime import datetime
from db import db
from routes import bp, _PROJECT_ROOT, _BACKUP_DIR, _load_meta, _save_meta, _make_zip

# ==========================================
# RUTAS DEL SISTEMA DE RESPALDOS
# ==========================================

@bp.route('/api/admin/backup/list')
def backup_list():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    entries = _load_meta()
    entries.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    return jsonify(entries)


@bp.route('/api/admin/backup/create', methods=['POST'])
def backup_create():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    payload     = request.get_json() or {}
    name        = payload.get('name', '').strip() or 'Respaldo sin título'
    description = payload.get('description', '').strip()
    ts          = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    zip_fname   = f'backup_{ts}.zip'
    zip_path    = os.path.join(_BACKUP_DIR, zip_fname)
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    try:
        _make_zip(zip_path)
        size  = os.path.getsize(zip_path)
        entry = {
            'id': ts, 'name': name, 'description': description,
            'filename': zip_fname, 'size': size,
            'created_at': datetime.utcnow().isoformat(), 'auto': False
        }
        entries = _load_meta()
        entries.append(entry)
        _save_meta(entries)
        return jsonify({'ok': True, 'entry': entry})
    except Exception as e:
        if os.path.exists(zip_path): os.remove(zip_path)
        return jsonify({'error': str(e)}), 500


@bp.route('/api/admin/backup/download/<backup_id>')
def backup_download(backup_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    entry = next((e for e in _load_meta() if e['id'] == backup_id), None)
    if not entry: return jsonify({'error': 'No encontrado'}), 404
    zip_path = os.path.join(_BACKUP_DIR, entry['filename'])
    if not os.path.exists(zip_path): return jsonify({'error': 'Archivo no encontrado'}), 404
    return send_file(zip_path, as_attachment=True, download_name=entry['filename'])


@bp.route('/api/admin/backup/delete/<backup_id>', methods=['DELETE'])
def backup_delete(backup_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    entries  = _load_meta()
    entry    = next((e for e in entries if e['id'] == backup_id), None)
    if not entry: return jsonify({'error': 'No encontrado'}), 404
    zip_path = os.path.join(_BACKUP_DIR, entry['filename'])
    if os.path.exists(zip_path): os.remove(zip_path)
    _save_meta([e for e in entries if e['id'] != backup_id])
    return jsonify({'ok': True})


@bp.route('/api/admin/backup/restore/<backup_id>', methods=['POST'])
def backup_restore(backup_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    entries  = _load_meta()
    entry    = next((e for e in entries if e['id'] == backup_id), None)
    if not entry: return jsonify({'error': 'Respaldo no encontrado'}), 404
    zip_path = os.path.join(_BACKUP_DIR, entry['filename'])
    if not os.path.exists(zip_path): return jsonify({'error': 'Archivo ZIP no encontrado'}), 404
    try:
        ts       = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        auto_zip = os.path.join(_BACKUP_DIR, f'pre_restore_{ts}.zip')
        _make_zip(auto_zip)
        auto_entry = {
            'id': f'pre_{ts}',
            'name': f'[AUTO] Antes de restaurar: {entry["name"]}',
            'description': f'Respaldo automático creado antes de restaurar "{entry["name"]}".',
            'filename': f'pre_restore_{ts}.zip',
            'size': os.path.getsize(auto_zip),
            'created_at': datetime.utcnow().isoformat(), 'auto': True
        }
        entries.append(auto_entry)
        _save_meta(entries)
        db.engine.dispose()
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(_PROJECT_ROOT)
        def _restart():
            import time; time.sleep(2)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        threading.Thread(target=_restart, daemon=True).start()
        return jsonify({'ok': True, 'restart': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
