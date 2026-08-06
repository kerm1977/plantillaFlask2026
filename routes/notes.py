from flask import request, jsonify, session, current_app
from models import Note
from db import db
from routes import bp
from datetime import datetime
import os
import uuid

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
