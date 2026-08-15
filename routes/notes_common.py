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

def _generate_public_slug(title):
    """Genera un slug único basado en el título: ej. 'reunion-julio-a1b2c3'."""
    base = _slugify(title)
    for _ in range(10):
        suffix = uuid.uuid4().hex[:6]
        candidate = f"{base}-{suffix}"
        if not Note.query.filter_by(public_token=candidate).first():
            return candidate
    return f"{base}-{uuid.uuid4().hex[:10]}"

def _slugify(text, max_len=40):
    """Convierte un título en un slug corto y legible (sin tildes, minúsculas, guiones)."""
    text = unicodedata.normalize('NFKD', text or '').encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text).strip('-')
    return text[:max_len].strip('-') or 'nota'

