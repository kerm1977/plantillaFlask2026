from flask import Blueprint, session
from models import User
from db import db
import os
import json
import zipfile

# ==========================================
# CONSTANTES Y HELPERS COMPARTIDOS
# ==========================================
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
_BACKUP_DIR   = os.path.join(_PROJECT_ROOT, 'backups')
_META_FILE    = os.path.join(_BACKUP_DIR, 'metadata.json')
_DB_PATH      = os.path.join(_PROJECT_ROOT, 'local_app.db')
_BACKUP_SKIP  = {'backups', '__pycache__', '.git', 'venv', 'env', 'node_modules',
                 '.idea', '.vscode', '.mypy_cache'}

def _load_meta():
    if not os.path.exists(_META_FILE): return []
    try:
        with open(_META_FILE, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def _save_meta(entries):
    os.makedirs(_BACKUP_DIR, exist_ok=True)
    with open(_META_FILE, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

def _make_zip(zip_path, skip_backup_dir=True):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for item in os.listdir(_PROJECT_ROOT):
            if item in _BACKUP_SKIP: continue
            if skip_backup_dir and item == 'backups': continue
            if item.startswith('templates_BACKUP_'): continue
            full = os.path.join(_PROJECT_ROOT, item)
            if os.path.isfile(full):
                if not full.endswith('.pyc'):
                    zf.write(full, item)
            elif os.path.isdir(full):
                for root_d, dirs, files in os.walk(full):
                    dirs[:] = [d for d in dirs if d not in _BACKUP_SKIP
                               and not d.startswith('templates_BACKUP_')]
                    for fname in files:
                        if fname.endswith('.pyc'): continue
                        fp = os.path.join(root_d, fname)
                        zf.write(fp, os.path.relpath(fp, _PROJECT_ROOT))

# ==========================================
# BLUEPRINT PRINCIPAL
# ==========================================
bp = Blueprint('main', __name__)

# --- FUNCIONES AUXILIARES DE SEGURIDAD ---
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

@bp.before_request
def ensure_session_avatar():
    if 'user_id' in session:
        if 'avatar' not in session or 'email' not in session:
            user = User.query.get(session['user_id'])
            if user:
                if 'avatar' not in session:
                    session['avatar'] = user.avatar or ''
                if 'email' not in session:
                    session['email'] = user.email or ''

# ==========================================
# REGISTRAR TODAS LAS SUB-RUTAS
# ==========================================
from routes import (        # noqa: E402, F401
    pages,
    pages_admin,
    pages_crm,
    auth,
    events,
    events_crud,
    music,
    gpx,
    about,
    pwa,
    admin_users,
    admin_actions,
    hiker_public,
    hiker_admin,
    backups,
    db_export,
    forms_crud,
    forms_public,
    forms_responses,
    rifas_public,
    rifas_selecciones,
    rifas_selecciones_select,
    rifas_admin,
    publicaciones,
)

# Re-exportar para app.py
from routes.about import inject_site_content  # noqa: E402, F401
