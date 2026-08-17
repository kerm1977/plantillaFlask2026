import os
import json
from datetime import datetime
from models_notes import Note

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_DATA_FILE = os.path.join(_PROJECT_ROOT, 'data', 'active_note.json')


def _load():
    if not os.path.exists(_DATA_FILE):
        return {}
    try:
        with open(_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data):
    os.makedirs(os.path.dirname(_DATA_FILE), exist_ok=True)
    with open(_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_active_note():
    data = _load()
    note_id = data.get('note_id')
    if not note_id:
        return None
    try:
        note_id = int(note_id)
    except (ValueError, TypeError):
        return None
    note = Note.query.get(note_id)
    if not note:
        return None
    return {
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'is_public': bool(data.get('is_public', False)),
        'updated_at': data.get('updated_at', '')
    }


def set_active_note(note_id, is_public=False):
    try:
        note_id = int(note_id)
    except (ValueError, TypeError):
        return None
    note = Note.query.get(note_id)
    if not note:
        return None
    _save({
        'note_id': note_id,
        'is_public': bool(is_public),
        'updated_at': datetime.utcnow().isoformat()
    })
    return get_active_note()


def clear_active_note():
    _save({})
    return None
