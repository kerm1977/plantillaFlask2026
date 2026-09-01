# routes/home_media.py
import os
from flask import request, jsonify, session, url_for
from werkzeug.utils import secure_filename
from routes import bp
from db import db
from models import HomeMedia


UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'home_media')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'mp4', 'webm', 'mov'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _ensure_upload_dir():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@bp.route('/api/home-media', methods=['GET'])
def api_home_media_public():
    items = HomeMedia.query.filter_by(is_active=True).order_by(HomeMedia.sort_order.asc(), HomeMedia.id.asc()).all()
    return jsonify([i.to_dict() for i in items])


@bp.route('/api/home-media/all', methods=['GET'])
def api_home_media_all():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    items = HomeMedia.query.order_by(HomeMedia.sort_order.asc(), HomeMedia.id.asc()).all()
    return jsonify([i.to_dict() for i in items])


@bp.route('/api/home-media', methods=['POST'])
def api_home_media_create():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    data = request.form.to_dict()
    media_type = data.get('type', 'image')
    title = data.get('title', '').strip() or None
    url = data.get('url', '').strip() or None
    is_active = data.get('is_active', 'true').lower() == 'true'
    sort_order = int(data.get('sort_order', 0) or 0)
    filename = None

    if media_type == 'image':
        file = request.files.get('file')
        if not file or file.filename == '':
            return jsonify({'error': 'Debe subir una imagen'}), 400
        if not _allowed_file(file.filename):
            return jsonify({'error': 'Formato no permitido'}), 400
        _ensure_upload_dir()
        filename = secure_filename(file.filename)
        base, ext = os.path.splitext(filename)
        counter = 1
        while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
            filename = f"{base}_{counter}{ext}"
            counter += 1
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    elif media_type in ('youtube', 'facebook', 'link'):
        if not url:
            return jsonify({'error': 'La URL es requerida'}), 400
        if media_type == 'youtube':
            url = _normalize_youtube_url(url)
    else:
        return jsonify({'error': 'Tipo no válido'}), 400

    item = HomeMedia(
        type=media_type,
        title=title,
        url=url,
        filename=filename,
        is_active=is_active,
        sort_order=sort_order,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({'ok': True, 'item': item.to_dict()})


@bp.route('/api/home-media/<int:media_id>', methods=['PUT'])
def api_home_media_update(media_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    item = HomeMedia.query.get_or_404(media_id)
    data = request.form.to_dict()
    if 'type' in data:
        item.type = data.get('type', item.type)
    if 'title' in data:
        item.title = data.get('title', '').strip() or None
    if 'is_active' in data:
        item.is_active = data.get('is_active', 'true').lower() == 'true'
    item.sort_order = int(data.get('sort_order', item.sort_order) or 0)

    if 'url' in data:
        url = data.get('url', '').strip() or None
        if item.type == 'youtube' and url:
            url = _normalize_youtube_url(url)
        item.url = url

    if item.type == 'image':
        file = request.files.get('file')
        if file and file.filename != '':
            if not _allowed_file(file.filename):
                return jsonify({'error': 'Formato no permitido'}), 400
            _ensure_upload_dir()
            # Borrar anterior si existe
            if item.filename:
                old = os.path.join(UPLOAD_FOLDER, item.filename)
                if os.path.exists(old):
                    try:
                        os.remove(old)
                    except Exception:
                        pass
            filename = secure_filename(file.filename)
            base, ext = os.path.splitext(filename)
            counter = 1
            while os.path.exists(os.path.join(UPLOAD_FOLDER, filename)):
                filename = f"{base}_{counter}{ext}"
                counter += 1
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            item.filename = filename

    db.session.commit()
    return jsonify({'ok': True, 'item': item.to_dict()})


@bp.route('/api/home-media/<int:media_id>', methods=['DELETE'])
def api_home_media_delete(media_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403

    item = HomeMedia.query.get_or_404(media_id)
    if item.filename:
        path = os.path.join(UPLOAD_FOLDER, item.filename)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
    db.session.delete(item)
    db.session.commit()
    return jsonify({'ok': True})


def _normalize_youtube_url(url):
    """Dejar solo el ID de video para facilitar el embed."""
    import re
    # ya es un embed
    if '/embed/' in url:
        return url
    # watch?v=ID
    m = re.search(r'[?&]v=([^&#]+)', url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    # youtu.be/ID
    m = re.search(r'youtu\.be/([^?&#]+)', url)
    if m:
        return f"https://www.youtube.com/embed/{m.group(1)}"
    return url
