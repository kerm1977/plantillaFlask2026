from flask import request, jsonify, session, current_app, send_file
from models import Note
from db import db
from routes import bp
from datetime import datetime
import os
import uuid
import base64
import io
from html import escape
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Image, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


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
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=50, leftMargin=50,
                                topMargin=50, bottomMargin=50)
        styles = getSampleStyleSheet()
        style_title = styles['Title']
        style_title.alignment = 1  # centered
        style_title.textColor = '#000000'

        story = []
        story.append(Paragraph(escape(title), style_title))
        story.append(Spacer(1, 0.2 * inch))

        img_stream = io.BytesIO(img_bytes)
        img = Image(img_stream, width=7.5 * inch, height=9.5 * inch)
        img.drawWidth = 7.5 * inch
        img.drawHeight = 9.5 * inch
        img.preserveAspectRatio = True
        story.append(img)

        doc.build(story)
        buffer.seek(0)
        return send_file(buffer, as_attachment=True,
                         download_name=f"{title.replace(' ', '_')}.pdf",
                         mimetype='application/pdf')
    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500
