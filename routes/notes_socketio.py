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

def handle_join_note(data):
    room = (data or {}).get('room')
    if room:
        join_room(room)

def handle_leave_note(data):
    room = (data or {}).get('room')
    if room:
        leave_room(room)

def handle_note_cursor(data):
    room = (data or {}).get('room')
    if not room:
        return
    emit('note_cursor', data, room=room, include_self=False)

def handle_note_edit(data):
    room = (data or {}).get('room')
    if not room:
        return
    emit('note_edit', data, room=room, include_self=False)

