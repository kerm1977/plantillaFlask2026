from flask import request, jsonify, session, current_app, send_file, render_template
from models import Note
from db import db
from routes import bp
from datetime import datetime
import os
import uuid
import base64
import io
import tempfile
from html import escape
import re
import unicodedata
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _slugify(text, max_len=40):
    """Convierte un título en un slug corto y legible (sin tildes, minúsculas, guiones)."""
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text[:max_len].strip('-') or 'nota'


def _generate_public_slug(title):
    """Genera un slug único basado en el título: ej. 'reunion-julio-a1b2c3'."""
    base = _slugify(title)
    for _ in range(10):
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{base}-{suffix}"
        if not Note.query.filter_by(public_token=candidate).first():
            return candidate
    return f"{base}-{uuid.uuid4().hex[:10]}"


@bp.route('/api/notes', methods=['GET'])
def list_notes():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    notes = Note.query.filter_by(user_id=session['user_id']).order_by(Note.updated_at.desc()).all()
    return jsonify({'notes': [{'id': n.id, 'title': n.title, 'content': n.content, 'created_at': n.created_at.isoformat(), 'updated_at': n.updated_at.isoformat()} for n in notes]})


@bp.route('/api/notes', methods=['POST'])
def create_note():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    note = Note(
        title=data.get('title', 'Sin título'),
        content=data.get('content', ''),
        user_id=session['user_id']
    )
    db.session.add(note)
    db.session.commit()
    return jsonify({'ok': True, 'id': note.id})


@bp.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    note = Note.query.get(note_id)
    if not note or note.user_id != session['user_id']:
        return jsonify({'error': 'Nota no encontrada'}), 404
    data = request.json or {}
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    note = Note.query.get(note_id)
    if not note or note.user_id != session['user_id']:
        return jsonify({'error': 'Nota no encontrada'}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/api/notes/<int:note_id>/share', methods=['POST'])
def share_note(note_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    note = Note.query.get(note_id)
    if not note or note.user_id != session['user_id']:
        return jsonify({'error': 'Nota no encontrada'}), 404
    if not note.public_token:
        note.public_token = _generate_public_slug(note.title)
        db.session.commit()
    return jsonify({'ok': True, 'token': note.public_token, 'url': f'/notas/publicas/{note.public_token}'})


@bp.route('/api/notes/<int:note_id>/unshare', methods=['POST'])
def unshare_note(note_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    note = Note.query.get(note_id)
    if not note or note.user_id != session['user_id']:
        return jsonify({'error': 'Nota no encontrada'}), 404
    note.public_token = None
    db.session.commit()
    return jsonify({'ok': True})


@bp.route('/notas/publicas/<token>', methods=['GET'])
def note_public_page(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return render_template('notas_publica_404.html'), 404
    return render_template('notas_publica.html', token=token, note=note)


@bp.route('/notas/publicas/<token>/manifest.json', methods=['GET'])
def note_public_manifest(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return jsonify({'error': 'No encontrada'}), 404
    title = note.title or 'Nota Compartida'
    manifest = {
        'name': title,
        'short_name': title[:20],
        'description': f'Nota colaborativa: {title}',
        'start_url': f'/notas/publicas/{token}',
        'scope': f'/notas/publicas/{token}',
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': '#ff8c00',
        'icons': [
            {'src': '/static/uploads/icons/icon-192x192.jpg', 'type': 'image/jpeg', 'sizes': '192x192', 'purpose': 'any maskable'},
            {'src': '/static/uploads/icons/icon-512x512.jpg', 'type': 'image/jpeg', 'sizes': '512x512', 'purpose': 'any maskable'}
        ]
    }
    return jsonify(manifest)


@bp.route('/api/notes/public/<token>', methods=['GET'])
def get_public_note(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return jsonify({'error': 'Enlace inválido o expirado'}), 404
    return jsonify({'ok': True, 'title': note.title, 'content': note.content, 'updated_at': note.updated_at.isoformat()})


@bp.route('/api/notes/public/<token>', methods=['PUT'])
def update_public_note(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return jsonify({'error': 'Enlace inválido o expirado'}), 404
    data = request.json or {}
    note.title = data.get('title', note.title)
    note.content = data.get('content', note.content)
    note.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True, 'updated_at': note.updated_at.isoformat()})


@bp.route('/api/notes/public/<token>/upload-image', methods=['POST'])
def upload_public_note_image(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return jsonify({'error': 'Enlace inválido o expirado'}), 404
    if 'image' not in request.files:
        return jsonify({'error': 'No se envió imagen'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nombre vacío'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': 'Formato no permitido'}), 400

    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'notes')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f'note_{uuid.uuid4().hex[:8]}_{file.filename}'
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    return jsonify({'ok': True, 'url': f'/static/uploads/notes/{filename}'})


@bp.route('/api/notes/export-json', methods=['GET'])
def export_notes_json():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    notes = Note.query.filter_by(user_id=session['user_id']).order_by(Note.updated_at.desc()).all()
    export_data = [{
        'title': n.title,
        'content': n.content,
        'created_at': n.created_at.isoformat(),
        'updated_at': n.updated_at.isoformat()
    } for n in notes]
    return jsonify({'ok': True, 'notes': export_data})


@bp.route('/api/notes/import-json', methods=['POST'])
def import_notes_json():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    notes_data = data.get('notes', [])
    imported = 0
    for n_data in notes_data:
        note = Note(
            title=n_data.get('title', 'Sin título'),
            content=n_data.get('content', ''),
            user_id=session['user_id']
        )
        db.session.add(note)
        imported += 1
    db.session.commit()
    return jsonify({'ok': True, 'imported': imported})


@bp.route('/api/notes/upload-image', methods=['POST'])
def upload_note_image():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    if 'image' not in request.files:
        return jsonify({'error': 'No se envió imagen'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Nombre vacío'}), 400
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({'error': 'Formato no permitido'}), 400
    
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'notes')
    os.makedirs(upload_dir, exist_ok=True)
    filename = f'note_{uuid.uuid4().hex[:8]}_{file.filename}'
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    
    return jsonify({'ok': True, 'url': f'/static/uploads/notes/{filename}'})


@bp.route('/api/notes/export-pdf', methods=['POST'])
def export_note_pdf():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    data = request.json or {}
    title = data.get('title', 'nota')
    image_base64 = data.get('image', '')
    if not image_base64:
        return jsonify({'error': 'No se envió imagen'}), 400
    try:
        header, encoded = image_base64.split(',', 1)
        img_bytes = base64.b64decode(encoded)
    except Exception:
        return jsonify({'error': 'Imagen inválida'}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        reader = ImageReader(tmp_path)
        img_w, img_h = reader.getSize()

        buffer = io.BytesIO()
        c = pdfcanvas.Canvas(buffer, pagesize=letter)
        page_w, page_h = letter
        margin = 50

        # title
        c.setFont('Helvetica-Bold', 18)
        text_w = c.stringWidth(title, 'Helvetica-Bold', 18)
        c.drawString((page_w - text_w) / 2, page_h - margin, title)

        # image area below title
        top = page_h - margin - 30
        bottom = margin
        left = margin
        right = page_w - margin
        max_w = right - left
        max_h = top - bottom

        ratio = min(max_w / float(img_w), max_h / float(img_h))
        draw_w = img_w * ratio
        draw_h = img_h * ratio
        x = (page_w - draw_w) / 2
        y = top - draw_h

        c.drawImage(tmp_path, x, y, width=draw_w, height=draw_h)
        c.showPage()
        c.save()

        os.unlink(tmp_path)

        buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name=f"{title.replace(' ', '_')}.pdf",
                         mimetype='application/pdf')
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
