# ==============================================================
#   BLINDADO - NO MODIFICAR SIN PERMISO EXPLICITO DEL DUENO
#   Explicar antes de editar. Contenido sagrado protegido.
# ==============================================================
"""Mini-Dropbox del dashboard: explora static/uploads (recursivo).

Todos los endpoints son SOLO superusuario. Los paths se validan contra
la raíz de uploads para impedir path traversal.
"""
import os
from flask import request, jsonify, session, url_for
from werkzeug.utils import secure_filename
from routes import bp

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads'))

_TIPOS = {
    'imagen': {'png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'svg', 'ico'},
    'video':  {'mp4', 'webm', 'mov', 'avi', 'mkv', 'wmv', 'm4v', 'mpg', 'mpeg'},
    'audio':  {'mp3', 'wav', 'ogg', 'm4a', 'wma', 'flac', 'aac'},
}


def _deny():
    return session.get('role') != 'Superusuario'


def _safe_rel(rel):
    """Normaliza un path relativo; None si sale de la raíz de uploads."""
    rel = (rel or '').replace('\\', '/').lstrip('/')
    full = os.path.realpath(os.path.join(_ROOT, rel))
    root = os.path.realpath(_ROOT)
    if full != root and not full.startswith(root + os.sep):
        return None
    return full


def _tipo(fname):
    ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
    for t, exts in _TIPOS.items():
        if ext in exts:
            return t
    return 'otro'


@bp.route('/api/multimedia/list')
def api_mm_list():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    files, folders = [], set()
    for root_d, dirs, names in os.walk(_ROOT):
        dirs.sort()
        rel_dir = os.path.relpath(root_d, _ROOT).replace('\\', '/')
        if rel_dir == '.':
            rel_dir = ''
        elif rel_dir:
            folders.add(rel_dir)
        for n in sorted(names):
            if n.startswith('.'):
                continue
            fp = os.path.join(root_d, n)
            rel = f'{rel_dir}/{n}' if rel_dir else n
            try:
                st = os.stat(fp)
            except OSError:
                continue
            files.append({'path': rel, 'name': n, 'folder': rel_dir,
                          'tipo': _tipo(n), 'size': st.st_size,
                          'mtime': int(st.st_mtime),
                          'url': url_for('static', filename='uploads/' + rel)})
    return jsonify({'ok': True, 'files': files, 'folders': sorted(folders)})


@bp.route('/api/multimedia/upload', methods=['POST'])
def api_mm_upload():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    dest_dir = _safe_rel(request.form.get('folder', ''))
    if dest_dir is None or not os.path.isdir(dest_dir):
        return jsonify({'error': 'Carpeta inválida'}), 400
    saved = []
    for f in request.files.getlist('files'):
        if not f or not f.filename:
            continue
        name = secure_filename(f.filename)
        base, ext = os.path.splitext(name)
        i = 1
        while os.path.exists(os.path.join(dest_dir, name)):
            name = f'{base}_{i}{ext}'
            i += 1
        f.save(os.path.join(dest_dir, name))
        saved.append(name)
    if not saved:
        return jsonify({'error': 'Sin archivos'}), 400
    return jsonify({'ok': True, 'saved': saved})


@bp.route('/api/multimedia/mkdir', methods=['POST'])
def api_mm_mkdir():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    name = secure_filename((request.json or {}).get('name', ''))
    if not name:
        return jsonify({'error': 'Nombre inválido'}), 400
    dest = _safe_rel(name)
    if dest is None:
        return jsonify({'error': 'Carpeta inválida'}), 400
    os.makedirs(dest, exist_ok=True)
    return jsonify({'ok': True})


@bp.route('/api/multimedia/rename', methods=['POST'])
def api_mm_rename():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json or {}
    src = _safe_rel(data.get('path'))
    new = secure_filename(data.get('name', ''))
    if not src or not os.path.isfile(src) or not new:
        return jsonify({'error': 'Datos inválidos'}), 400
    dest = os.path.join(os.path.dirname(src), new)
    if _safe_rel(os.path.relpath(dest, _ROOT)) is None or os.path.exists(dest):
        return jsonify({'error': 'Nombre ya existe o inválido'}), 400
    os.rename(src, dest)
    return jsonify({'ok': True})


@bp.route('/api/multimedia/move', methods=['POST'])
def api_mm_move():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json or {}
    src = _safe_rel(data.get('path'))
    dest_dir = _safe_rel(data.get('folder', ''))
    if not src or not os.path.isfile(src) or dest_dir is None or not os.path.isdir(dest_dir):
        return jsonify({'error': 'Datos inválidos'}), 400
    dest = os.path.join(dest_dir, os.path.basename(src))
    if os.path.exists(dest):
        return jsonify({'error': 'Ya existe un archivo con ese nombre allí'}), 400
    os.rename(src, dest)
    return jsonify({'ok': True})


@bp.route('/api/multimedia/delete', methods=['POST'])
def api_mm_delete():
    if _deny():
        return jsonify({'error': 'No autorizado'}), 403
    data = request.json or {}
    src = _safe_rel(data.get('path'))
    if not src or not os.path.isfile(src):
        return jsonify({'error': 'Archivo inválido'}), 400
    os.remove(src)
    return jsonify({'ok': True})
