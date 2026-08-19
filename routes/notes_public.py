from flask import request, jsonify, session, current_app, send_file, render_template
from flask_socketio import join_room, leave_room, emit
from models import Note
from db import db
from routes import bp, ALLOWED_IMAGE_EXTENSIONS
from socketio_instance import socketio
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
from .notes_common import _slugify, _generate_public_slug

def get_public_note(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return jsonify({'error': 'Enlace inválido o expirado'}), 404
    return jsonify({'ok': True, 'title': note.title, 'content': note.content, 'updated_at': note.updated_at.isoformat()})

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

def note_public_page(token):
    note = Note.query.filter_by(public_token=token).first()
    if not note:
        return render_template('notas_publica_404.html'), 404
    return render_template('notas_publica.html', token=token, note=note)

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

