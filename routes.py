from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
from models import User, Notification, Event, Hiker, EventRegistration, SiteContent
from users import hash_password, check_password
from db import db
from datetime import datetime
import os
import json
import re
import secrets
import string
from sqlalchemy import text
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

# --- FUNCIONES AUXILIARES DE SEGURIDAD ---
def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
# -----------------------------------------

@bp.route('/')
def home():
    notifications = Notification.query.all()
    return render_template('home.html', notifications=notifications)

@bp.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
    return render_template('perfil.html', user=user)

@bp.route('/calendario')
def calendario():
    # Protegemos la ruta para que solo Superusuarios puedan acceder
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    
    # Obtener todos los eventos ordenados por fecha
    eventos_db = Event.query.order_by(Event.fecha_inicio).all()
    
    meses_es = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
        5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
        9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    
    eventos_procesados = []
    for ev in eventos_db:
        if getattr(ev, 'fecha_inicio', None):
            fecha_dt = ev.fecha_inicio
            
            # Blindaje: Por si la fecha viene como string desde SQLite
            if isinstance(fecha_dt, str):
                try:
                    fecha_dt = datetime.strptime(fecha_dt, '%Y-%m-%d').date()
                except ValueError:
                    try:
                        fecha_dt = datetime.strptime(fecha_dt, '%d/%m/%Y').date()
                    except ValueError:
                        continue # Si el formato es totalmente ilegible, lo omite sin crashear
            
            # Extracción segura de mes y día
            mes_num = getattr(fecha_dt, 'month', 1)
            dia_num = getattr(fecha_dt, 'day', 1)
            
            eventos_procesados.append({
                'mes': meses_es.get(mes_num, 'S/M'),
                'dia': str(dia_num),
                'nombre': getattr(ev, 'nombre_lugar', 'Caminata'),
                'categoria': getattr(ev, 'actividad', 'Caminata') or 'Caminata',
                'dificultad': getattr(ev, 'dificultad', 'Moderada') or 'Moderada'
            })
    
    # Pasamos los eventos ya procesados al HTML sin errores de Json
    return render_template('calendario.html', eventos=eventos_procesados)

@bp.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('dashboard.html')

@bp.route('/eventos')
def eventos():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('eventos.html')

@bp.route('/detalles_evento/<int:event_id>')
def detalles_evento(event_id):
    evento = Event.query.get_or_404(event_id)
    return render_template('ver_evento.html', evento=evento)

@bp.route('/api/get_events')
def get_events():
    events = Event.query.order_by(Event.created_at.desc()).all()
    is_super = session.get('role') == 'Superusuario'
    output = []
    
    for e in events:
        # LÓGICA DE NEGOCIO EN EL BACKEND (Donde debe estar)
        # Si es logística segura y NO es admin, ocultamos datos
        if e.logistica_segura and not is_super:   
            destino_text = "Ver en chat"
            hora_text = "Ver en chat"
        else:
            destino_text = e.lugar_salida
            hora_text = e.hora_salida
                
        # Calcular precio o devolver "PENDIENTE"
        try:
            precio_val = int(e.precio) if e.precio else 0
        except (ValueError, TypeError):
            precio_val = 0
            
        precio_mostrar = f"{e.moneda or ''}{precio_val}" if precio_val > 0 else "PENDIENTE"
                
        output.append({
            "id": e.id,
            "poster": f"/static/uploads/{e.poster}" if e.poster else "/static/default.png",
            "nombreLugar": e.nombre_lugar,
            "dificultad": e.dificultad,
            "actividad": e.actividad,
            "precio": precio_mostrar,
            "destino": destino_text,
            "hora_salida": hora_text or "Por definir",
            "logistica_segura": e.logistica_segura,
            "fecha": e.fecha_unica if e.dias == 1 else f"{e.fecha_inicio} al {e.fecha_regreso}",
            "solo_chat": e.solo_chat, 
            "capacidad": e.capacidad,
            "is_sold_out": e.is_sold_out # Mandamos el booleano al frontend
        })
    return jsonify(output)

@bp.route('/api/toggle_espacio/<int:event_id>', methods=['POST'])
def toggle_espacio(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    # Ya no manipulamos strings, solo invertimos el booleano
    evento.is_sold_out = not evento.is_sold_out
    db.session.commit()
    return jsonify({"success": True, "is_sold_out": evento.is_sold_out})

@bp.route('/api/make_public/<int:event_id>', methods=['POST'])
def make_public(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    # Quitamos la privacidad limpiamente
    evento.logistica_segura = False
    evento.solo_chat = False
    db.session.commit()
    return jsonify({"success": True})

@bp.route('/api/create_event', methods=['POST'])
def create_event():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    try:
        file = request.files.get('poster')
        filename = "default_event.png"
        
        # Validación de seguridad: Extensión permitida
        if file and file.filename != '':
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))

        destino_db = request.form.get('destinoInternacional') if request.form.get('actividad') == 'Internacional' else request.form.get('lugarSalida')

        new_event = Event(
            poster=filename,
            nombre_lugar=request.form.get('nombreLugar'),
            dificultad=request.form.get('dificultad'),
            actividad=request.form.get('actividad'),
            moneda=request.form.get('moneda'),
            precio=int(request.form.get('precio', 0) if request.form.get('precio') else 0),
            reserva=int(request.form.get('reserva', 0) if request.form.get('reserva') else 0),
            capacidad=request.form.get('capacidad'),
            sinpe=request.form.get('sinpe'),
            cuenta=request.form.get('cuenta'),
            solo_chat=request.form.get('solo_chat') == 'true',
            logistica_segura=request.form.get('logistica_segura') == 'true', # Nuevo booleano
            dias=int(request.form.get('dias', 1) if request.form.get('dias') else 1),
            fecha_unica=request.form.get('fechaUnica'),
            fecha_inicio=request.form.get('fechaInicio'),
            fecha_regreso=request.form.get('fechaRegreso'),
            hora_salida=request.form.get('horaSalida'),
            lugar_salida=destino_db,
            puntos_recogida=request.form.get('puntosRecogida'),
            itinerario=request.form.get('itinerario'),
            incluye=request.form.get('incluye')
        )
        db.session.add(new_event)
        db.session.commit()
        return jsonify({"success": True, "event_id": new_event.id})
    except Exception as e:
        db.session.rollback()
        # En producción, usar logging en lugar de print
        print(f"Error grave al guardar evento: {e}")
        return jsonify({"error": "Error interno del servidor al crear el evento"}), 500

@bp.route('/api/update_event/<int:event_id>', methods=['POST'])
def update_event(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    evento = Event.query.get_or_404(event_id)
    try:
        file = request.files.get('poster')
        if file and file.filename != '':
            if not allowed_file(file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(f"event_{os.urandom(4).hex()}_{file.filename}")
            upload_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, filename))
            evento.poster = filename

        destino_db = request.form.get('destinoInternacional') if request.form.get('actividad') == 'Internacional' else request.form.get('lugarSalida')

        evento.nombre_lugar = request.form.get('nombreLugar', evento.nombre_lugar)
        evento.dificultad = request.form.get('dificultad', evento.dificultad)
        evento.actividad = request.form.get('actividad', evento.actividad)
        evento.moneda = request.form.get('moneda', evento.moneda)
        evento.precio = int(request.form.get('precio', evento.precio) if request.form.get('precio') else 0)
        evento.reserva = int(request.form.get('reserva', evento.reserva) if request.form.get('reserva') else 0)
        evento.capacidad = request.form.get('capacidad', evento.capacidad)
        evento.sinpe = request.form.get('sinpe', evento.sinpe)
        evento.cuenta = request.form.get('cuenta', evento.cuenta)
        
        # Leemos los booleanos reales del form
        evento.solo_chat = request.form.get('solo_chat') == 'true'
        evento.logistica_segura = request.form.get('logistica_segura') == 'true'
        
        evento.dias = int(request.form.get('dias', evento.dias) if request.form.get('dias') else 1)
        evento.fecha_unica = request.form.get('fechaUnica', evento.fecha_unica)
        evento.fecha_inicio = request.form.get('fechaInicio', evento.fecha_inicio)
        evento.fecha_regreso = request.form.get('fechaRegreso', evento.fecha_regreso)
        evento.hora_salida = request.form.get('horaSalida', evento.hora_salida)
        evento.lugar_salida = destino_db if destino_db else evento.lugar_salida
        evento.puntos_recogida = request.form.get('puntosRecogida', evento.puntos_recogida)
        evento.itinerario = request.form.get('itinerario', evento.itinerario)
        evento.incluye = request.form.get('incluye', evento.incluye)

        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        print(f"Error al actualizar evento: {e}")
        return jsonify({"error": "Error interno del servidor al actualizar"}), 500

@bp.route('/api/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    try:
        db.session.delete(evento)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar evento"}), 500

# ==========================================
# RUTAS REPRODUCTOR DE MÚSICA
# ==========================================
MUSICA_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'musica')
MUSICA_METADATA_FILE = os.path.join(MUSICA_FOLDER, 'metadata.json')
ALLOWED_AUDIO = {'mp3', 'ogg', 'wav', 'flac', 'm4a', 'aac'}

def _load_musica_meta():
    if os.path.exists(MUSICA_METADATA_FILE):
        with open(MUSICA_METADATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_musica_meta(data):
    os.makedirs(MUSICA_FOLDER, exist_ok=True)
    with open(MUSICA_METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _safe_musica_name(name):
    return '/' not in name and '\\' not in name and '..' not in name

@bp.route('/api/musica')
def list_musica():
    if not os.path.exists(MUSICA_FOLDER):
        return jsonify([])
    meta = _load_musica_meta()
    songs = []
    for fname in sorted(os.listdir(MUSICA_FOLDER)):
        ext = fname.rsplit('.', 1)[-1].lower() if '.' in fname else ''
        if ext in ALLOWED_AUDIO:
            songs.append({
                'filename': fname,
                'display_name': meta.get(fname, os.path.splitext(fname)[0]),
                'url': '/static/musica/' + fname
            })
    return jsonify(songs)

@bp.route('/api/musica/rename', methods=['POST'])
def rename_musica():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json() or {}
    filename = payload.get('filename', '')
    new_name = payload.get('new_name', '').strip()
    if not new_name or not _safe_musica_name(filename):
        return jsonify({'error': 'Datos inválidos'}), 400
    meta = _load_musica_meta()
    meta[filename] = new_name
    _save_musica_meta(meta)
    return jsonify({'ok': True})

@bp.route('/api/musica/delete', methods=['POST'])
def delete_musica():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json() or {}
    filename = payload.get('filename', '')
    if not _safe_musica_name(filename):
        return jsonify({'error': 'Nombre inválido'}), 400
    path = os.path.join(MUSICA_FOLDER, filename)
    if os.path.exists(path) and os.path.isfile(path):
        os.remove(path)
    meta = _load_musica_meta()
    meta.pop(filename, None)
    _save_musica_meta(meta)
    return jsonify({'ok': True})

# ==========================================
# RUTAS GPX POR EVENTO
# ==========================================
GPX_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'gpx')

@bp.route('/api/evento/<int:event_id>/gpx', methods=['POST'])
def upload_gpx(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    if 'gpx_file' not in request.files:
        return jsonify({'error': 'No se envió archivo'}), 400
    gpx_file = request.files['gpx_file']
    if not gpx_file.filename.lower().endswith('.gpx'):
        return jsonify({'error': 'Solo se permiten archivos .gpx'}), 400
    os.makedirs(GPX_FOLDER, exist_ok=True)
    filename = secure_filename(f"evento_{event_id}_{gpx_file.filename}")
    gpx_file.save(os.path.join(GPX_FOLDER, filename))
    evento.gpx_filename = filename
    db.session.commit()
    return jsonify({'ok': True, 'filename': filename})

@bp.route('/api/evento/<int:event_id>/gpx', methods=['DELETE'])
def delete_gpx(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    if evento.gpx_filename:
        path = os.path.join(GPX_FOLDER, evento.gpx_filename)
        if os.path.exists(path):
            os.remove(path)
        evento.gpx_filename = None
        evento.gpx_password = None
        db.session.commit()
    return jsonify({'ok': True})

@bp.route('/api/evento/<int:event_id>/gpx/password', methods=['POST'])
def set_gpx_password(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    payload = request.get_json() or {}
    pwd = payload.get('password', '').strip()
    if not pwd:
        chars = string.ascii_uppercase + string.digits
        pwd = ''.join(secrets.choice(chars) for _ in range(6))
    evento.gpx_password = pwd
    db.session.commit()
    return jsonify({'ok': True, 'password': pwd})

@bp.route('/api/evento/<int:event_id>/gpx/download')
def download_gpx(event_id):
    evento = Event.query.get_or_404(event_id)
    if not evento.gpx_filename:
        return jsonify({'error': 'No hay GPX para este evento'}), 404
    if evento.gpx_password:
        clave = request.args.get('clave', '')
        if clave.strip().upper() != evento.gpx_password.strip().upper():
            return jsonify({'error': 'Contraseña incorrecta'}), 403
    return send_from_directory(GPX_FOLDER, evento.gpx_filename, as_attachment=True)

@bp.route('/api/evento/<int:event_id>/organicmaps', methods=['POST'])
def set_organicmaps(event_id):
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    evento = Event.query.get_or_404(event_id)
    payload = request.get_json() or {}
    evento.organicmaps_url = payload.get('url', '').strip()
    db.session.commit()
    return jsonify({'ok': True})

# ==========================================
# CONTENIDO EDITABLE DEL SITIO
# ==========================================
DEFAULT_SITE_CONTENT = {
    'quienes_somos': (
        "En San Diego de la Unión de Cartago, nace en el mes de Octubre, un grupo de senderismo llamado "
        "la tribu de los libres y hace referencia a las tribus en general que siempre han sido los guardianes "
        "y amantes de la naturaleza.\n\n"
        "Lleva como base la filosofía Ubuntu, proveniente de las tribus sudafricanas y que significa:\n\n"
        "“Soy porque tú eres. Eres porque somos.”\n\n"
        "Pero Ubuntu, ni su significado, se refieren a ningún dogma político, ni religión, sino... "
        "Se trata de una ética mundial que se enfoca en la lealtad propia y con los demás, englobando el "
        "sentido de la vida visto con ojos de lealtad, estabilidad emocional y hermandad que se resume en que:\n\n"
        "“Tenemos la responsabilidad sobre los demás, especialmente sobre los vulnerables, y el medio ambiente.”\n\n"
        "La vida de la tribu, es la voluntad de vivir la solidaridad entre iguales. Por eso, la tribu hiking "
        "hace énfasis a uno de sus lemas que lleva desde sus inicios:\n\n"
        "“Esta es una historia escrita, con el cariño y el corazón de sus miembros”"
    ),
    'mision': (
        "Ser el grupo de senderismo de referencia en Costa Rica, promoviendo la naturaleza, la hermandad "
        "y la filosofía Ubuntu entre sus miembros y comunidades."
    ),
    'vision': (
        "Inspirar a cada persona a reconectar con la naturaleza y con los demás, forjando lazos de lealtad, "
        "solidaridad y respeto mutuo en cada caminata, pero promoviendo la participación activa y sincera "
        "de esta bonita actividad."
    ),
    'valores': (
        "Hermandad: Creemos en la fuerza del grupo y en que cada miembro es esencial para el todo.\n"
        "Ubuntu: “Soy porque tú eres. Eres porque somos.” Es nuestra guía de vida.\n"
        "Respeto a la naturaleza: Somos guardianes del entorno que recorremos.\n"
        "Solidaridad: Tenemos la responsabilidad sobre los demás, especialmente sobre los vulnerables y el medio ambiente."
    )
}

def inject_site_content():
    for key, value in DEFAULT_SITE_CONTENT.items():
        if not SiteContent.query.filter_by(key=key).first():
            db.session.add(SiteContent(key=key, value=value))
    db.session.commit()

@bp.route('/api/about', methods=['GET'])
def get_about():
    rows = SiteContent.query.filter(SiteContent.key.in_(DEFAULT_SITE_CONTENT.keys())).all()
    data = {row.key: row.value for row in rows}
    return jsonify(data)

@bp.route('/api/about', methods=['POST'])
def update_about():
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'Sin permiso'}), 403
    payload = request.get_json()
    for key in DEFAULT_SITE_CONTENT.keys():
        if key in payload:
            row = SiteContent.query.filter_by(key=key).first()
            if row:
                row.value = payload[key]
            else:
                db.session.add(SiteContent(key=key, value=payload[key]))
    db.session.commit()
    return jsonify({'ok': True})

# ==========================================
# RUTAS DE PWA (PROGRESIVE WEB APP)
# ==========================================
@bp.route('/manifest.json')
def manifest():
    manifest_data = {
        "name": "Caminatas La Tribu",
        "short_name": "La Tribu",
        "description": "Gestión de caminatas, eventos y comunidad de La Tribu de Los Libres.",
        "lang": "es",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#ffe0bd",
        "theme_color": "#ff8c00",
        "categories": ["sports", "social", "lifestyle"],
        "icons": [
            {
                "src": "/static/logo.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any"
            },
            {
                "src": "/static/logo.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "shortcuts": [
            {
                "name": "Inicio",
                "url": "/",
                "icons": [{"src": "/static/logo.png", "sizes": "96x96"}]
            }
        ]
    }
    return Response(json.dumps(manifest_data), mimetype='application/manifest+json')

@bp.route('/sw.js')
def sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

# ==========================================
# RUTAS DE AUTENTICACIÓN Y PERFIL
# ==========================================
@bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email').lower()).first()
    if user and check_password(data.get('password'), user.password_hash):
        if user.status == 'Bloqueado':
            return jsonify({'error': 'Usuario bloqueado'}), 403
        session['user_id'] = user.id
        session['role'] = user.role
        return jsonify({'success': True})
    return jsonify({'error': 'Credenciales inválidas'}), 401

@bp.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data.get('email').lower()).first():
        return jsonify({'error': 'Email ya registrado'}), 400
        
    try:
        new_user = User(
            name=data.get('name'),
            last_name_1=data.get('last_name_1'),
            last_name_2=data.get('last_name_2'),
            email=data.get('email').lower(),
            password_hash=hash_password(data.get('password'))
        )
        
        if data.get('phone_code'): new_user.phone_code = data.get('phone_code')
        if data.get('phone'): new_user.phone = data.get('phone')
        if data.get('dob'): new_user.dob = datetime.strptime(data.get('dob'), '%Y-%m-%d').date()

        if data.get('whatsapp') and hasattr(new_user, 'whatsapp'): new_user.whatsapp = data.get('whatsapp')
        if data.get('facebook') and hasattr(new_user, 'facebook'): new_user.facebook = data.get('facebook')
        if data.get('instagram') and hasattr(new_user, 'instagram'): new_user.instagram = data.get('instagram')
        if data.get('address') and hasattr(new_user, 'address'): new_user.address = data.get('address')
        if data.get('institution') and hasattr(new_user, 'institution'): new_user.institution = data.get('institution')
        if data.get('other_info') and hasattr(new_user, 'other_info'): new_user.other_info = data.get('other_info')

        db.session.add(new_user)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback() 
        return jsonify({'error': str(e)}), 500

@bp.route('/api/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
        
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'Usuario no encontrado'}), 404

    try:
        user.name = request.form.get('name', user.name)
        user.last_name_1 = request.form.get('last_name_1', user.last_name_1)
        user.last_name_2 = request.form.get('last_name_2', user.last_name_2)
        user.email = request.form.get('email', user.email).lower()
        
        if request.form.get('phone_code'): user.phone_code = request.form.get('phone_code')
        if request.form.get('phone'): user.phone = request.form.get('phone')
        
        dob_str = request.form.get('dob')
        if dob_str: user.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
        
        if request.form.get('whatsapp') and hasattr(user, 'whatsapp'): user.whatsapp = request.form.get('whatsapp')
        if request.form.get('facebook') and hasattr(user, 'facebook'): user.facebook = request.form.get('facebook')
        if request.form.get('instagram') and hasattr(user, 'instagram'): user.instagram = request.form.get('instagram')
        if request.form.get('address') and hasattr(user, 'address'): user.address = request.form.get('address')
        if request.form.get('institution') and hasattr(user, 'institution'): user.institution = request.form.get('institution')
        if request.form.get('other_info') and hasattr(user, 'other_info'): user.other_info = request.form.get('other_info')

        avatar_file = request.files.get('avatar')
        if avatar_file and avatar_file.filename != '':
            if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({"error": "Formato de imagen no permitido"}), 400
                
            filename = secure_filename(avatar_file.filename)
            filename = f"user_{user.id}_{filename}"
            static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
            os.makedirs(static_folder, exist_ok=True)
            filepath = os.path.join(static_folder, filename)
            avatar_file.save(filepath)
            user.avatar = f"uploads/{filename}" 

        db.session.commit()
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Error interno al guardar los datos'}), 500

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

# ==========================================
# RUTAS DE ADMINISTRACIÓN (DASHBOARD)
# ==========================================
@bp.route('/api/admin/users')
def admin_get_users():
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    users = User.query.all()
    output = []
    for u in users:
        output.append({
            'id': u.id,
            'name': u.name,
            'last_name_1': u.last_name_1,
            'last_name_2': u.last_name_2,
            'email': u.email,
            'role': u.role,
            'status': u.status,
            'dob': u.dob.strftime('%Y-%m-%d') if u.dob else None,
            'phone': f"{u.phone_code or ''} {u.phone or 'No registrado'}",
            'created': u.created_at.strftime('%d de %B, %Y - %H:%M') if u.created_at else 'N/A',
            'updated': u.updated_at.strftime('%d de %B, %Y - %H:%M') if u.updated_at else 'N/A',
            'avatar': u.avatar
        })
    return jsonify(output)

@bp.route('/api/admin/toggle_status/<int:user_id>', methods=['POST'])
def admin_toggle_status(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == session['user_id']:
        return jsonify({'error': 'No puedes bloquear tu propia cuenta principal'}), 400
    
    u = User.query.get_or_404(user_id)
    u.status = 'Bloqueado' if u.status == 'Activo' else 'Activo'
    db.session.commit()
    return jsonify({'success': True, 'new_status': u.status})

@bp.route('/api/admin/delete_user/<int:user_id>', methods=['DELETE'])
def admin_delete_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    if user_id == session['user_id']:
        return jsonify({'error': 'No puedes eliminar tu propia cuenta principal'}), 400
        
    u = User.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    return jsonify({'success': True})

@bp.route('/api/admin/update_user/<int:user_id>', methods=['POST'])
def admin_update_user(user_id):
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
        
    u = User.query.get_or_404(user_id)
    
    u.name = request.form.get('name', u.name)
    u.last_name_1 = request.form.get('last_name_1', u.last_name_1)
    u.last_name_2 = request.form.get('last_name_2', u.last_name_2)
    u.email = request.form.get('email', u.email).lower()
    
    new_role = request.form.get('role')
    if new_role:
        u.role = new_role
        if new_role == 'Superusuario': u.weight = 100
        elif new_role == 'Administrador': u.weight = 50
        elif new_role == 'Colaborador': u.weight = 10
        else: u.weight = 1
        
    new_pass = request.form.get('password')
    if new_pass:
        u.password_hash = hash_password(new_pass)
        
    if request.form.get('phone'): 
        u.phone = request.form.get('phone')
        
    avatar_file = request.files.get('avatar')
    if avatar_file and avatar_file.filename != '':
        if not allowed_file(avatar_file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"error": "Formato de imagen no permitido"}), 400
            
        filename = secure_filename(avatar_file.filename)
        filename = f"user_{u.id}_{filename}"
        static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
        os.makedirs(static_folder, exist_ok=True)
        avatar_file.save(os.path.join(static_folder, filename))
        u.avatar = f"uploads/{filename}"

    db.session.commit()
    return jsonify({'success': True})


# ==========================================
# SISTEMA CRM E INSCRIPCIONES (LA TRIBU)
# ==========================================

@bp.route('/inscripcion/<path:identifier>')
def inscripcion_evento(identifier):
    """
    Ruta pública para el formulario de inscripción a un evento.
    Soporta identificadores numéricos (/inscripcion/20) y slugs amigables (/inscripcion/caminata-isla-venado-20).
    """
    import re # Importamos 're' aquí por si no está en la parte superior de tu archivo routes.py
    
    if identifier.isdigit():
        # Si el link es antiguo y solo tiene el número (ej: /inscripcion/20)
        evento = Event.query.get_or_404(int(identifier))
    else:
        # Si es un link nuevo con texto, buscamos el ID al final (ej: caminata-isla-venado-20 -> extrae el 20)
        match = re.search(r'-(\d+)$', identifier)
        if match:
            evento_id = int(match.group(1))
            evento = Event.query.get_or_404(evento_id)
        else:
            # Fallback de seguridad: si el link no tiene número al final por alguna razón, 
            # intenta buscar el evento por el nombre aproximado.
            nombre_real = identifier.replace('-', ' ')
            evento = Event.query.filter(Event.nombre_lugar.ilike(f"%{nombre_real}%")).order_by(Event.id.desc()).first_or_404()
            
    return render_template('formulario_inscripcion.html', evento=evento)

@bp.route('/editar_caminante/<identifier>')
def editar_caminante(identifier):
    """
    Abre el formulario en modo 'edición' usando la cédula (CRM) o el PIN (Usuario).
    """
    # Intentamos buscar primero por cédula
    hiker = Hiker.query.filter_by(cedula=identifier).first()
    
    # Si no aparece, intentamos buscar por PIN
    if not hiker:
        hiker = Hiker.query.filter_by(pin_secreto=identifier).first()
        
    if not hiker:
        # Si de ninguna forma existe, lo mandamos al inicio
        return redirect(url_for('main.home'))
        
    return render_template('editar_caminante.html', hiker=hiker)

@bp.route('/api/hiker/check/<cedula>')
def check_hiker(cedula):
    # API Silenciosa para autocompletar formularios si el caminante ya existe
    try:
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        if hiker:
            # Shield para fecha_nacimiento física
            f_nac_str = ""
            try:
                if hasattr(hiker, 'fecha_nacimiento') and hiker.fecha_nacimiento:
                    f_nac_str = hiker.fecha_nacimiento.strftime('%Y-%m-%d')
            except:
                f_nac_str = ""

            return jsonify({
                'found': True,
                'nombre_completo': hiker.nombre_completo,
                'telefono': hiker.telefono,
                'fecha_nacimiento': f_nac_str,
                'tipo_sangre': hiker.tipo_sangre,
                'alergias': hiker.alergias,
                'enfermedades_cronicas': hiker.enfermedades_cronicas,
                'contacto_emergencia_nombre': hiker.contacto_emergencia_nombre,
                'contacto_emergencia_telefono': hiker.contacto_emergencia_telefono
            })
    except:
        pass
    return jsonify({'found': False})

@bp.route('/api/hiker/register', methods=['POST'])
def register_hiker():
    data = request.get_json()
    
    try:
        cedula = data.get('cedula', '').strip()
        event_id = data.get('event_id')
        
        if not cedula:
            return jsonify({'success': False, 'error': 'La cédula es obligatoria'}), 400

        # 1. ESCUDO ANTI-DUPLICADOS (Buscamos si la cédula ya existe)
        hiker = Hiker.query.filter_by(cedula=cedula).first()
        
        if not hiker:
            # Si NO existe, creamos un nuevo caminante
            hiker = Hiker(cedula=cedula)
            db.session.add(hiker)
        
        # 2. ACTUALIZAMOS SIEMPRE SU INFORMACIÓN
        hiker.nombre_completo = data.get('nombre_completo', hiker.nombre_completo)
        hiker.telefono = data.get('telefono', hiker.telefono)
        hiker.tipo_sangre = data.get('tipo_sangre', hiker.tipo_sangre)
        hiker.alergias = data.get('alergias', hiker.alergias)
        hiker.enfermedades_cronicas = data.get('enfermedades_cronicas', hiker.enfermedades_cronicas)
        hiker.contacto_emergencia_nombre = data.get('contacto_emergencia_nombre', hiker.contacto_emergencia_nombre)
        hiker.contacto_emergencia_telefono = data.get('contacto_emergencia_telefono', hiker.contacto_emergencia_telefono)
        
        # INTEGRACIÓN SEGURA FECHA NACIMIENTO
        f_nac = data.get('fecha_nacimiento')
        if f_nac:
            try:
                # Solo intentamos guardar si la columna existe en el objeto
                hiker.fecha_nacimiento = datetime.strptime(f_nac, '%Y-%m-%d').date()
            except:
                pass

        # Generar PIN si es nuevo
        if not hiker.pin_secreto:
            import random, string
            hiker.pin_secreto = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
        db.session.commit()

        # 3. REGISTRO AL EVENTO
        if event_id:
            inscripcion_existente = EventRegistration.query.filter_by(event_id=event_id, hiker_id=hiker.id).first()
            if not inscripcion_existente:
                nueva_inscripcion = EventRegistration(event_id=event_id, hiker_id=hiker.id)
                db.session.add(nueva_inscripcion)
                db.session.commit()

        return jsonify({'success': True, 'pin': hiker.pin_secreto})

    except Exception as e:
        db.session.rollback()
        print(f"Error registrando caminante: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/agenda')
def agenda():
    # Solo visible para el Superusuario (Directorio global de la Tribu)
    if session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
    return render_template('agenda.html')

@bp.route('/api/admin/fix_database')
def fix_database():
    """
    Ruta de emergencia para inyectar la columna faltante en producción 
    sin consola, sin apagar el servidor y sin perder datos.
    """
    if session.get('role') != 'Superusuario':
        return "Acceso denegado. Debes iniciar sesión como administrador.", 403
    try:
        db.session.execute(text("ALTER TABLE hiker ADD COLUMN fecha_nacimiento DATE"))
        db.session.commit()
        return "<h1>✅ Base de datos actualizada con éxito.</h1><p>La columna 'fecha_nacimiento' fue agregada a tus 10,000 registros de forma segura. Ya puedes ir al formulario y registrar caminantes sin error.</p><a href='/'>Volver al inicio</a>"
    except Exception as e:
        db.session.rollback()
        return f"<h1>⚠️ Resultado</h1><p>{str(e)}</p><p><b>Si el error de arriba dice 'duplicate column name', significa que la columna ya se agregó correctamente y tu base de datos está perfecta.</b></p><a href='/'>Volver al inicio</a>"

@bp.route('/api/admin/hikers')
def admin_get_hikers():
    """
    Ruta para el Directorio CRM con protección contra fallos físicos de la DB.
    Si la columna fecha_nacimiento falta, el API sigue enviando los 10,000 registros
    omitiendo solo ese dato, evitando el error de JSON en el CRM.
    """
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        # Intentamos obtener los caminantes. 
        hikers = Hiker.query.all()
        output = []
        for h in hikers:
            # Escudo de lectura para la columna conflictiva
            f_nac = ""
            try:
                if hasattr(h, 'fecha_nacimiento') and h.fecha_nacimiento:
                    f_nac = h.fecha_nacimiento.strftime('%Y-%m-%d')
            except:
                f_nac = ""

            output.append({
                'id': h.id,
                'cedula': h.cedula,
                'nombre_completo': h.nombre_completo,
                'telefono': h.telefono,
                'tipo_sangre': h.tipo_sangre,
                'fecha_nacimiento': f_nac, 
                'alergias': h.alergias,
                'enfermedades_cronicas': getattr(h, 'enfermedades_cronicas', ""),
                'contacto_emergencia_nombre': h.contacto_emergencia_nombre,
                'contacto_emergencia_telefono': h.contacto_emergencia_telefono,
                'pin_secreto': h.pin_secreto
            })
        return jsonify(output)
        
    except Exception as e:
        # SI LA CONSULTA ORM FALLA TOTALMENTE (SELECT fallido por columna faltante)
        # Lanzamos un salvavidas manual para rescatar los 10,000 registros
        if "no such column: hiker.fecha_nacimiento" in str(e):
            print("EJECUTANDO SALVAVIDAS: Columna fecha_nacimiento no encontrada físicamente.")
            # Consulta SQL pura sin la columna problemática
            sql = text("SELECT id, cedula, nombre_completo, telefono, tipo_sangre, alergias, enfermedades_cronicas, contacto_emergencia_nombre, contacto_emergencia_telefono, pin_secreto FROM hiker")
            result = db.session.execute(sql)
            output = []
            for row in result:
                output.append({
                    'id': row[0], 'cedula': row[1], 'nombre_completo': row[2], 'telefono': row[3],
                    'tipo_sangre': row[4], 'fecha_nacimiento': "", 'alergias': row[5],
                    'enfermedades_cronicas': row[6], 'contacto_emergencia_nombre': row[7],
                    'contacto_emergencia_telefono': row[8], 'pin_secreto': row[9]
                })
            return jsonify(output)
        
        # Si es otro error distinto, devolvemos JSON de error para no romper el frontend
        return jsonify({'error': f"Error crítico en Base de Datos: {str(e)}"}), 500

@bp.route('/api/admin/delete_hiker/<int:hiker_id>', methods=['DELETE'])
def admin_delete_hiker(hiker_id):
    """
    Elimina a un caminante blindado contra errores físicos de base de datos.
    Si falla la carga del objeto por la columna faltante, ejecuta SQL puro.
    """
    if session.get('role') != 'Superusuario':
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        # 1. Intentamos el camino normal (ORM)
        try:
            hiker = Hiker.query.get(hiker_id)
            if hiker:
                # Borramos inscripciones primero para no violar llaves foráneas
                EventRegistration.query.filter_by(hiker_id=hiker_id).delete()
                db.session.delete(hiker)
                db.session.commit()
                return jsonify({'success': True})
        except Exception as e_orm:
            # Si el ORM falla (probablemente por columna fecha_nacimiento no encontrada)
            if "no such column" in str(e_orm):
                print(f"Salvavidas de borrado activado para ID {hiker_id}")
                # 2. Camino de emergencia: SQL Puro
                db.session.rollback() # Limpiamos la sesión fallida
                
                # Borramos inscripciones con SQL
                db.session.execute(text("DELETE FROM event_registration WHERE hiker_id = :id"), {'id': hiker_id})
                # Borramos al caminante con SQL
                db.session.execute(text("DELETE FROM hiker WHERE id = :id"), {'id': hiker_id})
                
                db.session.commit()
                return jsonify({'success': True})
            else:
                raise e_orm # Si es otro error, lo lanzamos al catch externo

        return jsonify({'error': 'Caminante no encontrado'}), 404

    except Exception as e:
        db.session.rollback()
        print(f"ERROR CRÍTICO AL BORRAR: {str(e)}")
        # Siempre devolvemos JSON para evitar el error de parsing en el frontend
        return jsonify({'error': f"Error al eliminar: {str(e)}"}), 500

@bp.route('/api/hiker/pin/<pin>')
def get_hiker_by_pin(pin):
    hiker = Hiker.query.filter_by(pin_secreto=pin).first()
    if hiker:
        f_nac = ""
        try:
            if h.fecha_nacimiento: f_nac = h.fecha_nacimiento.strftime('%Y-%m-%d')
        except: pass
        return jsonify({
            'found': True,
            'nombre_completo': hiker.nombre_completo,
            'cedula': hiker.cedula,
            'telefono': hiker.telefono,
            'tipo_sangre': hiker.tipo_sangre,
            'fecha_nacimiento': f_nac, 
            'alergias': hiker.alergias,
            'enfermedades_cronicas': hiker.enfermedades_cronicas,
            'contacto_emergencia_nombre': hiker.contacto_emergencia_nombre,
            'contacto_emergencia_telefono': hiker.contacto_emergencia_telefono
        })
    return jsonify({'found': False})