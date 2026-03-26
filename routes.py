# routes.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
from models import User, Notification, Event
from users import hash_password, check_password
from db import db
from datetime import datetime
import os
import json
from werkzeug.utils import secure_filename

bp = Blueprint('main', __name__)

@bp.route('/')
def home():
    notifications = Notification.query.all()
    return render_template('home.html', notifications=notifications)

@bp.route('/profile')
def profile():
    """Ruta para visualizar el perfil del usuario logueado."""
    if 'user_id' not in session:
        return redirect(url_for('main.home'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('main.home'))
        
    return render_template('perfil.html', user=user)

@bp.route('/dashboard')
def dashboard():
    """Ruta para el panel de administración exclusivo de Superusuarios."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
        
    return render_template('dashboard.html')

@bp.route('/eventos')
def eventos():
    """Ruta para la creación y gestión de eventos (Solo Superusuarios)."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return redirect(url_for('main.home'))
        
    return render_template('eventos.html')

@bp.route('/detalles_evento/<int:event_id>')
def detalles_evento(event_id):
    """Ruta para ver los detalles completos de un evento público."""
    evento = Event.query.get_or_404(event_id)
    return render_template('ver_evento.html', evento=evento)

@bp.route('/api/get_events')
def get_events():
    """Obtiene los eventos de SQLite para mostrarlos en el Home"""
    events = Event.query.order_by(Event.created_at.desc()).all()
    is_super = session.get('role') == 'Superusuario'
    output = []
    
    for e in events:
        lugar_raw = e.lugar_salida or ''
        logistica_segura = False
        
        # Detectamos el sello invisible en la base de datos
        if lugar_raw.startswith('SEGURO_'):
            logistica_segura = True
            lugar_real = lugar_raw.replace('SEGURO_', '')
            # REGLA DE NEGOCIO: Ocultar Lugar y Hora si es privado y NO ES Superusuario
            if logistica_segura and not is_super:   
                destino_text = "Ver en chat"
                hora_text = "Ver en chat"
            else:
                destino_text = lugar_real
                hora_text = e.hora_salida
        else:
            lugar_real = lugar_raw
            destino_text = lugar_real
            hora_text = e.hora_salida
                
        # NUEVA REGLA PROTEGIDA: Si el precio es 0, texto, o está vacío, mostrar "PENDIENTE"
        try:
            precio_val = int(e.precio) if e.precio else 0
        except (ValueError, TypeError):
            precio_val = 0
            
        if precio_val > 0:
            moneda = e.moneda if e.moneda else ''
            precio_mostrar = f"{moneda}{precio_val}"
        else:
            precio_mostrar = "PENDIENTE"
                
        output.append({
            "id": e.id,
            "poster": f"/static/uploads/{e.poster}" if e.poster else "/static/default.png",
            "nombreLugar": e.nombre_lugar,
            "dificultad": e.dificultad,
            "actividad": e.actividad,
            "precio": precio_mostrar,
            "destino": destino_text,
            "hora_salida": hora_text or "Por definir",
            "logistica_segura": logistica_segura,
            "fecha": e.fecha_unica if e.dias == 1 else f"{e.fecha_inicio} al {e.fecha_regreso}",
            "solo_chat": e.solo_chat, # Se mantiene para control frontend, pero la fecha siempre se renderiza
            "capacidad": e.capacidad
        })
    return jsonify(output)

@bp.route('/api/toggle_espacio/<int:event_id>', methods=['POST'])
def toggle_espacio(event_id):
    """Marca un evento como 'AGOTADO' o lo devuelve a su estado original."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    
    if evento.capacidad and str(evento.capacidad).startswith('AGOTADO_'):
        evento.capacidad = str(evento.capacidad).replace('AGOTADO_', '')
    elif evento.capacidad == 'AGOTADO':
        evento.capacidad = '14-17' 
    else:
        evento.capacidad = f"AGOTADO_{evento.capacidad}"
        
    db.session.commit()
    return jsonify({"success": True})

@bp.route('/api/make_public/<int:event_id>', methods=['POST'])
def make_public(event_id):
    """Remueve todas las restricciones de privacidad (Día y Logística) de un evento."""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    
    # Quitar el sello de seguridad en la base de datos
    if evento.lugar_salida and str(evento.lugar_salida).startswith('SEGURO_'):
        evento.lugar_salida = str(evento.lugar_salida).replace('SEGURO_', '')
        
    db.session.commit()
    return jsonify({"success": True})

@bp.route('/api/create_event', methods=['POST'])
def create_event():
    """Guarda un nuevo evento en SQLite con su imagen poster"""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    try:
        file = request.files.get('poster')
        filename = "default_event.png"
        if file and file.filename != '':
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
        print(f"Error grave al guardar evento: {e}")
        return jsonify({"error": str(e)}), 500

@bp.route('/api/update_event/<int:event_id>', methods=['POST'])
def update_event(event_id):
    """Actualiza un evento existente en SQLite"""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
    
    evento = Event.query.get_or_404(event_id)
    try:
        file = request.files.get('poster')
        if file and file.filename != '':
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
        evento.solo_chat = request.form.get('solo_chat') == 'true'
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
        return jsonify({"error": str(e)}), 500

@bp.route('/api/delete_event/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Elimina un evento de SQLite permanentemente"""
    if 'user_id' not in session or session.get('role') != 'Superusuario':
        return jsonify({"error": "No autorizado"}), 403
        
    evento = Event.query.get_or_404(event_id)
    try:
        db.session.delete(evento)
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# RUTAS DE PWA (PROGRESIVE WEB APP)
# ==========================================
@bp.route('/manifest.json')
def manifest():
    """Genera el manifiesto con el MimeType estricto exigido por Chrome."""
    manifest_data = {
        "name": "Caminatas La Tribu",
        "short_name": "La Tribu",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#ff8c00",
        "icons": [
            {
                "src": "/static/uploads/icons/icon-192x192.jpg",
                "sizes": "192x192",
                "type": "image/jpeg"
            },
            {
                "src": "/static/uploads/icons/icon-512x512.jpg",
                "sizes": "512x512",
                "type": "image/jpeg",
                "purpose": "any maskable"
            }
        ]
    }
    return Response(json.dumps(manifest_data), mimetype='application/manifest+json')

@bp.route('/sw.js')
def sw():
    """Expone el Service Worker en la raíz del sitio para que tenga permisos globales."""
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
        print(f"Error grave en registro: {e}") 
        return jsonify({'error': 'Error interno de base de datos al registrar'}), 500

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
        print(f"Error al actualizar perfil: {e}")
        return jsonify({'error': 'Error interno al guardar los datos'}), 500

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.home'))

# ==========================================
# RUTAS DEL REPRODUCTOR DE MÚSICA
# ==========================================
@bp.route('/reproductor')
def reproductor():
    """Ruta principal para cargar el reproductor de música de La Tribu"""
    return render_template('music.html')

@bp.route('/api/upload_default_logo', methods=['POST'])
def upload_default_logo():
    """Sube y sobrescribe manualmente la imagen logo.png predeterminada."""
    # Permite a los usuarios con sesión subir la imagen
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado. Inicia sesión para subir la imagen."}), 403

    try:
        file = request.files.get('logo')
        if not file or file.filename == '':
            return jsonify({"error": "No se seleccionó ninguna imagen"}), 400

        # Ruta hacia /static/music/
        upload_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'music')
        os.makedirs(upload_path, exist_ok=True)
        
        # Forzamos a que se guarde con el nombre exacto 'logo.png', reemplazando el anterior
        filepath = os.path.join(upload_path, 'logo.png')
        file.save(filepath)

        return jsonify({"success": True})
    except Exception as e:
        print(f"Error al subir logo.png: {e}")
        return jsonify({"error": str(e)}), 500

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
        filename = secure_filename(avatar_file.filename)
        filename = f"user_{u.id}_{filename}"
        static_folder = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
        os.makedirs(static_folder, exist_ok=True)
        avatar_file.save(os.path.join(static_folder, filename))
        u.avatar = f"uploads/{filename}"

    db.session.commit()
    return jsonify({'success': True})