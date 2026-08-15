from flask import request, jsonify, session, current_app, send_file, render_template
from flask_socketio import join_room, leave_room, emit
from models import Note
from db import db
from routes import bp
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

